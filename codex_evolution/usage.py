"""Observed response tokens, separate from legacy context/accounting snapshots.

No prices or account totals are inferred. Importers and exports use allowlists;
ordinary message analytics must not consume these non-natural usage records.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

TOKEN_FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens",
                "reasoning_output_tokens", "total_tokens")
REQUIRED_FIELDS = ("input_tokens", "output_tokens", "total_tokens")
MAX_TOKEN_COUNT = 2**53 - 1
SUMMARY_COUNTS = ("response_records", "recorded_threads", "legacy_snapshots")
COVERAGE_COUNTS = (
    "imported_threads", "threads_with_response_usage", "threads_without_response_usage",
    "response_records", "duplicate_response_records", "conflicting_response_records",
    "ambiguous_provider_records",
    "legacy_threads", "legacy_snapshot_records", "invalid_usage_records",
    "unlocated_invalid_usage_records",
    "unknown_model_records", "cached_input_records", "reasoning_output_records",
)
CAVEATS = (
    "只统计已导入记录中明确提供用量的响应；不是账户总用量、订阅额度或账单。",
    "缓存输入已包含在输入 Token 中，推理输出已包含在输出 Token 中，不重复相加。",
    "模型按记录的模型上下文归属；重路由或压缩时可能不同于实际执行或计费模型。",
    "旧版累计快照单独供参考，不与逐响应用量相加；上下文填充也不视为消费。",
    "没有记录或缺少细分字段时显示未知；没有用量的月份不补为零。",
    "覆盖线程仅指当前导入范围；缺失响应、其他设备和云端历史无法由此推算。",
    "重复响应按提供方、原始线程和响应标识去重；冲突保留排序最前的记录并单独计数。",
    "未知提供方仅在同一响应存在唯一已知提供方时兼容去重；多个提供方有歧义的未知记录不计入总量。",
)
DEMO_CAVEAT = "全部数据为合成演示样本，不是你的真实用量。"


def _count(value):
    return value if type(value) is int and 0 <= value <= MAX_TOKEN_COUNT else None


def _label(value, default="unknown") -> str:
    return value.strip() if isinstance(value, str) and 0 < len(value.strip()) <= 200 else default


def normalize_usage(kind: str, counters, *, provider="unknown", model="unknown",
                    response_id="", evidence_thread_id=None) -> dict | None:
    """Keep supported counters only. Missing optional breakdowns remain unknown."""
    if kind not in {"response", "legacy_snapshot"} or not isinstance(counters, dict):
        return None
    values = {key: _count(counters.get(key)) for key in TOKEN_FIELDS}
    if any(values[key] is None for key in REQUIRED_FIELDS):
        return None
    if any(key in counters and counters[key] is not None and values[key] is None for key in TOKEN_FIELDS):
        return None
    if (values["cached_input_tokens"] is not None
            and values["cached_input_tokens"] > values["input_tokens"]):
        return None
    if (values["reasoning_output_tokens"] is not None
            and values["reasoning_output_tokens"] > values["output_tokens"]):
        return None
    response_id = _label(response_id, "")
    if kind == "response" and not response_id:
        return None
    normalized = {"kind": kind, "provider": _label(provider), "model": _label(model),
                  "response_id": response_id if kind == "response" else "", "counters": values,
                  "evidence_thread_id": _label(evidence_thread_id, "") or None}
    if kind == "legacy_snapshot":
        # Codex can manufacture this shape when marking a full context window.
        # It is retained as a flagged snapshot, never added to observed consumption.
        normalized["context_fill"] = (values["total_tokens"] > 0
                                      and values["input_tokens"] == values["output_tokens"] == 0)
    return normalized


def _token_totals(records: list[dict]) -> dict:
    return {key: sum(r["counters"][key] for r in records)
            if records and all(r["counters"][key] is not None for r in records) else None
            for key in TOKEN_FIELDS}


def _months_between(start: str, end: str) -> list[str]:
    y, m = map(int, start.split("-"))
    ey, em = map(int, end.split("-"))
    result = []
    while (y, m) <= (ey, em) and len(result) < 1200:
        result.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return result


def analyze_usage(raw_rows: list[dict], *, start: str = "", end: str = "", project: str = "",
                  tz: str = "UTC", mode: str = "live") -> dict:
    """Deduplicate complete response records before filtering or aggregating.

    Storage UIDs intentionally remain source-local so replacing one imported
    file cannot delete the surviving copy of a response from a different file.
    """
    for value in (start, end):
        if value and not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
            raise ValueError("Month filters must use YYYY-MM.")
    if start and end and start > end:
        raise ValueError("Start month must not be after end month.")
    try:
        zone = timezone.utc if tz == "UTC" else ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"Unknown timezone {tz}; install OS timezone data or choose UTC.") from exc

    def in_filter(record):
        return ((not start or record["month"] >= start) and (not end or record["month"] <= end)
                and (not project or record["project"] == project))

    prepared, usage_records = [], []
    source_evidence = defaultdict(set)
    invalid = unlocated_invalid = 0
    for row in raw_rows:
        try:
            stamp = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=timezone.utc)
            local_time = stamp.astimezone(zone)
        except (KeyError, TypeError, AttributeError, ValueError, OverflowError):
            unlocated_invalid += row.get("role") == "usage"
            continue
        base = {"thread_id": str(row.get("thread_id", "unknown")),
                "project": str(row.get("project", "unassigned")),
                "timestamp": stamp.astimezone(timezone.utc).isoformat(timespec="milliseconds"),
                "month": local_time.strftime("%Y-%m"),
                "source": str(row.get("source", "")), "line": row.get("line", 0)}
        prepared.append(base)
        if row.get("role") == "user" and row.get("natural"):
            source_evidence[base["source"]].add(base["thread_id"])
        if row.get("role") != "usage":
            continue
        try:
            payload = json.loads(row["text"])
            normalized = normalize_usage(payload.get("kind"), payload.get("counters"),
                                         provider=payload.get("provider"), model=payload.get("model"),
                                         response_id=payload.get("response_id"),
                                         evidence_thread_id=payload.get("evidence_thread_id")) if isinstance(payload, dict) else None
        except (KeyError, TypeError, ValueError, RecursionError):
            normalized = None
        if normalized is None:
            invalid += in_filter(base)
            continue
        usage_records.append(dict(base, **normalized))

    known_providers = defaultdict(set)
    for record in usage_records:
        candidate = record["evidence_thread_id"] or record["thread_id"]
        record["_evidence_threads"] = [candidate] if candidate in source_evidence[record["source"]] else []
        if record["kind"] == "response" and record["provider"] != "unknown":
            known_providers[(record["thread_id"], record["response_id"])].add(record["provider"])

    def evidence_thread(records, owner):
        candidates = {candidate for record in records for candidate in record["_evidence_threads"]}
        if owner in candidates:
            return owner
        return next(iter(candidates)) if len(candidates) == 1 else None

    def order(record):
        return (record["timestamp"], record["source"], str(record["line"]).zfill(12),
                json.dumps(record, sort_keys=True, ensure_ascii=False))

    # Sorting makes the winner independent of upload/query iteration order.
    unique, duplicate_records, conflict_records, ambiguous_records = {}, [], [], []
    snapshots = []
    for record in sorted(usage_records, key=order):
        if record["kind"] == "legacy_snapshot":
            snapshots.append(record)
            continue
        identity = (record["thread_id"], record["response_id"])
        providers = known_providers[identity]
        if record["provider"] == "unknown":
            if len(providers) > 1:
                ambiguous_records.append(record)
                continue
            if len(providers) == 1:
                record["provider"] = next(iter(providers))
        key = (record["provider"], record["thread_id"], record["response_id"])
        if key in unique:
            original = unique[key]
            original["_evidence_threads"] = sorted(set(original["_evidence_threads"] + record["_evidence_threads"]))
            duplicate_records.append(original)
            if record["counters"] != original["counters"]:
                conflict_records.append(original)
        else:
            unique[key] = record
    responses = [record for record in unique.values() if in_filter(record)]
    selected_snapshots = [record for record in snapshots if in_filter(record)]
    latest = {}
    for record in selected_snapshots:
        latest[record["thread_id"]] = record

    all_months = sorted({record["month"] for record in prepared})
    all_projects = sorted({record["project"] for record in prepared})
    selected_months = sorted({record["month"] for record in prepared if in_filter(record)})
    lower = start or (selected_months[0] if selected_months else "")
    upper = end or (selected_months[-1] if selected_months else "")
    months = _months_between(lower, upper) if lower and upper and lower <= upper else []
    monthly_groups, model_groups, thread_groups = defaultdict(list), defaultdict(list), defaultdict(list)
    for record in responses:
        monthly_groups[record["month"]].append(record)
        model_groups[(record["model"], record["provider"])].append(record)
        thread_groups[record["thread_id"]].append(record)
    monthly = [dict(month=month, **_token_totals(monthly_groups[month]),
                    response_records=len(monthly_groups[month])) for month in months]
    models = [dict(model=model, provider=provider, **_token_totals(records), response_records=len(records))
              for (model, provider), records in sorted(model_groups.items())]
    models.sort(key=lambda item: (-(item["total_tokens"] or 0), item["provider"], item["model"]))
    threads = []
    for thread_id, records in thread_groups.items():
        newest = max(records, key=order)
        model_names = sorted({record["model"] for record in records})
        threads.append({"thread_id": thread_id, "project": newest["project"],
                        "evidence_thread_id": evidence_thread(records, thread_id),
                        "model": model_names[0] if len(model_names) == 1 else "multiple",
                        "start": min(record["timestamp"] for record in records),
                        "end": newest["timestamp"], "total_tokens": sum(record["counters"]["total_tokens"] for record in records),
                        "response_records": len(records)})
    threads.sort(key=lambda item: (-item["total_tokens"], item["thread_id"]))
    legacy = [dict(thread_id=record["thread_id"], project=record["project"], model=record["model"],
                   evidence_thread_id=evidence_thread([record], record["thread_id"]),
                   timestamp=record["timestamp"], context_fill=record["context_fill"], **record["counters"])
              for record in sorted(latest.values(), key=order, reverse=True)[:20]]
    imported_threads = {record["thread_id"] for record in prepared if in_filter(record)}
    recorded_threads = {record["thread_id"] for record in responses}
    coverage = {
        "imported_threads": len(imported_threads), "threads_with_response_usage": len(recorded_threads),
        "threads_without_response_usage": len(imported_threads - recorded_threads),
        "response_records": len(responses),
        "duplicate_response_records": sum(in_filter(record) for record in duplicate_records),
        "conflicting_response_records": sum(in_filter(record) for record in conflict_records),
        "ambiguous_provider_records": sum(in_filter(record) for record in ambiguous_records),
        "legacy_threads": len(latest), "legacy_snapshot_records": len(selected_snapshots),
        "invalid_usage_records": invalid,
        "unlocated_invalid_usage_records": unlocated_invalid,
        "unknown_model_records": sum(record["model"] == "unknown" for record in responses),
        "cached_input_records": sum(record["counters"]["cached_input_tokens"] is not None for record in responses),
        "reasoning_output_records": sum(record["counters"]["reasoning_output_tokens"] is not None for record in responses),
    }
    return {"schema_version": "1.0", "mode": mode, "timezone": tz,
            "filters": {"start": start, "end": end, "project": project},
            "summary": dict(_token_totals(responses), response_records=len(responses),
                            recorded_threads=len(recorded_threads), legacy_snapshots=len(latest)),
            "monthly": monthly, "models": models, "threads": threads[:20], "legacy": legacy,
            "available_months": all_months,
            "projects": [{"value": value, "label": value.rstrip("/\\").replace("\\", "/").split("/")[-1] or "unassigned"}
                         for value in all_projects],
            "coverage": coverage, "caveats": ([DEMO_CAVEAT] if mode == "demo" else []) + list(CAVEATS)}


def _public_label(value) -> str:
    """Allow short model/provider slugs, not paths, key-shaped strings or prose."""
    if (isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:+-]{0,99}", value)
            and not value.lower().startswith(("sk-", "sk_", "token-", "secret-"))):
        return value
    return "unknown"


def public_usage(data: dict) -> dict:
    """Export aggregate allowlists only, including nested dictionaries."""
    def numeric(source, fields):
        source = source if isinstance(source, dict) else {}
        return {key: value if type(value := source.get(key)) is int and value >= 0 else None for key in fields}

    summary = numeric(data.get("summary"), TOKEN_FIELDS + SUMMARY_COUNTS)
    monthly = []
    for item in data.get("monthly", []):
        if isinstance(item, dict) and re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", str(item.get("month", ""))):
            monthly.append(dict(month=item["month"], **numeric(item, TOKEN_FIELDS + ("response_records",))))
    models = [dict(model=_public_label(item.get("model")), provider=_public_label(item.get("provider")),
                   **numeric(item, TOKEN_FIELDS + ("response_records",)))
              for item in data.get("models", []) if isinstance(item, dict)]
    zone = data.get("timezone")
    try:
        if not isinstance(zone, str):
            raise ValueError("Missing timezone")
        ZoneInfo(zone)
    except (ZoneInfoNotFoundError, ValueError):
        zone = "unknown"
    filters = data.get("filters") if isinstance(data.get("filters"), dict) else {}
    period = {key: value if isinstance(value := filters.get(key), str)
              and re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value) else "" for key in ("start", "end")}
    if period["start"] and period["end"] and period["start"] > period["end"]:
        period = {"start": "", "end": ""}
    return {"schema_version": "1.0", "mode": data.get("mode") if data.get("mode") in {"live", "demo"} else "unknown",
            "timezone": zone, "period": period, "summary": summary, "monthly": monthly, "models": models,
            "coverage": numeric(data.get("coverage"), COVERAGE_COUNTS),
            "caveats": ([DEMO_CAVEAT] if data.get("mode") == "demo" else []) + list(CAVEATS)}
