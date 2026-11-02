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
  if(typeof module==='object'&&module.exports) module.exports={calculateSheetPurchase};
  if(root) root.petCostSheetPurchase=calculateSheetPurchase;
})(typeof window!=='undefined'?window:null);
