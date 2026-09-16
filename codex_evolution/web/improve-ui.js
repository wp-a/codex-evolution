/* Browser-local prompts and improvement notes. No model request or server write. */
(() => {
  'use strict';
  const PREFIX = 'codex-evolution-improve-v1:';
  const MAX_ENTRIES = 100;
  const FIELDS = ['goal', 'context', 'scope', 'success'];
  const OUTCOMES = {pending: '待观察', helpful: '有帮助', 'not-helpful': '没有帮助', inconclusive: '暂不确定'};
  const memory = new Map();
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const text = (value, limit = 4000) => typeof value === 'string' ? value.slice(0, limit) : '';
  const finite = value => typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : null;
  const normalizeMode = mode => mode === 'demo' ? 'demo' : 'live';
  const format = value => value == null ? '无记录' : Number(value).toLocaleString('zh-CN', {maximumFractionDigits: 1});
  const percent = value => value == null ? '无记录' : `${format(value)}%`;
  const blankDraft = () => ({adjustment: '', criteria: '', result: ''});
  const fresh = () => ({brief: {goal: '', context: '', scope: '', success: '', prompt: ''}, draft: blankDraft(), entries: [], editingId: '', resultDrafts: new Map(), deletingId: '', warning: ''});

  function cleanBaseline(value) {
    const baseline = value && typeof value === 'object' ? value : {};
    const period = baseline.period && typeof baseline.period === 'object' ? baseline.period : {};
    return {period: {start: text(period.start, 32), end: text(period.end, 32), timezone: text(period.timezone, 80)}, natural_messages: finite(baseline.natural_messages), bare_continue_rate: finite(baseline.bare_continue_rate), verification_rate: finite(baseline.verification_rate)};
  }

  function stateFor(mode) {
    const key = normalizeMode(mode);
    if (memory.has(key)) return memory.get(key);
    const state = fresh();
    try {
      const raw = localStorage.getItem(PREFIX + key);
      if (raw) {
        const saved = JSON.parse(raw);
        if (!saved || typeof saved !== 'object' || saved.version !== 1 || !Array.isArray(saved.entries)) throw new Error('invalid journal');
        for (const field of FIELDS) state.brief[field] = text(saved.brief?.[field]);
        state.brief.prompt = text(saved.brief?.prompt, 18000);
        for (const field of Object.keys(state.draft)) state.draft[field] = text(saved.draft?.[field]);
        const ids = new Set();
        for (const entry of saved.entries.slice(0, MAX_ENTRIES)) {
          if (!entry || typeof entry !== 'object') continue;
          const id = text(entry.id, 100);
          if (!id || ids.has(id) || !text(entry.adjustment).trim() || !text(entry.criteria).trim()) continue;
          ids.add(id);
          state.entries.push({id, created_at: text(entry.created_at, 32), updated_at: text(entry.updated_at, 32), adjustment: text(entry.adjustment), criteria: text(entry.criteria), result: text(entry.result), outcome: Object.hasOwn(OUTCOMES, entry.outcome) ? entry.outcome : 'pending', baseline: cleanBaseline(entry.baseline)});
        }
        const editingId = text(saved.editingId, 100);
        if (state.entries.some(entry => entry.id === editingId)) state.editingId = editingId;
      }
    } catch {
      state.warning = '无法读取浏览器中的改进记录。原保存内容尚未覆盖；你仍可填写新草稿，保存时会重新建立记录。';
    }
    memory.set(key, state);
    return state;
  }

  function snapshot(state) {
    return {version: 1, brief: {...state.brief}, draft: {...state.draft}, editingId: state.editingId, entries: state.entries};
  }

  function persist(mode, state) {
    try {
      localStorage.setItem(PREFIX + normalizeMode(mode), JSON.stringify(snapshot(state)));
      state.warning = '';
      return true;
    } catch {
      state.warning = '浏览器未能保存记录。当前输入仍在本页中，请先导出备份；关闭页面可能丢失尚未保存的内容。';
      return false;
    }
  }

  function baselineFor(analysis) {
    const summary = analysis?.summary || {};
    return cleanBaseline({period: {start: summary.start || '', end: summary.end || '', timezone: analysis?.timezone || ''}, natural_messages: summary.natural_messages, bare_continue_rate: summary.bare_continue_rate, verification_rate: summary.verification_rate});
  }

  function generatePrompt(brief) {
    const labels = {goal: '本次目标', context: '当前上下文与证据', scope: '范围与边界', success: '验收标准'};
    return FIELDS.map(field => `${labels[field]}：\n${brief[field].trim() || '（待补充）'}`).join('\n\n');
  }

  function periodText(baseline) {
    const {start, end, timezone} = baseline.period;
    return start || end ? `${start || '起点未知'} 至 ${end || '终点未知'}${timezone ? ' · ' + timezone : ''}` : '保存时没有可用日期记录';
  }

  function field(name, label, hint, value, rows = 3) {
    return `<label class="improve-field" for="improve-${name}"><span>${escape(label)}</span><textarea id="improve-${name}" data-improve-field="${name}" rows="${rows}" maxlength="${name === 'prompt' ? 18000 : 4000}" placeholder="${escape(hint)}">${escape(value)}</textarea></label>`;
  }

  function recommendationList(analysis) {
    if (!analysis?.summary?.natural_messages) return `<div class="improve-empty"><h3>先定下一个具体目标</h3><p>当前筛选没有自然消息，暂不根据记录提出建议。你可以直接准备任务简报，也可以导入记录后再来看看。</p><button class="btn" data-page="data">导入我的记录</button></div>`;
    return `<ol class="improve-recommendations">${(analysis.recommendations || []).slice(0, 3).map((rec, index) => `<li><span class="improve-step">${String(index + 1).padStart(2, '0')}</span><div><h3>${escape(rec.title)}</h3><p class="improve-reason">${escape(rec.reason)}</p><p>${escape(rec.action)}</p></div><button class="btn small" data-action="improve-adopt" data-improve-index="${index}">试试这个方法 <span aria-hidden="true">↗</span></button></li>`).join('')}</ol>`;
  }

  function entryHTML(entry, state) {
    const draft = state.resultDrafts.get(entry.id) || entry;
    const date = /^\d{4}-\d{2}-\d{2}/.test(entry.created_at) ? entry.created_at.slice(0, 10) : '日期未知';
    return `<article class="improve-entry" data-improve-record="${escape(entry.id)}">
      <div class="improve-entry-head"><div><span class="improve-date">${escape(date)}</span><h3>${escape(entry.adjustment)}</h3></div><span class="badge${entry.outcome === 'helpful' ? ' green' : ''}">${escape(OUTCOMES[entry.outcome])}</span></div>
      <dl class="improve-entry-detail"><div><dt>验收标准</dt><dd>${escape(entry.criteria)}</dd></div><div><dt>开始时的记录</dt><dd><span>${escape(periodText(entry.baseline))}</span><span class="improve-baseline-numbers">${format(entry.baseline.natural_messages)} 条自然消息 · 单独「继续」 ${percent(entry.baseline.bare_continue_rate)} · 验证词 ${percent(entry.baseline.verification_rate)}</span></dd></div></dl>
      <div class="improve-result-grid"><label class="improve-field" for="improve-outcome-${escape(entry.id)}"><span>这次尝试怎么样？</span><select id="improve-outcome-${escape(entry.id)}" data-improve-entry="${escape(entry.id)}" data-improve-result="outcome">${Object.entries(OUTCOMES).map(([key, label]) => `<option value="${key}"${draft.outcome === key ? ' selected' : ''}>${label}</option>`).join('')}</select></label><label class="improve-field" for="improve-result-${escape(entry.id)}"><span>观察结果与依据</span><textarea id="improve-result-${escape(entry.id)}" rows="3" maxlength="4000" data-improve-entry="${escape(entry.id)}" data-improve-result="result" placeholder="记录实际结果，例如：发现了遗漏的验收步骤；也可写下没有改善的原因。">${escape(draft.result)}</textarea></label></div>
      <div class="improve-entry-actions"><button class="btn small" data-action="improve-result-save" data-improve-id="${escape(entry.id)}">保存结果</button><button class="btn ghost small" data-action="improve-edit" data-improve-id="${escape(entry.id)}">编辑尝试</button>${state.deletingId === entry.id ? `<span class="improve-delete-confirm">删除这条记录？</span><button class="btn danger small" data-action="improve-delete-confirm" data-improve-id="${escape(entry.id)}">确认删除</button><button class="btn ghost small" data-action="improve-delete-cancel">取消</button>` : `<button class="btn ghost small" data-action="improve-delete" data-improve-id="${escape(entry.id)}">删除</button>`}</div>
    </article>`;
  }

  function render(analysis, mode) {
    const state = stateFor(mode);
    const baseline = baselineFor(analysis);
    return `<div class="improve-workspace">
      <div class="improve-intro"><p>选一个方法，在下一次任务里试用，回来记录结果。</p><span>仅保存在当前浏览器，结果由你记录。${normalizeMode(mode) === 'demo' ? '演示笔记与个人笔记分开保存。' : '不会自动发送给 Codex 或模型。'}</span></div>
      ${state.warning ? `<div class="notice amber improve-storage-warning" role="status">${escape(state.warning)}</div>` : ''}
      <section class="panel improve-suggestions"><div class="panel-head"><div><h2>从记录中找到一个切入点</h2><p>建议来自当前日期与项目筛选；词面信号只提供线索。</p></div><button class="btn ghost small" data-page="reports">查看复盘依据 <span aria-hidden="true">→</span></button></div><div class="panel-body">${recommendationList(analysis)}</div></section>
      <section class="panel improve-brief"><div class="panel-head"><div><h2>把下一次任务说清楚</h2><p>整理目标、上下文、边界与验收标准，再按你的任务编辑。</p></div><span class="badge">任务简报</span></div><div class="panel-body improve-brief-grid"><div class="improve-brief-fields">${field('goal', '本次目标', '这次希望交付什么？', state.brief.goal)}${field('context', '当前上下文与证据', '已有结果、相关文件、遇到的问题。', state.brief.context)}${field('scope', '范围与边界', '需要处理的范围，以及需要保留的限制。', state.brief.scope)}${field('success', '验收标准', '什么具体结果说明这次任务已经完成？', state.brief.success)}<div class="improve-buttons"><button class="btn primary" data-action="improve-generate">生成任务提示 <span aria-hidden="true">→</span></button><button class="btn" data-action="improve-draft-save">保存草稿</button></div></div><div class="improve-prompt-editor">${field('prompt', '可编辑的任务提示', '填写左侧内容后生成。未填写的项会标为「待补充」。', state.brief.prompt, 15)}<div class="improve-buttons"><button class="btn" data-action="improve-copy">复制任务提示</button><button class="btn ghost small" data-action="improve-prompt-export">导出文本</button></div><p class="improve-hint">生成后可继续编辑。再次生成会更新右侧内容；复制后由你选择粘贴到哪个任务。</p></div></div></section>
      <section class="panel improve-journal" id="improve-journal"><div class="panel-head"><div><h2>${state.editingId ? '编辑这次尝试' : '留下一次改进尝试'}</h2><p>只改变一个做法，更容易在结束时说清楚发生了什么。</p></div><span class="badge">${state.entries.length} 条记录</span></div><div class="panel-body"><div class="improve-compose">${field('adjustment', '这次调整什么', '例如：任务结束时，请 AI 列出实际验证结果和未解决问题。', state.draft.adjustment, 3)}${field('criteria', '用什么判断是否有帮助', '例如：交付说明包含运行过的检查、检查结果与剩余问题。', state.draft.criteria, 3)}</div>${field('result', '目前的观察（可稍后补充）', '这次尝试有什么实际结果？尚未开始可以留空。', state.draft.result, 2)}<p class="improve-baseline-preview">${state.editingId ? '编辑会保留最初保存的基线。' : `保存时附上当前汇总作为基线：${format(baseline.natural_messages)} 条自然消息，${escape(periodText(baseline))}。`}基线是记录背景，不代表效果评分。</p><div class="improve-buttons"><button class="btn primary" data-action="improve-save">${state.editingId ? '保存修改' : '保存这次尝试'}</button>${state.editingId ? '<button class="btn" data-action="improve-edit-cancel">取消编辑</button>' : '<button class="btn ghost small" data-action="improve-draft-save">保存草稿</button>'}</div></div><div class="improve-journal-list">${state.entries.length ? state.entries.map(entry => entryHTML(entry, state)).join('') : '<div class="improve-empty"><h3>你的第一条尝试，从一个小调整开始</h3><p>保存后，你可以标记「有帮助」「没有帮助」或「暂不确定」，并补充实际结果。应用不会自动判断改进是否有效。</p></div>'}</div><div class="panel-foot improve-journal-foot"><span>导出包含你填写的文字和基线汇总。清除浏览器数据或更换地址后，这些笔记可能不可用。</span><button class="btn small" data-action="improve-export">导出改进记录</button></div></section>
    </div>`;
  }

  function handleInput(el, mode) {
    if (!el?.dataset) return false;
    const state = stateFor(mode);
    const name = el.dataset.improveField;
    if (name && (FIELDS.includes(name) || name === 'prompt')) {
      state.brief[name] = text(el.value, name === 'prompt' ? 18000 : 4000);
      return true;
    }
    if (name && Object.hasOwn(state.draft, name)) {
      state.draft[name] = text(el.value);
      return true;
    }
    const entry = state.entries.find(item => item.id === el.dataset.improveEntry);
    const resultField = el.dataset.improveResult;
    if (entry && ['outcome', 'result'].includes(resultField)) {
      const draft = state.resultDrafts.get(entry.id) || {outcome: entry.outcome, result: entry.result};
      if (resultField === 'result') draft.result = text(el.value);
      else if (Object.hasOwn(OUTCOMES, el.value)) draft.outcome = el.value;
      state.resultDrafts.set(entry.id, draft);
      return true;
    }
    return false;
  }

  async function handleAction(action, el, context) {
    if (!action?.startsWith('improve-')) return false;
    const {analysis, mode, render: redraw, toast, copy, downloadText} = context;
    const state = stateFor(mode);
    const id = el?.dataset?.improveId;
    const entry = state.entries.find(item => item.id === id);
    const save = message => {const ok = persist(mode, state); redraw(); toast(ok ? message : state.warning);};
    switch (action) {
      case 'improve-adopt': {
        const index = Number(el.dataset.improveIndex);
        const rec = Number.isInteger(index) && index >= 0 ? analysis?.recommendations?.[index] : null;
        if (!rec || !analysis?.summary?.natural_messages) return true;
        state.editingId = '';
        state.draft = {adjustment: text(rec.action || rec.title), criteria: '', result: ''};
        redraw();
        if (typeof document !== 'undefined') document.getElementById('improve-adjustment')?.focus();
        toast('已填入尝试方法，请补充如何判断是否有帮助。');
        return true;
      }
      case 'improve-generate':
        if (!FIELDS.some(field => state.brief[field].trim())) {toast('先填写至少一项任务信息。'); return true;}
        state.brief.prompt = generatePrompt(state.brief);
        save('任务提示已生成并保存；请检查待补充项。');
        return true;
      case 'improve-draft-save': save('草稿已保存在当前浏览器。'); return true;
      case 'improve-copy':
        if (!state.brief.prompt.trim()) {toast('先生成或填写任务提示。'); return true;}
        await copy(state.brief.prompt);
        return true;
      case 'improve-prompt-export':
        if (!state.brief.prompt.trim()) {toast('先生成或填写任务提示。'); return true;}
        downloadText(state.brief.prompt, `codex-evolution-task-brief-${normalizeMode(mode)}.txt`);
        return true;
      case 'improve-save': {
        if (!state.draft.adjustment.trim() || !state.draft.criteria.trim()) {toast('请填写这次调整和验收标准，再保存尝试。'); return true;}
        const now = new Date().toISOString();
        const editing = state.entries.find(item => item.id === state.editingId);
        if (editing && editing.outcome !== 'pending' && !state.draft.result.trim()) {toast('这条记录已有结果判断，请保留观察依据，或先将判断改为待观察。'); return true;}
        if (!editing && state.entries.length >= MAX_ENTRIES) {toast('已保存 100 条记录。请先导出备份，再删除不再需要的条目。'); return true;}
        if (editing) {Object.assign(editing, state.draft, {updated_at: now}); state.resultDrafts.delete(editing.id);}
        else state.entries.unshift({id: crypto.randomUUID(), created_at: now, updated_at: now, ...state.draft, outcome: 'pending', baseline: baselineFor(analysis)});
        state.draft = blankDraft();
        state.editingId = '';
        save('尝试已保存。任务结束后，回来补充实际结果。');
        return true;
      }
      case 'improve-result-save': {
        if (!entry) return true;
        const draft = state.resultDrafts.get(id) || entry;
        if (draft.outcome !== 'pending' && !draft.result.trim()) {toast('请补充观察结果，让这次判断有据可查。'); return true;}
        entry.outcome = draft.outcome;
        entry.result = draft.result;
        entry.updated_at = new Date().toISOString();
        state.resultDrafts.delete(id);
        save('观察结果已保存。');
        return true;
      }
      case 'improve-edit':
        if (!entry) return true;
        state.editingId = entry.id;
        state.draft = {adjustment: entry.adjustment, criteria: entry.criteria, result: entry.result};
        redraw();
        if (typeof document !== 'undefined') document.getElementById('improve-adjustment')?.focus();
        return true;
      case 'improve-edit-cancel': state.editingId = ''; state.draft = blankDraft(); redraw(); return true;
      case 'improve-delete': state.deletingId = id || ''; redraw(); return true;
      case 'improve-delete-cancel': state.deletingId = ''; redraw(); return true;
      case 'improve-delete-confirm':
        if (!entry || state.deletingId !== id) return true;
        state.entries = state.entries.filter(item => item.id !== id);
        state.resultDrafts.delete(id);
        if (state.editingId === id) {state.editingId = ''; state.draft = blankDraft();}
        state.deletingId = '';
        save('已删除这条改进记录。');
        return true;
      case 'improve-export':
        downloadText(JSON.stringify({format: 'codex-evolution-improvement-journal', ...snapshot(state), entries: state.entries.map(item => ({...item, ...(state.resultDrafts.get(item.id) || {}), unsaved_result: state.resultDrafts.has(item.id)})), mode: normalizeMode(mode), exported_at: new Date().toISOString(), note: '用户自行填写的改进记录；基线为保存时的记录汇总，不代表效果评分。unsaved_result 标记尚未保存的观察草稿。'}, null, 2), `codex-evolution-improvement-${normalizeMode(mode)}.json`, 'application/json;charset=utf-8');
        toast('已导出记录和草稿，包含你填写的文字。');
        return true;
      default: return false;
    }
  }

  window.EvolutionImprove = {render, handleInput, handleAction};
})();
