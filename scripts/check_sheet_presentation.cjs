// Offline product catalog, real Chromium; never navigate to an affiliate.
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),out=path.join(root,'audit-results/sheet-presentation');
fs.mkdirSync(out,{recursive:true});
const server=http.createServer((req,res)=>{
 const rel=new URL(req.url,'http://localhost').pathname.replace(/^\/pet-cost-jp\//,'');
 const file=path.resolve(root,'site',rel.endsWith('/')?rel+'index.html':rel);
 if(!file.startsWith(path.join(root,'site')+path.sep)||!fs.existsSync(file)||fs.statSync(file).isDirectory()){res.writeHead(404);res.end();return;}
 res.setHeader('Content-Type',({'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json','.webp':'image/webp','.svg':'image/svg+xml'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);
});
(async()=>{
 await new Promise(resolve=>server.listen(8776,'127.0.0.1',resolve));
 const browser=await chromium.launch(),records=[];
 try{
  for(const width of [320,390,1440]){
   const context=await browser.newContext({viewport:{width,height:900},isMobile:width<500,hasTouch:width<500});
   await context.route(/google-analytics\.com|googletagmanager\.com|analytics\.google\.com/,r=>r.abort());
   const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
   const response=await page.goto('http://127.0.0.1:8776/pet-cost-jp/categories/pet-sheets/?test=1',{waitUntil:'networkidle'});
   assert.equal(response.status(),200);
   assert.equal(await page.locator('[data-size-summary]').count(),3);
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
   await page.locator('[data-usage-panel] > summary').click();
   await page.locator('[data-usage-input]').fill('5');
   await page.locator('[data-usage-form] button[type=submit]').click();
   assert((await page.locator('[data-row-usage]:visible').count())>0);
   assert.equal(errors.length,0,errors.join(','));
   await page.screenshot({path:path.join(out,`comparison-${width}.png`),fullPage:true,animations:'disabled'});
   await page.locator('[data-size-summary]').first().scrollIntoViewIfNeeded();
   await page.screenshot({path:path.join(out,`overview-${width}.png`),animations:'disabled'});
   records.push({width,status:response.status(),canonical,errors,overflow:false});await context.close();
  }
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({status:'PASS',records},null,2));
  const {default:lighthouse}=await import(require.resolve('lighthouse'));
  const launcher=await import(require.resolve('chrome-launcher'));
  const chrome=await launcher.launch({chromePath:chromium.executablePath(),chromeFlags:['--headless','--no-sandbox']});
  try{for(const desktop of [false,true]){
   const result=await lighthouse('http://127.0.0.1:8776/pet-cost-jp/categories/pet-sheets/?test=1',
    {port:chrome.port,output:'json',onlyCategories:['performance','accessibility','best-practices','seo'],
     blockedUrlPatterns:['*googletagmanager.com*','*google-analytics.com*','*analytics.google.com*'],
     ...(desktop?{formFactor:'desktop',screenEmulation:{mobile:false,width:1440,height:900,deviceScaleFactor:1,disabled:false},throttlingMethod:'provided'}:{})});
   assert(!result.lhr.runtimeError);fs.writeFileSync(path.join(out,`lighthouse-${desktop?'desktop':'mobile'}.json`),result.report);
   console.log('LIGHTHOUSE',desktop?'desktop':'mobile',JSON.stringify(Object.fromEntries(Object.entries(result.lhr.categories).map(([k,v])=>[k,v.score]))));
  }}finally{await chrome.kill();}
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
