(() => {
  const TEST_KEY = 'pet_cost_operator_test_v1';
  const params = new URLSearchParams(location.search);
  let operator = false;
  try { operator = localStorage.getItem(TEST_KEY) === '1'; } catch (_) {}
  if (params.get('test') === '1' || params.get('test') === '0') {
    operator = params.get('test') === '1';
    try {
      if (operator) localStorage.setItem(TEST_KEY, '1');
      else localStorage.removeItem(TEST_KEY);
    } catch (_) {}
    const url = new URL(location.href);
    url.searchParams.delete('test');
    try { history.replaceState(history.state, '', url.href); } catch (_) {}
  }

  const send = (name, data = {}) => {
    if (typeof window.gtag !== 'function') return;
    const payload = { site_id: 'pet-cost-jp', ...data };
    if (operator) payload.operator_test = '1';
    window.gtag('event', name, payload);
  };

  window.petCostTrack = send;

  function applyGroupFilter(select, group) {
    const rankAll = select.dataset.rankAll === '1';
    let visibleRank = 0;
    document.querySelectorAll('[data-product-row]').forEach((row) => {
      const visible = group === 'all' || row.dataset.group === group;
      row.hidden = !visible;
      const rank = row.querySelector('[data-rank-cell]');
      if (!rank) return;
      if (!visible) return;
      if (group === 'all' && !rankAll) rank.textContent = '—';
      else { visibleRank += 1; rank.textContent = String(visibleRank); }
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    const category = document.body.dataset.categoryId || '';
    document.querySelectorAll('[data-group-filter]').forEach((select) => applyGroupFilter(select, select.value));
    if (category) {
      send('comparison_view', { category_id: category });
      send('view_item_list', { item_list_id: category, item_list_name: category });
    }

    document.addEventListener('change', (event) => {
      const select = event.target.closest('[data-group-filter]');
      if (!select) return;
      const group = select.value;
      applyGroupFilter(select, group);
      send('comparison_filter', { category_id: category, filter_type: 'group', filter_value: group });
    });

    document.addEventListener('click', (event) => {
      const button = event.target.closest('[data-calc-button]');
      if (!button) return;
      const section = button.closest('.section');
      const price = Number(section.querySelector('[data-calc-price]')?.value || 0);
      const qty = Number(section.querySelector('[data-calc-qty]')?.value || 0);
      const result = section.querySelector('[data-calc-result]');
      if (!(price > 0) || !(qty > 0) || !result) return;
      const unitPrice = price / qty;
      const visible = [...document.querySelectorAll('[data-product-row]')]
        .filter((row) => !row.hidden)
        .map((row) => Number(row.dataset.rowUnitPrice || 0))
        .filter((x) => x > 0);
      const benchmark = visible.length ? Math.min(...visible) : 0;
      let verdict = 'benchmark_unavailable';
      let text = `入力価格は約 ¥${unitPrice < 100 ? unitPrice.toFixed(1) : Math.round(unitPrice).toLocaleString()} / 単位です。`;
      if (benchmark > 0) {
        const diff = ((unitPrice - benchmark) / benchmark) * 100;
        if (diff <= -2) verdict = 'store_cheaper';
        else if (diff >= 2) verdict = 'online_cheaper';
        else verdict = 'roughly_same';
        text += diff <= -2
          ? ` 表示中の最安候補より約 ${Math.abs(diff).toFixed(0)}% 安い価格です。`
          : diff >= 2
            ? ` 表示中の最安候補より約 ${diff.toFixed(0)}% 高い価格です。`
            : ' 表示中の最安候補とほぼ同水準です。';
      }
      result.textContent = text;
      result.style.display = 'block';
      const group = document.querySelector('[data-group-filter]')?.value || 'all';
      send('unit_calculator_use', {
        category_id: category,
        filter_value: group,
        input_price: price,
        input_quantity: qty,
        calculated_unit_price: Number(unitPrice.toFixed(4)),
        benchmark_unit_price: Number(benchmark.toFixed(4)),
        comparison_result: verdict
      });
    });

    document.addEventListener('click', (event) => {
      const link = event.target.closest('a[data-affiliate-link]');
      if (!link) return;
      const data = {
        merchant: link.dataset.merchant || 'rakuten',
        category_id: link.dataset.categoryId || category,
        item_id: link.dataset.itemId || '',
        item_name: link.dataset.itemName || '',
        unit_metric: link.dataset.metric || '',
        unit_price: Number(link.dataset.unitPrice || 0),
        position: Number(link.dataset.position || 0),
        conversion_source: link.dataset.conversionSource || 'comparison_table'
      };
      send('affiliate_click', data);
      send('product_result_click', data);
      send('select_item', {
        item_list_id: data.category_id,
        item_list_name: data.category_id,
        items: [{ item_id: data.item_id, item_name: data.item_name, index: data.position, affiliation: data.merchant }]
      });
    });
  });
})();
