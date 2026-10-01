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
    }
    function changed(field){const ok=store();$('[data-profile-message]')?.replaceChildren(document.createTextNode(saved?(ok?'この端末に保存しました。':'端末に保存できません。このページでは使えます。'):'このページで使用中。保存は任意です。'));render();track('pet_profile_change',{species:selected,profile_field:field});}
    document.addEventListener('click',e=>{
      const pet=e.target.closest('[data-pet-select]');if(pet){selected=pet.dataset.petSelect;store();render();track('pet_species_select',{species:selected});}
      const age=e.target.closest('[data-profile-age]');if(age&&validPet(selected)){pets[selected].age=age.dataset.profileAge;changed('age');}
      const size=e.target.closest('[data-profile-size]');if(size&&selected==='dog'){pets.dog.size=size.dataset.profileSize;changed('size');}
      if(e.target.closest('[data-profile-age-clear]')&&validPet(selected)){pets[selected].age='';changed('age');}
      if(e.target.closest('[data-profile-size-clear]')&&selected==='dog'){pets.dog.size='';changed('size');}
      if(e.target.closest('[data-profile-clear]')){pets={dog:clean({}),cat:clean({})};saved=false;store();render();if($('[data-profile-message]'))$('[data-profile-message]').textContent='プロフィールを削除しました。';track('pet_profile_clear');}
      const route=e.target.closest('[data-living-route]');if(route){track('pet_supply_select',{species:selected,supply:route.dataset.livingRoute});const legacy={'pet-sheets':1,'cat-litter':1,'system-toilet-sheets':1};if(legacy[route.dataset.livingRoute])track('pet_category_select',{category_id:route.dataset.livingRoute,conversion_source:'pet_start'});}
      const b=e.target.closest('[data-play-select]');if(b){play=b.dataset.playSelect;$$('[data-play-select]').forEach(n=>n.setAttribute('aria-pressed',String(n===b)));updateToys();track('pet_play_select',{species:selected,play_type:play,result_count:$$('[data-toy-candidate]:not([hidden])').length});}
    });
    document.addEventListener('change',e=>{
      if(e.target.matches('[data-profile-save]')){saved=e.target.checked;changed('save');}
      if(e.target.matches('[data-profile-weight]')&&validPet(selected)){const raw=e.target.value.trim();const p=clean({...pets[selected],weight:raw});if(raw&&!p.weight){$('[data-profile-message]').textContent='体重は0より大きい200kg以下の数値を入力してください。';return;}pets[selected].weight=p.weight;changed('weight');}
      if(e.target.matches('[data-profile-breed]')&&validPet(selected)){pets[selected].breed=e.target.value.trim().slice(0,40);changed('breed');}
    });
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
