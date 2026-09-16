/* Recorded Token usage. No model pricing, remote requests, or inferred counts. */
(function () {
  'use strict';

  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
  const known = value => typeof value === 'number' && Number.isFinite(value) && value >= 0;
  const number = value => known(value) ? value.toLocaleString('en-US', {maximumFractionDigits:0}) : '未记录';
  const rows = value => Array.isArray(value) ? value : [];
  const modelName = value => !value || value === 'unknown' ? '未记录模型' : value === 'multiple' ? '多模型' : String(value);
  const providerName = value => !value || value === 'unknown' ? '未记录提供方' : String(value);
  const projectName = value => String(value || '').split(/[\\/]/).filter(Boolean).pop() || '未记录项目';
  const dateLabel = value => value ? String(value).replace('T', ' ').slice(0, 16) : '未记录时间';
  const value = (amount, suffix='') => `<span class="usage-number${known(amount) ? '' : ' usage-missing'}">${number(amount)}</span>${known(amount) && suffix ? `<span class="usage-unit">${esc(suffix)}</span>` : ''}`;

  function metric(title, amount, note, extraClass='') {
    return `<article class="kpi usage-kpi ${extraClass}"><h2 class="kpi-title">${esc(title)}</h2><div class="kpi-value">${value(amount)}</div><p class="kpi-note">${note}</p></article>`;
  }

  function monthlyChart(monthly) {
    if (!monthly.length) return '<p class="usage-empty-note">当前范围没有逐次用量，暂时无法绘制月度趋势。</p>';
    const max = Math.max(1, ...monthly.filter(row => known(row.total_tokens)).map(row => row.total_tokens));
    return `<ol class="usage-months" aria-label="每月记录的总 Token 数">${monthly.map(row => {
      const available = known(row.total_tokens);
      const width = available ? Math.max(0, Math.min(100, row.total_tokens / max * 100)) : 0;
      return `<li class="usage-month${available ? '' : ' is-missing'}"><span class="usage-month-label">${esc(row.month)}</span><span class="usage-month-track" aria-hidden="true">${available ? `<span class="usage-month-bar" style="width:${width.toFixed(3)}%"></span>` : '<span class="usage-month-gap">—</span>'}</span><span class="usage-month-value">${value(row.total_tokens)}<small>${known(row.response_records) ? `${number(row.response_records)} 条记录` : '逐次记录未提供'}</small></span></li>`;
    }).join('')}</ol>`;
  }

  function tokenCell(amount, childAmount, childLabel) {
    return `<td class="usage-numeric">${value(amount)}<small>${esc(childLabel)} ${value(childAmount)}</small></td>`;
  }

  function modelsTable(models) {
    if (!models.length) return '<p class="usage-empty-note">没有可按模型上下文分组的逐次用量记录。</p>';
    return `<div class="usage-table-scroll" role="region" aria-label="按记录中的模型上下文分组，表格可横向滚动" tabindex="0"><table class="usage-table usage-model-table"><thead><tr><th scope="col">模型上下文</th><th scope="col">输入 Token</th><th scope="col">输出 Token</th><th scope="col">总 Token</th><th scope="col">逐次记录</th></tr></thead><tbody>${models.map(row => `<tr><th scope="row"><span class="usage-model-name">${esc(modelName(row.model))}</span><small>${esc(providerName(row.provider))}</small></th>${tokenCell(row.input_tokens, row.cached_input_tokens, '其中缓存')}${tokenCell(row.output_tokens, row.reasoning_output_tokens, '其中推理')}<td class="usage-numeric usage-total">${value(row.total_tokens)}</td><td class="usage-numeric">${value(row.response_records)}</td></tr>`).join('')}</tbody></table></div>`;
  }

  function threadsTable(threads) {
    if (!threads.length) return '<p class="usage-empty-note">当前范围没有可回看的逐次用量线程。</p>';
    return `<div class="usage-table-scroll" role="region" aria-label="高用量线程，表格可横向滚动" tabindex="0"><table class="usage-table usage-thread-table"><thead><tr><th scope="col">项目 / 模型上下文</th><th scope="col">记录时间</th><th scope="col">总 Token</th><th scope="col">逐次记录</th><th scope="col"><span class="usage-sr-only">查看证据</span></th></tr></thead><tbody>${threads.map((row, index) => `<tr><th scope="row"><span class="usage-model-name">${esc(projectName(row.project))}</span><small>${esc(modelName(row.model))}</small></th><td class="usage-dates">${esc(dateLabel(row.start))}<small>至 ${esc(dateLabel(row.end))}</small></td><td class="usage-numeric usage-total">${value(row.total_tokens)}</td><td class="usage-numeric">${value(row.response_records)}</td><td>${row.evidence_thread_id ? `<button class="btn small" data-thread="${esc(row.evidence_thread_id)}" aria-label="查看第 ${index + 1} 个高用量线程原文">回看原文 <span aria-hidden="true">↗</span></button>` : '<span class="usage-missing">未导入可定位的原文</span>'}</td></tr>`).join('')}</tbody></table></div>`;
  }

  function legacyTable(legacy) {
    if (!legacy.length) return '<p class="usage-empty-note">当前范围没有累计快照。</p>';
    return `<div class="usage-table-scroll" role="region" aria-label="累计快照参考，表格可横向滚动" tabindex="0"><table class="usage-table usage-legacy-table"><thead><tr><th scope="col">项目 / 模型上下文</th><th scope="col">快照时间</th><th scope="col">累计输入</th><th scope="col">累计输出</th><th scope="col">快照总数</th><th scope="col"><span class="usage-sr-only">查看证据</span></th></tr></thead><tbody>${legacy.map((row, index) => `<tr><th scope="row"><span class="usage-model-name">${esc(projectName(row.project))}</span><small>${esc(modelName(row.model))}</small>${row.context_fill === true ? '<span class="badge amber">可能是上下文填充</span>' : ''}</th><td class="usage-dates">${esc(dateLabel(row.timestamp))}</td>${tokenCell(row.input_tokens, row.cached_input_tokens, '其中缓存')}${tokenCell(row.output_tokens, row.reasoning_output_tokens, '其中推理')}<td class="usage-numeric">${value(row.total_tokens)}${row.context_fill === true ? '<small>不表示真实消费</small>' : ''}</td><td>${row.evidence_thread_id ? `<button class="btn small" data-thread="${esc(row.evidence_thread_id)}" aria-label="查看第 ${index + 1} 个累计快照线程原文">回看原文 <span aria-hidden="true">↗</span></button>` : '<span class="usage-missing">未导入可定位的原文</span>'}</td></tr>`).join('')}</tbody></table></div>`;
  }

  function render(data) {
    data = data || {};
    const summary = data.summary || {};
    const monthly = rows(data.monthly);
    const models = rows(data.models);
    const threads = rows(data.threads);
    const legacy = rows(data.legacy);
    const coverage = data.coverage || {};
    const hasResponses = known(summary.response_records) && summary.response_records > 0;
    const hasLegacy = legacy.length > 0;
    const caveats = rows(data.caveats).filter(item => typeof item === 'string');
    const coverageFacts = [
      ['尚无逐次用量的线程', coverage.threads_without_response_usage, '个'],
      ['重复用量记录', coverage.duplicate_response_records, '条'],
      ['冲突用量记录', coverage.conflicting_response_records, '条'],
      ['存储内无效用量', coverage.invalid_usage_records, '条'],
      ['提供方归属有歧义（已排除）', coverage.ambiguous_provider_records, '条'],
      ['模型上下文未记录', coverage.unknown_model_records, '条'],
      ['有缓存输入子项', coverage.cached_input_records, '条'],
      ['有推理输出子项', coverage.reasoning_output_records, '条'],
    ].filter(([, amount]) => known(amount));

    return `<div class="usage-page">
      <div class="usage-intro-note"><p><strong>先看用在哪里，再决定怎么调整。</strong>这里统计已导入记录中的 Token；尚未接入服务商账单，不代表账户总用量或实际费用。</p><button class="btn" data-action="export-usage">导出用量 JSON <span aria-hidden="true">↓</span></button></div>
      ${!hasResponses ? `<section class="panel usage-import-state" aria-labelledby="usage-import-title"><span class="usage-state-marker" aria-hidden="true">${hasLegacy ? '部分记录可用' : '从一份用量记录开始'}</span><h2 id="usage-import-title">${hasLegacy ? '已找到累计快照，尚无逐次用量' : '当前范围没有 Token 用量记录'}</h2><p>选择包含用量事件的 rollout JSONL；仅 history.jsonl 没有 Token 记录。也可以调整日期或项目筛选。</p><button class="btn primary" data-page="data">导入用量记录 <span aria-hidden="true">→</span></button></section>` : ''}
      <div class="kpi-grid usage-kpis">
        ${metric('记录的总 Token', summary.total_tokens, '仅汇总逐次用量，累计快照另列。', 'usage-kpi-primary')}
        ${metric('输入 Token', summary.input_tokens, `其中缓存输入 ${value(summary.cached_input_tokens)}<span class="usage-kpi-detail">缓存属于输入子项，不重复相加。</span>`)}
        ${metric('输出 Token', summary.output_tokens, `其中推理输出 ${value(summary.reasoning_output_tokens)}<span class="usage-kpi-detail">推理属于输出子项，不重复相加。</span>`)}
        ${metric('逐次用量记录', summary.response_records, `覆盖 ${value(summary.recorded_threads)}${known(coverage.imported_threads) ? ` / ${number(coverage.imported_threads)}` : ''} 个线程<span class="usage-kpi-detail">一次用量记录不等于一次任务。</span>`)}
      </div>
      <section class="panel usage-section" aria-labelledby="usage-month-title"><div class="panel-head"><div><h2 id="usage-month-title">每月 Token 用量</h2><p>比较记录中的消耗规模。未记录月份保留空档，不补成 0。</p></div><span class="usage-caption">单位：Token</span></div><div class="panel-body">${monthlyChart(monthly)}</div></section>
      <section class="panel usage-section" aria-labelledby="usage-model-title"><div class="panel-head"><div><h2 id="usage-model-title">按模型上下文查看</h2><p>模型名来自会话记录中的上下文，不保证是实际处理请求或计费的模型。</p></div></div><div class="panel-body">${modelsTable(models)}</div></section>
      <section class="panel usage-section" aria-labelledby="usage-thread-title"><div class="panel-head"><div><h2 id="usage-thread-title">用量较高的线程</h2><p>最多展示 20 个线程。回看任务范围与对话，判断消耗是否与任务相称；用量高本身不代表浪费。</p></div><button class="btn ghost" data-page="improve">查看改进建议 <span aria-hidden="true">→</span></button></div><div class="panel-body">${threadsTable(threads)}</div></section>
      <section class="panel usage-section usage-legacy" aria-labelledby="usage-legacy-title"><div class="panel-head"><div><h2 id="usage-legacy-title">旧版累计快照</h2><p>每个线程取当前筛选范围内最新的快照，最多展示 20 个线程。快照单独参考，无法还原逐次消耗，不加入上方总量、月趋势或模型分组。</p></div><span class="badge amber">${number(known(summary.legacy_snapshots) ? summary.legacy_snapshots : legacy.length)} 个线程有快照</span></div><div class="panel-body">${legacyTable(legacy)}</div></section>
      <section class="usage-coverage" aria-labelledby="usage-coverage-title"><h2 id="usage-coverage-title">这份用量覆盖了什么</h2><p>当前筛选范围内，${known(coverage.imported_threads) ? `已导入 ${number(coverage.imported_threads)} 个线程；` : ''}包含 ${value(summary.response_records)} 条逐次用量记录、${value(summary.recorded_threads)} 个有逐次用量的线程，以及 ${number(known(summary.legacy_snapshots) ? summary.legacy_snapshots : legacy.length)} 个有累计快照的线程。</p><p>“未记录”表示没有对应数据或字段不完整，不等于 0。其他设备、未导入会话及未写入本地文件的用量不在此统计中。</p>${coverageFacts.length ? `<dl class="usage-coverage-facts">${coverageFacts.map(([label, amount, unit]) => `<div><dt>${esc(label)}</dt><dd>${number(amount)} <span>${unit}</span></dd></div>`).join('')}</dl>` : ''}<p>“存储内无效用量”只检查已存入本机数据库的记录；导入时被拒绝的记录，请在“导入与隐私”查看最近一次导入诊断。</p>${known(coverage.unlocated_invalid_usage_records) ? `<p class="usage-global-diagnostic"><strong>全导入范围 · 无法归月：</strong>${number(coverage.unlocated_invalid_usage_records)} 条存储用量记录无法定位时间。此项不受当前日期或项目筛选影响。</p>` : ''}${caveats.length ? `<ul>${caveats.map(item => `<li>${esc(item)}</li>`).join('')}</ul>` : ''}</section>
    </div>`;
  }

  window.EvolutionUsage = {render};
})();
