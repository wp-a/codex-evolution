import json
import unittest

from codex_evolution.analytics import analyze
from codex_evolution.reports import public_analysis, report_html, report_markdown
from tests.helpers import row


def payload_with_growth():
    # Small synthetic observations, never a copy of a user's calibration metrics.
    messages = {
        "2026-01-01": ["请你先明确目标并提供一份可以复核的详细测试方案", "普通说明"],
        "2026-02-01": ["帮我继续", "执行修改"],
        "2026-03-01": ["继续", "确认测试结果"],
    }
    records = []
    for day, texts in messages.items():
        for text in texts:
            records.append(row(text, day=day, line=len(records) + 1))
    return analyze(records, mode="demo")


class GrowthReportTests(unittest.TestCase):
    def test_public_exports_keep_growth_aggregates_without_raw_fields(self):
        payload = payload_with_growth()
        exported = public_analysis(payload)
        self.assertIn("growth", exported)
        text = json.dumps(exported, ensure_ascii=False)
        for forbidden in ("raw", "source", "thread_id", "/Users/", "hash"):
            self.assertNotIn(forbidden, text.lower())
        self.assertEqual(exported["growth"], payload["growth"])

    def test_growth_allowlist_removes_unknown_fields_at_every_depth(self):
        payload = payload_with_growth()
        private = "PRIVATE_EXPORT_SENTINEL"

        def inject(value):
            if isinstance(value, dict):
                for child in list(value.values()):
                    inject(child)
                value["raw_text"] = private
                value["source"] = "/Users/secret/history.jsonl"
                value["thread_id"] = "secret-thread"
                value["unknown_future_field"] = {"text": private}
            elif isinstance(value, list):
                for child in value:
                    inject(child)

        inject(payload["growth"])
        growth = public_analysis(payload).get("growth", {})
        self.assertIn("comparison", growth)
        for output in (json.dumps(growth), report_markdown(payload), report_html(payload)):
            for secret in (private, "/Users/secret", "secret-thread", "unknown_future_field", "raw_text"):
                self.assertNotIn(secret, output)

    def test_growth_allowlist_rejects_objects_in_scalar_and_string_list_fields(self):
        payload = payload_with_growth()
        private = {"raw_text": "PRIVATE_WRONG_TYPE"}
        payload["growth"]["comparison"]["signals"][0]["label"] = private
        payload["growth"]["comparison"]["signals"][0]["start_rate_pct"] = private
        payload["growth"]["readout"]["observed"] = private
        payload["growth"]["audit"]["keep"].append(private)
        payload["growth"]["strengths"].append(private)
        exported = public_analysis(payload).get("growth", {})
        self.assertIn("comparison", exported)
        self.assertNotIn("PRIVATE_WRONG_TYPE", json.dumps(exported))
        for output in (report_markdown(payload), report_html(payload)):
            self.assertNotIn("PRIVATE_WRONG_TYPE", output)

    def test_markdown_and_html_render_the_evidence_chain(self):
        payload = payload_with_growth()
        markdown = report_markdown(payload)
        rendered = report_html(payload)
        for output in (markdown, rendered):
            for marker in ("变化台账", "任务推进信号", "人机协作进化时间线", "四行轻协议", "第一性原理审计", "50%", "启发式", "heuristic", "可重叠", "不是能力", "可选"):
                self.assertIn(marker, output)
        self.assertIn("pooled_natural_message_rate", json.dumps(public_analysis(payload), ensure_ascii=False))

    def test_full_growth_replaces_the_legacy_monthly_timeline(self):
        payload = payload_with_growth()
        markdown = report_markdown(payload)
        self.assertEqual(markdown.count("## 人机协作进化时间线"), 1)
        output = report_html(payload)
        self.assertNotIn("## 人机协作进化时间线", output)
        self.assertEqual(output.count("<h2>人机协作进化时间线"), 1)

    def test_rates_show_denominators_and_deltas_use_percentage_points(self):
        payload = payload_with_growth()
        signals = payload["growth"]["comparison"]["signals"]
        # Keep report formatting tests independent of analytics precision choices.
        signals[0].update(start_hits=1, end_hits=0, start_denom=2, end_denom=2,
                          start_rate_pct=50, end_rate_pct=0, delta_pp=-50)
        short = next(signal for signal in signals if signal["label"] == "≤20字短提示")
        short.update(start_value=50, end_value=100, delta=50, start_denom=2, end_denom=2)
        for output in (report_markdown(payload), report_html(payload)):
            self.assertIn("50%（1/2）", output)
            self.assertIn("-50 个百分点", output)
            self.assertIn("+50 个百分点", output)
            self.assertIn("Unicode 字符", output)
            self.assertIn("n=2", output)
        self.assertIn("<section", report_html(payload))
        self.assertIn("<caption>变化台账</caption>", report_html(payload))

    def test_zero_denominators_show_unavailable_instead_of_percentages(self):
        payload = payload_with_growth()
        signal = payload["growth"]["comparison"]["signals"][0]
        signal.update(start_rate_pct=0, start_denom=0, start_hits=0, delta_pp=0)
        cell = payload["growth"]["phase_matrix"]["rows"][0]["cells"][0]
        cell.update(rate_pct=0, hits=0, denom=0)
        for output in (report_markdown(payload), report_html(payload)):
            self.assertIn("无数据（n=0）", output)
            self.assertNotIn("0%（0/0）", output)

    def test_short_and_empty_windows_render_only_compact_growth_boundary(self):
        for records in ([], [row("继续")], [row("继续"), row("测试", day="2026-03-01", line=2)]):
            payload = analyze(records)
            for output in (report_markdown(payload), report_html(payload)):
                self.assertIn("至少需要三个", output)
                self.assertNotIn("四行轻协议", output)
                self.assertNotIn("第一性原理审计", output)
                self.assertNotIn("| 信号 |", output)

    def test_growth_html_escapes_visible_labels_and_is_self_contained(self):
        payload = payload_with_growth()
        payload["growth"]["comparison"]["signals"][0]["label"] = '<script>alert("growth")</script>'
        output = report_html(payload)
        self.assertNotIn('<script>alert("growth")', output)
        self.assertIn("&lt;script&gt;", output)
        self.assertNotIn("<script src=", output)
        self.assertNotIn('<link rel="stylesheet"', output)

    def test_legacy_payload_without_growth_still_exports(self):
        payload = payload_with_growth()
        del payload["growth"]
        self.assertNotIn("growth", public_analysis(payload))
        self.assertIn("统计口径", report_markdown(payload))
        self.assertIn("<!doctype html>", report_html(payload))


if __name__ == "__main__":
    unittest.main()
