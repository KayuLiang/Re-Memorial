const $ = (id) => document.getElementById(id);
const state = { ingredients: [], items: [], category: 'all', sessionId: localStorage.getItem('rm-cooking-session'), result: null, preview: null };
const categories = [['all', '全部'], ['vegetable', '蔬菜'], ['fruit', '水果'], ['meat', '肉类'], ['seafood', '海鲜'], ['mushroom', '菌菇'], ['other', '其他']];
const itemName = (item) => typeof item === 'string' ? item : item.id;

async function api(path, body) {
  const response = await fetch(path, body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
}

function renderFilters() {
  $('filters').innerHTML = categories.map(([id, label]) => `<button type="button" data-category="${id}" class="${state.category === id ? 'active' : ''}" aria-pressed="${state.category === id}">${label}</button>`).join('');
  $('filters').querySelectorAll('button').forEach((button) => button.addEventListener('click', () => {
    state.category = button.dataset.category;
    renderFilters(); renderIngredients();
  }));
}

function renderIngredients() {
  const query = $('search').value.trim();
  const items = state.ingredients.filter((item) => {
    const matches = state.category === 'all' || (state.category === 'other' ? !item.categories.some((c) => ['vegetable', 'fruit', 'meat', 'seafood', 'mushroom'].includes(c)) : item.categories.includes(state.category));
    return matches && item.id.includes(query);
  });
  $('ingredientList').innerHTML = items.length ? items.map((item) => `<button type="button" class="ingredient" data-id="${escapeHtml(item.id)}" ${state.sessionId ? 'disabled' : ''}><span>${escapeHtml(item.id)}</span><span><span class="fixed">FIXED ${item.fixed}</span><span class="plus" aria-hidden="true">+</span></span></button>`).join('') : '<p class="empty">没有匹配的食材。</p>';
  $('ingredientList').querySelectorAll('button').forEach((button) => button.addEventListener('click', () => { state.items.push(button.dataset.id); changed(); }));
}

function renderTray() {
  $('potCount').textContent = `${state.items.length} 份`;
  $('trayHint').textContent = state.sessionId ? '本锅已固定投料' : '点击食材可重复投入';
  $('tray').innerHTML = state.items.length ? state.items.map((item, index) => `<button type="button" data-index="${index}" ${state.sessionId ? 'disabled' : ''} aria-label="移除 ${escapeHtml(itemName(item))}">${escapeHtml(itemName(item))} <span aria-hidden="true">×</span></button>`).join('') : '<p class="empty">锅中还没有食材。</p>';
  $('tray').querySelectorAll('button').forEach((button) => button.addEventListener('click', () => { state.items.splice(Number(button.dataset.index), 1); changed(); }));
}

function renderPreview() {
  const view = state.preview;
  $('targetValue').textContent = view?.target ?? '—';
  if (!view) { $('preview').innerHTML = '<p class="empty">尚未投料。点击食材开始。</p>'; return; }
  if (view.kind === 'processed') {
    $('preview').innerHTML = `<div class="candidate"><strong>${escapeHtml(view.item.id)}</strong><div class="status">单料加工 · Fixed ${view.item.fixed}</div></div>`;
    return;
  }
  if (view.kind === 'wet_goop_no_recipe') {
    $('preview').innerHTML = '<p class="pending">没有合法菜谱，进入潮湿黏糊分支。WetGoopTarget 仍为【配置待补】，暂不能确认。</p>';
    return;
  }
  $('preview').innerHTML = view.candidates.map((c) => `<div class="candidate"><strong>${escapeHtml(c.name)}</strong><div class="meta"><span>${escapeHtml(c.spec || '规格待补')}</span><span>冲突 ${c.conflict}</span><span>目标 ${c.target ?? '待补'}</span><span>预算 ${c.budget ?? '待补'}</span></div><div class="status">${escapeHtml(c.status)}</div></div>`).join('') + (view.target === null ? '<p class="pending">候选菜的 Target/规格仍待配置，暂不能确认。</p>' : '');
}

function renderResult() {
  const result = state.result;
  $('stateText').textContent = result?.status === 'cooked' ? '本锅已结算' : result?.status === 'processed' ? '加工完成' : result?.status === 'configuration_pending' ? '配置待补' : result?.status === 'insufficient_energy' ? '精力不足' : '等待烹饪';
  if (!result) { $('result').innerHTML = '<p class="empty">检定结果会留在此处。退出或刷新后，同一锅的随机结果不会重抽。</p>'; return; }
  if (result.status === 'configuration_pending') { $('result').innerHTML = `<p class="pending">${escapeHtml(result.reason)} 仍待策划配置。本锅保留，可以在配置完成后再结算。</p>`; return; }
  if (result.status === 'insufficient_energy') { $('result').innerHTML = `<p class="pending">本次需要 ${result.energy_cost} 点精力。调整试玩参数后可继续。</p>`; return; }
  if (result.status === 'processed') { $('result').innerHTML = `<div class="dish-quality">INGREDIENT PROCESSING</div><div class="dish-name">${escapeHtml(result.item.id)}</div><p class="empty">保留原料 Fixed ${result.item.fixed}，可在下一锅继续使用。</p><button class="carry-button" id="carryButton" type="button">带入下一锅 ↗</button>`; $('carryButton').addEventListener('click', () => reset([result.item])); return; }
  if (result.status !== 'cooked') { $('result').innerHTML = `<p class="pending">${escapeHtml(result.status)}</p>`; return; }
  const format = (value) => value == null ? '待补' : value;
  $('result').innerHTML = `<div class="dish-quality">${escapeHtml(result.quality)} · ${result.large_portion ? '大份量' : '单份'}</div><div class="dish-name">${escapeHtml(result.name)}</div><dl class="result-grid"><div><dt>COOK SCORE / TARGET</dt><dd>${format(result.score)} / ${format(result.target)}</dd></div><div><dt>RESULT RANK</dt><dd>${escapeHtml(result.rank || '—')}</dd></div><div><dt>BASE / FINAL BUDGET</dt><dd>${format(result.base_budget)} / ${format(result.final_budget)}</dd></div><div><dt>SATIETY / XP</dt><dd>${format(result.satiety)} / ${format(result.xp_delta)}</dd></div></dl><p class="empty">骰面：${result.rolls.join(' + ')}。效果具体内容仍待配置。</p>`;
}

let previewGeneration = 0;
async function changed() {
  renderTray(); renderIngredients();
  const generation = ++previewGeneration;
  if (!state.items.length) { state.preview = null; renderPreview(); return; }
  try {
    const view = await api('/api/preview', { items: state.items });
    if (generation === previewGeneration) { state.preview = view; renderPreview(); }
  } catch (error) { if (generation === previewGeneration) $('preview').innerHTML = `<p class="pending">${escapeHtml(error.message)}</p>`; }
}

function selectedDice() {
  return [$('die1'), $('die2'), $('die3')].map((select) => Number(select.value)).filter(Boolean);
}

async function cook() {
  if (!state.items.length) return;
  $('cookButton').disabled = true;
  try {
    if (!state.sessionId) {
      const started = await api('/api/start', { items: state.items });
      state.sessionId = started.id;
      localStorage.setItem('rm-cooking-session', state.sessionId);
      renderTray(); renderIngredients();
    }
    state.result = await api('/api/cook', { id: state.sessionId, dice_sides: selectedDice(), cooking_level: Number($('level').value), energy: Number($('energy').value) });
    renderResult();
  } catch (error) { $('stateText').textContent = '请求失败'; $('result').innerHTML = `<p class="pending">${escapeHtml(error.message)}</p>`; }
  finally { $('cookButton').disabled = state.result?.status === 'cooked' || state.result?.status === 'processed'; }
}

function reset(items = []) {
  state.items = items; state.sessionId = null; state.result = null; state.preview = null;
  localStorage.removeItem('rm-cooking-session');
  $('cookButton').disabled = false;
  renderTray(); renderIngredients(); renderPreview(); renderResult();
  if (items.length) changed();
}

async function init() {
  const data = await api('/api/data');
  state.ingredients = data.ingredients;
  $('recipeCount').textContent = `${data.recipe_count} 道`;
  for (const [index, id] of ['die1', 'die2', 'die3'].entries()) {
    $(id).innerHTML = '<option value="0">不使用</option>' + [4, 6, 8, 10, 12, 20].map((side) => `<option value="${side}">d${side}</option>`).join('');
    $(id).value = index < 2 ? '6' : '0';
  }
  $('search').addEventListener('input', renderIngredients);
  $('cookButton').addEventListener('click', cook);
  $('resetButton').addEventListener('click', () => reset());
  renderFilters();
  if (state.sessionId) {
    try {
      const session = await api(`/api/session?id=${encodeURIComponent(state.sessionId)}`);
      state.items = session.items; state.preview = session.preview; state.result = session.result;
      $('cookButton').disabled = state.result?.status === 'cooked' || state.result?.status === 'processed';
    } catch (_) { state.sessionId = null; localStorage.removeItem('rm-cooking-session'); }
  }
  renderTray(); renderIngredients(); renderPreview(); renderResult();
}

init().catch((error) => { $('preview').innerHTML = `<p class="pending">${escapeHtml(error.message)}</p>`; });
