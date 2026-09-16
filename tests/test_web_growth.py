import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GrowthWebContractTests(unittest.TestCase):
    def test_report_view_has_growth_dossier_renderers_and_boundaries(self):
        app = (ROOT / "codex_evolution" / "web" / "app.js").read_text(encoding="utf-8")
        for marker in (
            "growthLedger",
            "growthPhaseMatrix",
            "growthEvolution",
            "这份记录说明了什么",
            "提示习惯的变化",
            "任务推进信号",
            "长任务进度模板",
            "哪些流程值得保留",
            "暂无足够数据生成成长档案",
        ):
            self.assertIn(marker, app)

    def test_styles_include_compact_growth_layout_and_focus_states(self):
        css = (ROOT / "codex_evolution" / "web" / "styles.css").read_text(encoding="utf-8")
        for marker in ("growth-ledger", "growth-phase", "growth-evolution", "focus-visible"):
            self.assertIn(marker, css)


if __name__ == "__main__":
    unittest.main()
