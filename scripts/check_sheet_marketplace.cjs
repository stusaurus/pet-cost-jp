// Read-only browser audit: never visit real affiliate destinations or send analytics.
const {chromium,webkit}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const base='https://stusaurus.github.io/pet-cost-jp/';
const fixture=process.env.SHEET_MARKETPLACE_FIXTURE==='1';
const groups={regular:'レギュラー',wide:'ワイド','super-wide':'スーパーワイド'};
const specs={'4520699667989':['regular',112],'4520699672143':['wide',54],
 '4520699676066':['super-wide',23],'4972316207571':['super-wide',36]};
const pages=['','regular/','wide/','super-wide/'];
const root=path.resolve(__dirname,'..');
function verifyLink(link,jan){
 const u=new URL(link.href); assert.equal(u.protocol,'https:');
 assert.equal(link.id,jan); assert.equal(link.source,'marketplace_comparison');
 assert.equal(link.metric,'per_sheet'); assert.equal(link.category,'pet-sheets');
 for(const rel of ['sponsored','nofollow','noopener']) assert(link.rel.split(/\s+/).includes(rel));
 assert.equal(link.target,'_blank');
 if(link.mall==='rakuten'){
  assert.equal(u.hostname,'hb.afl.rakuten.co.jp');
  const t=new URL(u.searchParams.get('pc'));
  assert.equal(t.protocol,'https:');assert.equal(t.hostname,'item.rakuten.co.jp');
  assert.match(t.pathname,/^\/[\w-]+\/[\w.-]+\/?$/);
 }else{
  assert.equal(link.mall,'yahoo'); assert.equal(u.hostname,'ck.jp.ap.valuecommerce.com');
  assert.equal(u.pathname,'/servlet/referral');
  for(const key of ['sid','pid']) assert.match(u.searchParams.get(key)||'',/^\d+$/);
  if(!fixture){assert.equal(u.searchParams.get('sid'),'3790024');assert.equal(u.searchParams.get('pid'),'892760229');}
  const t=new URL(u.searchParams.get('vc_url'));assert.equal(t.protocol,'https:');
  assert(['store.shopping.yahoo.co.jp','lohaco.yahoo.co.jp'].includes(t.hostname));
  assert(t.hostname==='store.shopping.yahoo.co.jp'?/^\/[\w-]+\/[\w.-]+\.html$/.test(t.pathname):/^\/store\/h-lohaco\/item\/[\w-]+\/?$/i.test(t.pathname));
 }
}
(async()=>{
 const results=[];
 for(const [browserName,engine] of Object.entries({chromium,webkit})){
  const browser=await engine.launch();
  try{
   for(const width of [320,390,1440]){
    const context=await browser.newContext({viewport:{width,height:900},locale:'ja-JP'});
    await context.addInitScript(()=>{window.__marketplaceEvents=[];window.addEventListener('DOMContentLoaded',()=>{
      window.gtag=(...args)=>window.__marketplaceEvents.push(args);
      document.addEventListener('click',e=>{if(e.target.closest('#sheet-marketplace a[data-affiliate-link]'))e.preventDefault();},true);
    });});
    await context.route('**/*',route=>{
      const u=new URL(route.request().url());
      if(fixture&&u.origin==='https://stusaurus.github.io'&&u.pathname.startsWith('/pet-cost-jp/')){
        const rel=u.pathname.slice('/pet-cost-jp/'.length);
        const f=path.resolve(root,'site',rel.endsWith('/')?rel+'index.html':rel);
        if(f.startsWith(path.join(root,'site')+path.sep)&&fs.existsSync(f)&&fs.statSync(f).isFile())return route.fulfill({path:f});
        return route.abort();
      }
      if(!fixture&&u.origin==='https://stusaurus.github.io')return route.continue();
      return route.abort();
    });
    const expected=new Map();
    for(const suffix of pages){
     const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
     const response=await page.goto(base+'categories/pet-sheets/'+suffix+'?test=1',{waitUntil:'domcontentloaded'});
     assert.equal(response.status(),200);
     const cards=await page.locator('[data-sheet-marketplace-jan]').evaluateAll(nodes=>nodes.map(n=>({
       jan:n.dataset.sheetMarketplaceJan,title:n.querySelector('h3').textContent,
       note:n.querySelector('.sheet-mall-note').textContent,
       offers:[...n.querySelectorAll('.sheet-mall-offer')].map(o=>{const a=o.querySelector('a[data-affiliate-link]');return {
        text:o.textContent,price:Number(o.querySelector('.sheet-mall-price').textContent.replace(/[^0-9]/g,'')),
        mall:a.dataset.merchant,href:a.href,rel:a.rel,target:a.target,id:a.dataset.itemId,
        category:a.dataset.categoryId,source:a.dataset.conversionSource,metric:a.dataset.metric,
        unit:Number(a.dataset.unitPrice),width:a.getBoundingClientRect().width,height:a.getBoundingClientRect().height};})})));
     if(!suffix)assert(cards.length>0,'No published comparison pairs; investigate fresh retrieval');
     else assert.deepEqual(cards.map(c=>c.jan),[...expected.keys()].filter(j=>specs[j][0]===suffix.slice(0,-1)));
     for(const c of cards){
      assert(specs[c.jan],'Unknown JAN');const [group,count]=specs[c.jan];
      assert(c.title.includes(groups[group]));assert(c.title.includes(count+'枚'));
      assert.deepEqual(c.offers.map(o=>o.mall),['rakuten','yahoo']);
      for(const o of c.offers){verifyLink(o,c.jan);assert(o.price>0);assert(Math.abs(o.unit-o.price/count)<=0.000051);
       assert(o.text.includes((o.price/count).toLocaleString('en-US',{minimumFractionDigits:1,maximumFractionDigits:1})+'円'));
       assert(o.width>0&&o.height>=44);if(o.text.includes('送料・条件は販売店で確認'))assert(o.text.includes('購入総額：送料未確定'));}
      const [a,b]=c.offers;
      assert(c.note.includes('送料差は未反映'));
      if(a.price===b.price)assert(c.note.includes('同額'));
      else assert(c.note.includes(Math.abs(a.price-b.price).toLocaleString('en-US')+'円低い'));
      if(!suffix){assert(!expected.has(c.jan));expected.set(c.jan,c.offers.map(o=>[o.mall,o.price,o.href]));}
      else assert.deepEqual(c.offers.map(o=>[o.mall,o.price,o.href]),expected.get(c.jan));
     }
     if(cards.length){
      assert(await page.locator('#sheet-marketplace a[href="https://developer.yahoo.co.jp/sitemap/"]').count()===1);
      for(const mall of ['rakuten','yahoo']){
       await page.locator('#sheet-marketplace a[data-merchant="'+mall+'"]').first().click();
       assert(await page.evaluate(m=>window.__marketplaceEvents.some(e=>e[0]==='event'&&e[1]==='affiliate_click'&&e[2]?.merchant===m&&e[2]?.operator_test==='1'&&e[2]?.conversion_source==='marketplace_comparison'),mall));
      }
      const out=path.join(root,'audit-results','marketplace',browserName);fs.mkdirSync(out,{recursive:true});
      await page.locator('#sheet-marketplace').screenshot({path:path.join(out,(suffix.replace('/','')||'all')+'-'+width+'.png')});
     }
     assert.equal(errors.length,0);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2),'Horizontal overflow');
     results.push({browser:browserName,width,page:suffix||'all',pairs:cards.length});
     await page.close();
    }
    await context.close();
   }
  }finally{await browser.close();}
 }
 console.log('MARKETPLACE_AUDIT '+JSON.stringify(results));
})().catch(e=>{console.error(e.message);process.exitCode=1});
