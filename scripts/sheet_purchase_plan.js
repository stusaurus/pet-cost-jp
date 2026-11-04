/* Household pet sheet purchase arithmetic. No prices, products or assumptions
 * are created here: quantities and prices come from accepted published rows. */
(function(root){
  'use strict';
  function calculateSheetPurchase(sheetsPerSet, productPrice, sheetsPerDay, days=30){
    const finite=[sheetsPerSet,productPrice,sheetsPerDay,days].every(Number.isFinite);
    if(!finite || !Number.isSafeInteger(sheetsPerSet) || sheetsPerSet<=0 ||
       !Number.isSafeInteger(days) || days<1 || days>366 ||
       productPrice<=0 || sheetsPerDay<=0 || sheetsPerDay>1000) return null;
    const required=Math.ceil(sheetsPerDay*days);
    if(!Number.isSafeInteger(required)||required<=0) return null;
    const sets=Math.ceil(required/sheetsPerSet);
    const purchaseTotal=sets*productPrice;
    if(!Number.isFinite(purchaseTotal)||purchaseTotal<=0) return null;
    return {
      sheetsRequired:required,
      sheetsPerSet,
      setsToBuy:sets,
      purchaseTotal,
      remainingSheets:sets*sheetsPerSet-required,
      daysPerSet:sheetsPerSet/sheetsPerDay,
      consumptionCost:required*productPrice/sheetsPerSet
    };
  }
  // Stock is scoped to the selected sheet size and never implies cross-size fit.
  // Keep the original function unchanged for existing consumers and tests.
  function calculateSheetPurchaseWithStock(sheetsPerSet,productPrice,sheetsPerDay,stockSheets=0,days=30){
    const initial=calculateSheetPurchase(sheetsPerSet,productPrice,sheetsPerDay,days);
    if(!initial || !Number.isSafeInteger(stockSheets) || stockSheets<0 || stockSheets>100000) return null;
    const shortage=Math.max(0,initial.sheetsRequired-stockSheets);
    const setsToBuy=Math.ceil(shortage/sheetsPerSet);
    const purchaseTotal=setsToBuy*productPrice;
    if(!Number.isFinite(purchaseTotal) || purchaseTotal<0) return null;
    return {
      ...initial, stockSheets, shortage, setsToBuy, purchaseTotal,
      remainingSheets:stockSheets+setsToBuy*sheetsPerSet-initial.sheetsRequired,
      noBuy:setsToBuy===0
    };
  }
  if(typeof module==='object'&&module.exports) module.exports={calculateSheetPurchase,calculateSheetPurchaseWithStock};
  if(root){root.petCostSheetPurchase=calculateSheetPurchase;root.petCostSheetPurchaseWithStock=calculateSheetPurchaseWithStock;}
})(typeof window!=='undefined'?window:null);
