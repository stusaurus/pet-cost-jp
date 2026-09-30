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
    const metric = $('[data-metric]')?.dataset.metric || 'per_sheet';
    const metricLabel = $('[data-metric-label]')?.dataset.metricLabel || '1枚';
    const quantityLabel = row => quantity(row).toLocaleString('ja-JP', { maximumFractionDigits: 6 }) + (metric === 'per_liter' ? 'L' : '枚');
    const allRows = $$('[data-product-row]').sort((a, b) => unit(a) - unit(b));
    let visibleRows = [];
    let activeGroup = $('[data-group-filter]')?.dataset.defaultGroup || 'all';
    let activeLabel = '';
    let angleRole = 'unit';
    let stats = { min: 0, median: 0, minTotal: 0, maxQuantity: 0 };
    let calcActive = false;

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
      text('[data-featured-condition]', activeLabel + ' · ' + visibleRows.length + '件を比較');
      const tied = visibleRows.filter(r => Math.abs(unit(r) - stats.min) < 1e-9).length;
      text('[data-featured-badge]', tied > 1 ? '現在最安（同単価 ' + tied + '件）' : activeGroup === 'all' && category === 'cat-litter' ? '素材を問わず比較した最安' : 'この条件の最安');
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
        [['unit', '単価重視', '単価最安'], ['total', '初期支出重視', '支払総額が最小'], ['bulk', 'まとめ買い重視', '最大容量']].forEach(([role, label, sub]) => {
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
      text('[data-sticky-min]', stats.min > 0 ? formatYen(stats.min) + ' / ' + metricLabel : '比較対象なし');
      text('[data-sticky-gap]', relativeLabel(stats.min, stats.median));
      text('[data-sticky-count]', visibleRows.length + '件');
      text('[data-result-status]', activeLabel + ' · ' + visibleRows.length + '件の結果' + (feedback ? 'を更新しました' : ''));
      text('[data-list-context]', activeLabel + ' · ' + visibleRows.length + '件 · ' + metricLabel + 'あたり');
      text('[data-calc-condition]', activeLabel);
      $$('[data-empty-result], [data-list-empty]').forEach(node => { node.hidden = !!visibleRows.length; });
      updateFeatured(); updateTop3(); updateAngles();
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
    if (filter) applyGroup($('[data-group-button][aria-pressed="true"]')?.dataset.group || activeGroup);
    const panel = $('[data-condition-panel]'), sticky = $('[data-comparison-sticky]');
    if (panel && sticky) {
      let queued = false;
      const compact = () => { sticky.classList.toggle('is-compact', panel.getBoundingClientRect().bottom <= ($('.topnav')?.getBoundingClientRect().height || 48)); queued = false; };
      window.addEventListener('scroll', () => { if (!queued) { queued = true; window.requestAnimationFrame(compact); } }, { passive: true });
      window.addEventListener('resize', compact);
      compact();
    }
    $('[data-calculator]')?.addEventListener('submit', event => { event.preventDefault(); calculate(true); });
    $$('[data-calc-price], [data-calc-qty]').forEach(input => input.addEventListener('input', () => { if (calcActive) calculate(false); }));
    if (category) { send('comparison_view', { category_id: category }); send('view_item_list', { item_list_id: category, item_list_name: category }); }
    document.addEventListener('click', event => {
      const groupButton = event.target.closest('[data-group-button]');
      if (groupButton) {
        if (groupButton.getAttribute('aria-pressed') === 'true') return;
        $$('[data-group-button]').forEach(button => { const active = button === groupButton; button.setAttribute('aria-pressed', String(active)); button.classList.toggle('active', active); });
        applyGroup(groupButton.dataset.group || 'all', true);
        send('comparison_filter', { category_id: category, filter_type: 'group', filter_value: activeGroup, result_count: visibleRows.length, min_unit_price: stats.min, median_unit_price: stats.median });
      }
      const angle = event.target.closest('[data-angle-card]');
      if (angle && angleRole !== angle.dataset.angleRole) {
        angleRole = angle.dataset.angleRole; updateAngles(); respond($('[data-angle-detail]'));
        send('comparison_angle_select', { category_id: category, filter_value: activeGroup, angle_role: angleRole, item_id: anglePicks()[angleRole]?.dataset.itemId || '' });
      }
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
