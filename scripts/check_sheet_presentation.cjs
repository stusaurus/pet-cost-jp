// Offline product catalog, real Chromium; never navigate to an affiliate.
const {chromium,webkit}=require('playwright');
const browserName=process.env.SHEET_QA_BROWSER||'chromium';
if(!['chromium','webkit'].includes(browserName))throw new Error('Unsupported sheet QA browser');
const publicSite=process.env.SHEET_QA_PUBLIC==='1';
const qaUrl=(publicSite?'https://stusaurus.github.io/pet-cost-jp/':'http://127.0.0.1:8776/pet-cost-jp/')+'categories/pet-sheets/?test=1';
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),out=path.join(root,'audit-results/sheet-presentation',browserName);
fs.mkdirSync(out,{recursive:true});
const server=http.createServer((req,res)=>{
 const rel=new URL(req.url,'http://localhost').pathname.replace(/^\/pet-cost-jp\//,'');
 const file=path.resolve(root,'site',rel.endsWith('/')?rel+'index.html':rel);
 if(!file.startsWith(path.join(root,'site')+path.sep)||!fs.existsSync(file)||fs.statSync(file).isDirectory()){res.writeHead(404);res.end();return;}
 res.setHeader('Content-Type',({'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json','.webp':'image/webp','.svg':'image/svg+xml'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);
});
(async()=>{
 await new Promise(resolve=>server.listen(8776,'127.0.0.1',resolve));
 const browser=await ({chromium,webkit}[browserName]).launch(),records=[];
 try{
  for(const width of [320,390,1440]){
   const context=await browser.newContext({viewport:{width,height:900},isMobile:width<500,hasTouch:width<500});
   await context.route(/google-analytics\.com|googletagmanager\.com|analytics\.google\.com/,r=>r.abort());
   const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
   const response=await page.goto(qaUrl,{waitUntil:'networkidle'});
   assert.equal(response.status(),200);
   assert.equal(await page.locator('[data-size-summary]').count(),3);
   const monthlyGuide=page.locator('.monthly-sheet-guide');
   assert(await monthlyGuide.isVisible());
   assert.equal(await monthlyGuide.locator('.monthly-sheet-examples li').count(),4);
   assert((await monthlyGuide.innerText()).includes('30日で150枚'));
   const thickness=page.locator('.sheet-thickness-guide');
   assert.equal(await thickness.evaluate(el=>el.open),false);
   await thickness.locator('summary').click();
   assert(await page.locator('#sheet-thickness-cost').isVisible());
   const reference=monthlyGuide.locator('a[href="https://www.aeonpet.com/topics/pet-column_175.html"]');
   assert.equal(await reference.count(),1);
   assert.equal(await reference.getAttribute('data-affiliate-link'),null);
   assert((await monthlyGuide.innerText()).includes('吸収性能の順位ではありません'));
   assert.equal(await page.locator('h1').count(),1);
   assert(await page.locator('meta[name=description]').getAttribute('content'));
   assert(await page.evaluate(()=>[...document.querySelectorAll('script[type="application/ld+json"]')].every(el=>{try{JSON.parse(el.textContent);return true}catch{return false}})));
   await monthlyGuide.screenshot({path:path.join(out,'thickness-guide-'+width+'.png'),animations:'disabled'});
   await monthlyGuide.locator('a[href="#comparison-conditions"]').last().click();
   assert.equal(await page.locator('#comparison-conditions').count(),1);
   await thickness.locator('summary').click();
   assert.equal(await thickness.evaluate(el=>el.open),false);
   assert(await page.locator('[data-size-summary]').first().isVisible());
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));
   const canonical=await page.locator('link[rel=canonical]').getAttribute('href');
   assert.equal(canonical,'https://stusaurus.github.io/pet-cost-jp/categories/pet-sheets/');
   for(const link of await page.locator('[data-size-overview]').all()){
    const group=await link.getAttribute('data-size-overview');await link.click();
    assert.equal(await page.locator('[data-group-button][aria-pressed=true]').getAttribute('data-group'),group);
    const rows=await page.locator('[data-product-row]:visible').evaluateAll(rows=>rows.map(row=>row.dataset.group));
    assert(rows.length>0&&rows.every(g=>g===group));
    const purchase=page.locator('[data-product-row]:visible [data-affiliate-link]').first();
    assert((await purchase.getAttribute('href')).startsWith('https://'));
    assert((await purchase.getAttribute('rel')).includes('sponsored'));
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));
   }
   const usagePanel=page.locator('[data-usage-panel]');
   assert(await usagePanel.evaluate(el=>el.open===true),'Sheet usage must expand after size choice');
   await page.locator('[data-usage-input]').fill('5');
   await page.locator('[data-usage-form] button[type=submit]').click();
   assert((await page.locator('[data-row-usage]:visible').count())>0);
   const first=page.locator('[data-product-row]:visible').first();
   const setSize=Number(await first.getAttribute('data-quantity'));
   const productPrice=Number(await first.getAttribute('data-total-price'));
   const shipping=await first.getAttribute('data-shipping');
   const sets=Math.ceil(150/setSize),leftover=sets*setSize-150;
   const plan=page.locator('[data-featured-usage] [data-sheet-purchase-plan]');
   assert(await plan.isVisible(),'Published purchase plan should show after input');
   const details=await plan.innerText();
   assert(details.includes('150枚'));
   assert(details.includes(sets+'セット'));
   assert(details.includes(leftover+'枚'));
   assert(details.includes('¥'+(sets*productPrice).toLocaleString('ja-JP')));
   assert(details.includes(shipping==='送料込み'?'送料込み表示':'送料未加算'));
   // Real published rows: exclude shipping-unknown offers from 30-day checkout choice.
   const eligible=await page.locator('[data-product-row]:visible').evaluateAll(rows=>rows
     .filter(row=>row.dataset.shipping==='送料込み')
     .map(row=>({id:row.dataset.itemId,quantity:Number(row.dataset.quantity),
       price:Number(row.dataset.totalPrice)}))
     .filter(row=>Number.isSafeInteger(row.quantity)&&row.quantity>0&&row.price>0));
   const cashChoice=page.locator('[data-angle-role="total"]');
   if(eligible.length>=2){
     const expected=[...eligible].sort((a,b)=>
       Math.ceil(150/a.quantity)*a.price-Math.ceil(150/b.quantity)*b.price||
       a.price/a.quantity-b.price/b.quantity||a.price-b.price)[0];
     assert.match(await cashChoice.innerText(),/30日分の購入額/);
     await cashChoice.click();
     assert.equal(await page.locator('[data-angle-link]').getAttribute('data-item-id'),expected.id);
     assert.match(await page.locator('[data-angle-reason]').innerText(),/送料込み表示/);
     assert((await cashChoice.innerText()).includes('¥'+(Math.ceil(150/expected.quantity)*expected.price).toLocaleString('ja-JP')));
   }else{
     assert.match(await cashChoice.innerText(),/今日は出費を抑える/);
     assert(!(await cashChoice.innerText()).includes('30日分の購入額'));
   }
   const stockInput=page.locator('[data-sheet-stock-input]');
   assert.equal(await stockInput.inputValue(),'0');
   await stockInput.fill('150');
   assert((await plan.innerText()).includes('今は買い足し不要'));
   assert((await plan.innerText()).includes('0セット'));
   assert((await plan.innerText()).includes('¥0'));
   await cashChoice.click();
   assert.match(await page.locator('[data-angle-reason]').innerText(),/手持ちシーツだけ/);
   assert.equal(await page.locator('[data-angle-link]').isVisible(),false);
   await plan.screenshot({path:path.join(out,'no-buy-'+width+'.png'),animations:'disabled'});
   await stockInput.fill('40');
   assert((await plan.innerText()).includes('110枚'));
   assert((await plan.innerText()).includes(Math.ceil(110/setSize)+'セット'));
   assert((await plan.innerText()).includes('¥'+(Math.ceil(110/setSize)*productPrice).toLocaleString('ja-JP')));
   assert.equal(await page.locator('[data-angle-link]').isVisible(),true);
   await stockInput.fill('-1');
   assert.equal(await page.locator('[data-sheet-stock-error]').isVisible(),true);
   assert.equal(await plan.count(),0);
   await stockInput.fill('0');
   assert.equal(await plan.isVisible(),true);
   const currentGroup=await page.locator('[data-group-button][aria-pressed=true]').getAttribute('data-group');
   await stockInput.fill('150');
   const nextGroup=await page.locator('[data-group-button]').evaluateAll((buttons,selected)=>buttons.map(b=>b.dataset.group).find(g=>g!==selected),currentGroup);
   if(nextGroup){
     await page.locator('[data-group-button][data-group="'+nextGroup+'"]').click();
     assert.equal(await stockInput.inputValue(),'0');
     assert.equal(await page.locator('[data-sheet-stock-error]').isVisible(),false);
   }
   await cashChoice.screenshot({path:path.join(out,'checkout-choice-'+width+'.png'),animations:'disabled'});
   await plan.scrollIntoViewIfNeeded();
   await page.screenshot({path:path.join(out,'purchase-plan-'+width+'.png'),animations:'disabled'});
   assert.equal(errors.length,0,errors.join(','));
   await page.screenshot({path:path.join(out,`comparison-${width}.png`),fullPage:true,animations:'disabled'});
   await page.locator('[data-size-summary]').first().scrollIntoViewIfNeeded();
   await page.screenshot({path:path.join(out,`overview-${width}.png`),animations:'disabled'});
   records.push({browser:browserName,width,status:response.status(),canonical,errors,overflow:false,
     purchasePlanVerified:true,stockNoBuyVerified:true,stockFitResetVerified:true,requiredSheets:150,setsToBuy:sets});await context.close();
  }
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({status:'PASS',records},null,2));
  if(browserName!=='chromium'||publicSite)return; // Lighthouse already runs in the unpublished preflight.
  const {default:lighthouse}=await import(require.resolve('lighthouse'));
  const launcher=await import(require.resolve('chrome-launcher'));
  // Give each Lighthouse run its own Chrome process so mobile and desktop
  // audits cannot share a broken CDP session or exhausted shared memory.
  for(const desktop of [false,true]){
   const chrome=await launcher.launch({chromePath:chromium.executablePath(),
    chromeFlags:['--headless','--no-sandbox','--disable-dev-shm-usage']});
   try{
    const result=await lighthouse('http://127.0.0.1:8776/pet-cost-jp/categories/pet-sheets/?test=1',
     {port:chrome.port,output:'json',onlyCategories:['performance','accessibility','best-practices','seo'],
      blockedUrlPatterns:['*googletagmanager.com*','*google-analytics.com*','*analytics.google.com*'],
      ...(desktop?{formFactor:'desktop',screenEmulation:{mobile:false,width:1440,height:900,deviceScaleFactor:1,disabled:false},throttlingMethod:'provided'}:{})});
    assert(!result.lhr.runtimeError);
    fs.writeFileSync(path.join(out,`lighthouse-${desktop?'desktop':'mobile'}.json`),result.report);
    console.log('LIGHTHOUSE',desktop?'desktop':'mobile',JSON.stringify(Object.fromEntries(Object.entries(result.lhr.categories).map(([k,v])=>[k,v.score]))));
   }finally{await chrome.kill();}
  }
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
