(() => {
  document.addEventListener('DOMContentLoaded', () => {
    const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
    const KEY='pet_cost_profiles_v1', speciesLabels={dog:'犬',cat:'猫'};
    const track=(n,d={})=>window.petCostTrack?.(n,d);
    const validPet=p=>p==='dog'||p==='cat';
    const clean=p=>({age:['young','adult','senior'].includes(p?.age)?p.age:'',size:['small','medium','large'].includes(p?.size)?p.size:'',weight:/^\d{1,3}(\.\d{1,2})?$/.test(p?.weight||'')&&Number(p.weight)>0&&Number(p.weight)<=200?p.weight:'',breed:typeof p?.breed==='string'?p.breed.slice(0,40):''});
    let pets={dog:clean({}),cat:clean({})}, selected=$('[data-discovery-species]')?.dataset.discoverySpecies||$('[data-profile]')?.dataset.species||'', saved=false, play='';
    try {const data=JSON.parse(localStorage.getItem(KEY)||'{}');if(data?.version===1){pets={dog:clean(data.dog),cat:clean(data.cat)};saved=true;if(!selected&&validPet(data.selected))selected=data.selected;}}catch(_){}
    const store=()=>{try{if(saved)localStorage.setItem(KEY,JSON.stringify({version:1,selected,...pets}));else localStorage.removeItem(KEY);return true;}catch(_){return false;}};
    const FOOD_KEY='pet_cost_food_preferences_v1', foodOptions=$$('[data-food-family-option]');
    let foodFamily='', foodDaily='', foodSaved=false, foodOrder='unit';
    const positive=t=>/^\d+(\.\d+)?$/.test(t)&&Number(t)>0&&Number(t)<=100000;
    if(foodOptions.length)try{const all=JSON.parse(localStorage.getItem(FOOD_KEY)||'{}'),f=all.version===1?all[selected]:null;if(f){foodFamily=foodOptions.some(n=>n.dataset.foodFamilyOption===f.family)?f.family:'';foodDaily=positive(f.daily)?f.daily:'';foodSaved=true;if(!pets[selected].age&&['young','adult','senior'].includes(f.age))pets[selected].age=f.age;if(!pets[selected].size&&['small','medium','large'].includes(f.size))pets[selected].size=f.size;}}catch(_){}
    if($('[data-food-usage]'))$('[data-food-usage]').value=foodDaily;
    function storeFood(){
      try {let all;try{all=JSON.parse(localStorage.getItem(FOOD_KEY)||'{}');}catch(_){all={};}if(all?.version!==1)all={version:1};if(foodSaved)all[selected]={family:foodFamily,daily:foodDaily,age:pets[selected].age,size:pets[selected].size};else delete all[selected];if(all.dog||all.cat)localStorage.setItem(FOOD_KEY,JSON.stringify(all));else localStorage.removeItem(FOOD_KEY);return true;}catch(_){return false;}
    }
    function updateFood(){
      if(!foodOptions.length)return;
      const p=pets[selected],fits=n=>p.age===n.dataset.age&&(!n.dataset.size||p.size===n.dataset.size);
      $$('[data-food-age]').forEach(n=>n.setAttribute('aria-pressed',String(n.dataset.foodAge===p.age)));
      $$('[data-food-size]').forEach(n=>n.setAttribute('aria-pressed',String(n.dataset.foodSize===p.size)));
      foodOptions.forEach(n=>n.hidden=!fits(n));
      const option=foodOptions.find(n=>n.dataset.foodFamilyOption===foodFamily&&fits(n));
      $('[data-food-results]').hidden=!option;
      $$('[data-food-family]').forEach(n=>n.setAttribute('aria-pressed',String(!!option&&n.dataset.foodFamily===foodFamily)));
      $('[data-food-fit-status]').textContent=!p.age?'年齢を選ぶと、対象条件を確認した銘柄が現れます。':selected==='dog'&&!p.size?'体格も選んでください。':'あなたの条件：'+({young:'幼齢',adult:'成犬・成猫',senior:'シニア'}[p.age])+(p.size?' · '+({small:'小型',medium:'中型',large:'大型'}[p.size]):'')+(foodOptions.some(fits)?' · 対象表記を確認して、いつもの銘柄を選んでください。':' · この条件で照合済みのごはんはまだありません。');
      if($('[data-food-save]'))$('[data-food-save]').checked=foodSaved;
      const rows=$$('[data-food-candidate]'), candidates=rows.filter(n=>option&&n.dataset.family===foodFamily&&fits(n));
      rows.forEach(n=>n.hidden=!candidates.includes(n));
      candidates.sort((a,b)=>foodOrder==='amount'?Number(b.dataset.grams)-Number(a.dataset.grams):Number(a.dataset[foodOrder==='price'?'price':'unit'])-Number(b.dataset[foodOrder==='price'?'price':'unit'])||Number(a.dataset.price)-Number(b.dataset.price));
      const yen=x=>'¥'+Math.round(x).toLocaleString('ja-JP');
      candidates.forEach((n,i)=>{
        $('[data-food-reason]',n).textContent=i?'同じ銘柄の別の容量':({unit:'掲載候補内で100g単価が最小',price:'掲載候補内で商品総額が最小',amount:'掲載候補内で合計量が最大'}[foodOrder]);
        const g=Number(n.dataset.grams),price=Number(n.dataset.price),daily=Number(foodDaily);
        $('[data-food-duration]',n).textContent=foodDaily?'約'+(g/daily).toLocaleString('ja-JP',{maximumFractionDigits:1})+'日分 · 1日約'+yen(price/g*daily)+' · 30日約'+yen(price/g*daily*30):'使用量を入れると、持つ期間と30日分の費用が分かります。';
        $('[data-affiliate-link]',n).dataset.position=String(i+1);$('.food-candidates').append(n);
      });
      if(option){const label=$('h3',option).textContent;$('[data-food-answer]').textContent=candidates.length?label+' · '+candidates.length+'件。'+({unit:'同じごはんを、単価で比較中。',price:'今回の出費が小さい順。',amount:'合計量が多い順。'}[foodOrder]):label+'の照合済み候補は現在取得できていません。後ほど確認してください。';}
    }
    function updateToys(){
      if(!$('[data-toy-status]'))return;
      const p=pets[selected]||{}, rows=$$('[data-toy-candidate]');let count=0;
      rows.forEach(row=>{const fits=play&&row.dataset.play===play&&(!p.age||row.dataset.age===p.age)&&(!p.size||row.dataset.size===p.size);row.hidden=!fits;if(fits)count++;});
      $('[data-toy-status]').textContent=play?speciesLabels[selected]+' · 選んだ遊び方 · 商品表記を確認した候補 '+count+'件':'遊び方を選んでください。価格・品質のランキングではありません。';
      $('[data-toy-empty]').hidden=!play||count>0;
    }
    function render(){
      $$('[data-pet-select]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.petSelect===selected)));
      $$('[data-pet-routes]').forEach(n=>n.hidden=n.dataset.petRoutes!==selected);
      if($('[data-living-status]'))$('[data-living-status]').textContent=selected?speciesLabels[selected]+'の用品を選べます。プロフィールは任意です。':'犬・猫を選ぶと、その子の用品が現れます。';
      $$('[data-profile-species]').forEach(n=>{n.hidden=n.dataset.profileSpecies!==selected;const p=pets[n.dataset.profileSpecies];$$('[data-profile-age]',n).forEach(b=>b.setAttribute('aria-pressed',String(p.age===b.dataset.profileAge)));$$('[data-profile-size]',n).forEach(b=>b.setAttribute('aria-pressed',String(p.size===b.dataset.profileSize)));$('[data-profile-weight]',n).value=p.weight;$('[data-profile-breed]',n).value=p.breed;});
      $$('[data-profile-save]').forEach(n=>n.checked=saved);
      $$('[data-profile-summary]').forEach(n=>n.textContent=selected?speciesLabels[selected]+(pets[selected].age?' · 年齢を設定済み':' · 年齢未指定')+(saved?' · 端末に保存':' · このページで利用'):'犬・猫を選んでから設定できます');
      updateToys();
      updateFood();
    }
    function changed(field){const ok=store();if(foodOptions.length)storeFood();$('[data-profile-message]')?.replaceChildren(document.createTextNode(saved?(ok?'この端末に保存しました。':'端末に保存できません。このページでは使えます。'):'このページで使用中。保存は任意です。'));render();track('pet_profile_change',{species:selected,profile_field:field});}
    document.addEventListener('click',e=>{
      const pet=e.target.closest('[data-pet-select]');if(pet){selected=pet.dataset.petSelect;store();render();track('pet_species_select',{species:selected});}
      const age=e.target.closest('[data-profile-age]');if(age&&validPet(selected)){pets[selected].age=age.dataset.profileAge;changed('age');}
      const size=e.target.closest('[data-profile-size]');if(size&&selected==='dog'){pets.dog.size=size.dataset.profileSize;changed('size');}
      if(e.target.closest('[data-profile-age-clear]')&&validPet(selected)){pets[selected].age='';changed('age');}
      if(e.target.closest('[data-profile-size-clear]')&&selected==='dog'){pets.dog.size='';changed('size');}
      if(e.target.closest('[data-profile-clear]')){pets={dog:clean({}),cat:clean({})};saved=false;store();render();if($('[data-profile-message]'))$('[data-profile-message]').textContent='プロフィールを削除しました。';track('pet_profile_clear');}
      const route=e.target.closest('[data-living-route]');if(route){track('pet_supply_select',{species:selected,supply:route.dataset.livingRoute});const legacy={'pet-sheets':1,'cat-litter':1,'system-toilet-sheets':1};if(legacy[route.dataset.livingRoute])track('pet_category_select',{category_id:route.dataset.livingRoute,conversion_source:'pet_start'});}
      const b=e.target.closest('[data-play-select]');if(b){play=b.dataset.playSelect;$$('[data-play-select]').forEach(n=>n.setAttribute('aria-pressed',String(n===b)));updateToys();track('pet_play_select',{species:selected,play_type:play,result_count:$$('[data-toy-candidate]:not([hidden])').length});}
      const fa=e.target.closest('[data-food-age]');if(fa){pets[selected].age=fa.dataset.foodAge;changed('age');storeFood();track('pet_food_condition_select',{species:selected,condition_type:'age'});}
      const fs=e.target.closest('[data-food-size]');if(fs){pets[selected].size=fs.dataset.foodSize;changed('size');storeFood();track('pet_food_condition_select',{species:selected,condition_type:'size'});}
      const ff=e.target.closest('[data-food-family]');if(ff){foodFamily=ff.dataset.foodFamily;updateFood();storeFood();track('pet_food_family_select',{species:selected,food_family:foodFamily,result_count:$$('[data-food-candidate]:not([hidden])').length});}
      const fo=e.target.closest('[data-food-order]');if(fo){foodOrder=fo.dataset.foodOrder;$$('[data-food-order]').forEach(n=>n.setAttribute('aria-pressed',String(n===fo)));updateFood();track('pet_food_buying_select',{species:selected,buying_style:foodOrder});}
      if(e.target.closest('[data-food-clear]')){foodFamily='';foodDaily='';foodSaved=false;storeFood();$('[data-food-usage]').value='';updateFood();track('pet_food_preferences_clear',{species:selected});}
    });
    document.addEventListener('change',e=>{
      if(e.target.matches('[data-profile-save]')){saved=e.target.checked;changed('save');}
      if(e.target.matches('[data-profile-weight]')&&validPet(selected)){const raw=e.target.value.trim();const p=clean({...pets[selected],weight:raw});if(raw&&!p.weight){$('[data-profile-message]').textContent='体重は0より大きい200kg以下の数値を入力してください。';return;}pets[selected].weight=p.weight;changed('weight');}
      if(e.target.matches('[data-profile-breed]')&&validPet(selected)){pets[selected].breed=e.target.value.trim().slice(0,40);changed('breed');}
      if(e.target.matches('[data-food-save]')){foodSaved=e.target.checked;const ok=storeFood();$('[data-food-usage-status]').textContent=foodSaved?(ok?'この端末に保存しました。':'端末に保存できません。このページでは使えます。'):'このページで利用中。端末への保存は任意です。';}
    });
    $('[data-food-usage-form]')?.addEventListener('submit',e=>{e.preventDefault();const raw=$('[data-food-usage]').value.trim();foodDaily=positive(raw)?raw:'';updateFood();storeFood();$('[data-food-usage-status]').textContent=raw&&!foodDaily?'0より大きい100,000g以下の数値を入力してください。日数の表示を解除しました。':foodDaily?'入力した1日量で計算。給与量の推薦ではありません。':'使用量を解除しました。単価で比較できます。';if(foodDaily)track('pet_food_usage_set',{species:selected});});
    $('[data-food-calculator]')?.addEventListener('submit',e=>{
      e.preventDefault();const read=s=>{const t=$(s).value.trim();return /^\d+(\.\d+)?$/.test(t)?Number(t):NaN;};
      const grams=read('[data-food-weight]'),price=read('[data-food-price]'),daily=read('[data-food-daily]'),output=$('[data-food-outcome]');
      if(![grams,price,daily].every(x=>Number.isFinite(x)&&x>0&&x<=1e7)||grams/daily>1e7){output.textContent='内容量・価格・1日量に、0より大きい有効な数値を入力してください。';return;}
      const yen=x=>'約¥'+Math.round(x).toLocaleString('ja-JP');output.replaceChildren();
      [['持つ期間','約'+(grams/daily).toLocaleString('ja-JP',{maximumFractionDigits:1})+'日分'],['1日の費用',yen(price/grams*daily)],['30日分',yen(price/grams*daily*30)],['100gあたり',yen(price/grams*100)],['1kgあたり',yen(price/grams*1000)]].forEach(([label,value])=>{const n=document.createElement('div'),s=document.createElement('span'),b=document.createElement('b');s.textContent=label;b.textContent=value;n.append(s,b);output.append(n);});
      const note=document.createElement('p');note.textContent=grams.toLocaleString('ja-JP')+'g ÷ '+daily.toLocaleString('ja-JP')+'g/日。入力した袋の価格から計算。送料は未加算。';output.append(note);
      track('pet_food_calculator_use',{species:selected});
    });
    render();
  });
})();
