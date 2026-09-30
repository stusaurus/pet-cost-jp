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

  const formatYen = (value) => {
    if (!(value > 0)) return '-';
    if (value < 10) return '¥' + value.toFixed(2);
    if (value < 100) return '¥' + value.toFixed(1);
    return '¥' + Math.round(value).toLocaleString('ja-JP');
  };

  const relativeLabel = (value, median) => {
    if (!(value > 0) || !(median > 0)) return '';
    const diff = ((value - median) / median) * 100;
    if (Math.abs(diff) < 2) return '中央値付近';
    return diff < 0
      ? '中央値より' + Math.abs(diff).toFixed(0) + '%安い'
      : '中央値より' + diff.toFixed(0) + '%高い';
  };

  const currentRows = () => [...document.querySelectorAll('[data-product-row]')];

  function updateFeatured(row, rankText, median, visibleRows = []) {
    const box = document.querySelector('[data-featured-box]');
    if (!box) return;
    if (!row) {
      box.hidden = true;
      return;
    }
    box.hidden = false;
    const img = box.querySelector('[data-featured-image]');
    const title = box.querySelector('[data-featured-title]');
    const shop = box.querySelector('[data-featured-shop]');
    const unit = box.querySelector('[data-featured-unit]');
    const total = box.querySelector('[data-featured-total]');
    const badge = box.querySelector('[data-featured-badge]');
    const diff = box.querySelector('[data-featured-diff]');
    const reasons = box.querySelector('[data-featured-reasons]');
    const link = box.querySelector('[data-affiliate-link]');

    if (img) {
      if (row.dataset.image) {
        img.src = row.dataset.image;
        img.alt = row.dataset.itemName || '商品画像';
        img.hidden = false;
      } else {
        img.removeAttribute('src');
        img.hidden = true;
      }
    }
    if (title) title.textContent = row.dataset.itemName || '';
    if (shop) shop.textContent = row.dataset.shop || '';
    if (unit) unit.textContent = formatYen(Number(row.dataset.rowUnitPrice || 0));
    if (total) total.textContent = '総額 ' + formatYen(Number(row.dataset.totalPrice || 0));
    if (badge) badge.textContent = rankText || '表示中の最安';
    if (diff) diff.textContent = relativeLabel(Number(row.dataset.rowUnitPrice || 0), median);

    if (reasons) {
      reasons.innerHTML = '';
      const rows = visibleRows.length ? visibleRows : [row];
      const totals = rows.map((item) => Number(item.dataset.totalPrice || 0)).filter((x) => x > 0);
      const quantities = rows.map((item) => Number(item.dataset.quantity || 0)).filter((x) => x > 0);
      const minTotal = totals.length ? Math.min(...totals) : 0;
      const maxQuantity = quantities.length ? Math.max(...quantities) : 0;
      const total = Number(row.dataset.totalPrice || 0);
      const quantity = Number(row.dataset.quantity || 0);
      const unit = Number(row.dataset.rowUnitPrice || 0);
      const chips = [{ text: '単価最安', cls: 'is-primary' }];

      if (unit > 0 && median > 0) {
        const pct = ((median - unit) / median) * 100;
        if (pct >= 2) chips.push({ text: '中央値より' + pct.toFixed(0) + '%安い', cls: '' });
      }
      if (total > 0 && minTotal > 0 && Math.abs(total - minTotal) < 1e-9) {
        chips.push({ text: '支払総額も最小', cls: 'is-warm' });
      }
      if (quantity > 0 && maxQuantity > 0 && Math.abs(quantity - maxQuantity) < 1e-9) {
        chips.push({ text: '最大容量', cls: 'is-cool' });
      }

      chips.slice(0, 4).forEach((chip) => {
        const span = document.createElement('span');
        span.className = 'cover-reason' + (chip.cls ? ' ' + chip.cls : '');
        span.textContent = chip.text;
        reasons.appendChild(span);
      });
    }

    if (link) {
      link.href = row.dataset.url || '#';
      link.dataset.itemId = row.dataset.itemId || '';
      link.dataset.itemName = row.dataset.itemName || '';
      link.dataset.unitPrice = row.dataset.rowUnitPrice || '0';
      link.dataset.position = '1';
    }
  }

  function updateSnapshot(visibleRows, median) {
    const strip = document.querySelector('[data-top3-strip]');
    const message = document.querySelector('[data-deal-message]');
    const dot = document.querySelector('[data-deal-dot]');
    const topRows = visibleRows.slice(0, 3);

    if (strip) {
      strip.innerHTML = '';
      topRows.forEach((row, index) => {
        const link = document.createElement('a');
        link.className = 'top3-card';
        link.href = row.dataset.url || '#';
        link.target = '_blank';
        link.rel = 'nofollow sponsored noopener';
        link.dataset.top3Card = '1';
        link.dataset.affiliateLink = '1';
        link.dataset.merchant = 'rakuten';
        link.dataset.categoryId = document.body.dataset.categoryId || '';
        const sourceLink = row.querySelector('a[data-affiliate-link]');
        link.dataset.metric = sourceLink?.dataset.metric || '';
        link.dataset.itemId = row.dataset.itemId || '';
        link.dataset.itemName = row.dataset.itemName || '';
        link.dataset.unitPrice = row.dataset.rowUnitPrice || '0';
        link.dataset.position = String(index + 1);
        link.dataset.conversionSource = 'top3_snapshot';

        const rank = document.createElement('span');
        rank.className = 'top3-rank';
        rank.textContent = String(index + 1);
        link.appendChild(rank);

        if (row.dataset.image) {
          const img = document.createElement('img');
          img.className = 'top3-img';
          img.src = row.dataset.image;
          img.alt = '';
          img.loading = 'lazy';
          img.width = 50;
          img.height = 50;
          link.appendChild(img);
        }

        const copy = document.createElement('span');
        copy.className = 'top3-copy';

        const name = document.createElement('span');
        name.className = 'top3-name';
        name.textContent = row.dataset.itemName || '';
        copy.appendChild(name);

        const unit = document.createElement('span');
        unit.className = 'top3-unit';
        unit.textContent = formatYen(Number(row.dataset.rowUnitPrice || 0));
        const small = document.createElement('small');
        const metricLabel = sourceLink?.dataset.metric === 'per_liter' ? ' / 1L' : ' / 1枚';
        small.textContent = metricLabel;
        unit.appendChild(small);
        copy.appendChild(unit);

        const total = document.createElement('span');
        total.className = 'top3-total';
        total.textContent = '総額 ' + formatYen(Number(row.dataset.totalPrice || 0));
        copy.appendChild(total);

        link.appendChild(copy);
        strip.appendChild(link);
      });
    }

    const cheapest = topRows.length ? Number(topRows[0].dataset.rowUnitPrice || 0) : 0;
    if (message) {
      message.textContent = cheapest > 0 && median > 0
        ? relativeLabel(cheapest, median)
        : '比較できる商品がありません';
    }
    if (dot) {
      let position = 50;
      if (cheapest > 0 && median > 0) {
        const diff = ((cheapest - median) / median) * 100;
        position = Math.max(5, Math.min(95, 50 + diff * 1.25));
      }
      dot.style.left = position.toFixed(1) + '%';
    }
  }

  function updateAngles(visibleRows) {
    const grid = document.querySelector('[data-angle-grid]');
    if (!grid || !visibleRows.length) return;

    const picks = [
      {
        role: 'unit',
        icon: '💰',
        label: '単価最安',
        row: [...visibleRows].sort((a, b) =>
          Number(a.dataset.rowUnitPrice || 0) - Number(b.dataset.rowUnitPrice || 0)
        )[0],
        value: (row) => {
          const sourceLink = row.querySelector('a[data-affiliate-link]');
          const suffix = sourceLink?.dataset.metric === 'per_liter' ? ' / 1L' : ' / 1枚';
          return formatYen(Number(row.dataset.rowUnitPrice || 0)) + suffix;
        }
      },
      {
        role: 'total',
        icon: '🧾',
        label: '支払総額が最小',
        row: [...visibleRows].sort((a, b) =>
          Number(a.dataset.totalPrice || 0) - Number(b.dataset.totalPrice || 0)
        )[0],
        value: (row) => formatYen(Number(row.dataset.totalPrice || 0))
      },
      {
        role: 'bulk',
        icon: '📦',
        label: '最大容量',
        row: [...visibleRows].sort((a, b) =>
          Number(b.dataset.quantity || 0) - Number(a.dataset.quantity || 0)
        )[0],
        value: (row) => row.dataset.quantityEvidence || String(row.dataset.quantity || '')
      }
    ];

    grid.innerHTML = '';
    picks.forEach((pick) => {
      const row = pick.row;
      if (!row) return;
      const sourceLink = row.querySelector('a[data-affiliate-link]');
      const link = document.createElement('a');
      link.className = 'angle-card';
      link.href = row.dataset.url || '#';
      link.target = '_blank';
      link.rel = 'nofollow sponsored noopener';
      link.dataset.angleCard = '1';
      link.dataset.angleRole = pick.role;
      link.dataset.affiliateLink = '1';
      link.dataset.merchant = 'rakuten';
      link.dataset.categoryId = document.body.dataset.categoryId || '';
      link.dataset.metric = sourceLink?.dataset.metric || '';
      link.dataset.itemId = row.dataset.itemId || '';
      link.dataset.itemName = row.dataset.itemName || '';
      link.dataset.unitPrice = row.dataset.rowUnitPrice || '0';
      link.dataset.position = '0';
      link.dataset.conversionSource = 'comparison_angle_' + pick.role;

      const icon = document.createElement('span');
      icon.className = 'angle-icon';
      icon.textContent = pick.icon;
      link.appendChild(icon);

      const label = document.createElement('span');
      label.className = 'angle-label';
      label.textContent = pick.label;
      link.appendChild(label);

      const value = document.createElement('span');
      value.className = 'angle-value';
      value.textContent = pick.value(row);
      link.appendChild(value);

      const name = document.createElement('span');
      name.className = 'angle-name';
      name.textContent = row.dataset.itemName || '';
      link.appendChild(name);

      const cta = document.createElement('span');
      cta.className = 'angle-cta';
      cta.textContent = '楽天で確認 →';
      link.appendChild(cta);

      grid.appendChild(link);
    });
  }

  function updateValueBadges(visibleRows, median) {
    if (!visibleRows.length) return;

    const unitValues = visibleRows
      .map((row) => Number(row.dataset.rowUnitPrice || 0))
      .filter((x) => x > 0);
    const totalValues = visibleRows
      .map((row) => Number(row.dataset.totalPrice || 0))
      .filter((x) => x > 0);
    const quantities = visibleRows
      .map((row) => Number(row.dataset.quantity || 0))
      .filter((x) => x > 0);

    const minUnit = unitValues.length ? Math.min(...unitValues) : 0;
    const minTotal = totalValues.length ? Math.min(...totalValues) : 0;
    const maxQuantity = quantities.length ? Math.max(...quantities) : 0;

    visibleRows.forEach((row) => {
      const mount = row.querySelector('[data-value-badges]');
      if (!mount) return;
      mount.innerHTML = '';

      const unit = Number(row.dataset.rowUnitPrice || 0);
      const total = Number(row.dataset.totalPrice || 0);
      const quantity = Number(row.dataset.quantity || 0);
      const badges = [];

      if (unit > 0 && minUnit > 0 && Math.abs(unit - minUnit) < 1e-9) {
        badges.push({ cls: 'is-best-unit', text: '単価最安' });
      }

      if (unit > 0 && median > 0) {
        const diff = ((median - unit) / median) * 100;
        if (diff >= 2) {
          badges.push({ cls: 'is-discount', text: '中央値より' + diff.toFixed(0) + '%安い' });
        }
      }

      if (total > 0 && minTotal > 0 && Math.abs(total - minTotal) < 1e-9) {
        badges.push({ cls: 'is-low-total', text: '支払総額が最小' });
      }

      if (quantity > 0 && maxQuantity > 0 && Math.abs(quantity - maxQuantity) < 1e-9) {
        badges.push({ cls: 'is-bulk', text: '最大容量' });
      }

      badges.slice(0, 3).forEach((badge) => {
        const span = document.createElement('span');
        span.className = 'value-badge ' + badge.cls;
        span.textContent = badge.text;
        mount.appendChild(span);
      });

      if (!badges.length) {
        const empty = document.createElement('span');
        empty.className = 'value-badge-empty';
        empty.textContent = '価格特徴を比較中';
        mount.appendChild(empty);
      }
    });
  }

  function updateStickySummary(visibleRows, median) {
    const condition = document.querySelector('[data-sticky-condition]');
    const minNode = document.querySelector('[data-sticky-min]');
    const gapNode = document.querySelector('[data-sticky-gap]');
    const countNode = document.querySelector('[data-sticky-count]');
    const active = document.querySelector('[data-group-button][aria-pressed="true"]');
    const metric = document.querySelector('a[data-affiliate-link]')?.dataset.metric === 'per_liter' ? '1L' : '1枚';

    const prices = visibleRows
      .map((row) => Number(row.dataset.rowUnitPrice || 0))
      .filter((x) => x > 0)
      .sort((a, b) => a - b);
    const cheapest = prices.length ? prices[0] : 0;

    if (condition) condition.textContent = active?.dataset.groupLabel || '現在の条件';
    if (minNode) minNode.textContent = cheapest > 0 ? formatYen(cheapest) + ' / ' + metric : '-';
    if (gapNode) gapNode.textContent = cheapest > 0 && median > 0 ? relativeLabel(cheapest, median) : '-';
    if (countNode) countNode.textContent = String(visibleRows.length) + '件';
  }

  function updateSummary(visibleRows, rankAll) {
    const prices = visibleRows
      .map((row) => Number(row.dataset.rowUnitPrice || 0))
      .filter((x) => x > 0)
      .sort((a, b) => a - b);

    const countNode = document.querySelector('[data-stat-count]');
    const minNode = document.querySelector('[data-stat-min]');
    const medianNode = document.querySelector('[data-stat-median]');
    const visibleNode = document.querySelector('[data-visible-count]');

    if (countNode) countNode.textContent = String(visibleRows.length) + '件';
    if (visibleNode) visibleNode.textContent = String(visibleRows.length) + '件';
    if (minNode) minNode.textContent = prices.length ? formatYen(prices[0]) : '-';
    const middle = prices.length ? prices[Math.floor(prices.length / 2)] : 0;
    if (medianNode) medianNode.textContent = prices.length ? formatYen(middle) : '-';

    visibleRows.forEach((row) => {
      const node = row.querySelector('[data-price-diff]');
      if (node) node.textContent = relativeLabel(Number(row.dataset.rowUnitPrice || 0), middle);
    });
    updateValueBadges(visibleRows, middle);
    updateStickySummary(visibleRows, middle);

    updateFeatured(
      visibleRows[0],
      rankAll ? '表示中の1位' : 'この条件の1位',
      middle,
      visibleRows
    );
    updateSnapshot(visibleRows, middle);
    updateAngles(visibleRows);
  }

  function applyGroupFilter(group) {
    const container = document.querySelector('[data-group-filter]');
    if (!container) return;
    const rankAll = container.dataset.rankAll === '1';
    let visibleRank = 0;
    const visibleRows = [];

    currentRows().forEach((row) => {
      const visible = group === 'all' || row.dataset.group === group;
      row.hidden = !visible;
      const rank = row.querySelector('[data-rank-cell]');
      const rankBadge = row.querySelector('[data-rank-badge]');
      const showcase = row.querySelector('[data-rank-showcase-label]');
      const affiliate = row.querySelector('a[data-affiliate-link]');
      row.classList.remove('is-rank-1', 'is-rank-2', 'is-rank-3');
      if (showcase) {
        showcase.hidden = true;
        showcase.textContent = '';
      }
      if (!visible) return;

      visibleRows.push(row);
      const visualRank = visibleRows.length;
      if (visualRank <= 3) {
        row.classList.add('is-rank-' + visualRank);
        if (showcase) {
          showcase.hidden = false;
          showcase.textContent = visualRank === 1 ? 'この条件の最安' : visualRank === 2 ? '2nd PRICE' : '3rd PRICE';
        }
      }
      if (affiliate) affiliate.dataset.position = String(visualRank);
      if (group === 'all' && !rankAll) {
        if (rank) rank.textContent = '—';
        if (rankBadge) rankBadge.textContent = '条件別';
      } else {
        visibleRank += 1;
        if (rank) rank.textContent = String(visibleRank);
        if (rankBadge) rankBadge.textContent = visibleRank === 1 ? '最安' : visibleRank + '位';
      }
    });

    updateSummary(visibleRows, rankAll || group !== 'all');
  }

  function setupRevealMotion() {
    const reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const nodes = [...document.querySelectorAll('.section, .category-card, .shop-card, .step, .angle-card')];
    if (!nodes.length || reduced || !('IntersectionObserver' in window)) {
      nodes.forEach((node) => node.classList.add('is-visible'));
      return;
    }

    document.documentElement.classList.add('motion-ready');
    nodes.forEach((node, index) => {
      node.classList.add('reveal-item');
      node.style.transitionDelay = Math.min(index % 5, 4) * 45 + 'ms';
    });

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    nodes.forEach((node) => observer.observe(node));
  }

  document.addEventListener('DOMContentLoaded', () => {
    setupRevealMotion();
    const category = document.body.dataset.categoryId || '';
    const activeButton = document.querySelector('[data-group-button][aria-pressed="true"]');
    if (activeButton) {
      const current = document.querySelector('[data-current-condition]');
      if (current) current.textContent = activeButton.dataset.groupLabel || activeButton.textContent.trim();
      applyGroupFilter(activeButton.dataset.group || 'all');
    }

    if (category) {
      send('comparison_view', { category_id: category });
      send('view_item_list', { item_list_id: category, item_list_name: category });
    }

    document.addEventListener('click', (event) => {
      const button = event.target.closest('[data-group-button]');
      if (!button) return;
      const container = button.closest('[data-group-filter]');
      if (!container) return;

      container.querySelectorAll('[data-group-button]').forEach((node) => {
        const active = node === button;
        node.setAttribute('aria-pressed', active ? 'true' : 'false');
        node.classList.toggle('active', active);
      });

      const group = button.dataset.group || 'all';
      const current = document.querySelector('[data-current-condition]');
      if (current) current.textContent = button.dataset.groupLabel || button.textContent.trim();
      applyGroupFilter(group);
      send('comparison_filter', {
        category_id: category,
        filter_type: 'group',
        filter_value: group
      });
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
      const visible = currentRows()
        .filter((row) => !row.hidden)
        .map((row) => Number(row.dataset.rowUnitPrice || 0))
        .filter((x) => x > 0);
      const benchmark = visible.length ? Math.min(...visible) : 0;

      let verdict = 'benchmark_unavailable';
      let text = '入力価格は ' + formatYen(unitPrice) + ' / 単位です。';
      if (benchmark > 0) {
        const diff = ((unitPrice - benchmark) / benchmark) * 100;
        if (diff <= -2) verdict = 'store_cheaper';
        else if (diff >= 2) verdict = 'online_cheaper';
        else verdict = 'roughly_same';

        text += diff <= -2
          ? ' 表示中の最安候補より約 ' + Math.abs(diff).toFixed(0) + '% 安い価格です。'
          : diff >= 2
            ? ' 表示中の最安候補より約 ' + diff.toFixed(0) + '% 高い価格です。'
            : ' 表示中の最安候補とほぼ同水準です。';
      }

      result.textContent = text;
      result.style.display = 'block';
      const group = document.querySelector('[data-group-button][aria-pressed="true"]')?.dataset.group || 'all';

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
      const link = event.target.closest('a[data-editorial-category]');
      if (!link) return;
      send('homepage_editorial_click', {
        category_id: link.dataset.editorialCategory || '',
        editorial_position: Number(link.dataset.editorialPosition || 0),
        conversion_source: 'homepage_editorial'
      });
    });

    document.addEventListener('click', (event) => {
      const link = event.target.closest('a[data-spotlight-link]');
      if (!link) return;
      send('daily_spotlight_click', {
        category_id: link.dataset.categoryId || '',
        price_gap_percent: Number(link.dataset.gapPercent || 0),
        conversion_source: 'daily_price_gap'
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
        items: [{
          item_id: data.item_id,
          item_name: data.item_name,
          index: data.position,
          affiliation: data.merchant
        }]
      });
    });
  });
})();
