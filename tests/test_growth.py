import unittest

from codex_evolution.analytics import analyze
from tests.helpers import row


class GrowthDossierTests(unittest.TestCase):
    def test_growth_dossier_uses_pooled_natural_message_rates(self):
        rows = []
        messages = {
            "2026-01-01": ["请你先明确目标", "规划范围"],
            "2026-02-01": ["请继续", "执行修改"],
            "2026-03-01": ["帮我设计方案", "验证证据"],
            "2026-04-01": ["帮我继续", "运行测试"],
            "2026-05-01": ["继续", "确认结果"],
            "2026-06-01": ["继续", "帮我交付"],
        }
        line = 1
        for day, texts in messages.items():
            for text in texts:
                rows.append(row(text, day=day, line=line))
                line += 1

        data = analyze(rows)
        growth = data["growth"]
        comparison = growth["comparison"]

        self.assertTrue(comparison["available"])
        self.assertEqual(comparison["basis"], "pooled_natural_message_rate")
        self.assertEqual(comparison["denominator"], "natural_messages")
        self.assertEqual([len(period["months"]) for period in comparison["periods"]], [2, 2, 2])
        self.assertEqual([period["natural_messages"] for period in comparison["periods"]], [4, 4, 4])
        self.assertEqual(
            [signal["label"] for signal in comparison["signals"]],
            ["请/请你", "帮我", "继续", "自然消息中位长度", "≤20字短提示", "验证/证据", "确认"],
        )
        continue_signal = next(signal for signal in comparison["signals"] if signal["label"] == "继续")
        self.assertEqual(continue_signal["start_rate_pct"], 25.0)
        self.assertEqual(continue_signal["end_rate_pct"], 50.0)
        self.assertEqual(continue_signal["delta_pp"], 25.0)

        matrix = growth["phase_matrix"]
        self.assertEqual(len(matrix["rows"]), 6)
        self.assertEqual(
            [row_data["label"] for row_data in matrix["rows"]],
            ["发起/目标", "规划/拆解", "执行/交付", "验证/证据", "反馈/迭代", "反思/收尾"],
        )
        self.assertTrue(all(cell["denom"] == 2 for row_data in matrix["rows"] for cell in row_data["cells"]))
        self.assertTrue(all(event["heuristic"] for event in growth["evolution"]))
        self.assertEqual(growth["strengths"], [])
        self.assertEqual([field["label"] for field in growth["protocol"]["fields"]], ["目标", "当前状态/证据", "边界", "验收标准"])
        self.assertIn("内容哈希", " ".join(growth["audit"]["avoid"]))

    def test_growth_rates_pool_unequal_months_and_expose_counts(self):
        messages = {
            "2026-01-01": ["请继续"],
            "2026-02-01": ["alpha", "beta", "gamma"],
            "2026-03-01": ["检查复核确认"],
            "2026-04-01": ["delta"],
            "2026-05-01": ["继续继续继续", "epsilon", "zeta"],
            "2026-06-01": ["继续确认"],
        }
        rows = []
        for day, texts in messages.items():
            for text in texts:
                rows.append(row(text, day=day, line=len(rows) + 1))
        rows.append(row("继续确认", day="2026-05-01", role="assistant", line=len(rows) + 1))
        rows.append(row("<environment_context>继续确认</environment_context>", day="2026-05-01", line=len(rows) + 1))

        comparison = analyze(rows)["growth"]["comparison"]
        self.assertEqual([period["label"] for period in comparison["periods"]],
                         ["前期（1–2月）", "中期（3–4月）", "后期（5–6月）"])
        signals = {signal["label"]: signal for signal in comparison["signals"]}
        continuation = signals["继续"]
        self.assertEqual((continuation["start_hits"], continuation["start_denom"], continuation["start_rate_pct"]), (1, 4, 25.0))
        self.assertEqual((continuation["end_hits"], continuation["end_denom"], continuation["end_rate_pct"]), (2, 4, 50.0))
        self.assertEqual((continuation["peak_month"], continuation["peak_hits"], continuation["peak_denom"], continuation["peak_rate_pct"]),
                         ("2026-01", 1, 1, 100.0))
        for label in ("验证/证据", "确认"):
            self.assertEqual((signals[label]["start_hits"], signals[label]["end_hits"], signals[label]["end_denom"]), (0, 1, 4))
        # Phrase unions count a message once even when several phrases match.
        middle_verification = comparison["periods"][1]["phase_rates"]["验证/证据"]
        self.assertEqual(middle_verification, {"hits": 1, "denom": 2, "rate_pct": 50.0})

    def test_growth_endpoints_use_active_months_and_unicode_length_boundary(self):
        rows = [row("甲" * 21, day="2026-01-01")]
        for day, texts in {
            "2026-02-01": ["短", "句", "子"],
            "2026-03-01": ["中"],
            "2026-04-01": ["间"],
            "2026-05-01": ["后"],
            "2026-06-01": ["  " + "甲" * 20 + "  ", "乙" * 21, "🧪" * 19],
        }.items():
            for text in texts:
                rows.append(row(text, day=day, line=len(rows) + 1))

        comparison = analyze(rows, start="2025-12", end="2026-07")["growth"]["comparison"]
        signals = {signal["label"]: signal for signal in comparison["signals"]}
        length = signals["自然消息中位长度"]
        self.assertEqual((length["start_month"], length["end_month"]), ("2026-01", "2026-06"))
        self.assertEqual((length["start_value"], length["end_value"], length["delta"]), (21.0, 20.0, -1.0))
        self.assertIn("start_denom", length)
        self.assertEqual((length["start_denom"], length["end_denom"]), (1, 3))
        self.assertNotEqual(length["start_value"], comparison["periods"][0]["median_chars"])
        short = signals["≤20字短提示"]
        self.assertEqual((short["start_value"], short["end_value"]), (0.0, 66.67))
        self.assertEqual((short["start_hits"], short["end_hits"], short["start_denom"], short["end_denom"]), (0, 2, 1, 3))

    def test_growth_matrix_keeps_gap_months_null_without_creating_periods(self):
        rows = [row("请先写测试再总结", day="2026-01-01"), row("继续", day="2026-04-01", line=2)]
        growth = analyze(rows, start="2025-12", end="2026-05")["growth"]
        self.assertFalse(growth["comparison"]["available"])
        self.assertEqual(growth["comparison"]["periods"], [])
        matrix = growth["phase_matrix"]
        self.assertEqual(matrix["months"], ["2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05"])
        for phase in matrix["rows"]:
            cells = {cell["month"]: cell for cell in phase["cells"]}
            self.assertEqual(cells["2026-02"], {"month": "2026-02", "hits": 0, "denom": 0, "rate_pct": None})
            self.assertEqual(cells["2026-01"]["rate_pct"], 100.0)
        self.assertEqual([event["month"] for event in growth["evolution"]], ["2026-01", "2026-04"])

    def test_growth_timeline_without_hits_does_not_invent_a_focus(self):
        growth = analyze([row("alpha", day="2026-01-01")])["growth"]
        event = growth["evolution"][0]
        self.assertEqual(event["label"], "未命中阶段词组")
        self.assertEqual(event["signals"], [])
        self.assertTrue(event["heuristic"])

    def test_literal_evidence_request_counts_as_verification_signal(self):
        rows = [row("证据", day="2026-01-01"), row("alpha", day="2026-02-01", line=2),
                row("请给出证据", day="2026-03-01", line=3)]
        growth = analyze(rows)["growth"]
        signal = next(signal for signal in growth["comparison"]["signals"] if signal["label"] == "验证/证据")
        self.assertEqual((signal["start_hits"], signal["end_hits"]), (1, 1))
        self.assertEqual((signal["start_rate_pct"], signal["end_rate_pct"]), (100.0, 100.0))
        self.assertIn("验证/证据", growth["evolution"][0]["signals"])

    def test_growth_timeline_is_bounded_and_retains_observed_endpoints(self):
        rows = [row("继续", day=f"2026-{month:02d}-01", line=month) for month in range(1, 10)]
        growth = analyze(rows)["growth"]
        self.assertEqual(len(growth["evolution"]), 6)
        months = [event["month"] for event in growth["evolution"]]
        self.assertEqual(months, sorted(set(months)))
        self.assertEqual((months[0], months[-1]), ("2026-01", "2026-09"))

    def test_empty_growth_has_no_comparison_or_timeline(self):
        growth = analyze([])["growth"]
        self.assertFalse(growth["comparison"]["available"])
        self.assertEqual(growth["comparison"]["periods"], [])
        self.assertEqual(growth["comparison"]["signals"], [])
        self.assertEqual(growth["evolution"], [])
        self.assertEqual(len(growth["phase_matrix"]["rows"]), 6)
        self.assertTrue(all(phase["cells"] == [] for phase in growth["phase_matrix"]["rows"]))

    def test_growth_window_below_three_active_months_is_explicitly_compact(self):
        data = analyze([row("继续", day="2026-01-01"), row("验证", day="2026-02-01", line=2)])
        growth = data["growth"]
        self.assertFalse(growth["comparison"]["available"])
        self.assertEqual(growth["comparison"]["signals"], [])
        self.assertIn("至少需要三个", growth["comparison"]["reason"])
        self.assertEqual(growth["phase_matrix"]["months"], ["2026-01", "2026-02"])


if __name__ == "__main__":
    unittest.main()
