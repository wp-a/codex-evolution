from __future__ import annotations
import csv
import html
import io
import json
from .rules import COMPILED_WORDS, COMPILED_STAGES


_NUMBER = (int, float, type(None))
_RATE_FIELDS = {"hits": _NUMBER, "denom": _NUMBER, "rate_pct": _NUMBER}
_PHASE_LABELS = ("发起/目标", "规划/拆解", "执行/交付", "验证/证据", "反馈/迭代", "反思/收尾")
_GROWTH_FIELDS = {
    "comparison": {
        "available": bool, "basis": str, "denominator": str, "overlap": bool, "reason": str,
        "periods": [{
            "label": str, "months": [str], "natural_messages": _NUMBER, "threads": _NUMBER,
            "median_chars": _NUMBER, "short_le20_pct": _NUMBER,
            "term_rates": {label: _RATE_FIELDS for label in ("请/请你", "帮我", "继续", "确认")},
            "phase_rates": {label: _RATE_FIELDS for label in _PHASE_LABELS},
        }],
        "signals": [{
            "id": str, "label": str, "kind": str, "unit": str,
            "start_period": str, "end_period": str, "start_month": str, "end_month": str,
            "start_rate_pct": _NUMBER, "end_rate_pct": _NUMBER, "delta_pp": _NUMBER,
            "start_value": _NUMBER, "end_value": _NUMBER, "delta": _NUMBER,
            "start_hits": _NUMBER, "end_hits": _NUMBER,
            "start_denom": _NUMBER, "end_denom": _NUMBER,
            "peak_month": str, "peak_rate_pct": _NUMBER, "peak_hits": _NUMBER, "peak_denom": _NUMBER,
        }],
    },
    "phase_matrix": {
        "months": [str], "basis": str, "denominator": str, "overlap": bool, "heuristic": bool,
        "rows": [{"id": str, "label": str, "cells": [{"month": str, **_RATE_FIELDS}]}],
    },
    "evolution": [{"month": str, "label": str, "note": str, "signals": [str], "heuristic": bool}],
    "readout": {"observed": str, "caution": str, "next": str},
    # No qualitative strengths are inferred or exported by this contract.
    "strengths": [],
    "protocol": {"mode": str, "note": str, "fields": [{"id": str, "label": str, "hint": str}]},
    "audit": {"keep": [str], "avoid": [str]},
}
_OMIT = object()


def _allowlist(value, schema):
    """Copy only declared aggregate fields, rejecting unexpected nested types."""
    if isinstance(schema, dict):
        if not isinstance(value, dict):
            return _OMIT
        out = {}
        for key, field in schema.items():
            if key in value:
                selected = _allowlist(value[key], field)
                if selected is not _OMIT:
                    out[key] = selected
        return out
    if isinstance(schema, list):
        if not isinstance(value, list):
            return _OMIT
        if not schema:
            return []
        selected = [_allowlist(item, schema[0]) for item in value]
        return [item for item in selected if item is not _OMIT]
    types = schema if isinstance(schema, tuple) else (schema,)
    return value if type(value) in types else _OMIT


def _public_growth(data: dict) -> dict:
    selected = _allowlist(data.get("growth"), _GROWTH_FIELDS)
    return {} if selected is _OMIT else selected


def public_analysis(data: dict) -> dict:
    """Allowlist: shareable reports omit raw messages, paths, project names and IDs."""
    keys = ["schema_version", "ruleset_version", "mode", "timezone", "summary", "monthly", "words", "stages", "changes", "activity", "caveats", "recommendations"]
    out = {k: data[k] for k in keys if k in data}
    if isinstance(data.get("growth"), dict):
        out["growth"] = _public_growth(data)
    # Still sensitive behavioral aggregates. Not called anonymous or safe automatically.
    return out


def _growth_number(value, unit="", *, signed=False) -> str:
    if value is None:
        return "无数据"
    return f"{value:+g}{unit}" if signed else f"{value:g}{unit}"


def _growth_measure(value, unit, denom=None, hits=None) -> str:
    if denom == 0:
        return "无数据（n=0）"
    measured = _growth_number(value, unit)
    if denom is not None:
        evidence = f"{hits:g}/{denom:g}" if hits is not None else f"n={denom:g}"
        measured += f"（{evidence}）"
    return measured


def _growth_sections(data: dict) -> list[dict]:
    growth = _public_growth(data)
    if not growth:
        return []
    comparison = growth.get("comparison", {})
    if not comparison.get("available"):
        return [{"title": "成长档案 · 观察窗口", "paragraphs": [
            comparison.get("reason", "至少需要三个有自然消息的月份才能形成三阶段对照。"),
            "短窗口只描述已观察到的词面现状，不生成成长或因果判断。",
        ]}]

    periods = comparison.get("periods", [])
    period_rows = [[period.get("label", "—"), "、".join(period.get("months", [])),
                    f"n={period.get('natural_messages', 0)}",
                    _growth_number(period.get("median_chars"), " Unicode 字符"),
                    _growth_number(period.get("short_le20_pct"), "%")] for period in periods]
    ledger = []
    for signal in comparison.get("signals", []):
        endpoint = signal.get("kind") == "monthly_endpoint" or "start_value" in signal
        unit = "%" if signal.get("unit") == "%" else " Unicode 字符"
        start_value = signal.get("start_value" if endpoint else "start_rate_pct")
        end_value = signal.get("end_value" if endpoint else "end_rate_pct")
        start = _growth_measure(start_value, unit, signal.get("start_denom"), signal.get("start_hits"))
        end = _growth_measure(end_value, unit, signal.get("end_denom"), signal.get("end_hits"))
        delta = signal.get("delta" if endpoint else "delta_pp")
        if signal.get("start_denom") == 0 or signal.get("end_denom") == 0 or start_value is None or end_value is None:
            delta = None
        change = _growth_number(delta, " 个百分点" if unit == "%" else " Unicode 字符", signed=True)
        if endpoint:
            basis = f"首尾活跃月 {signal.get('start_month', '—')} → {signal.get('end_month', '—')}"
        else:
            basis = f"合并自然消息 {signal.get('start_period', '前期')} → {signal.get('end_period', '后期')}"
        if signal.get("peak_month"):
            peak = _growth_measure(signal.get("peak_rate_pct"), "%", signal.get("peak_denom"), signal.get("peak_hits"))
            basis += f"；月峰值 {signal['peak_month']}：{peak}"
        ledger.append([signal.get("label", "—"), start, end, change, basis])

    matrix = growth.get("phase_matrix", {})
    months = matrix.get("months", [])
    phase_rows = []
    for phase in matrix.get("rows", []):
        cells = {cell.get("month"): cell for cell in phase.get("cells", [])}
        phase_rows.append([phase.get("label", "—")] + [
            _growth_measure(cells.get(month, {}).get("rate_pct"), "%", cells.get(month, {}).get("denom", 0), cells.get(month, {}).get("hits"))
            for month in months
        ])

    sections = [
        {"title": "三阶段观察范围", "paragraphs": [
            "按活跃月份分为前、中、后三段；段内合并命中数 / 自然消息数，不平均月百分比。首尾月份可能不完整。",
        ], "table": (["阶段", "月份", "自然消息分母", "中位长度", "≤20字短提示"], period_rows)},
        {"title": "变化台账", "paragraphs": [
            "词面命中率以 % 表示，比例差以百分点表示；中位长度与短提示比例比较首尾活跃月。缺少分母时不补造计数。",
        ], "table": (["信号", "起点", "终点", "变化", "比较口径 / 峰值"], ledger)},
        {"title": "任务推进信号", "paragraphs": [
            "六组词面信号可重叠，同一条自然消息可计入多组；不是互斥阶段或实际完成率。单元格为命中率（命中数/自然消息数）；空月为无数据。",
        ], "table": (["任务信号", *months], phase_rows)},
        {"title": "人机协作进化时间线 · 启发式锚点（heuristic）", "paragraphs": [
            "月份锚点由词面规则选取，是描述性线索，不是能力或因果结论。",
        ], "table": (["月份", "启发式锚点", "观察说明"], [
            [event.get("month", "—"), event.get("label", "—") + "（启发式）", event.get("note", "")]
            for event in growth.get("evolution", [])
        ])},
    ]
    readout = growth.get("readout", {})
    sections.append({"title": "观察、解释边界与下一步", "items": [
        f"{label}：{readout[key]}" for key, label in (("observed", "观察"), ("caution", "解释边界"), ("next", "下一步")) if key in readout
    ]})
    protocol = growth.get("protocol", {})
    if protocol.get("fields"):
        sections.append({"title": "四行轻协议 · 可选", "paragraphs": [protocol.get("note", "长任务节点可用；短任务不强制。")],
                         "items": [f"{field.get('label', '—')}：{field.get('hint', '')}" for field in protocol["fields"]]})
    audit = growth.get("audit", {})
    if audit:
        sections.append({"title": "第一性原理审计", "items": [
            "保留：" + "；".join(audit.get("keep", [])), "避免：" + "；".join(audit.get("avoid", [])),
        ]})
    return sections


def _growth_markdown(data: dict) -> list[str]:
    lines = []
    for section in _growth_sections(data):
        lines += ["", "## " + section["title"], ""]
        for paragraph in section.get("paragraphs", []):
            lines += [paragraph, ""]
        if "table" in section:
            headers, rows = section["table"]
            def md_row(cells):
                return "| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", " ") for cell in cells) + " |"
            lines += [md_row(headers), md_row(["---"] * len(headers))]
            lines += [md_row(row) for row in rows]
        lines += ["- " + item for item in section.get("items", [])]
    return lines


def _growth_html(data: dict) -> str:
    e = html.escape
    sections = []
    for section in _growth_sections(data):
        content = f"<section class=\"growth\"><h2>{e(section['title'])}</h2>"
        content += "".join(f"<p>{e(paragraph)}</p>" for paragraph in section.get("paragraphs", []))
        if "table" in section:
            headers, rows = section["table"]
            content += f"<div class=\"table\"><table><caption>{e(section['title'])}</caption><thead><tr>"
            content += "".join(f"<th scope=\"col\">{e(str(header))}</th>" for header in headers) + "</tr></thead><tbody>"
            for row in rows:
                content += "<tr>" + "".join(f"<th scope=\"row\">{e(str(cell))}</th>" if index == 0 else f"<td>{e(str(cell))}</td>" for index, cell in enumerate(row)) + "</tr>"
            content += "</tbody></table></div>"
        if section.get("items"):
            content += "<ul>" + "".join(f"<li>{e(item)}</li>" for item in section["items"]) + "</ul>"
        sections.append(content + "</section>")
    return "".join(sections)


def report_markdown(data: dict, *, include_growth: bool = True) -> str:
    s = data["summary"]
    fmt = lambda v, suffix="": "N/A" if v is None else f"{v}{suffix}"
    lines = ["# Codex Evolution · 人机协作成长报告", "", f"> 数据模式：{'合成演示 / SYNTHETIC DEMO' if data['mode'] == 'demo' else '本机已导入记录'}。不是能力评分或账号全量。", "",
             "## 数据范围", "", f"观察窗口：{s['start']} → {s['end']}；时区：{data['timezone']}。",
             f"自然用户消息：{s['natural_messages']}；自然消息线程：{s['threads']}；活跃天数：{s['active_days']}。",
             f"消息中位长度：{fmt(s['median_length'], ' Unicode 字符')}；≤20 字提示占比：{fmt(s['short_rate'], '%')}。", "",
             "## 高频指令词", "", "| 词组 | 命中数 | 自然消息命中率 |", "|---|---:|---:|"]
    for w in sorted(data["words"], key=lambda w: -w["count"]):
        lines.append(f"| {w['label']} | {w['count']} | {fmt(w['rate'], '%')} |")
    lines += ["", "## 阶段变化（分子 / 分母加权）", ""]
    for c in data["changes"]:
        lines.append(f"- {c['label']}：{c['early']}%（{c['early_hits']}/{c['early_n']}）→ {c['late']}%（{c['late_hits']}/{c['late_n']}），变化 {c['delta_pp']:+.2f} 个百分点。早期 {', '.join(c['early_months'])}；晚期 {', '.join(c['late_months'])}。")
    if not data["changes"]:
        lines.append("观察月份不足两个，暂不进行早晚阶段比较。")
    if not _public_growth(data).get("comparison", {}).get("available"):
        lines += ["", "## 人机协作进化时间线", "", "| 月份 | 自然消息 | 主要主题信号 | 验证词命中率 | 已记录工具事件 |", "|---|---:|---|---:|---:|"]
        for m in data["monthly"]:
            lines.append(f"| {m['month']} | {m['count']} | {m['focus']}（启发式） | {fmt(m['stage_rates']['verify'], '%')} | {m['tool_calls']} |")
    if include_growth:
        lines += _growth_markdown(data)
    lines += ["", "## 下一步协作建议", ""]
    for r in data["recommendations"]:
        lines += [f"### {r['title']}", r["reason"], "", r["action"], ""]
    lines += ["## 统计口径与限制", ""] + [f"- {c}" for c in data["caveats"]]
    lines += ["", f"规则版本：{data['ruleset_version']}。本报告只导出汇总，不包含原始消息、绝对路径、项目名或线程 ID。", "分享前仍应检查行为汇总本身是否敏感。", ""]
    return "\n".join(lines)


def report_csv(data: dict) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["month", "natural_messages", "median_length", "short_rate_pct"] + [k + "_hits" for k, _, _ in COMPILED_WORDS] + [k + "_rate_pct" for k, _, _ in COMPILED_WORDS])
    for m in data["monthly"]:
        writer.writerow([m["month"], m["count"], m["median_length"], m["short_rate"]] + [m["words"][k] for k, _, _ in COMPILED_WORDS] + [m["word_rates"][k] for k, _, _ in COMPILED_WORDS])
    return "\ufeff" + out.getvalue()


def report_html(data: dict) -> str:
    e = html.escape
    s = data["summary"]
    cells = []
    headers = "".join(f"<th>{e(m['month'])}<small>n={m['count']}</small></th>" for m in data["monthly"])
    for k, label, _ in COMPILED_WORDS:
        row = f"<tr><th>{e(label)}</th>"
        for m in data["monthly"]:
            v = m["word_rates"][k]
            opacity = 0 if v is None else min(v / 50, 1)
            row += f'<td style="background:rgba(118,105,255,{.10 + opacity * .85:.2f})" title="{m["words"][k]}/{m["count"]}">{"—" if v is None else f"{v:.0f}%"}</td>'
        cells.append(row + "</tr>")
    # Render the dossier as real tables, without duplicating it in the text appendix.
    markdown = e(report_markdown(data, include_growth=False))
    growth = _growth_html(data)
    demo = "SYNTHETIC DEMO / 合成演示数据" if data["mode"] == "demo" else "LOCAL IMPORT / 本机已导入记录"
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Codex Evolution · Report</title>
<style>body{{margin:0;background:#101116;color:#e7e8f1;font:15px/1.7 system-ui,-apple-system,sans-serif}}main{{max-width:1120px;margin:auto;padding:56px 24px}}h1{{font-size:38px;letter-spacing:-1px}}.label{{color:#aea0ff;font:12px ui-monospace,monospace;letter-spacing:2px}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:28px 0}}.card{{background:#1a1b25;padding:20px;border:1px solid #2d2e3c;border-radius:14px}}b{{display:block;font-size:30px}}.table{{overflow:auto;border-radius:14px;background:#191a23;padding:18px}}table{{border-spacing:5px;width:100%;font-size:12px;white-space:nowrap}}td{{text-align:center;border-radius:4px;padding:9px}}th{{text-align:left;font-weight:500}}small{{display:block;color:#9699ab}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.9 system-ui;background:#191a23;padding:28px;border-radius:14px}}@media(max-width:600px){{.cards{{grid-template-columns:1fr 1fr}}main{{padding:28px 16px}}}}@media print{{body{{background:white;color:black}}.card,.table,pre{{background:white;border:1px solid #ddd}}}}</style>
<main><div class="label">CODEX EVOLUTION / {demo}</div><h1>看见协作的进化。</h1><p>{e(str(s['start']))} — {e(str(s['end']))} · {e(data['timezone'])} · 规则统计，不是能力评分</p>
<div class="cards"><div class="card"><small>自然用户消息</small><b>{s['natural_messages']:,}</b></div><div class="card"><small>对话线程</small><b>{s['threads']}</b></div><div class="card"><small>中位提示长度</small><b>{s['median_length'] or '—'}</b></div><div class="card"><small>验证词信号</small><b>{s['verification_rate'] if s['verification_rate'] is not None else '—'}%</b></div></div>
<h2>指令词趋势热力图</h2><p>含该词组的自然用户消息 / 当月自然用户消息；悬停查看分子与分母。</p><div class="table"><table><thead><tr><th>词组 / 月份</th>{headers}</tr></thead><tbody>{''.join(cells)}</tbody></table></div>
{growth}<h2>基础报告与统计口径</h2><pre>{markdown}</pre><p>Created locally with Codex Evolution · MIT · Independent community project</p></main></html>'''
