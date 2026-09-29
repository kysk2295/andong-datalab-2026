import {createRelayState,relayReducer,POPUP_ITEMS,restorePopupActivities} from './relay-model.js';

export const TOUR_SAVE='andong-relay-v1';
export const POPUP_SAVE='andong-relay-popup-v1';
// A standalone visit uses its own save. Never manufacture earlier relay checkpoints.
export function createPopupVisit(){return {...createRelayState(),started:true,stage:6};}
export function restorePopupVisit(raw){
 let s=createPopupVisit();
 try{
  const x=JSON.parse(raw);if(x.version!==1)return s;
  for(const id of Array.isArray(x.cart)?x.cart:[])if(Object.hasOwn(POPUP_ITEMS,id))s=relayReducer(s,{type:'BUY',id,method:x.popupPayments?.[id]});
  const attempts=Number.isInteger(x.gameAttempts)?Math.min(3,Math.max(0,x.gameAttempts)):0;
  const hits=Number.isInteger(x.gameScore)?Math.min(attempts,Math.max(0,x.gameScore)):0;
  for(let i=0;i<attempts;i++)s=relayReducer(s,{type:'THROW',hit:i<hits});
  s=relayReducer(s,{type:'PERFORMANCE',score:x.performanceScore});
  s=restorePopupActivities(s,x);
  if(x.finished)s=relayReducer(s,{type:'FINISH'});
 }catch{}
 return s;
}
export function popupSaveKey(standalone){return standalone?POPUP_SAVE:TOUR_SAVE;}
