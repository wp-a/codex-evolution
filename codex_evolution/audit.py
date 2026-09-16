"""Conservative static instruction/plan audits. Findings are proposals, never edits."""
from __future__ import annotations
import difflib
import os
import re
from pathlib import Path, PurePosixPath
from typing import Any

APPROVAL = re.compile(r"确认|批准|同意|审批|\bapprov\w*\b|\bconfirm\w*\b|\bpermission\b", re.I)
BLANKET = re.compile(r"每一步|每次(?:操作|修改|执行)|任何(?:操作|修改|动作)|所有(?:操作|修改)|始终|无论|每个阶段|each step|every (?:action|change|step)|any (?:action|change)|always ask", re.I)
NEGATIVE = re.compile(r"不要|不需要|无需|不用|避免|规避|不得|禁止|\bdo not\b|\bdon't\b|\bavoid\b|\bnever\b", re.I)
SENSITIVE = re.compile(r"生产|部署|删除|凭证|密钥|外部发布|付费|支付|破坏|访问权限|production|deploy|delet|credential|secret|publish|payment|destructive", re.I)
INTEGRITY = re.compile(r"供应链|发布制品|下载|完整性|签名|校验和|supply.chain|artifact|integrity|signature|download", re.I)
AUTONOMY = re.compile(r"自主(?:推进|执行|完成)|无需.*确认|不用.*确认|不要.*确认|autonom\w*|without.*confirm|without.*approv", re.I)
UNCERTAIN = re.compile(r"不确定|疑问|uncertain|unclear|ambigu", re.I)
STOP = re.compile(r"停止|暂停|必须询问|先询问|stop|pause|ask", re.I)
HASH = re.compile(r"\bSHA(?:-?256|-?512|-?1)?\b|哈希|\bhash(?:es)?\b", re.I)
GATE = re.compile(r"\bGate\b|闸门|关卡|多轮审核|三轮审核|重复审核|每轮审核", re.I)
FALLBACK = re.compile(r"兜底|fallback", re.I)
PLAN_ONLY = re.compile(r"只(?:给|提供|输出).*?(?:方案|计划)|仅.*(?:方案|计划)|不要执行|plan only|only.*plan", re.I)
COMPLETE = re.compile(r"必须.*(?:实现|完成|交付)|完成实现.*测试|finish.*implement|must.*deliver", re.I)
MAX_AUDIT_FILES = 100
MAX_AUDIT_BYTES = 64 * 1024


def load_files(root: str | Path) -> tuple[list[dict], list[str]]:
    path = Path(root).expanduser().resolve()
    if not path.exists():
        raise ValueError("Instruction path does not exist.")
    warnings = []
    candidates = []
    if path.is_file():
        if path.name not in {"AGENTS.md", "AGENTS.override.md", "SKILL.md"}:
            raise ValueError("Select AGENTS.md, AGENTS.override.md, SKILL.md, or a project folder.")
        candidates = [path]
        base = path.parent
    else:
        base = path
        for folder, dirs, names in os.walk(path, followlinks=False):
            dirs[:] = [d for d in dirs if d not in {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__"}
                       and not (Path(folder) / d).is_symlink()]
            for name in sorted(names):
                f = Path(folder) / name
                if name in {"AGENTS.md", "AGENTS.override.md", "SKILL.md"} and not f.is_symlink():
                    candidates.append(f)
            if len(candidates) > MAX_AUDIT_FILES:
                warnings.append("Only the first 100 instruction files are reviewed; narrow the selected folder.")
                break
    files = []
    for f in sorted(candidates)[:MAX_AUDIT_FILES]:
        try:
            if f.stat().st_size > MAX_AUDIT_BYTES:
                warnings.append(f"Skipped {f.name}: exceeds 64 KiB. Select a smaller instruction file.")
                continue
            files.append({"path": f.relative_to(base).as_posix(), "text": f.read_text(encoding="utf-8-sig")})
        except (OSError, UnicodeError) as exc:
            warnings.append(f"{f.name}: {exc}")
    return files, warnings


def compatible(a: dict, b: dict) -> bool:
    # Different sibling AGENTS scopes are not simultaneous. Skills are conditional.
    if a["path"].endswith("SKILL.md") or b["path"].endswith("SKILL.md"):
        return True
    pa, pb = PurePosixPath(a["path"]).parent, PurePosixPath(b["path"]).parent
    return pa == pb or pa in pb.parents or pb in pa.parents


def audit_instructions(files: list[dict]) -> dict:
    if not isinstance(files, list) or len(files) > MAX_AUDIT_FILES:
        raise ValueError("Provide at most 100 instruction files.")
    validated = []
    for file in files:
        if not isinstance(file, dict) or not isinstance(file.get("text"), str) or not isinstance(file.get("path"), str):
            raise ValueError("Each file requires string path and text fields.")
        if len(file["text"].encode("utf-8")) > MAX_AUDIT_BYTES:
            raise ValueError("An instruction file exceeds 64 KiB.")
        name = PurePosixPath(file["path"]).name
        validated.append({"path": file["path"][:300], "text": file["text"],
                          "kind": "skill" if name == "SKILL.md" else "agents", "active": True})
    paths = {f["path"] for f in validated if f["text"].strip()}
    for f in validated:
        if f["path"].endswith("AGENTS.md"):
            override = str(PurePosixPath(f["path"]).with_name("AGENTS.override.md"))
            if override in paths:
                f["active"] = False
                f["scope_note"] = "Same-directory AGENTS.override.md takes precedence; this file is shadowed."
    findings, protected, lines = [], [], []
    replacements: dict[str, dict[int, str]] = {}

    def add(rule: str, title: str, ref: dict, impact: str, suggestion: str, *, priority: str = "P2",
            expands: bool = False, related: list[dict] | None = None, replacement: str | None = None) -> None:
        item = {"id": f"instruction-{len(findings) + 1}", "rule": rule, "title": title,
                "priority": priority, "path": ref["path"], "line": ref["line"], "quote": ref["quote"],
                "impact": impact, "suggestion": suggestion, "permission_expansion": expands,
                "intent": "needs-review", "confidence": "heuristic", "related": related or []}
        findings.append(item)
        if replacement is not None:
            replacements.setdefault(ref["path"], {}).setdefault(ref["line"], replacement)

    for f in validated:
        if not f["active"]:
            continue
        for number, raw in enumerate(f["text"].splitlines(), 1):
            text = raw.strip()
            if not text or text.startswith("#") or text.startswith("```"):
                continue
            ref = {"path": f["path"], "line": number, "quote": raw, "kind": f["kind"]}
            lines.append(ref)
            is_sensitive = bool(SENSITIVE.search(text))
            is_approval = bool(APPROVAL.search(text))
            protected_here = is_sensitive and is_approval
            if protected_here:
                protected.append(dict(ref, reason="涉及明确批准或高影响操作：保留原规则，不以反冗余名义删除。"))
            if HASH.search(text) and INTEGRITY.search(text) and not NEGATIVE.search(text):
                protected.append(dict(ref, reason="涉及制品/供应链完整性：哈希校验有具体保护对象，应保留。"))
                continue
            if protected_here:
                continue
            if is_approval and BLANKET.search(text) and not NEGATIVE.search(text):
                suggestion = "将常规步骤与受保护动作分开：已授权范围内的低风险、可逆操作可连续推进；显式要求批准的动作仍需批准。此建议会缩小确认范围，必须经你审阅后才可采用。"
                add("blanket-confirmation", "全局确认要求可能打断常规推进", ref,
                    "字面要求可能让读取、局部修改、定向测试也逐步等待。不能仅凭措辞断定这不是你的有意要求。",
                    suggestion, priority="P1", expands=True,
                    replacement="- 在用户已授权的范围内自主推进低风险、可逆的常规步骤；保留所有显式批准要求，范围或授权不明时先澄清。")
            elif UNCERTAIN.search(text) and STOP.search(text) and not NEGATIVE.search(text):
                add("vague-stop", "「有疑问就停止」缺少阻塞条件", ref,
                    "对不影响安全或正确性的细节也可能停止，增加不必要的来回。",
                    "把停止条件限定为：缺失信息会实质影响结果、存在不可逆风险，或授权不明确；其他情况记录合理假设并在既有授权内推进。",
                    expands=True, replacement="- 仅在信息缺失会实质影响正确性、不可逆风险或授权时澄清；其余记录假设，在已授权范围内推进。")
            if HASH.search(text) and BLANKET.search(text) and not NEGATIVE.search(text):
                add("blanket-hash", "哈希要求没有区分保护对象", ref,
                    "每次编辑都做哈希比较可能不提供额外正确性证据，但规则检查不能判断具体业务的完整性要求。",
                    "标明哈希要保证的制品完整性或来源；对普通代码修改采用定向测试和差异检查，保留安全/合规要求。")
        if f["kind"] == "skill":
            fm = re.match(r"\A---\s*\n(.*?)\n---(?:\n|$)", f["text"], re.S)
            if not fm or not all(re.search(rf"(?m)^{name}:\s*\S", fm.group(1)) for name in ("name", "description")):
                add("skill-metadata", "Skill 缺少清晰的发现元数据", {"path": f["path"], "line": 1, "quote": f["text"].splitlines()[0] if f["text"] else ""},
                    "缺少 name 或 description 会影响技能识别；触发条件也无法从元数据审阅。",
                    "添加 YAML frontmatter 的 name 和 description，并在 description 中说明何时触发、何时不触发。")
    broad = [r for r in lines if APPROVAL.search(r["quote"]) and BLANKET.search(r["quote"])
             and not NEGATIVE.search(r["quote"]) and not SENSITIVE.search(r["quote"])]
    auto = [r for r in lines if AUTONOMY.search(r["quote"])]
    for gate in broad:
        other = next((a for a in auto if (a["path"], a["line"]) != (gate["path"], gate["line"]) and compatible(gate, a)), None)
        if other:
            conditional = gate["kind"] == "skill" or other["kind"] == "skill"
            add("autonomy-conflict", "自主推进与逐步确认存在潜在冲突", gate,
                ("仅在相关 Skill 被加载时，" if conditional else "在重叠目录作用域内，") + "两条指令可能同时生效。更具体/更近的规则也可能是有意覆盖，需结合实际工作目录审阅。",
                "明确哪类步骤自主推进、哪类动作必须批准，并写出例外优先级；不要直接删除批准要求。",
                priority="P1", related=[other])
    plan_only = [r for r in lines if PLAN_ONLY.search(r["quote"])]
    completes = [r for r in lines if COMPLETE.search(r["quote"])]
    for p in plan_only:
        c = next((c for c in completes if c != p and compatible(p, c)), None)
        if c:
            add("completion-conflict", "只给计划与必须交付的完成条件不一致", p,
                "一个任务可能在计划阶段停止，也可能超出仅分析的授权；需要限定各自触发条件。",
                "把 analysis-only 和 implementation 两种模式分开：按用户本次要求选择，不能把计划自动当作执行授权。",
                priority="P1", related=[c])
    # Exact duplicate rules only, with real overlap checks. No speculative similarity score.
    seen: dict[str, list[dict]] = {}
    for ref in lines:
        normalized = re.sub(r"[\s\-*>，。,.；;]+", "", ref["quote"]).casefold()
        if len(normalized) < 22:
            continue
        previous = next((p for p in seen.get(normalized, []) if compatible(ref, p)), None)
        if previous and not (APPROVAL.search(ref["quote"]) and SENSITIVE.search(ref["quote"])):
            add("overlapping-duplicate", "重叠作用域出现相同指令", ref,
                "同一规则重复维护会增加漂移风险；Skill 与 AGENTS 的重复仅在该 Skill 激活时形成重叠。",
                "指定唯一维护位置，并在局部文件描述差异或清楚引用它；确保移除重复不会让规则失去原有覆盖范围。",
                related=[previous])
        seen.setdefault(normalized, []).append(ref)
    diffs = []
    for f in validated:
        edits = replacements.get(f["path"], {})
        if not edits:
            continue
        old = f["text"].splitlines(keepends=True)
        new = [edits.get(i, line.rstrip("\r\n")) + ("\n" if line.endswith("\n") else "") for i, line in enumerate(old, 1)]
        diff = "".join(difflib.unified_diff(old, new, fromfile="a/" + f["path"], tofile="b/" + f["path"]))
        diffs.append({"path": f["path"], "diff": diff, "status": "proposal-only", "permission_expansion": True})
    findings.sort(key=lambda f: (f["priority"], f["path"], f["line"]))
    return {"mode": "instructions", "engine": "local-rules", "files": [
        {k: v for k, v in f.items() if k != "text"} for f in validated], "findings": findings,
        "protected": protected, "diffs": diffs,
        "summary": {"files": len(validated), "findings": len(findings), "preserved": len(protected),
                    "permission_expansions": sum(f["permission_expansion"] for f in findings)},
        "limitations": ["这是静态规则预审，不是完整语义证明；未命中不代表没有冲突。",
                        "各目录 AGENTS 不一定同时生效；同目录 override 优先，Skill 仅在激活时加入上下文。",
                        "未读取全局指令、config.toml 的备用文件名、平台策略或运行时已加载指令，除非你显式提供。",
                        "所有 diff 都是供审阅的建议。没有修改文件、安装技能或扩大任何运行权限。"]}


def audit_plan(text: str) -> dict:
    if not isinstance(text, str) or len(text) > 64_000:
        raise ValueError("Provide a plan of at most 64,000 characters.")
    findings, protected = [], []
    for line, raw in enumerate(text.splitlines(), 1):
        value = raw.strip()
        if not value or value.startswith("#"):
            continue
        ref = {"path": "plan.md", "line": line, "quote": raw}
        if APPROVAL.search(value) and SENSITIVE.search(value):
            protected.append(dict(ref, reason="显式高影响操作批准要求，保留。"))
            continue
        if HASH.search(value) and INTEGRITY.search(value) and not NEGATIVE.search(value):
            protected.append(dict(ref, reason="制品完整性校验有明确保护目标，保留。"))
            continue
        if NEGATIVE.search(value):
            continue
        flags = []
        if HASH.search(value):
            flags.append(("hash-purpose", "核实哈希比较是否在保护实际不变量", "明确保护对象；普通编辑优先采用定向测试，制品/供应链校验保留。"))
        if GATE.search(value):
            flags.append(("gate-purpose", "核实重复 Gate / 审核是否提供新证据", "合并目的相同的审核；每道关卡说明独立的风险和完成条件。"))
        if FALLBACK.search(value):
            flags.append(("fallback-purpose", "核实兜底是否有已知失败场景", "保留有明确故障模型的兜底；没有使用路径或证据的分支先延后，而不是直接删除安全机制。"))
        if re.search(r"微服务|事件总线|通用(?:框架|平台)|多代理|microservice|event.bus|multi.agent", value, re.I):
            flags.append(("complexity-purpose", "核实架构复杂度与当前目标是否相称", "先验证单流程或单模块能否满足已知需求；只有独立部署、规模或隔离需求成立时再拆分。"))
        for rule, title, suggestion in flags:
            findings.append(dict(ref, id=f"plan-{len(findings)+1}", rule=rule, title=title, priority="P2",
                                 impact="这是值得核对的线索，不是认定该设计错误；需要结合实际需求与证据。",
                                 suggestion=suggestion, permission_expansion=False, confidence="heuristic", related=[]))
    needs = []
    for label, pattern in [("目标 / 用户价值", r"目标|解决|用户|goal|user"), ("本次范围 / 非目标", r"范围|非目标|不做|scope|out.of.scope"),
                           ("验收 / 完成标准", r"验收|完成标准|可验证|acceptance|done")]:
        if not re.search(pattern, text, re.I):
            needs.append(label)
    return {"mode": "plan", "engine": "local-rules", "files": [{"path": "plan.md", "kind": "plan", "active": True}],
            "findings": findings, "protected": protected, "diffs": [], "missing_context": needs,
            "summary": {"files": 1, "findings": len(findings), "preserved": len(protected), "permission_expansions": 0},
            "limitations": ["反冗余审核不能仅靠关键词判断项目方向；这些是待核实的问题，不是删除清单。",
                            "没有检查完整代码仓库或运行结果；语义深审仅基于你选择的输入。",
                            "没有自动改动任何文件。保留安全、数据完整性与明确批准要求。"]}
