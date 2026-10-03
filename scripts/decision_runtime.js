(() => {
  document.addEventListener('DOMContentLoaded', () => {
    const source=document.getElementById('decision-data'); if(!source)return;
    const products=JSON.parse(source.textContent), byKey=new Map(products.map(p=>[p.key,p]));
    const KEY='pet_cost_saved_products_v1', selected=new Set(); let saved=new Set();
    try { const raw=JSON.parse(localStorage.getItem(KEY)||'[]');if(Array.isArray(raw))saved=new Set(raw.filter(k=>typeof k==='string').slice(0,100)); }catch(_){}
    const $=s=>document.querySelector(s), status=$('[data-decision-status]');
    const money=n=>'¥'+Number(n).toLocaleString('ja-JP',{maximumFractionDigits:2});
    const track=(name,data)=>window.petCostTrack?.(name,data);
    const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
    const button=(label,action)=>{const b=el('button',label);b.type='button';b.className='btn secondary';b.addEventListener('click',action);return b;};
    function store(){try{localStorage.setItem(KEY,JSON.stringify([...saved]));return true;}catch(_){return false;}}
    function save(p){if(saved.has(p.key))saved.delete(p.key);else if(saved.size<100)saved.add(p.key);const ok=store();render();status.textContent=ok?'保存した商品を更新しました。':'端末に保存できません。このページで検討できます。';track('product_save',{category_id:p.category,item_id:p.id,saved:saved.has(p.key)?'1':'0'});}
    function compare(p){
      if(selected.has(p.key)){selected.delete(p.key);render();return;}
      const first=byKey.get([...selected][0]);
      if(first&&(first.category!==p.category||first.group!==p.group)){status.textContent='同じカテゴリ・サイズ・素材・対応シリーズ、または同じフード銘柄で比較してください。';return;}
      if(selected.size>=3){status.textContent='比較は3件までです。選択を外すと別の商品を追加できます。';return;}
      selected.add(p.key);render();status.textContent=selected.size+'件を比較中。「保存・比較欄を見る」から確認できます。';track('product_compare',{category_id:p.category,item_id:p.id,result_count:selected.size});
    }
    const links=[];
    products.filter(p=>p.category===document.body.dataset.categoryId).forEach(p=>{
      const a=[...document.querySelectorAll('article [data-affiliate-link]')].find(n=>n.dataset.itemId===p.id);if(!a)return;
      const article=a.closest('article');article.id='product-'+p.id;
      const actions=el('div');actions.className='decision-actions';
      const saveButton=button('保存する',()=>save(p)),compareButton=button('並べて比較',()=>compare(p));
      saveButton.dataset.productSave=p.key;compareButton.dataset.productCompare=p.key;actions.append(saveButton,compareButton);article.append(actions);links.push({p,saveButton,compareButton});
      const jump=el('a','保存・比較欄を見る');jump.href='#decision-heading';jump.className='text-link';actions.append(jump);
      const history=el('details');history.className='observed-prices';history.append(el('summary','価格履歴を見る'));
      history.append(el('p','実際に取得した商品価格。送料・クーポン・ポイントは含みません。'));
      for(const h of p.history)history.append(el('p',h.date+' · '+money(h.price)+(h.unit?' · '+money(h.unit)+' / '+p.metric:'')));
      if(p.history.length<2)history.append(el('p','履歴の記録を開始しました。次回以降の取得価格と比較できます。'));
      article.append(history);
    });
    function render(){
      links.forEach(({p,saveButton,compareButton})=>{saveButton.textContent=saved.has(p.key)?'保存済み・解除':'保存する';saveButton.setAttribute('aria-pressed',String(saved.has(p.key)));compareButton.textContent=selected.has(p.key)?'比較から外す':'並べて比較';compareButton.setAttribute('aria-pressed',String(selected.has(p.key)));});
      const shelf=$('[data-saved-products]');shelf.replaceChildren();
      const current=[...saved].map(k=>byKey.get(k)).filter(Boolean);
      if(!current.length)shelf.append(el('p','商品カードの「保存する」から、候補をここに残せます。'));
      current.forEach(p=>{const card=el('div');card.className='saved-product';const a=el('a',p.name);card.id='saved-'+p.key;a.href=p.page+'#saved-'+p.key;card.append(a,el('p',money(p.price)+' · '+p.shipping),button('比較に追加',()=>compare(p)),button('保存を解除',()=>save(p)));shelf.append(card);});
      if(saved.size>current.length)shelf.append(el('p','保存した商品の一部は現在の掲載対象外です。古い価格は表示していません。'));
      const mount=$('[data-product-comparison]');mount.replaceChildren();if(!selected.size)return;
      mount.append(el('h3','選んだ候補を並べて比較'));
      mount.append(el('p','同じ条件の掲載商品を比較。商品価格の比較で、品質や相性の順位ではありません。'));
      const list=el('div');list.className='decision-grid';
      [...selected].map(k=>byKey.get(k)).filter(Boolean).forEach(p=>{
        const card=el('article');const img=el('img');img.src=p.image;img.alt=p.name;img.width=96;img.height=96;img.loading='lazy';if(p.image)card.append(img);
        card.append(el('h4',p.name),el('p','商品価格 '+money(p.price)),el('p',p.shipping));
        if(p.unit)card.append(el('p',money(p.unit)+' / '+p.metric),el('p','内容量 '+(p.metric==='100g'?p.quantity/10+'kg':p.quantity+(p.metric==='1L'?'L':'枚'))));
        if(p.age||p.size)card.append(el('p',[({young:'幼齢用',adult:'成犬・成猫用',senior:'シニア用'})[p.age],({small:'小型用',medium:'中型用',large:'大型用'})[p.size]].filter(Boolean).join(' · ')));
        if(p.dimensions)card.append(el('p','寸法 '+p.dimensions));
        const a=el('a','楽天で現在価格・仕様を確認');a.className='btn secondary';a.href=p.url;a.target='_blank';a.rel='nofollow sponsored noopener';
        Object.assign(a.dataset,{affiliateLink:'',categoryId:p.category,itemId:p.id,itemName:p.name,conversionSource:'saved_comparison',position:String([...selected].indexOf(p.key)+1),...(p.unit?{unitPrice:String(p.unit),metric:p.metric}: {})});
        card.append(a,button('比較から外す',()=>{selected.delete(p.key);render();}));list.append(card);
      });mount.append(list);
    }
    render();
  });
})();
