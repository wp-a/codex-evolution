"""Deterministic metrics with denominators, source references and explicit limits."""
from __future__ import annotations
import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .ingest import canonical_messages
from .rules import COMPILED_WORDS, COMPILED_STAGES, COMPILED_TOPICS, RULESET_VERSION, BARE_CONTINUE, stage_hits


# The growth dossier deliberately has a small, inspectable vocabulary.  These
# are message-level surface signals, not an intent model or a performance
# score.  A message matching more than one group is retained in every matching
# group; the groups are allowed to overlap.
GROWTH_TERM_PATTERNS: dict[str, tuple[str, ...]] = {
    "请/请你": ("请你", "请"),
    "帮我": ("帮我",),
    "继续": ("继续",),
    "确认": ("确认",),
}

GROWTH_PHASE_PATTERNS: dict[str, tuple[str, ...]] = {
    "发起/目标": ("帮我", "请你", "请", "需要", "给我", "想要", "如何", "怎么", "为什么", "为啥"),
    "规划/拆解": ("先", "规划", "计划", "步骤", "方案", "拆解", "路线", "优先级", "按照", "根据"),
    "执行/交付": ("创建", "生成", "制作", "写", "实现", "开发", "运行", "部署", "上线", "安装", "配置"),
    "验证/证据": ("检查", "审查", "复核", "核对", "排查", "诊断", "验证", "证据", "测试", "确认", "确定", "复现", "证明", "验收"),
    "反馈/迭代": ("继续", "优化", "改进", "调整", "完善", "收敛", "修改", "改一下", "改成", "改为", "修复", "修一下", "修好", "再", "重新"),
    "反思/收尾": ("总结", "报告", "复盘", "下一步", "教程", "经验"),
}

GROWTH_SIGNAL_ORDER = (
    "请/请你",
    "帮我",
    "继续",
    "自然消息中位长度",
    "≤20字短提示",
    "验证/证据",
    "确认",
)


def pct(n: int, d: int) -> float | None:
    return round(100 * n / d, 2) if d else None


def month_keys(start: str, end: str) -> list[str]:
    y, m = map(int, start.split("-"))
    ey, em = map(int, end.split("-"))
    out = []
    while (y, m) <= (ey, em) and len(out) < 1200:
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def project_label(value: str) -> str:
    # Basename only for display; internal filtering uses an opaque per-analysis key.
    return value.rstrip("/\\").replace("\\", "/").split("/")[-1] or "unassigned"


def prepare(rows: list[dict], tz: str = "UTC") -> tuple[list[dict], int]:
    try:
        zone = timezone.utc if tz == "UTC" else ZoneInfo(tz)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown timezone {tz}; install OS timezone data or choose UTC.") from exc
    # Usage is retained for the dedicated ledger, never as conversation evidence.
    canonical, duplicates = canonical_messages([row for row in rows if row.get("role") != "usage"])
    for r in canonical:
        dt = datetime.fromisoformat(r["timestamp"]).astimezone(zone)
        r["month"] = dt.strftime("%Y-%m")
        r["day"] = dt.strftime("%Y-%m-%d")
    return canonical, duplicates


def select(rows: list[dict], start: str = "", end: str = "", project: str = "") -> list[dict]:
    for value in (start, end):
        if value and not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
            raise ValueError("Month filters must use YYYY-MM.")
    if start and end and start > end:
        raise ValueError("Start month must not be after end month.")
    return [r for r in rows if (not start or r["month"] >= start)
            and (not end or r["month"] <= end) and (not project or r["project"] == project)]


def _growth_patterns_hit(text: str, patterns: tuple[str, ...]) -> bool:
    """Return one message-level hit for a visible phrase union.

    This intentionally uses the already-normalized message text and a literal
    phrase match.  It is kept separate from the general word dictionary so the
    seven growth signals remain easy to inspect and change.
    """
    folded = text.casefold()
    return any(pattern.casefold() in folded for pattern in patterns)


def _growth_rate(records: list[dict], patterns: tuple[str, ...]) -> dict:
    hits = sum(1 for record in records if _growth_patterns_hit(record["text"], patterns))
    return {"hits": hits, "denom": len(records), "rate_pct": pct(hits, len(records))}


def _growth_month_span(months: list[str]) -> str:
    """Format an observed-month span without implying missing months existed."""
    if not months:
        return ""
    if len(months) == 1:
        try:
            return f"{int(months[0][5:7])}月"
        except (ValueError, IndexError):
            return months[0]
    # Keep the full year when an observed span crosses a year boundary.
    if months[0][:4] != months[-1][:4]:
        return f"{months[0]}–{months[-1]}"
    try:
        first = int(months[0][5:7])
        last = int(months[-1][5:7])
        return f"{first}–{last}月"
    except (ValueError, IndexError):
        return f"{months[0]}–{months[-1]}"


def _growth_period_chunks(months: list[str]) -> list[list[str]]:
    """Split active observed months into three contiguous balanced periods."""
    if len(months) < 3:
        return []
    quotient, remainder = divmod(len(months), 3)
    chunks: list[list[str]] = []
    cursor = 0
    for index in range(3):
        size = quotient + (1 if index < remainder else 0)
        chunk = months[cursor:cursor + size]
        if chunk:
            chunks.append(chunk)
        cursor += size
    return chunks if len(chunks) == 3 else []


def _growth_period_summary(index: int, months: list[str], natural_by_month: dict[str, list[dict]]) -> dict:
    records = [record for month in months for record in natural_by_month.get(month, [])]
    period_names = ("前期", "中期", "后期")
    return {
        "label": f"{period_names[index]}（{_growth_month_span(months)}）",
        "months": list(months),
        "natural_messages": len(records),
        "threads": len({record["thread_id"] for record in records}),
        "median_chars": statistics.median(len(record["text"].strip()) for record in records) if records else None,
        "short_le20_pct": pct(sum(len(record["text"].strip()) <= 20 for record in records), len(records)),
        "term_rates": {
            label: _growth_rate(records, patterns)
            for label, patterns in GROWTH_TERM_PATTERNS.items()
        },
        "phase_rates": {
            label: _growth_rate(records, patterns)
            for label, patterns in GROWTH_PHASE_PATTERNS.items()
        },
    }


def _growth_monthly_endpoint(
    *,
    signal_id: str,
    label: str,
    field: str,
    unit: str,
    monthly_by_month: dict[str, dict],
    natural_months: list[str],
    natural_by_month: dict[str, list[dict]],
) -> dict:
    first = monthly_by_month.get(natural_months[0], {})
    last = monthly_by_month.get(natural_months[-1], {})
    start_value = first.get(field)
    end_value = last.get(field)
    # Active months always have a value, but keep a null-safe contract if a
    # caller supplies a legacy/partial monthly row.
    start_value = float(start_value) if start_value is not None else None
    end_value = float(end_value) if end_value is not None else None
    delta = round(end_value - start_value, 2) if start_value is not None and end_value is not None else None
    signal = {
        "id": signal_id,
        "label": label,
        "kind": "monthly_endpoint",
        "start_month": natural_months[0],
        "end_month": natural_months[-1],
        "start_value": start_value,
        "end_value": end_value,
        "start_denom": len(natural_by_month[natural_months[0]]),
        "end_denom": len(natural_by_month[natural_months[-1]]),
        "delta": delta,
        "unit": unit,
    }
    if field == "short_rate":
        signal["start_hits"] = sum(len(record["text"].strip()) <= 20 for record in natural_by_month[natural_months[0]])
        signal["end_hits"] = sum(len(record["text"].strip()) <= 20 for record in natural_by_month[natural_months[-1]])
    return signal


def _growth_signals(
    periods: list[dict],
    monthly: list[dict],
    natural_months: list[str],
    natural_by_month: dict[str, list[dict]],
) -> list[dict]:
    if len(periods) != 3 or not natural_months:
        return []

    first, last = periods[0], periods[-1]
    signals: list[dict] = []
    for signal_id, label in (("request", "请/请你"), ("help", "帮我"), ("continue", "继续")):
        start = first["term_rates"][label]
        end = last["term_rates"][label]
        monthly_rates = [
            (month, _growth_rate(natural_by_month.get(month, []), GROWTH_TERM_PATTERNS[label]))
            for month in natural_months
        ]
        # ``None`` only occurs for an empty month, which cannot be in
        # natural_months; still normalize defensively for hand-built callers.
        available_rates = [(month, rate) for month, rate in monthly_rates if rate["rate_pct"] is not None]
        signal = {
            "id": signal_id,
            "label": label,
            "kind": "term",
            "start_period": first["label"],
            "end_period": last["label"],
            "start_rate_pct": start["rate_pct"],
            "end_rate_pct": end["rate_pct"],
            "delta_pp": round((end["rate_pct"] or 0) - (start["rate_pct"] or 0), 2),
            "start_hits": start["hits"],
            "end_hits": end["hits"],
            "start_denom": start["denom"],
            "end_denom": end["denom"],
            "unit": "%",
        }
        # Only the continuation signal gets a peak in the compact ledger.  A
        # tie resolves to the earliest observed month for stable output.
        if label == "继续" and available_rates:
            peak_month, peak_rate = max(
                available_rates,
                key=lambda item: item[1]["rate_pct"],
            )
            signal["peak_month"] = peak_month
            signal["peak_rate_pct"] = peak_rate["rate_pct"]
            signal["peak_hits"] = peak_rate["hits"]
            signal["peak_denom"] = peak_rate["denom"]
        signals.append(signal)

    verify_start = first["phase_rates"]["验证/证据"]
    verify_end = last["phase_rates"]["验证/证据"]
    signals.append({
        "id": "verification",
        "label": "验证/证据",
        "kind": "phase",
        "start_period": first["label"],
        "end_period": last["label"],
        "start_rate_pct": verify_start["rate_pct"],
        "end_rate_pct": verify_end["rate_pct"],
        "delta_pp": round((verify_end["rate_pct"] or 0) - (verify_start["rate_pct"] or 0), 2),
        "start_hits": verify_start["hits"],
        "end_hits": verify_end["hits"],
        "start_denom": verify_start["denom"],
        "end_denom": verify_end["denom"],
        "unit": "%",
    })

    monthly_by_month = {row["month"]: row for row in monthly}
    signals.append(_growth_monthly_endpoint(
        signal_id="median_chars", label="自然消息中位长度", field="median_length", unit="字",
        monthly_by_month=monthly_by_month, natural_months=natural_months,
        natural_by_month=natural_by_month,
    ))
    signals.append(_growth_monthly_endpoint(
        signal_id="short_le20_pct", label="≤20字短提示", field="short_rate", unit="%",
        monthly_by_month=monthly_by_month, natural_months=natural_months,
        natural_by_month=natural_by_month,
    ))

    confirmation_start = first["term_rates"]["确认"]
    confirmation_end = last["term_rates"]["确认"]
    signals.append({
        "id": "confirmation",
        "label": "确认",
        "kind": "term",
        "start_period": first["label"],
        "end_period": last["label"],
        "start_rate_pct": confirmation_start["rate_pct"],
        "end_rate_pct": confirmation_end["rate_pct"],
        "delta_pp": round((confirmation_end["rate_pct"] or 0) - (confirmation_start["rate_pct"] or 0), 2),
        "start_hits": confirmation_start["hits"],
        "end_hits": confirmation_end["hits"],
        "start_denom": confirmation_start["denom"],
        "end_denom": confirmation_end["denom"],
        "unit": "%",
    })
    signal_order = {label: index for index, label in enumerate(GROWTH_SIGNAL_ORDER)}
    return sorted(signals, key=lambda item: signal_order.get(item["label"], len(signal_order)))


def _growth_phase_matrix(months: list[str], natural_by_month: dict[str, list[dict]]) -> dict:
    rows = []
    for index, (label, patterns) in enumerate(GROWTH_PHASE_PATTERNS.items(), start=1):
        cells = []
        for month in months:
            cells.append({"month": month, **_growth_rate(natural_by_month.get(month, []), patterns)})
        rows.append({"id": f"phase-{index:02d}", "label": label, "cells": cells})
    return {
        "months": list(months),
        "rows": rows,
        "basis": "natural_message_rate",
        "denominator": "natural_messages",
        "overlap": True,
        "heuristic": True,
    }


def _growth_evolution(natural_months: list[str], natural_by_month: dict[str, list[dict]]) -> list[dict]:
    """Select up to six descriptive monthly anchors; never infer causality."""
    if not natural_months:
        return []
    target_count = min(6, len(natural_months))
    positions = {
        round(index * (len(natural_months) - 1) / max(1, target_count - 1))
        for index in range(target_count)
    }
    events = []
    for position in sorted(positions):
        month = natural_months[position]
        records = natural_by_month.get(month, [])
        phase_rates = [
            (label, _growth_rate(records, patterns)["rate_pct"] or 0.0)
            for label, patterns in GROWTH_PHASE_PATTERNS.items()
        ]
        phase_rates.sort(key=lambda item: (-item[1], item[0]))
        focus, focus_rate = phase_rates[0] if phase_rates else ("—", 0.0)
        active = [label for label, rate in phase_rates[:2] if rate > 0]
        events.append({
            "month": month,
            "label": f"阶段焦点：{focus}" if active else "未命中阶段词组",
            "note": (f"该月“{focus}”命中率 {focus_rate:.1f}%；与词面现象一致，不作因果判断。"
                     if active else "该月自然消息未命中阶段词组；不据此推断任务阶段或能力。"),
            "signals": active,
            "heuristic": True,
        })
    return events


def _growth_readout(signals: list[dict], periods: list[dict]) -> dict[str, str]:
    if not periods or not signals:
        return {
            "observed": "自然月份不足三个阶段，暂不生成首尾变化台账。",
            "caution": "短窗口只能描述词面现状，不能形成成长或因果判断。",
            "next": "扩大同一口径的观察窗口，或先记录一个可验收目标。",
        }
    by_label = {item["label"]: item for item in signals}
    short = by_label.get("≤20字短提示")
    verify = by_label.get("验证/证据")
    observed = []
    if short and short.get("start_value") is not None and short.get("end_value") is not None:
        observed.append(f"短提示 {short['start_value']:.1f}→{short['end_value']:.1f}%")
    if verify and verify.get("start_rate_pct") is not None and verify.get("end_rate_pct") is not None:
        observed.append(f"验证/证据 {verify['start_rate_pct']:.1f}→{verify['end_rate_pct']:.1f}%")
    return {
        "observed": "；".join(observed) + "。分母与口径见变化台账。",
        "caution": "词面变化可能来自任务阶段、线程上下文和采集覆盖；它是观察线索，不是能力或因果结论。",
        "next": "长任务节点可选补四行轻协议；短任务不强制，完成后用同一口径复看。",
    }


def _growth_dossier(monthly: list[dict], natural_months: list[str], natural_by_month: dict[str, list[dict]]) -> dict:
    chunks = _growth_period_chunks(natural_months)
    periods = [_growth_period_summary(index, chunk, natural_by_month) for index, chunk in enumerate(chunks)]
    signals = _growth_signals(periods, monthly, natural_months, natural_by_month)
    comparison: dict = {
        "available": len(periods) == 3,
        "basis": "pooled_natural_message_rate",
        "denominator": "natural_messages",
        "overlap": True,
        "periods": periods,
        "signals": signals,
    }
    if len(periods) != 3:
        comparison["reason"] = "至少需要三个有自然消息的月份才能形成三阶段对照。"
    return {
        "comparison": comparison,
        "phase_matrix": _growth_phase_matrix([row["month"] for row in monthly], natural_by_month),
        "evolution": _growth_evolution(natural_months, natural_by_month),
        "readout": _growth_readout(signals, periods),
        # Qualitative strengths are intentionally user-calibrated, not inferred
        # from sparse lexical proxies.
        "strengths": [],
        "protocol": {
            "mode": "optional_checkpoint",
            "fields": [
                {"id": "goal", "label": "目标", "hint": "这次要改变什么？"},
                {"id": "state", "label": "当前状态/证据", "hint": "已有哪条证据？"},
                {"id": "boundary", "label": "边界", "hint": "哪些不做？"},
                {"id": "acceptance", "label": "验收标准", "hint": "什么算完成？"},
            ],
            "note": "长任务节点可用；短任务不强制。",
        },
        "audit": {
            "keep": ["范围与截止点", "一次透明规范化", "异常可见"],
            "avoid": [
                "能力分数、固定门槛与每步 Gate",
                "内容哈希与摘要比对",
                "重复审核、过度设边界、叠加兜底链与因果结论",
            ],
        },
    }


def analyze(raw_rows: list[dict], *, start: str = "", end: str = "", project: str = "",
            tz: str = "UTC", mode: str = "live") -> dict:
    rows, duplicates = prepare(raw_rows, tz)
    projects = sorted({r["project"] for r in rows if r["role"] == "user"})
    months_available = sorted({r["month"] for r in rows if r["role"] == "user"})
    rows = select(rows, start, end, project)
    users = [r for r in rows if r["role"] == "user" and r["natural"]]
    n = len(users)
    grouped = defaultdict(list)
    all_grouped = defaultdict(list)
    for r in users:
        grouped[r["month"]].append(r)
    for r in rows:
        all_grouped[r["month"]].append(r)
    bounds = sorted(grouped)
    months = month_keys(start or bounds[0], end or bounds[-1]) if bounds else []
    # Growth uses only active months with at least one canonical natural user
    # message.  Empty calendar months remain visible in the ordinary monthly
    # series (with null rates), but must not be treated as zero-usage periods.
    natural_months = sorted(grouped)
    lengths = [len(r["text"].strip()) for r in users]
    monthly = []
    for month in months:
        ms = grouped[month]
        words = {key: sum(bool(rx.search(r["text"])) for r in ms) for key, _, rx in COMPILED_WORDS}
        stages = {key: sum(bool(rx.search(r["text"])) for r in ms) for key, _, rx in COMPILED_STAGES}
        topic_counts = [(label, sum(bool(rx.search(r["text"])) for r in ms)) for label, rx in COMPILED_TOPICS]
        top_label, top_count = max(topic_counts, key=lambda t: t[1], default=("暂无证据", 0))
        tools = Counter(r["tool"] for r in all_grouped[month] if r["role"] == "tool" and r["tool"])
        monthly.append({"month": month, "count": len(ms), "threads": len({r["thread_id"] for r in ms}),
                        "words": words, "word_rates": {k: pct(v, len(ms)) for k, v in words.items()},
                        "stages": stages, "stage_rates": {k: pct(v, len(ms)) for k, v in stages.items()},
                        "median_length": statistics.median([len(r["text"].strip()) for r in ms]) if ms else None,
                        "short_rate": pct(sum(len(r["text"].strip()) <= 20 for r in ms), len(ms)),
                        "bare_continue_rate": pct(sum(bool(BARE_CONTINUE.match(r["text"])) for r in ms), len(ms)),
                        "focus": top_label if top_count else "暂无证据", "focus_hits": top_count,
                        "tool_calls": sum(tools.values()), "tools": dict(tools),
                        "sample_size_warning": len(ms) < 30})
    word_totals = [{"key": k, "label": label,
                    "count": sum(bool(rx.search(r["text"])) for r in users)} for k, label, rx in COMPILED_WORDS]
    for word in word_totals:
        word["rate"] = pct(word["count"], n)
    stage_totals = [{"key": k, "label": label,
                     "count": sum(bool(rx.search(r["text"])) for r in users)} for k, label, rx in COMPILED_STAGES]
    for stage in stage_totals:
        stage["rate"] = pct(stage["count"], n)
    change_keys = ["continue", "please", "help", "verify", "reflect", "plan"]
    # Compare disjoint early/late thirds of observed calendar months, weighted by messages.
    width = max(1, len(months) // 3)
    early, late = monthly[:width], monthly[-width:]
    changes = []
    if len(months) >= 2:
        for key in change_keys:
            a_count, b_count = sum(m["count"] for m in early), sum(m["count"] for m in late)
            a_hits, b_hits = sum(m["words"][key] for m in early), sum(m["words"][key] for m in late)
            a, b = pct(a_hits, a_count), pct(b_hits, b_count)
            if a is None or b is None:
                continue
            label = next(label for k, label, _ in COMPILED_WORDS if k == key)
            changes.append({"key": key, "label": label, "early": a, "late": b,
                            "delta_pp": round(b - a, 2), "early_hits": a_hits, "late_hits": b_hits,
                            "early_n": a_count, "late_n": b_count,
                            "early_months": [m["month"] for m in early], "late_months": [m["month"] for m in late],
                            "small_sample": min(a_count, b_count) < 30})
    activity = Counter(r["day"] for r in users)
    evidence_rate = next((s["rate"] for s in stage_totals if s["key"] == "verify"), None)
    bare = sum(bool(BARE_CONTINUE.match(r["text"])) for r in users)
    caveats = [
        "词频是自然用户消息的规则命中率，同条消息同词组最多记一次；词组与阶段可以重叠。",
        "阶段、主题与工作流是词典启发式信号，不是实际任务结果、成功率或个人能力评分。",
        "时间按所选时区归月；空月不等于零命中。早晚阶段用分子/分母加权，不平均月百分比。",
        "短提示可能依赖线程上下文；验证词增加不证明实际执行了测试。",
        "仅覆盖已导入的本机记录，不代表云端账号或其他设备的全量历史。",
    ]
    if mode == "demo":
        caveats.insert(0, "全部数据为固定随机种子生成的合成演示样本，不是你的真实记录。")
    return {
        "schema_version": "1.0", "ruleset_version": RULESET_VERSION, "mode": mode, "timezone": tz,
        "filters": {"start": start, "end": end, "project": project},
        "available_months": months_available,
        "projects": [{"value": p, "label": project_label(p)} for p in projects],
        "summary": {"natural_messages": n, "threads": len({r["thread_id"] for r in users}),
                    "all_records_in_filter": len(rows), "mirrors_removed_all_data": duplicates,
                    "median_length": statistics.median(lengths) if lengths else None,
                    "short_rate": pct(sum(l <= 20 for l in lengths), n),
                    "bare_continue_rate": pct(bare, n), "bare_continue_count": bare,
                    "verification_rate": evidence_rate,
                    "start": min(activity, default=None), "end": max(activity, default=None),
                    "active_days": len(activity), "tool_events": sum(r["role"] == "tool" for r in rows)},
        "monthly": monthly, "words": word_totals, "stages": stage_totals,
        "changes": changes, "activity": dict(sorted(activity.items())),
        "caveats": caveats,
        "recommendations": recommendations(n, bare, stage_totals),
        "growth": _growth_dossier(monthly, natural_months, dict(grouped)),
    }


def recommendations(n: int, bare: int, stages: list[dict]) -> list[dict]:
    rates = {s["key"]: s["rate"] or 0 for s in stages}
    if not n:
        return [{"title": "先导入数据，再作判断", "reason": "当前筛选没有自然用户消息。", "action": "导入本机历史或调整日期与项目筛选。"}]
    out = []
    if bare / n >= .04:
        out.append({"title": "让「继续」带上轻量检查点", "reason": f"当前范围有 {bare} 条单独的继续类提示。上下文可能足够，不代表每条都需要补写。",
                    "action": "仅在阶段切换或方向不明时用：继续。先简述已完成、证据与未决风险，再推进已授权的下一步。"})
    if rates.get("reflect", 0) < 12:
        out.append({"title": "在真正结束时留下收尾记录", "reason": f"收尾词信号命中率为 {rates.get('reflect', 0):.1f}%，不等于实际收尾率。",
                    "action": "任务结束时记录结果、验证方式和剩余问题；不要把每个小步骤都变成一轮审核。"})
    out.append({"title": "把重复流程沉淀为可审阅的 Skill", "reason": "跨线程重复步骤可以提供候选；重复出现并不证明流程有效。",
                "action": "先检查候选的证据线程和适用范围，再保留触发条件、输入、最小步骤及完成标准。"})
    return out[:3]


def evidence(raw_rows: list[dict], *, word: str = "", stage: str = "", month: str = "", query: str = "",
             start: str = "", end: str = "", project: str = "", tz: str = "UTC", offset: int = 0,
             limit: int = 40, thread: str = "") -> dict:
    rows, _ = prepare(raw_rows, tz)
    rows = select(rows, start, end, project)
    if thread:
        matched = [r for r in rows if r["thread_id"] == thread]
    else:
        matched = [r for r in rows if r["role"] == "user" and r["natural"]]
    if month:
        matched = [r for r in matched if r["month"] == month]
    if query:
        matched = [r for r in matched if query.casefold() in r["text"].casefold()]
    for key, rules in ((word, COMPILED_WORDS), (stage, COMPILED_STAGES)):
        if key:
            rx = next((rx for k, _, rx in rules if k == key), None)
            if rx is None:
                raise ValueError("Unknown rule key.")
            matched = [r for r in matched if rx.search(r["text"])]
    total = len(matched)
    if not thread:
        matched = list(reversed(matched))
    items = []
    for i, r in enumerate(matched[max(0, offset):max(0, offset) + min(100, max(1, limit))]):
        items.append({"id": r["uid"], "thread_id": r["thread_id"], "timestamp": r["timestamp"],
                      "month": r["month"], "role": r["role"], "text": r["text"],
                      "source": Path(r["source"]).name, "line": r["line"],
                      "project": project_label(r["project"]), "stages": stage_hits(r["text"]), "tool": r.get("tool", "")})
    return {"total": total, "offset": offset, "items": items}


def mine_workflows(raw_rows: list[dict], *, start: str = "", end: str = "", project: str = "", tz: str = "UTC", min_threads: int = 3) -> list[dict]:
    rows, _ = prepare(raw_rows, tz)
    rows = select(rows, start, end, project)
    threads = defaultdict(list)
    for r in rows:
        if r["role"] == "user" and r["natural"]:
            threads[r["thread_id"]].append(r)
    # One primary intent per prompt, with explicit completion/verification favored.
    priority = ["reflect", "verify", "plan", "execute", "goal", "iterate"]
    patterns = defaultdict(dict)
    labels = {key: label for key, label, _ in COMPILED_STAGES}
    for thread_id, messages in threads.items():
        seq = []
        for r in messages:
            hits = stage_hits(r["text"])
            primary = next((s for s in priority if s in hits), None)
            if primary and (not seq or seq[-1][0] != primary):
                seq.append((primary, r))
        for i in range(max(0, len(seq) - 2)):
            window = seq[i:i + 3]
            key = tuple(x[0] for x in window)
            if len(set(key)) < 3 or "verify" not in key:
                continue
            patterns[key].setdefault(thread_id, [x[1] for x in window])
    ranked = sorted(((k, v) for k, v in patterns.items() if len(v) >= min_threads),
                    key=lambda item: (-len(item[1]), item[0]))[:8]
    candidates = []
    for idx, (key, support) in enumerate(ranked, 1):
        refs = []
        for thread_id, records in list(support.items())[:3]:
            refs.append({"thread_id": thread_id, "messages": [
                {"id": r["uid"], "quote": r["text"][:240], "source": Path(r["source"]).name, "line": r["line"]}
                for r in records]})
        candidates.append({"id": f"workflow-{idx}", "name": " → ".join(labels[s].split(" / ")[0] for s in key),
                           "stages": list(key), "support_threads": len(support), "total_threads": len(threads),
                           "support_rate": pct(len(support), len(threads)), "evidence": refs,
                           "status": "候选 · 未验证成效", "skill": skill_markdown(key, len(support))})
    return candidates


def skill_markdown(stages: tuple[str, ...], count: int) -> str:
    instructions = {
        "goal": "明确用户要交付的结果；先读取现有上下文，不重复询问已有答案。",
        "plan": "限定本次范围、非目标和最小验收标准；只有实质阻塞或权限不清时澄清。",
        "execute": "在已授权范围内执行最小可逆变更，复用现有实现，避免新增冗余兜底和 Gate。",
        "verify": "选择与风险相称的定向验证，给出真实命令、结果与未验证项，不编造通过。",
        "iterate": "结合反馈修正当前实现，不把局部调整扩大成未获授权的重构。",
        "reflect": "汇总交付、验证证据与剩余问题；不要把规划或部分完成称为全部完成。",
    }
    slug = "evolution-" + "-".join(stages)
    steps = "\n".join(f"{i}. {instructions[s]}" for i, s in enumerate(stages, 1))
    return f'''---
name: {slug}
description: Apply a scoped, evidence-backed implementation workflow when the user requests an authorized project change. Do not trigger for open-ended questions or analysis-only requests.
---

# Evidence-backed workflow (review draft)

## Provenance
This candidate pattern appears in {count} imported threads. This is a heuristic
sequence of user-request signals, NOT proof of successful tool execution.
Review the supporting conversations before adopting this draft.

## Inputs
- Goal and current context
- Authorized scope and explicit approval requirements
- A concrete completion criterion

## Minimum workflow
{steps}

## Boundaries and approvals
Preserve all explicit user, project and platform approval requirements.
Never infer permission for deployment, destructive operations, external publishing,
credential access or expanded data access from this skill.
Only ask for clarification when a missing fact blocks correct work or authorization.
If the user requested analysis only, stop at the analysis deliverable.

## Completion
Report what changed, what was actually verified, and remaining blockers.
Do not add blanket per-step confirmations, repeated hashes, or repeated audits.
Retain integrity checks when artifact provenance, security or compliance requires them.

## Adoption
This is a proposal, not an installed skill. Review scope and permissions before
saving it under .agents/skills/{slug}/SKILL.md.
'''
