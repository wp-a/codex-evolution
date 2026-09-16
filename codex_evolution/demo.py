"""Deterministic SYNTHETIC data, unrelated to any person's private history."""
from __future__ import annotations
import calendar
import random
from datetime import datetime, timedelta, timezone
from functools import lru_cache

COUNTS = [160, 210, 96, 420, 390, 420, 720, 520, 150]
PROJECTS = ["orbital-web", "vector-lab", "flow-agent", "deploy-kit", "paper-studio"]
LONG = [
    "请你帮我梳理这个项目的需求和目标，先分析现有实现，再给出具体的方案和范围。",
    "请详细解释这段代码为什么会出现问题，给我一份可执行的优化方案，并说明具体原因。",
    "需要设计一个更加清晰的产品界面，保留现有的功能和交互逻辑，输出具体修改建议。",
    "请先看一下现有模型和训练流程，分析数据集的结构，然后再说明有哪些可以改进的地方。",
    "如何将现有服务部署到新的环境？需要哪些准备工作？请结合这个项目给我计划。",
]
SHORT = ["继续", "帮我修改这段代码", "继续优化", "直接实现", "运行测试，给出证据", "看一下结果", "重新调整界面", "为什么测试失败", "确认部署结果", "帮我生成工作流", "继续，先核对当前目标"]
FLOW = ["梳理需求，明确目标", "先规划方案与范围", "实现并运行代码", "验证结果，给出测试证据", "总结本次修改与未决风险"]


@lru_cache(maxsize=1)
def demo_messages() -> list[dict]:
    rng = random.Random(20260906)
    rows: list[dict] = []
    serial = 0
    for month, count in enumerate(COUNTS, 1):
        span = 5 if month == 9 else calendar.monthrange(2026, month)[1]
        for i in range(count):
            serial += 1
            session = f"demo-{month:02d}-{i // 24:03d}"
            day = 1 + min(span - 1, i * span // count)
            dt = datetime(2026, month, day, 8, tzinfo=timezone.utc) + timedelta(minutes=i % 80)
            project = PROJECTS[(i // 24 + month) % len(PROJECTS)]
            if i % 24 < 5:
                text = FLOW[i % 24]
            elif rng.random() < .18 + month * .068:
                text = rng.choice(SHORT)
                if month >= 6 and rng.random() < .22:
                    text = "继续"
            else:
                text = rng.choice(LONG)
            if i % 17 == 0:
                text += "；仅处理当前范围。"
            if month >= 6 and i % 19 == 0:
                text = "核对现在的方向，有没有过度设计或多余 Gate。"
            source = f"synthetic/{session}.jsonl"
            line = (i % 24) * 3 + 1
            rows.append({"uid": f"demo-u-{serial}", "source": source, "line": line,
                         "thread_id": session, "timestamp": dt.isoformat(), "role": "user", "text": text,
                         "channel": "normalized", "project": project, "tool": "", "natural": True})
            rows.append({"uid": f"demo-a-{serial}", "source": source, "line": line + 1,
                         "thread_id": session, "timestamp": (dt + timedelta(seconds=10)).isoformat(),
                         "role": "assistant", "text": "[合成演示] 已完成当前分析，待验证项会单独标注；这不是实际执行证据。",
                         "channel": "normalized", "project": project, "tool": "", "natural": False})
            if i % 24 in {2, 3}:
                rows.append({"uid": f"demo-t-{serial}", "source": source, "line": line + 2,
                             "thread_id": session, "timestamp": (dt + timedelta(seconds=5)).isoformat(),
                             "role": "tool", "text": "[synthetic tool event]", "channel": "normalized",
                             "project": project, "tool": "exec_command" if month < 7 else "spawn_agent", "natural": False})
    return sorted(rows, key=lambda r: (r["timestamp"], r["line"]))
