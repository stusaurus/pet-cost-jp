(() => {
  const TEST_KEY = 'pet_cost_operator_test_v1';
  const params = new URLSearchParams(location.search);
  let operator = false;
  try { operator = localStorage.getItem(TEST_KEY) === '1'; } catch (_) {}
  const testValue = params.get('test') ?? params.get('operator_test');
  if (testValue === '1' || testValue === '0') {
    operator = testValue === '1';
    try { if (operator) localStorage.setItem(TEST_KEY, '1'); else localStorage.removeItem(TEST_KEY); } catch (_) {}
    const url = new URL(location.href);
    url.searchParams.delete('test');
    url.searchParams.delete('operator_test');
    try { history.replaceState(history.state, '', url.href); } catch (_) {}
  }
  const send = (name, data = {}) => {
    if (typeof window.gtag !== 'function') return;
    window.gtag('event', name, { site_id: 'pet-cost-jp', ...data, ...(operator ? { operator_test: '1' } : {}) });
  };
  window.petCostTrack = send;
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const formatYen = (value) => {
    if (!Number.isFinite(value) || value < 0) return '-';
    if (value < 10) return '¥' + value.toFixed(2);
    if (value < 100) return '¥' + value.toFixed(1);
    return '¥' + Math.round(value).toLocaleString('ja-JP');
  };
  const relativeLabel = (value, median) => {
    if (!(value > 0) || !(median > 0)) return '比較対象なし';
    const diff = (value - median) / median * 100;
    if (Math.abs(diff) < 2) return '中央値付近';
    return '中央値より' + Math.abs(diff).toFixed(0) + '%' + (diff < 0 ? '安い' : '高い');
  };
  const number = (row, key) => Number(row?.dataset[key] || 0);
  const unit = row => number(row, 'rowUnitPrice');
  const total = row => number(row, 'totalPrice');
  const quantity = row => number(row, 'quantity');
  const name = row => row?.dataset.displayName || row?.dataset.itemName || '';
  const text = (selector, value, root = document) => { const node = $(selector, root); if (node) node.textContent = value; };
  const element = (tag, className, value) => {
    const node = document.createElement(tag);
    node.className = className;
    if (value !== undefined) node.textContent = value;
    return node;
  };
  const motionAllowed = () => !(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const respond = (node) => {
    if (!node || !motionAllowed()) return;
    node.classList.remove('result-changed');
    void node.offsetWidth;
    node.classList.add('result-changed');
    node.addEventListener('animationend', () => node.classList.remove('result-changed'), { once: true });
  };
  const setBar = (node, value, maximum) => {
    if (node) node.style.setProperty('--bar', (maximum > 0 ? Math.max(0, Math.min(100, value / maximum * 100)) : 0).toFixed(2) + '%');
  };

  document.addEventListener('DOMContentLoaded', () => {
    const category = document.body.dataset.categoryId || '';
    const HOME_KEY = 'pet_cost_household_v1';
    let household = {};
    try { const stored = JSON.parse(localStorage.getItem(HOME_KEY) || '{}'); if (stored && typeof stored === 'object' && !Array.isArray(stored)) household = stored; } catch (_) {}
    const metric = $('[data-metric]')?.dataset.metric || 'per_sheet';
    const metricLabel = $('[data-metric-label]')?.dataset.metricLabel || '1枚';
    const quantityLabel = row => quantity(row).toLocaleString('ja-JP', { maximumFractionDigits: 6 }) + (metric === 'per_liter' ? 'L' : '枚');
    const allRows = $$('[data-product-row]').sort((a, b) => unit(a) - unit(b));
    let visibleRows = [];
    let activeGroup = '';
    let activeLabel = '';
    let angleRole = 'unit';
    let stats = { min: 0, median: 0, minTotal: 0, maxQuantity: 0 };
    let calcActive = false;
    const usagePeriod = $('[data-usage-form]')?.dataset.usagePeriod || 'day';
    const periodDays = { day: 1, week: 7, month: 30 }[usagePeriod];
    const periodLabel = { day: '1日', week: '1週間', month: '1か月' }[usagePeriod];
    let usage = null;
    let lastUsageEvent = 'null';
    const decimal = value => value.toLocaleString('ja-JP', { maximumFractionDigits: 1 });
    const daysText = value => value < 1 ? '1日未満' : decimal(value) + '日';
    const monthlyYen = value => '¥' + Math.round(value).toLocaleString('ja-JP');
    function saveHome() {
      if (!category || !activeGroup) return;
      household[category] = { group: activeGroup, usage };
      try { localStorage.setItem(HOME_KEY, JSON.stringify(household)); } catch (_) {}
    }
    function usageValues(row) {
      if (!usage || !row) return null;
      const duration = quantity(row) / usage;
      const days = duration * periodDays;
      const span = duration < .1 ? '0.1未満' : decimal(duration);
      const supply = usagePeriod === 'month' ? (duration < .1 ? '0.1か月未満' : '約' + span + 'か月分') : usagePeriod === 'week' ? (duration < .1 ? '0.1週間未満' : '約' + span + '週間分') : days < 1 ? '1日未満' : '約' + daysText(days) + '分';
      return { days, supply, monthly: unit(row) * usage * 30 / periodDays };
    }
    function renderUsage(mount, row) {
      if (!mount) return;
      const values = usageValues(row);
      mount.hidden = !values;
      mount.replaceChildren();
      if (!values) return;
      mount.appendChild(element('p', 'usage-equation', quantityLabel(row) + ' ÷ ' + periodLabel + usage.toLocaleString('ja-JP') + (metric === 'per_liter' ? 'L' : '枚')));
      const metrics = element('div', 'usage-metrics');
      const supply = element('div', 'usage-metric'); supply.appendChild(element('span', '', 'うちの使用量なら')); supply.appendChild(element('b', '', values.supply)); metrics.appendChild(supply);
      const cost = element('div', 'usage-metric'); cost.appendChild(element('span', '', '月の費用（30日分）')); cost.appendChild(element('b', '', '約' + monthlyYen(values.monthly))); metrics.appendChild(cost);
      mount.appendChild(metrics);
      mount.appendChild(element('p', 'usage-footnote', '新品を使い始めてから' + (values.days < 1 ? '1日未満' : '約' + daysText(values.days)) + 'で使い切る計算。送料別の送料は未加算。'));
    }
    function updateUsage() {
      const note = $('[data-usage-scale-note]'); if (note) note.hidden = !usage;
      text('[data-usage-teaser]', usage ? periodLabel + usage.toLocaleString('ja-JP') + (metric === 'per_liter' ? 'L' : '枚') + 'で比較中' : '任意 · どのくらい持つ？');
      renderUsage($('[data-featured-usage]'), visibleRows[0]);
      const picks = anglePicks();
      renderUsage($('[data-angle-usage]'), picks[angleRole]);
      allRows.forEach(row => {
        const mount = $('[data-row-usage]', row), values = usageValues(row);
        if (mount) { mount.hidden = !values; mount.textContent = values ? values.supply + ' · 30日分 約' + monthlyYen(values.monthly) : ''; }
      });
      $$('[data-top3-card]').forEach((link, i) => {
        let mount = $('[data-top3-usage]', link);
        if (!mount) { mount = element('span', 'top3-usage'); mount.dataset.top3Usage = '1'; $('.top3-copy', link)?.appendChild(mount); }
        const values = usageValues(visibleRows[i]);
        mount.hidden = !values; mount.textContent = values ? values.supply + ' · 30日分 約' + monthlyYen(values.monthly) : '';
      });
      const maxDays = Math.max(...Object.values(picks).map(row => usageValues(row)?.days || 0), 1);
      $$('[data-angle-card]').forEach(button => {
        const values = usageValues(picks[button.dataset.angleRole]);
        let mount = $('[data-angle-lifetime]', button);
        if (!mount) { mount = element('span', 'angle-lifetime'); mount.dataset.angleLifetime = '1'; button.appendChild(mount); }
        mount.hidden = !values; mount.replaceChildren();
        if (values) {
          mount.appendChild(element('span', '', values.supply));
          const track = element('span', 'bar-track'); const bar = element('i', 'bar-fill'); setBar(bar, values.days, maxDays); track.appendChild(bar); mount.appendChild(track);
        }
      });
    }
    function setUsage(emit = false, clear = false) {
      const input = $('[data-usage-input]'), error = $('[data-usage-error]');
      if (!input) return;
      if (clear) input.value = '';
      const empty = !input.value.trim();
      const value = empty ? null : readInput('[data-usage-input]');
      usage = value;
      input.setAttribute('aria-invalid', String(!empty && value === null));
      if (error) { error.hidden = empty || value !== null; error.textContent = '0より大きい、いつもの使用量を入力してください。'; }
      saveHome(); updateUsage();
      if (emit && (empty || value !== null) && lastUsageEvent !== String(value)) {
        lastUsageEvent = String(value);
        send('pet_usage_change', { category_id: category, filter_value: activeGroup, usage_period: usagePeriod, usage_enabled: value !== null });
      }
      if (!empty && value !== null) respond($('[data-featured-usage]'));
    }

    function affiliate(link, row, position, source) {
      if (!link || !row) return;
      link.href = row.dataset.url;
      link.target = '_blank';
      link.rel = 'nofollow sponsored noopener';
      Object.assign(link.dataset, { affiliateLink: '1', merchant: 'rakuten', categoryId: category, itemId: row.dataset.itemId || '', itemName: row.dataset.itemName || '', metric, unitPrice: String(unit(row)), position: String(position), conversionSource: source });
    }
    function reasons(row) {
      const result = [];
      if (unit(row) > 0 && Math.abs(unit(row) - stats.min) < 1e-9) result.push(['unit', '単価最安']);
      if (stats.median > 0 && unit(row) < stats.median * .98) result.push(['median', relativeLabel(unit(row), stats.median)]);
      if (total(row) > 0 && Math.abs(total(row) - stats.minTotal) < 1e-9) result.push(['total', '支払総額が最小']);
      if (quantity(row) > 0 && Math.abs(quantity(row) - stats.maxQuantity) < 1e-9) result.push(['bulk', '最大容量']);
      return result;
    }
    function updateReasons(row) {
      const mount = $('[data-value-badges]', row);
      if (!mount) return;
      const values = reasons(row);
      mount.replaceChildren();
      values.forEach(([role, value], index) => {
        const badge = element('span', 'value-badge' + (index === 0 ? ' is-primary' : ' value-badge-secondary'), value);
        badge.dataset.reasonRole = role;
        mount.appendChild(badge);
      });
      if (!values.length) mount.appendChild(element('span', 'value-badge', relativeLabel(unit(row), stats.median)));
    }
    function updateFeatured() {
      const box = $('[data-featured-box]');
      if (!box) return;
      const row = visibleRows[0];
      box.hidden = !row;
      if (!row) return;
      text('[data-featured-condition]', (activeGroup === 'all' ? '素材を問わず：' : 'あなたの条件：') + activeLabel + ' · ' + visibleRows.length + '件を比較');
      const tied = visibleRows.filter(r => Math.abs(unit(r) - stats.min) < 1e-9).length;
      text('[data-featured-badge]', tied > 1 ? '現在最安（同単価 ' + tied + '件）' : activeGroup === 'all' && category === 'cat-litter' ? '素材を問わず比較した最安' : 'うちの条件なら、現在最安');
      text('[data-featured-unit]', formatYen(unit(row)));
      text('[data-featured-diff]', relativeLabel(unit(row), stats.median));
      text('[data-featured-gap-amount]', formatYen(stats.median - unit(row)) + ' / ' + metricLabel + 'の差');
      text('[data-answer-min-value]', formatYen(unit(row)));
      text('[data-answer-median-value]', formatYen(stats.median));
      setBar($('[data-answer-min-bar]'), unit(row), Math.max(unit(row), stats.median));
      setBar($('[data-answer-median-bar]'), stats.median, Math.max(unit(row), stats.median));
      text('[data-featured-formula]', formatYen(total(row)) + ' ÷ ' + quantityLabel(row) + ' = ' + formatYen(unit(row)));
      text('[data-featured-title]', name(row));
      text('[data-featured-shop]', row.dataset.shop || '');
      text('[data-featured-total]', '商品総額 ' + formatYen(total(row)));
      text('[data-featured-quantity]', quantityLabel(row) + ' · ' + row.dataset.quantityEvidence);
      text('[data-featured-shipping]', row.dataset.shipping || '送料は楽天で確認');
      const img = $('[data-featured-image]');
      if (img) {
        img.hidden = !row.dataset.image;
        if (row.dataset.image) { img.src = row.dataset.image; img.alt = name(row); } else img.removeAttribute('src');
      }
      const mount = $('[data-featured-reasons]');
      if (mount) {
        mount.replaceChildren();
        reasons(row).filter(([role]) => role !== 'median').forEach(([role, value], index) => {
          const span = element('span', 'cover-reason' + (index === 0 ? ' is-primary' : ''), value);
          span.dataset.reasonRole = role;
          mount.appendChild(span);
        });
      }
      affiliate($('[data-affiliate-link]', box), row, 1, 'featured_product');
    }
    function updateTop3() {
      const strip = $('[data-top3-strip]');
      if (!strip) return;
      strip.replaceChildren();
      const max = Math.max(stats.median, ...visibleRows.slice(0, 3).map(unit), 1);
      visibleRows.slice(0, 3).forEach((row, index) => {
        const link = element('a', 'top3-card');
        link.dataset.top3Card = '1';
        affiliate(link, row, index + 1, 'top3_snapshot');
        link.appendChild(element('span', 'top3-rank', String(index + 1)));
        const copy = element('div', 'top3-copy');
        const value = element('span', 'top3-unit', formatYen(unit(row)));
        value.appendChild(element('small', '', ' / ' + metricLabel));
        copy.appendChild(value);
        const delta = unit(row) - stats.min;
        copy.appendChild(element('span', 'top3-difference', index === 0 ? '単価が最小' : Math.abs(delta) < 1e-9 ? '1位と同じ単価' : '1位より +' + formatYen(delta) + ' / ' + metricLabel));
        copy.appendChild(element('span', 'top3-name', name(row)));
        const meta = element('div', 'top3-meta');
        meta.appendChild(element('span', '', '商品総額 ' + formatYen(total(row))));
        meta.appendChild(element('span', '', relativeLabel(unit(row), stats.median)));
        copy.appendChild(meta);
        link.appendChild(copy);
        const chart = element('div', 'top3-chart');
        const track = element('span', 'bar-track');
        const bar = element('i', 'bar-fill');
        setBar(bar, unit(row), max);
        track.appendChild(bar);
        chart.appendChild(track);
        const caption = element('div', 'top3-chart-label');
        caption.appendChild(element('span', '', index === 0 ? '最小' : '同じ尺度で比較'));
        caption.appendChild(element('span', '', '楽天で確認'));
        chart.appendChild(caption);
        link.appendChild(chart);
        strip.appendChild(link);
      });
    }
    function anglePicks() {
      if (!visibleRows.length) return {};
      return {
        unit: [...visibleRows].sort((a, b) => unit(a) - unit(b) || total(a) - total(b))[0],
        total: [...visibleRows].sort((a, b) => total(a) - total(b) || unit(a) - unit(b))[0],
        bulk: [...visibleRows].sort((a, b) => quantity(b) - quantity(a) || unit(a) - unit(b))[0]
      };
    }
    function updateAngles() {
      const grid = $('[data-angle-grid]');
      const detail = $('[data-angle-detail]');
      if (!grid || !detail) return;
      grid.hidden = detail.hidden = !visibleRows.length;
      if (!visibleRows.length) return;
      const picks = anglePicks();
      if (!grid.children.length) {
        [['unit', '長く使って安く', '単価重視'], ['total', '今日は出費を抑える', '支払総額重視'], ['bulk', '買い足す回数を減らす', 'まとめ買い重視']].forEach(([role, label, sub]) => {
          const button = element('button', 'angle-card');
          button.type = 'button'; button.dataset.angleCard = '1'; button.dataset.angleRole = role;
          button.appendChild(element('span', 'angle-label', label)); button.appendChild(element('span', 'angle-sub', sub));
          const value = element('span', 'angle-value'); value.dataset.angleValue = '1'; button.appendChild(value); grid.appendChild(button);
        });
      }
      $$('[data-angle-card]', grid).forEach(button => {
        const role = button.dataset.angleRole, row = picks[role];
        button.setAttribute('aria-pressed', String(role === angleRole));
        text('[data-angle-value]', role === 'unit' ? formatYen(unit(row)) + ' / ' + metricLabel : role === 'total' ? formatYen(total(row)) : quantityLabel(row), button);
      });
      const row = picks[angleRole];
      text('[data-angle-name]', name(row));
      text('[data-angle-reason]', { unit: 'この条件で、単価が最小', total: 'この条件で、掲載商品価格が最小', bulk: 'この条件で、購入できる総数量が最大' }[angleRole]);
      text('[data-angle-unit]', formatYen(unit(row)));
      text('[data-angle-total]', formatYen(total(row)));
      text('[data-angle-quantity]', quantityLabel(row));
      let explanation = angleRole === 'unit' ? '1枚・1Lの負担を抑える選び方。購入額・送料も一緒に確認してください。' : angleRole === 'total' ? '掲載商品価格は最小。1枚・1Lの単価も確認すると、買う量とのバランスが分かります。' : '買う量をまとめる選び方。保管場所と、今回払う商品総額も確認してください。';
      if (angleRole !== 'unit' && row === picks.unit) explanation = '単価最安と同じ商品です。' + explanation;
      text('[data-angle-explain]', explanation);
      affiliate($('[data-angle-link]'), row, visibleRows.indexOf(row) + 1, 'comparison_angle_' + angleRole);
    }
    function applyGroup(group, feedback = false) {
      activeGroup = group;
      const active = $('[data-group-button][data-group="' + group + '"]');
      activeLabel = active?.dataset.groupLabel || '現在の条件';
      $$('[data-group-button]').forEach(button => { const selected = button === active; button.setAttribute('aria-pressed', String(selected)); button.classList.toggle('active', selected); });
      if (active?.closest('[data-other-conditions]')) active.closest('[data-other-conditions]').open = true;
      const results = $('[data-comparison-results]'), start = $('[data-condition-start]'), usagePanel = $('[data-usage-panel]');
      if (results) results.hidden = false;
      if (start) start.hidden = true;
      if (usagePanel) usagePanel.hidden = false;
      visibleRows = allRows.filter(row => group === 'all' || row.dataset.group === group);
      const prices = visibleRows.map(unit).filter(x => x > 0).sort((a, b) => a - b);
      const length = prices.length, middle = Math.floor(length / 2);
      stats = { min: prices[0] || 0, median: length ? length % 2 ? prices[middle] : (prices[middle - 1] + prices[middle]) / 2 : 0, minTotal: length ? Math.min(...visibleRows.map(total)) : 0, maxQuantity: length ? Math.max(...visibleRows.map(quantity)) : 0 };
      allRows.forEach(row => {
        const rank = visibleRows.indexOf(row) + 1;
        row.hidden = rank === 0;
        row.classList.remove('is-rank-1', 'is-rank-2', 'is-rank-3');
        if (rank > 0 && rank <= 3) row.classList.add('is-rank-' + rank);
        if (rank > 0) {
          text('[data-rank-cell]', String(rank), row);
          $('[data-affiliate-link]', row).dataset.position = String(rank);
          updateReasons(row);
        }
      });
      text('[data-sticky-condition]', activeLabel);
      text('[data-sticky-condition-title]', group === 'all' ? '素材指定なし' : 'あなたの条件');
      text('[data-sticky-min]', stats.min > 0 ? formatYen(stats.min) + ' / ' + metricLabel : '比較対象なし');
      text('[data-sticky-gap]', relativeLabel(stats.min, stats.median));
      text('[data-sticky-count]', visibleRows.length + '件');
      text('[data-result-status]', (group === 'all' ? '素材指定なし：' : 'あなたの条件：') + activeLabel + ' · ' + visibleRows.length + '件' + (feedback ? 'に更新しました' : 'を比較中'));
      text('[data-list-context]', activeLabel + ' · ' + visibleRows.length + '件 · ' + metricLabel + 'あたり');
      text('[data-calc-condition]', activeLabel);
      $$('[data-empty-result], [data-list-empty]').forEach(node => { node.hidden = !!visibleRows.length; });
      updateFeatured(); updateTop3(); updateAngles(); updateUsage(); saveHome();
      if (calcActive) calculate(false);
      if (feedback) { respond($('[data-featured-box]')); respond($('[data-top3-strip]')); respond($('[data-angle-detail]')); }
    }
    function readInput(selector) {
      const input = $(selector);
      const raw = (input?.value || '').normalize('NFKC').trim();
      const validText = /^(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?$/.test(raw);
      const value = validText ? Number(raw.replaceAll(',', '')) : NaN;
      const valid = Number.isFinite(value) && value > 0 && value <= 1e12;
      input?.setAttribute('aria-invalid', String(!valid));
      return valid ? value : null;
    }
    function calculate(emit = true) {
      const result = $('[data-calc-result]');
      if (!result) return;
      const price = readInput('[data-calc-price]'), qty = readInput('[data-calc-qty]');
      const error = $('[data-calc-error]'), placeholder = $('[data-calc-placeholder]');
      if (price === null || qty === null) {
        if (error) { error.hidden = false; error.textContent = '0より大きい値段と総数量を入力してください。'; }
        result.hidden = true;
        if (placeholder) placeholder.hidden = false;
        return;
      }
      calcActive = true;
      if (error) error.hidden = true;
      if (placeholder) placeholder.hidden = true;
      const value = price / qty, benchmark = stats.min;
      let verdict = 'benchmark_unavailable', message = 'この条件には比較できる掲載商品がありません。';
      if (benchmark > 0) {
        const diff = (value - benchmark) / benchmark * 100;
        verdict = diff <= -2 ? 'store_cheaper' : diff >= 2 ? 'online_cheaper' : 'roughly_same';
        message = verdict === 'store_cheaper' ? '掲載最安より約' + Math.abs(diff).toFixed(0) + '%安い店頭価格' : verdict === 'online_cheaper' ? '掲載最安より約' + diff.toFixed(0) + '%高い店頭価格' : '掲載最安とほぼ同じ単価（差は2%未満）';
      }
      result.replaceChildren();
      result.appendChild(element('p', 'calc-equation', formatYen(price) + ' ÷ ' + qty.toLocaleString('ja-JP') + (metric === 'per_liter' ? 'L' : '枚')));
      result.appendChild(element('p', 'calc-unit', formatYen(value) + ' / ' + metricLabel));
      result.appendChild(element('p', 'calc-verdict', message));
      result.appendChild(element('p', 'calc-context', '比較条件：' + activeLabel));
      if (benchmark > 0) {
        const max = Math.max(value, benchmark);
        [['店頭', value], ['掲載最安', benchmark]].forEach(([label, amount]) => {
          const row = element('div', 'chart-row'); row.appendChild(element('span', '', label));
          const track = element('span', 'bar-track'), bar = element('i', 'bar-fill'); setBar(bar, amount, max); track.appendChild(bar);
          row.appendChild(track); row.appendChild(element('b', 'chart-value', formatYen(amount))); result.appendChild(row);
        });
      }
      result.hidden = false;
      if (emit) {
        respond($('.calc-output'));
        send('unit_calculator_use', { category_id: category, filter_value: activeGroup, input_price: price, input_quantity: qty, calculated_unit_price: Number(value.toFixed(4)), benchmark_unit_price: Number(benchmark.toFixed(4)), comparison_result: verdict });
      }
    }
    const filter = $('[data-group-filter]');
    const saved = household[category];
    if (filter && saved && typeof saved.group === 'string' && $$('[data-group-button]').some(b => b.dataset.group === saved.group)) {
      usage = typeof saved.usage === 'number' && Number.isFinite(saved.usage) && saved.usage > 0 && saved.usage <= 1e12 ? saved.usage : null;
      if (usage) $('[data-usage-input]').value = String(usage);
      lastUsageEvent = String(usage);
      applyGroup(saved.group);
    }
    $$('[data-pet-category]').forEach(link => {
      const previous = household[link.dataset.petCategory];
      const labels = { regular: 'レギュラー', wide: 'ワイド', super_wide: 'スーパーワイド', paper: '紙', okara: 'おから', wood: '木', mineral: '鉱物', silica: 'シリカ', mixed: '混合素材', system: 'システムトイレ用', all: '素材指定なし', deotoilet: 'デオトイレ系', nyantomo: 'ニャンとも系', iris: 'アイリス系', universal: '各社共通・汎用', unknown: '素材不明' };
      if (previous && labels[previous.group]) text('[data-saved-condition]', '前回の条件：' + labels[previous.group], link);
    });
    const panel = $('[data-condition-panel]'), sticky = $('[data-comparison-sticky]');
    if (panel && sticky) {
      let queued = false;
      const compact = () => { sticky.classList.toggle('is-compact', panel.getBoundingClientRect().bottom <= ($('.topnav')?.getBoundingClientRect().height || 48)); queued = false; };
      window.addEventListener('scroll', () => { if (!queued) { queued = true; window.requestAnimationFrame(compact); } }, { passive: true });
      window.addEventListener('resize', compact);
      compact();
    }
    $('[data-calculator]')?.addEventListener('submit', event => { event.preventDefault(); calculate(true); });
    $('[data-usage-form]')?.addEventListener('submit', event => { event.preventDefault(); setUsage(true); });
    $('[data-usage-input]')?.addEventListener('input', () => setUsage(false));
    $('[data-usage-input]')?.addEventListener('change', () => setUsage(true));
    $$('[data-calc-price], [data-calc-qty]').forEach(input => input.addEventListener('input', () => { if (calcActive) calculate(false); }));
    if (category) { send('comparison_view', { category_id: category }); send('view_item_list', { item_list_id: category, item_list_name: category }); }
    document.addEventListener('click', event => {
      const groupButton = event.target.closest('[data-group-button]');
      if (groupButton) {
        if (groupButton.getAttribute('aria-pressed') === 'true') return;
        applyGroup(groupButton.dataset.group || 'all', true);
        send('comparison_filter', { category_id: category, filter_type: 'group', filter_value: activeGroup, result_count: visibleRows.length, min_unit_price: stats.min, median_unit_price: stats.median });
      }
      const angle = event.target.closest('[data-angle-card]');
      if (angle && angleRole !== angle.dataset.angleRole) {
        angleRole = angle.dataset.angleRole; updateAngles(); updateUsage(); respond($('[data-angle-detail]'));
        send('comparison_angle_select', { category_id: category, filter_value: activeGroup, angle_role: angleRole, item_id: anglePicks()[angleRole]?.dataset.itemId || '' });
      }
      if (event.target.closest('[data-usage-clear]')) setUsage(true, true);
      if (event.target.closest('[data-open-usage]')) { const usagePanel = $('[data-usage-panel]'); if (usagePanel) usagePanel.open = true; }
      const care = event.target.closest('[data-pet-category]');
      if (care) send('pet_category_select', { category_id: care.dataset.petCategory, conversion_source: 'household_start' });
      const editorial = event.target.closest('a[data-editorial-category]');
      if (editorial) send('homepage_editorial_click', { category_id: editorial.dataset.editorialCategory || '', editorial_position: Number(editorial.dataset.editorialPosition || 0), conversion_source: 'homepage_editorial' });
      const spotlight = event.target.closest('a[data-spotlight-link]');
      if (spotlight) send('daily_spotlight_click', { category_id: spotlight.dataset.categoryId || '', price_gap_percent: Number(spotlight.dataset.gapPercent || 0), conversion_source: 'daily_price_gap' });
      const link = event.target.closest('a[data-affiliate-link]');
      if (!link) return;
      const data = { merchant: link.dataset.merchant || 'rakuten', category_id: link.dataset.categoryId || category, item_id: link.dataset.itemId || '', item_name: link.dataset.itemName || '', unit_metric: link.dataset.metric || '', unit_price: Number(link.dataset.unitPrice || 0), position: Number(link.dataset.position || 0), conversion_source: link.dataset.conversionSource || 'comparison_table' };
      send('affiliate_click', data); send('product_result_click', data);
      send('select_item', { item_list_id: data.category_id, item_list_name: data.category_id, items: [{ item_id: data.item_id, item_name: data.item_name, index: data.position, affiliation: data.merchant }] });
    });
  });
})();
