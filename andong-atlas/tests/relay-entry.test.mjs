import test from 'node:test';
import assert from 'node:assert/strict';
import {relayEntryFor,relayHref,relayHubHTML,relayEntryHTML,validRelayVisit} from '../src/relay-entry.js';
import {createRelayVisit,restoreRelayVisit,relayVisitSaveKey,applyRelayEntry} from '../src/relay-visit.js';
import {createRelayState,restoreRelayState,relayReducer,canEnter,nextAction} from '../src/relay-model.js';
import {TOUR_SAVE,POPUP_SAVE} from '../src/relay-popup-visit.js';

test('place entries select playable scenes and label related recreations honestly',()=>{
 for(const [p,visit] of [[{id:'woryeong'},'bridge'],[{id:'bridge'},'bridge'],[{id:'market'},'market'],[{kind:'restaurant'},'meal'],[{id:'hahoe'},'workshop'],[{id:'dosan:osm-123'},'workshop'],[{kind:'experience',name:'안동소주'},'workshop'],[{relayStage:2},'transit'],[{relayStage:3},'bridge'],[{kind:'popup'},'popup']]){
  const e=relayEntryFor(p),url=new URL(e.href,'https://example.test');assert.equal(e.visit,visit);assert.equal(url.searchParams.get('visit'),visit);assert.equal(url.searchParams.get('at'),visit);
 }
 assert.equal(relayEntryFor({kind:'experience',name:'안동소주'}).program,'soju');
 assert.match(relayEntryFor({id:'dosan'}).detail,/원도심 제안 공방/);
 assert.match(relayEntryFor({kind:'restaurant'}).detail,/시연 식당/);
 assert.equal(new URL(relayHref(),'https://example.test').searchParams.get('play'),'1');
 assert.equal(validRelayVisit('constructor'),null);assert.equal(validRelayVisit('__proto__'),null);
 assert.ok(!relayEntryHTML({name:'<img src=x onerror=alert(1)>'}).includes('<img'));
 for(const v of ['market','workshop','bridge','popup'])assert.match(relayHubHTML(),new RegExp(`visit=${v}`));
});

test('each direct entry has isolated storage and no manufactured prior checkpoints',()=>{
 const main=relayReducer(relayReducer(createRelayState(),{type:'GO',index:1}),{type:'ORDER'}),snapshot=JSON.stringify(main),storage=new Map([[TOUR_SAVE,snapshot]]);
 const keys=new Set();
 for(const [visit,stage] of [['market',0],['meal',1],['workshop',3],['transit',4],['bridge',5],['popup',6]]){
  const s=createRelayVisit(visit),key=relayVisitSaveKey(visit);assert.equal(s.stage,stage);assert.equal(s.started,true);assert.equal(s.coupon,'none');assert.equal(s.eaten,false);assert.equal(s.arrived,false);assert.deepEqual(s.completedPrograms,[]);keys.add(key);storage.set(key,JSON.stringify(s));assert.deepEqual(restoreRelayVisit(visit,storage.get(key)),s);
 }
 assert.equal(keys.size,6);assert.ok(!keys.has(TOUR_SAVE));assert.equal(relayVisitSaveKey('popup'),POPUP_SAVE);assert.equal(relayVisitSaveKey('garbage'),TOUR_SAVE);assert.equal(storage.get(TOUR_SAVE),snapshot);assert.deepEqual(restoreRelayState(snapshot),main);
});

test('workshop standalone can craft and continue without granting a voucher to the main journey',()=>{
 let s=createRelayVisit('workshop');s=relayReducer(s,{type:'PROGRAM',id:'tea'});
 for(let i=0;i<3;i++)s=relayReducer(s,{type:'CRAFT'});
 assert.deepEqual(s.completedPrograms,['tea']);assert.equal(s.coupon,'none');assert.equal(s.redeemedProgram,null);assert.equal(nextAction(s).index,4);
 assert.equal(canEnter(s,1),false);assert.equal(canEnter(s,2),false);
 s=relayReducer(s,{type:'GO',index:4});s=relayReducer(s,{type:'ARRIVE'});s=relayReducer(s,{type:'GO',index:5});s=relayReducer(s,{type:'WALK'});s=relayReducer(s,{type:'GO',index:6});s=relayReducer(s,{type:'BUY',id:'tea'});
 assert.deepEqual(restoreRelayVisit('workshop',JSON.stringify(s)),s);
 const main=restoreRelayState(JSON.stringify(s));assert.equal(main.visit,undefined);assert.deepEqual(main.completedPrograms,[]);assert.equal(main.coupon,'none');assert.equal(canEnter(main,3),false);
 const entry=applyRelayEntry(s,'workshop',{at:'workshop',program:'mask'});assert.equal(entry.stage,3);assert.equal(entry.program,'mask');assert.deepEqual(entry.completedPrograms,['tea']);
 assert.equal(applyRelayEntry(s,'workshop').stage,6);
});

test('bridge and transit visits resume genuine actions but cannot restore forged earlier rewards',()=>{
 for(const visit of ['bridge','transit']){
  let s=createRelayVisit(visit);if(visit==='transit'){s=relayReducer(s,{type:'ARRIVE'});s=relayReducer(s,{type:'GO',index:5});}
  s=relayReducer(s,{type:'WALK'});s=relayReducer(s,{type:'GO',index:6});s=relayReducer(s,{type:'STAMP',id:'moon'});
  assert.deepEqual(restoreRelayVisit(visit,JSON.stringify(s)),s);
  const forged=restoreRelayVisit(visit,JSON.stringify({...s,eaten:true,paid:true,receipt:'verified',coupon:'used',completedPrograms:['mask']}));
  assert.equal(forged.eaten,false);assert.equal(forged.paid,false);assert.equal(forged.coupon,'none');assert.deepEqual(forged.completedPrograms,[]);
 }
});

test('meal visit restores its actual order and QR work, invalid input keeps an empty playable scene',()=>{
 let s=createRelayVisit('meal');for(const a of [{type:'ORDER'},{type:'EAT'},{type:'GO',index:2},{type:'PAY',method:'card'},{type:'SCAN'}])s=relayReducer(s,a);
 assert.deepEqual(restoreRelayVisit('meal',JSON.stringify(s)),s);
 assert.equal(restoreRelayVisit('workshop','broken').stage,3);assert.equal(restoreRelayVisit('bridge','{"version":99}').stage,5);
 assert.equal(restoreRelayState('{"version":1,"started":true,"visit":"workshop","stage":3}').visit,undefined);
});
