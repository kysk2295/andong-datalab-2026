import test from 'node:test';
import assert from 'node:assert/strict';
import {DINING_SEATS,diningLayout,diningStation} from '../src/relay-dining-layout.js';
import {createRelayState,relayReducer,restoreRelayState} from '../src/relay-model.js';
import {planWalk,clearWalk} from '../src/relay-navigation.js';

test('every selectable dining seat has a clear route from entrance and to the card reader',()=>{
 for(const id of Object.keys(DINING_SEATS)){
  const layout=diningLayout(id),station=diningStation(id),end=[station.position[0],station.position[2]];
  for(const [a,b] of [[[0,5.4],end],[end,[3,3.8]],[end,[0,5.65]]]){
   const path=planWalk(a,b,layout);assert.ok(path,id+' must be reachable');
   for(let i=1;i<path.length;i++)assert.ok(clearWalk(path[i-1],path[i],layout));
  }
 }
});
test('seat changes are accepted only before ordering, and survive a meal and receipt reload',()=>{
 let s=createRelayState();assert.equal(relayReducer(s,{type:'SEAT',id:'window'}),s);
 s=relayReducer(s,{type:'GO',index:1});s=relayReducer(s,{type:'SEAT',id:'window'});
 assert.equal(s.seat,'window');assert.deepEqual(restoreRelayState(JSON.stringify(s)),s);
 for(const action of [{type:'ORDER'},{type:'EAT'},{type:'GO',index:2},{type:'PAY',method:'card'}])s=relayReducer(s,action);
 assert.equal(relayReducer(s,{type:'SEAT',id:'center'}),s);assert.deepEqual(restoreRelayState(JSON.stringify(s)),s);
});
test('legacy saves keep progress at the centre table; invalid or inherited seat keys are rejected',()=>{
 let s=relayReducer(createRelayState(),{type:'GO',index:1});s=relayReducer(s,{type:'ORDER'});delete s.seat;
 const restored=restoreRelayState(JSON.stringify(s));assert.equal(restored.seat,'center');assert.equal(restored.ordered,true);
 for(const id of ['missing','constructor','__proto__']){const state=relayReducer(createRelayState(),{type:'GO',index:1});assert.equal(relayReducer(state,{type:'SEAT',id}),state);assert.equal(restoreRelayState(JSON.stringify({...s,seat:id})).seat,'center');}
});
