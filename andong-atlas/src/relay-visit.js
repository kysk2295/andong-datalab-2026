import {createRelayState,restoreRelayState,relayReducer,PROGRAMS} from './relay-model.js';
import {createPopupVisit,restorePopupVisit,TOUR_SAVE,POPUP_SAVE} from './relay-popup-visit.js';
import {RELAY_VISITS,validRelayVisit} from './relay-entry.js';

export function createRelayVisit(visit){
 if(visit==='popup')return createPopupVisit();
 return validRelayVisit(visit)?{...createRelayState(),visit,started:true,stage:RELAY_VISITS[visit]}:createRelayState();
}
export function relayVisitSaveKey(visit){return visit==='popup'?POPUP_SAVE:validRelayVisit(visit)?`andong-relay-visit-${visit}-v1`:TOUR_SAVE;}
export function restoreRelayVisit(visit,raw){
 if(visit==='popup')return restorePopupVisit(raw);
 return restoreRelayState(raw,validRelayVisit(visit));
}

// A clicked place link opens that scene once. Reloading resumes its saved activity.
export function applyRelayEntry(state,visit,{at,program}={}){
 if(!validRelayVisit(visit))return state;
 let next=at===visit?{...state,stage:RELAY_VISITS[visit]}:state;
 if(visit==='workshop'&&Object.hasOwn(PROGRAMS,program)&&next.stage===3)next=relayReducer(next,{type:'PROGRAM',id:program});
 return next;
}
