"""Versioned, inspectable heuristics. Hit rates are NOT success or ability scores."""
import re

RULESET_VERSION = "2026.09-v1"
WORDS = [
    ("continue", "继续", r"继续|\bcontinue\b|\bgo on\b"),
    ("help", "帮我", r"帮我|\bhelp me\b"),
    ("need", "需要 / 给我", r"需要|给我|\bi need\b|\bgive me\b"),
    ("look", "看一下 / 查看", r"看一下|查看|\btake a look\b|\binspect\b"),
    ("how", "如何 / 怎么", r"如何|怎么|\bhow\b"),
    ("please", "请 / 请你", r"请(?!求)|\bplease\b"),
    ("again", "再 / 重新", r"重新|再|\bagain\b|\bretry\b"),
    ("why", "为什么 / 为啥", r"为什么|为啥|\bwhy\b"),
    ("optimize", "优化", r"优化|\boptimi[sz]e\b|\bimprove\b"),
    ("direct", "直接", r"直接|\bdirectly\b"),
    ("verify", "验证 / 测试 / 确认", r"验证|测试|确认|核对|\btest\b|\bverify\b|\bconfirm\b"),
    ("constraint", "不要 / 必须 / 仅", r"不要|必须|仅|\bonly\b|\bmust\b|\bdo not\b"),
    ("plan", "规划 / 计划 / 方案", r"规划|计划|方案|\bplan\b|\bdesign\b"),
    ("format", "输出 / 格式", r"输出|格式|\boutput\b|\bformat\b"),
    ("reflect", "总结 / 报告 / 复盘", r"总结|报告|复盘|\bsummary\b|\bretrospective\b|\breport\b"),
]
STAGES = [
    ("goal", "发起 / 目标", r"目标|实现|需求|做一个|帮我|需要|\bgoal\b|\brequirement\b|\bbuild\b"),
    ("plan", "规划 / 拆解", r"计划|规划|方案|拆解|范围|\bplan\b|\bscope\b|\bdesign\b"),
    ("execute", "执行 / 交付", r"执行|运行|实现|交付|修改|生成|部署|\bimplement\b|\brun\b|\bdeliver\b|\bdeploy\b"),
    ("verify", "验证 / 证据", r"验证|测试|证据|核对|确认|\btest\b|\bverify\b|\bevidence\b|\bconfirm\b"),
    ("iterate", "反馈 / 迭代", r"继续|优化|重新|调整|再|修改|\bcontinue\b|\bimprove\b|\brevise\b"),
    ("reflect", "反思 / 收尾", r"复盘|总结|收尾|报告|\bretrospective\b|\bsummary\b|\breport\b"),
]
TOPICS = [
    ("研究 / 建模", r"论文|模型|训练|数据集|\bpaper\b|\bmodel\b|\btrain\b"),
    ("设计 / 产品", r"设计|界面|产品|交互|\bdesign\b|\bUI\b|\bproduct\b"),
    ("工程 / 重构", r"代码|重构|测试|实现|\bcode\b|\brefactor\b|\btest\b"),
    ("部署 / 运维", r"部署|服务器|环境|\bdeploy\b|\bserver\b|\bCI\b"),
    ("编排 / 技能", r"技能|工作流|代理|并行|\bskill\b|\bagent\b|\bworkflow\b"),
]
COMPILED_WORDS = [(key, label, re.compile(p, re.I)) for key, label, p in WORDS]
COMPILED_STAGES = [(key, label, re.compile(p, re.I)) for key, label, p in STAGES]
COMPILED_TOPICS = [(label, re.compile(p, re.I)) for label, p in TOPICS]
BARE_CONTINUE = re.compile(r"^\s*(继续|continue|go on|next)[。.!！\s]*$", re.I)


def word_hits(text: str) -> list[str]:
    return [key for key, _, rx in COMPILED_WORDS if rx.search(text)]


def stage_hits(text: str) -> list[str]:
    return [key for key, _, rx in COMPILED_STAGES if rx.search(text)]
