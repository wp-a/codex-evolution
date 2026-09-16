from pathlib import Path

CATALOG = [
    ("retrospective", "核心复盘指令", "把历史变成协作时间线与可追溯的变化报告。", "01 / REFLECT"),
    ("anti-bloat", "对抗式反冗余审核", "围绕真实需求，核对过度设计、兜底、Gate 与哈希。", "02 / SIMPLIFY"),
    ("instruction-audit", "AGENTS.md / Skill 审计", "定位自主性、澄清、批准与完成条件的潜在冲突。", "03 / ALIGN"),
    ("workflow-to-skill", "稳定工作流 → Skill", "从重复任务里发现可复用流程，生成可审阅草稿。", "04 / COMPOUND"),
    ("checkpoint", "轻量任务检查点", "把必要的「继续」升级为有目标、有边界的推进。", "05 / CONTINUE"),
]


def prompts() -> list[dict]:
    base = Path(__file__).parent / "prompts"
    return [{"id": key, "title": title, "description": description, "tag": tag,
             "text": (base / (key + ".md")).read_text(encoding="utf-8")} for key, title, description, tag in CATALOG]


def get_prompt(key: str) -> str:
    item = next((p for p in prompts() if p["id"] == key), None)
    if not item:
        raise ValueError("Unknown prompt.")
    return item["text"]
