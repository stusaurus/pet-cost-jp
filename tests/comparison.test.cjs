const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { JSDOM, VirtualConsole } = require('jsdom');
const root = path.resolve(__dirname, '..');
if (process.env.PET_COST_TEST_SITE !== '1') execFileSync('python3', ['scripts/build_site.py', '--reuse-data'], { cwd: root, env: { ...process.env, GA_MEASUREMENT_ID: '' } });
const categories = JSON.parse(fs.readFileSync(path.join(root, 'config/categories.json')));
const payloads = categories.map(c => JSON.parse(fs.readFileSync(path.join(root, `site/data/${c.id}.json`))));
async function open(html, id = '', options = {}) {
  const events = [], errors = [], console = new VirtualConsole();
  console.on('jsdomError', e => errors.push(e.message));
  const dom = new JSDOM(html, { url: `https://stusaurus.github.io/pet-cost-jp/${id ? `categories/${id}/` : ''}?test=1`, runScripts: 'dangerously', pretendToBeVisual: true, virtualConsole: console,
    beforeParse(window) {
      window.gtag = (...args) => events.push(args);
      window.dataLayer = [];
      window.dataLayer.push = args => events.push([...args]);
      window.matchMedia = () => ({ matches: !!options.reduced });
      if (options.household) window.localStorage.setItem('pet_cost_household_v1', JSON.stringify(options.household));
      if (options.profiles) window.localStorage.setItem('pet_cost_profiles_v1', JSON.stringify(options.profiles));
      if (options.savedProducts) window.localStorage.setItem('pet_cost_saved_products_v1', JSON.stringify(options.savedProducts));
      if (options.foodPreferences) window.localStorage.setItem('pet_cost_food_preferences_v1', JSON.stringify(options.foodPreferences));
      if (options.storageError) Object.defineProperty(window, 'localStorage', { get() { throw new Error('storage disabled'); } });
    }
  });
  await new Promise(resolve => dom.window.document.addEventListener('DOMContentLoaded', resolve));
  dom.window.document.addEventListener('click', e => { if (e.target.closest('a')) e.preventDefault(); });
  return { dom, document: dom.window.document, events, errors, close: () => dom.window.close() };
}
const get = (p, selector) => p.document.querySelector(selector);
const all = (p, selector) => [...p.document.querySelectorAll(selector)];
const text = (p, s) => get(p, s).textContent;
const events = (p, name) => p.events.filter(e => e[0] === 'event' && e[1] === name).map(e => e[2]);
const median = xs => { const s = [...xs].sort((a, b) => a - b); const m = Math.floor(s.length / 2); return s.length ? s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2 : 0; };
test('food fit precedes family prices; buying styles, duration, privacy and voluntary storage',async()=>{
  for(const key of ['dog-food','cat-food']){
    const dog=key.startsWith('dog'),family=dog?'mini-adult':'fit',pet=dog?'dog':'cat';
    let html=fs.readFileSync(path.join(root,`site/categories/${key}/index.html`),'utf8');
    const fixture=(g,price)=>`<article data-food-candidate data-family="${family}" data-age="adult" data-size="${dog?'small':''}" data-grams="${g}" data-price="${price}" data-unit="${price/g*100}" hidden><span data-food-reason></span><span data-food-duration></span><a data-affiliate-link data-category-id="${key}" data-metric="100g" data-unit-price="${price/g*100}" data-conversion-source="food_family" data-item-id="test-${g}" href="https://hb.afl.rakuten.co.jp/hgc/test/">確認</a></article>`;
    // Replace fetched rows with controlled amounts, independent of market availability.
    html=html.replace(/<div class="food-candidates">[\s\S]*?<\/div>\s*<p class="condition-note">同じ銘柄/,`<div class="food-candidates">${fixture(2000,3000)}${fixture(8000,8000)}</div><p class="condition-note">同じ銘柄`);
    const p=await open(html,key);
    try{
      assert.ok(get(p,'[data-food-results]').hidden);
      assert.equal(get(p,'[data-food-age="young"]').disabled,true);assert.equal(get(p,'[data-food-age="senior"]').disabled,true);assert.equal(get(p,'[data-food-age="adult"]').disabled,false);
      get(p,'[data-food-age="adult"]').click();if(dog){assert.equal(get(p,'[data-food-size="small"]').disabled,false);assert.equal(get(p,'[data-food-size="medium"]').disabled,true);assert.equal(get(p,'[data-food-size="large"]').disabled,true);assert.ok(get(p,'[data-food-family-option]').hidden);get(p,'[data-food-size="small"]').click();}
      assert.ok(!get(p,'[data-food-family-option]').hidden);assert.ok(get(p,'[data-food-results]').hidden);
      get(p,'[data-food-family]').click();assert.ok(!get(p,'[data-food-results]').hidden);
      assert.equal(all(p,'.food-candidates [data-food-candidate]:not([hidden])')[0].dataset.grams,'8000');
      get(p,'[data-food-order="price"]').click();assert.equal(all(p,'.food-candidates [data-food-candidate]:not([hidden])')[0].dataset.grams,'2000');
      get(p,'[data-food-order="amount"]').click();assert.equal(all(p,'.food-candidates [data-food-candidate]:not([hidden])')[0].dataset.grams,'8000');
      get(p,'[data-food-usage]').value='120';get(p,'[data-food-usage-form]').dispatchEvent(new p.dom.window.Event('submit',{bubbles:true,cancelable:true}));
      const durations=all(p,'[data-food-duration]').map(n=>n.textContent);assert.ok(durations.some(t=>t.includes('約16.7日分')&&t.includes('5,400')));assert.ok(durations.some(t=>t.includes('約66.7日分')&&t.includes('3,600')));
      assert.equal(p.dom.window.localStorage.getItem('pet_cost_food_preferences_v1'),null);
      const save=get(p,'[data-food-save]');save.checked=true;save.dispatchEvent(new p.dom.window.Event('change',{bubbles:true}));
      const stored=JSON.parse(p.dom.window.localStorage.getItem('pet_cost_food_preferences_v1'));assert.equal(stored[pet].daily,'120');assert.equal(stored[pet].family,family);
      assert.ok(!JSON.stringify(events(p,'pet_food_usage_set')).includes('120'));
      get(p,'.food-candidates [data-affiliate-link]').click();assert.equal(events(p,'affiliate_click').at(-1).unit_metric,'100g');assert.equal(events(p,'affiliate_click').at(-1).conversion_source,'food_family');assert.equal(events(p,'affiliate_click').at(-1).position,1);
      const restored=await open(html,key,{foodPreferences:stored});try{assert.ok(!get(restored,'[data-food-results]').hidden);assert.equal(get(restored,'[data-food-usage]').value,'120');assert.ok(text(restored,'[data-food-usage-status]').includes('保存した1日量'));assert.ok(text(restored,'[data-food-answer]').includes('2件'));}finally{restored.close();}
      get(p,'[data-food-usage]').value='0';get(p,'[data-food-usage-form]').dispatchEvent(new p.dom.window.Event('submit',{bubbles:true,cancelable:true}));assert.ok(text(p,'[data-food-usage-status]').includes('解除'));assert.ok(all(p,'[data-food-duration]').every(n=>!(/約[\d,.]+日分/.test(n.textContent))));
      get(p,'[data-profile-age="senior"]').click();assert.ok(get(p,'[data-food-results]').hidden);assert.equal(all(p,'[data-food-candidate]:not([hidden])').length,0);
      get(p,'[data-profile-age="adult"]').click();if(dog){get(p,'[data-profile-size="large"]').click();assert.ok(get(p,'[data-food-results]').hidden);assert.equal(get(p,'[data-food-size="large"]').disabled,true);get(p,'[data-food-size="small"]').click();}
      get(p,'[data-food-clear]').click();assert.equal(p.dom.window.localStorage.getItem('pet_cost_food_preferences_v1'),null);assert.ok(get(p,'[data-food-results]').hidden);assert.deepEqual(p.errors,[]);
    }finally{p.close();}
    const blocked=await open(html,key,{storageError:true});try{get(blocked,'[data-food-age="adult"]').click();if(dog)get(blocked,'[data-food-size="small"]').click();get(blocked,'[data-food-family]').click();get(blocked,'[data-food-save]').click();assert.ok(text(blocked,'[data-food-usage-status]').includes('保存できません'));assert.deepEqual(blocked.errors,[]);}finally{blocked.close();}
  }
});
test('pet-first journey, voluntary profile storage and telemetry privacy', async () => {
  const p=await open(fs.readFileSync(path.join(root,'site/index.html'),'utf8'));
  try {
    assert.ok(get(p,'[data-pet-routes="dog"]').hidden);
    get(p,'[data-pet-select="dog"]').click();
    assert.equal(all(p,'[data-pet-routes]:not([hidden]) [data-living-route]').length,3);
    get(p,'[data-profile-species="dog"] [data-profile-age="adult"]').click();
    get(p,'[data-profile-species="dog"] [data-profile-size="small"]').click();
    const weight=get(p,'[data-profile-species="dog"] [data-profile-weight]');weight.value='5.25';weight.dispatchEvent(new p.dom.window.Event('change',{bubbles:true}));
    const breed=get(p,'[data-profile-species="dog"] [data-profile-breed]');breed.value='秘密の犬種';breed.dispatchEvent(new p.dom.window.Event('change',{bubbles:true}));
    assert.equal(p.dom.window.localStorage.getItem('pet_cost_profiles_v1'),null);
    const save=get(p,'[data-profile-save]');save.checked=true;save.dispatchEvent(new p.dom.window.Event('change',{bubbles:true}));
    const data=JSON.parse(p.dom.window.localStorage.getItem('pet_cost_profiles_v1'));assert.equal(data.dog.weight,'5.25');assert.equal(data.dog.age,'adult');
    assert.ok(!JSON.stringify(p.events).includes('5.25'));assert.ok(!JSON.stringify(p.events).includes('秘密の犬種'));
    get(p,'[data-pet-select="cat"]').click();assert.equal(all(p,'[data-pet-routes]:not([hidden]) [data-living-route]').length,4);
    const resumeSource=get(p,'[data-pet-routes="cat"] [data-living-route="cat-litter"]');resumeSource.addEventListener('click',e=>e.preventDefault(),{once:true});resumeSource.click();
    const recent=JSON.parse(p.dom.window.localStorage.getItem('pet_cost_last_route_v1'));assert.equal(recent.species,'cat');assert.equal(recent.supply,'cat-litter');
    get(p,'[data-profile-clear]').click();assert.equal(p.dom.window.localStorage.getItem('pet_cost_profiles_v1'),null);
    assert.deepEqual(p.errors,[]);
  } finally {p.close();}
});
test('profiles restore only valid fields and work when storage is unavailable',async()=>{
  for(const options of [{profiles:{version:1,selected:'cat',cat:{age:'adult',weight:'NaN',breed:'ミックス'}}},{storageError:true}]) {
    const p=await open(fs.readFileSync(path.join(root,'site/index.html'),'utf8'),'',options);
    try {if(options.profiles){assert.ok(!get(p,'[data-pet-routes="cat"]').hidden);assert.equal(get(p,'[data-profile-species="cat"] [data-profile-weight]').value,'');}get(p,'[data-pet-select="dog"]').click();assert.ok(!get(p,'[data-pet-routes="dog"]').hidden);assert.deepEqual(p.errors,[]);}finally{p.close();}
  }
});
test('food calculator uses supplied grams and never estimates from weight',async()=>{
  for(const key of ['dog-food','cat-food']){
    const p=await open(fs.readFileSync(path.join(root,`site/categories/${key}/index.html`),'utf8'),key);
    try {get(p,'[data-food-weight]').value='2000';get(p,'[data-food-price]').value='3000';get(p,'[data-food-daily]').value='120';get(p,'[data-food-calculator]').dispatchEvent(new p.dom.window.Event('submit',{bubbles:true,cancelable:true}));const out=text(p,'[data-food-outcome]');assert.ok(out.includes('約16.7日分'));assert.ok(out.includes('約¥180'));assert.ok(out.includes('約¥5,400'));assert.ok(out.includes('約¥150'));assert.ok(out.includes('約¥1,500'));assert.deepEqual(JSON.parse(JSON.stringify(events(p,'pet_food_calculator_use').at(-1))),{site_id:'pet-cost-jp',species:key.startsWith('dog')?'dog':'cat',operator_test:'1'});get(p,'[data-food-daily]').value='0';get(p,'[data-food-calculator]').dispatchEvent(new p.dom.window.Event('submit',{bubbles:true,cancelable:true}));assert.ok(text(p,'[data-food-outcome]').includes('有効な数値'));assert.deepEqual(p.errors,[]);}finally{p.close();}
  }
});
test('play discovery filters by observed age/size and never treats unknown fit as confirmed',async()=>{
  let html=fs.readFileSync(path.join(root,'site/categories/dog-toys/index.html'),'utf8');
  html=html.replace('<div class="toy-candidates">','<div class="toy-candidates"><article data-toy-candidate data-play="chase" data-age="" data-size="small" hidden>年齢不明</article><article data-toy-candidate data-play="chase" data-age="adult" data-size="small" hidden>成犬表記</article>');
  const p=await open(html,'dog-toys');try{assert.equal(get(p,'[data-play-select="chase"]').disabled,false);get(p,'[data-play-select="chase"]').click();assert.equal(all(p,'[data-toy-candidate]:not([hidden])').length,2);get(p,'[data-profile-age="adult"]').click();assert.equal(all(p,'[data-toy-candidate]:not([hidden])').length,1);get(p,'[data-profile-age="senior"]').click();assert.equal(get(p,'[data-play-select="chase"]').disabled,true);assert.ok(!get(p,'[data-toy-empty]').hidden);get(p,'[data-profile-age-clear]').click();assert.equal(get(p,'[data-play-select="chase"]').disabled,false);assert.equal(all(p,'[data-toy-candidate]:not([hidden])').length,2);assert.deepEqual(p.errors,[]);}finally{p.close();}
});
const yen = x => x < 10 ? `¥${x.toFixed(2)}` : x < 100 ? `¥${x.toFixed(1)}` : `¥${Math.round(x).toLocaleString('ja-JP')}`;
function verify(p, category, items, group) {
  const expected = items.filter(x => group === 'all' || x.group === group).sort((a, b) => a.unit_price - b.unit_price);
  const rows = all(p, '[data-product-row]:not([hidden])');
  assert.deepEqual(rows.map(x => x.dataset.itemId), expected.map(x => x.product_id));
  assert.equal(text(p, '[data-sticky-count]'), `${expected.length}件`);
  assert.equal(text(p, '[data-sticky-condition]'), category.groups[group]);
  assert.equal(all(p, '[data-group-button][aria-pressed="true"]').length, 1);
  assert.equal(get(p, '[data-group-button][aria-pressed="true"]').dataset.group, group);
  assert.ok(get(p, '[data-condition-progress]').classList.contains('is-ready'));
  assert.equal(text(p, '[data-condition-progress]'), group === 'all' ? '素材指定なしの比較' : 'うちの条件で比較中');
  const middle = median(expected.map(x => x.unit_price));
  if (!expected.length) {
    assert.ok(get(p, '[data-featured-box]').hidden);
    assert.ok(!get(p, '[data-empty-result]').hidden);
    assert.equal(all(p, '[data-top3-card]').length, 0);
    assert.ok(get(p, '[data-angle-detail]').hidden);
    assert.ok(get(p, '[data-mobile-best]').hidden);
    return;
  }
  assert.equal(text(p, '[data-featured-unit]'), yen(expected[0].unit_price));
  assert.equal(text(p, '[data-answer-median-value]'), yen(middle));
  assert.equal(get(p, '[data-featured-box] [data-affiliate-link]').dataset.itemId, expected[0].product_id);
  assert.equal(get(p, '[data-mobile-best]').hidden, false);
  assert.equal(get(p, '[data-mobile-best-link]').dataset.itemId, expected[0].product_id);
  assert.equal(get(p, '[data-mobile-best-link]').dataset.conversionSource, 'mobile_best_bar');
  const top = all(p, '[data-top3-card]');
  assert.deepEqual(top.map(x => x.dataset.itemId), expected.slice(0, 3).map(x => x.product_id));
  const scale = Math.max(middle, ...expected.slice(0, 3).map(x => x.unit_price), 1);
  top.forEach((link, index) => {
    assert.equal(Number(link.dataset.position), index + 1);
    assert.equal(p.dom.window.getComputedStyle(link.querySelector('.bar-track')).display, 'block');
    assert.ok(Math.abs(parseFloat(link.querySelector('.bar-fill').style.getPropertyValue('--bar')) - expected[index].unit_price / scale * 100) < .01);
  });
  rows.forEach((row, index) => {
    const item = expected[index];
    assert.equal(row.querySelector('[data-rank-cell]').textContent, String(index + 1));
    assert.equal(row.querySelector('[data-affiliate-link]').href, item.url);
    assert.equal(row.querySelector('[data-affiliate-link]').dataset.itemName, item.name);
    assert.equal(Number(row.querySelector('[data-affiliate-link]').dataset.position), index + 1);
    assert.equal(row.matches('.is-rank-1, .is-rank-2, .is-rank-3'), index < 3);
    const roles = [...row.querySelectorAll('[data-reason-role]')].map(x => x.dataset.reasonRole);
    assert.equal(roles.includes('unit'), item.unit_price === expected[0].unit_price);
    assert.equal(roles.includes('median'), item.unit_price < middle * .98);
    assert.equal(roles.includes('total'), item.price === Math.min(...expected.map(x => x.price)));
    assert.equal(roles.includes('bulk'), item.quantity === Math.max(...expected.map(x => x.quantity)));
    assert.ok(!row.textContent.includes('価格特徴を比較中'));
  });
  const picks = {
    unit: [...expected].sort((a, b) => a.unit_price - b.unit_price || a.price - b.price)[0],
    total: [...expected].sort((a, b) => a.price - b.price || a.unit_price - b.unit_price)[0],
    bulk: [...expected].sort((a, b) => b.quantity - a.quantity || a.unit_price - b.unit_price)[0]
  };
  for (const [role, item] of Object.entries(picks)) {
    get(p, `[data-angle-role="${role}"]`).click();
    assert.equal(get(p, '[data-angle-link]').dataset.itemId, item.product_id);
    assert.equal(get(p, '[data-angle-link]').href, item.url);
    assert.equal(get(p, '[data-angle-link]').dataset.conversionSource, `comparison_angle_${role}`);
    assert.equal(all(p, '[data-angle-card][aria-pressed="true"]').length, 1);
  }
}
for (const { category, items } of payloads) {
  test(`${category.id}: every available filter synchronizes answer, TOP3, reasons, angles and tracking`, async () => {
    const p = await open(fs.readFileSync(path.join(root, `site/categories/${category.id}/index.html`), 'utf8'), category.id);
    try {
      assert.equal(events(p, 'comparison_view').length, 1);
      assert.equal(events(p, 'view_item_list').length, 1);
      assert.ok(get(p, '[data-comparison-results]').hidden);
      assert.equal(all(p, '[data-group-button][aria-pressed="true"]').length, 0);
      get(p, `[data-group-button][data-group="${category.default_group}"]`).click();
      verify(p, category, items, category.default_group);
      for (const button of all(p, '[data-group-button]')) {
        button.click();
        verify(p, category, items, button.dataset.group);
      }
      for (const e of events(p, 'comparison_filter')) {
        const selection = items.filter(x => e.filter_value === 'all' || x.group === e.filter_value);
        assert.equal(e.result_count, selection.length);
        assert.equal(e.median_unit_price, median(selection.map(x => x.unit_price)));
        assert.equal(e.site_id, 'pet-cost-jp');
        assert.equal(e.operator_test, '1');
      }
      const button = get(p, '[data-group-button][aria-pressed="true"]');
      const n = events(p, 'comparison_filter').length;
      button.click(); assert.equal(events(p, 'comparison_filter').length, n);
      const links = all(p, '[data-affiliate-link]').filter(a => !a.closest('[hidden]'));
      for (const link of links) {
        link.click();
        const e = events(p, 'affiliate_click').at(-1);
        assert.equal(e.item_id, link.dataset.itemId);
        assert.equal(e.position, Number(link.dataset.position));
        assert.equal(e.conversion_source, link.dataset.conversionSource);
        assert.equal(e.unit_metric, category.metric);
        assert.equal(e.operator_test, '1');
      }
      assert.equal(events(p, 'affiliate_click').length, links.length);
      assert.equal(events(p, 'product_result_click').length, links.length);
      assert.equal(events(p, 'select_item').length, links.length);
      assert.equal(p.dom.window.localStorage.getItem('pet_cost_operator_test_v1'), '1');
      assert.equal(p.dom.window.location.search, '');
      assert.deepEqual(p.errors, []);
    } finally { p.close(); }
  });
  test(`${category.id}: store comparison accepts decimals, rejects invalid input and refreshes benchmark on filter change`, async () => {
    const p = await open(fs.readFileSync(path.join(root, `site/categories/${category.id}/index.html`), 'utf8'), category.id);
    try {
      get(p, `[data-group-button][data-group="${category.default_group}"]`).click();
      const price = get(p, '[data-calc-price]'), qty = get(p, '[data-calc-qty]'), submit = get(p, '[data-calc-button]');
      for (const [a, b] of [['', '100'], ['0', '100'], ['-1', '100'], ['1e3', '100'], ['1000', '0'], ['1,00', '10']]) {
        price.value = a; qty.value = b; submit.click();
        assert.ok(!get(p, '[data-calc-error]').hidden);
        assert.ok(get(p, '[data-calc-result]').hidden);
      }
      assert.equal(events(p, 'unit_calculator_use').length, 0);
      price.value = '１，０００'; qty.value = '２．５'; submit.click();
      assert.ok(text(p, '[data-calc-result]').includes(`¥400 / ${category.metric_label}`));
      assert.equal(events(p, 'unit_calculator_use').at(-1).calculated_unit_price, 400);
      const button = all(p, '[data-group-button]').find(b => b.dataset.group !== category.default_group) || get(p, '[data-group-button]');
      button.click();
      const group = button.dataset.group;
      assert.ok(text(p, '[data-calc-result]').includes(category.groups[group]));
      const selection = items.filter(x => group === 'all' || x.group === group);
      if (!selection.length) { assert.ok(text(p, '[data-calc-result]').includes('比較できる掲載商品がありません')); return; }
      const best = Math.min(...selection.map(x => x.unit_price));
      assert.ok(text(p, '[data-calc-result]').includes(yen(best)));
      assert.equal(events(p, 'unit_calculator_use').length, 1);
      price.value = String(best * 100 * .5); qty.value = '100';
      price.dispatchEvent(new p.dom.window.Event('input', { bubbles: true }));
      assert.ok(text(p, '[data-calc-result]').includes('安い店頭価格'));
      submit.click();
      assert.equal(events(p, 'unit_calculator_use').at(-1).comparison_result, 'store_cheaper');
      assert.equal(events(p, 'unit_calculator_use').at(-1).benchmark_unit_price, best);
      assert.deepEqual(p.errors, []);
    } finally { p.close(); }
  });
}
function render(category, items) {
  return execFileSync('python3', ['-c', "import sys,json;sys.path.insert(0,'scripts');import build_site;p=json.load(sys.stdin);print(build_site.category_page(p['category'],p['items'],[p['category']],'2026-09-30 07:00 JST'))"], { cwd: root, input: JSON.stringify({ category, items }), env: { ...process.env, GA_MEASUREMENT_ID: '' }, encoding: 'utf8' });
}
test('tied minima, even median, one-item and empty groups have honest states', async () => {
  const category = { ...categories[0], groups: { regular: 'レギュラー', wide: 'ワイド', super_wide: 'スーパーワイド' } };
  const base = payloads[0].items[0];
  const items = [4, 4, 10, 20].map((u, i) => ({ ...base, product_id: `tie-${i}`, group: 'regular', unit_price: u, price: u * 100, quantity: 100 })).concat([{ ...base, product_id: 'one', group: 'wide', unit_price: 8, price: 800, quantity: 100 }]);
  const p = await open(render(category, items), category.id);
  try {
    get(p, '[data-group-button][data-group="regular"]').click();
    verify(p, category, items, 'regular');
    assert.equal(text(p, '[data-answer-median-value]'), '¥7.00');
    assert.ok(text(p, '[data-featured-badge]').includes('同単価 2件'));
    get(p, '[data-group="wide"][data-group-button]').click();
    verify(p, category, items, 'wide');
    assert.equal(text(p, '[data-featured-gap-amount]'), '¥0.00 / 1枚の差');
  } finally { p.close(); }
  const emptyCategory = { ...category, default_group: 'super_wide' };
  const empty = await open(render(emptyCategory, items), category.id);
  try {
    get(empty, '[data-group-button][data-group="super_wide"]').click();
    verify(empty, emptyCategory, items, 'super_wide');
    get(empty, '[data-calc-price]').value = '1000'; get(empty, '[data-calc-qty]').value = '100'; get(empty, '[data-calc-button]').click();
    assert.equal(events(empty, 'unit_calculator_use').at(-1).comparison_result, 'benchmark_unavailable');
    get(empty, '[data-group="regular"][data-group-button]').click();
    verify(empty, emptyCategory, items, 'regular');
    assert.equal(all(empty, '[data-angle-card] .angle-symbol svg').length, 3);
    assert.equal(all(empty, '[data-angle-card] .angle-state').length, 3);
    assert.ok(text(empty, '[data-calc-result]').includes('高い店頭価格'));
  } finally { empty.close(); }
});
test('homepage merged entry preserves both existing analytics events', async () => {
  const p = await open(fs.readFileSync(path.join(root, 'site/index.html'), 'utf8'));
  try {
    for (const link of all(p, '[data-editorial-category]')) link.click();
    assert.equal(events(p, 'homepage_editorial_click').length, 3);
    assert.equal(events(p, 'daily_spotlight_click').length, 3);
    assert.equal(events(p, 'affiliate_click').length, 0);
    assert.equal(events(p, 'comparison_view').length, 0);
    assert.deepEqual(p.errors, []);
  } finally { p.close(); }
});
test('quiet comparison standards opens from the trust strip without changing shopping telemetry', async () => {
  const p = await open(fs.readFileSync(path.join(root, 'site/index.html'), 'utf8'));
  try {
    const details = get(p, '#comparison-standards');
    assert.equal(details.open, false);
    get(p, '[data-open-standards]').click();
    assert.equal(details.open, true);
    assert.ok(details.textContent.includes('品質やペットとの相性'));
    assert.ok(details.textContent.includes('送料別の送料は未加算'));
    assert.equal(events(p, 'affiliate_click').length, 0);
    assert.equal(events(p, 'pet_category_select').length, 0);
    assert.ok(get(p, '.home-scene img').src.endsWith('/assets/living/home.webp'));
    assert.equal(all(p, '[data-pet-category] .care-art img.editorial-art').length, 3);
    assert.equal(all(p, '[data-pet-category] .care-art svg').length, 0);
    assert.deepEqual(p.errors, []);
  } finally { p.close(); }
});
test('reduced motion still updates immediately without result animation', async () => {
  const p = await open(fs.readFileSync(path.join(root, 'site/categories/pet-sheets/index.html'), 'utf8'), 'pet-sheets', { reduced: true });
  try {
    get(p, '[data-group-button][data-group="wide"]').click();
    assert.equal(all(p, '.result-changed').length, 0);
    assert.equal(text(p, '[data-sticky-condition]'), 'ワイド');
  } finally { p.close(); }
});

const usageExamples = [
  { index: 0, group: 'regular', qty: 800, price: 3280, rate: '5', supply: '約160日分', monthly: '約¥615', days: '約160日', smallSupply: '約40日分', otherMonthly: '約¥923' },
  { index: 1, group: 'paper', qty: 42, price: 2499, rate: '10', supply: '約4.2か月分', monthly: '約¥595', days: '約126日', smallSupply: '約1.1か月分', otherMonthly: '約¥893' },
  { index: 2, group: 'deotoilet', qty: 20, price: 1750, rate: '1', supply: '約20週間分', monthly: '約¥375', days: '約140日', smallSupply: '約5週間分', otherMonthly: '約¥563' }
];
for (const example of usageExamples) {
  test(`${categories[example.index].id}: optional usage translates supply and 30-day cost across all comparison surfaces`, async () => {
    const c = categories[example.index], base = payloads[example.index].items[0];
    const item = { ...base, product_id: 'usage-example', group: example.group, quantity: example.qty, price: example.price, unit_price: example.price / example.qty };
    const small = { ...item, product_id: 'small-pack', quantity: example.qty / 4, price: example.price / 3, unit_price: example.price / 3 / (example.qty / 4) };
    const otherGroup = Object.keys(c.groups).find(g => g !== example.group && g !== 'all');
    const other = { ...item, product_id: 'other-group', group: otherGroup, quantity: example.qty / 2, price: example.price * .75, unit_price: example.price * .75 / (example.qty / 2) };
    const p = await open(render(c, [item, small, other]), c.id);
    try {
      assert.ok(get(p, '[data-comparison-results]').hidden);
      get(p, `[data-group-button][data-group="${example.group}"]`).click();
      assert.ok(!get(p, '[data-comparison-results]').hidden);
      assert.ok(get(p, '[data-featured-usage]').hidden);
      assert.equal(get(p, '[data-usage-input]').value, '');
      const input = get(p, '[data-usage-input]');
      input.value = example.rate;
      input.dispatchEvent(new p.dom.window.Event('input', { bubbles: true }));
      assert.ok(text(p, '[data-featured-usage]').includes(example.supply));
      assert.ok(text(p, '[data-featured-usage]').includes(example.monthly));
      assert.ok(text(p, '[data-featured-usage]').includes(example.days));
      assert.ok(text(p, '[data-top3-card] [data-top3-usage]').includes(example.supply));
      assert.ok(text(p, '[data-product-row]:not([hidden]) [data-row-usage]').includes(example.supply));
      assert.equal(events(p, 'pet_usage_change').length, 0);
      input.dispatchEvent(new p.dom.window.Event('change', { bubbles: true }));
      get(p, '[data-usage-form] button[type="submit"]').click();
      assert.equal(events(p, 'pet_usage_change').length, 1);
      assert.equal(events(p, 'pet_usage_change')[0].usage_enabled, true);
      for (const role of ['unit', 'total', 'bulk']) {
        const button = get(p, `[data-angle-role="${role}"]`);
        assert.ok(!button.querySelector('[data-angle-lifetime]').hidden);
        button.click();
        const smallChosen = get(p, '[data-angle-link]').dataset.itemId === small.product_id;
        assert.ok(text(p, '[data-angle-usage]').includes(smallChosen ? example.smallSupply : example.supply));
      }
      const before = events(p, 'pet_usage_change').length;
      get(p, `[data-group-button][data-group="${otherGroup}"]`).click();
      assert.equal(events(p, 'pet_usage_change').length, before);
      assert.equal(input.value, example.rate);
      assert.ok(!get(p, '[data-featured-usage]').hidden);
      assert.ok(text(p, '[data-featured-usage]').includes(example.otherMonthly));
      for (const value of ['0', '-1', '1e3', '1,00', 'abc']) {
        input.value = value; input.dispatchEvent(new p.dom.window.Event('input', { bubbles: true }));
        assert.ok(!get(p, '[data-usage-error]').hidden);
        assert.ok(get(p, '[data-featured-usage]').hidden);
        assert.ok(get(p, '[data-angle-usage]').hidden);
        assert.equal(all(p, '[data-row-usage]:not([hidden])').length, 0);
      }
      input.value = '２．５'; input.dispatchEvent(new p.dom.window.Event('change', { bubbles: true }));
      assert.ok(!get(p, '[data-featured-usage]').hidden);
      assert.ok(get(p, '[data-usage-error]').hidden);
      get(p, '[data-usage-clear]').click();
      assert.ok(get(p, '[data-featured-usage]').hidden);
      assert.equal(input.value, '');
      assert.equal(events(p, 'pet_usage_change').at(-1).usage_enabled, false);
      assert.deepEqual(JSON.parse(p.dom.window.localStorage.getItem('pet_cost_household_v1'))[c.id], { group: otherGroup, usage: null });
      assert.deepEqual(p.errors, []);
    } finally { p.close(); }
  });
}
test('remembered household conditions restore per category; unavailable groups and blocked storage stay usable', async () => {
  const html = fs.readFileSync(path.join(root, 'site/categories/pet-sheets/index.html'), 'utf8');
  const p = await open(html, 'pet-sheets', { household: { 'pet-sheets': { group: 'wide', usage: 5 }, 'cat-litter': { group: 'paper', usage: 10 } } });
  try {
    assert.ok(!get(p, '[data-comparison-results]').hidden);
    assert.equal(text(p, '[data-sticky-condition]'), 'ワイド');
    assert.equal(get(p, '[data-usage-input]').value, '5');
    assert.ok(!get(p, '[data-featured-usage]').hidden);
    assert.equal(events(p, 'pet_usage_change').length, 0);
    assert.equal(events(p, 'comparison_filter').length, 0);
  } finally { p.close(); }
  for (const options of [{ household: { 'pet-sheets': { group: 'unavailable', usage: 5 } } }, { storageError: true }]) {
    const p = await open(html, 'pet-sheets', options);
    try {
      assert.ok(get(p, '[data-comparison-results]').hidden);
      get(p, '[data-group-button][data-group="regular"]').click();
      assert.ok(!get(p, '[data-comparison-results]').hidden);
      assert.deepEqual(p.errors, []);
    } finally { p.close(); }
  }
});
test('homepage starts with household choices and keeps price-gap analytics on the secondary disclosure', async () => {
  const p = await open(fs.readFileSync(path.join(root, 'site/index.html'), 'utf8'), '', { household: { 'cat-litter': { group: 'paper', usage: 10 } } });
  try {
    assert.ok(text(p, '[data-pet-category="cat-litter"] [data-saved-condition]').includes('前回の条件：紙'));
    for (const link of all(p, '[data-pet-category]')) link.click();
    assert.equal(events(p, 'pet_category_select').length, 3);
    assert.equal(events(p, 'daily_spotlight_click').length, 0);
    assert.ok(!get(p, '.home-price-details').open);
  } finally { p.close(); }
});

test('unsaved profile choices carry to food and toy routes without personal fields',async()=>{
 const p=await open(fs.readFileSync(path.join(root,'site/index.html'),'utf8'));
 try{get(p,'[data-pet-select="dog"]').click();get(p,'[data-profile-age="adult"]').click();get(p,'[data-profile-size="small"]').click();const link=get(p,'[data-living-route="dog-food"]');assert.ok(link.href.includes('age=adult'));assert.ok(link.href.includes('size=small'));assert.ok(!link.href.includes('weight'));assert.equal(p.dom.window.localStorage.getItem('pet_cost_profiles_v1'),null);}finally{p.close();}
});
test('save, restore, same-condition comparison, honest history and click attribution',async()=>{
 const html=fs.readFileSync(path.join(root,'site/categories/pet-sheets/index.html'),'utf8');const p=await open(html,'pet-sheets');
 try{
  const rows=JSON.parse(get(p,'#decision-data').textContent).filter(r=>r.category==='pet-sheets');const first=rows[0], same=rows.find(r=>r.group===first.group&&r.key!==first.key), other=rows.find(r=>r.group!==first.group);
  get(p,`[data-product-save="${first.key}"]`).click();assert.equal(JSON.parse(p.dom.window.localStorage.getItem('pet_cost_saved_products_v1'))[0],first.key);assert.ok(text(p,'[data-saved-products]').includes(first.name));
  get(p,`[data-product-compare="${first.key}"]`).click();get(p,`[data-product-compare="${same.key}"]`).click();assert.equal(all(p,'.decision-grid article').length,2);
  if(other){get(p,`[data-product-compare="${other.key}"]`).click();assert.equal(all(p,'.decision-grid article').length,2);assert.ok(text(p,'[data-decision-status]').includes('同じカテゴリ'));}
  get(p,'.decision-grid [data-affiliate-link]').click();assert.equal(events(p,'affiliate_click').at(-1).conversion_source,'saved_comparison');assert.equal(events(p,'affiliate_click').at(-1).operator_test,'1');assert.equal(events(p,'product_save').length,1);assert.deepEqual(p.errors,[]);
  assert.ok(get(p,'.observed-prices').textContent.includes('実際に取得した商品価格'));
  const restored=await open(html,'pet-sheets',{savedProducts:[first.key,'no-longer-published']});try{assert.ok(text(restored,'[data-saved-products]').includes(first.name));assert.ok(text(restored,'[data-saved-products]').includes('掲載対象外'));assert.equal(get(restored,`[data-product-save="${first.key}"]`).getAttribute('aria-pressed'),'true');assert.deepEqual(restored.errors,[]);}finally{restored.close();}
 }finally{p.close();}
});

test('food comparison labels keep dog and cat suitability separate',async()=>{
 for(const category of ['dog-food','cat-food']){
  const p=await open(fs.readFileSync(path.join(root,`site/categories/${category}/index.html`),'utf8'),category);
  try{get(p,'[data-food-age="adult"]').click();if(category==='dog-food')get(p,'[data-food-size="small"]').click();get(p,'[data-food-family]').click();const b=get(p,'[data-product-compare]');if(b){b.click();const label=text(p,'[data-product-comparison]');assert.ok(label.includes(category==='dog-food'?'成犬用':'成猫用'));assert.ok(!label.includes(category==='dog-food'?'成猫用':'成犬用'));}}finally{p.close();}
 }
});
