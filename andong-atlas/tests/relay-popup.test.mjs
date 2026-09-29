import test from 'node:test';
import assert from 'node:assert/strict';
import {createPopupVisit,restorePopupVisit,popupSaveKey,TOUR_SAVE,POPUP_SAVE} from '../src/relay-popup-visit.js';
import {createRelayState,relayReducer,restoreRelayState,canEnter} from '../src/relay-model.js';
import {popupLayout,POPUP_BOOTHS,POPUP_TUHO,popupMapPoint} from '../src/relay-popup-layout.js';
import {planWalk,clearWalk,canStand} from '../src/relay-navigation.js';

test('direct popup play neither unlocks nor rewrites the main relay',()=>{
 const tour=relayReducer(relayReducer(createRelayState(),{type:'GO',index:1}),{type:'ORDER'}),snapshot=JSON.stringify(tour);
 let visit=createPopupVisit();assert.equal(visit.stage,6);assert.equal(visit.started,true);
 assert.equal(visit.eaten,false);assert.equal(visit.arrived,false);assert.equal(visit.bridgeWalked,false);assert.equal(visit.coupon,'none');
 for(const action of [{type:'BUY',id:'tea',method:'card'},{type:'THROW',hit:true},{type:'PERFORMANCE',score:3},{type:'FINISH'}])visit=relayReducer(visit,action);
 const storage=new Map([[TOUR_SAVE,snapshot]]);storage.set(popupSaveKey(true),JSON.stringify(visit));
 assert.equal(popupSaveKey(false),TOUR_SAVE);assert.equal(popupSaveKey(true),POPUP_SAVE);assert.equal(storage.get(TOUR_SAVE),snapshot);
 assert.deepEqual(restoreRelayState(storage.get(TOUR_SAVE)),tour);assert.equal(canEnter(tour,6),false);
 assert.deepEqual(restorePopupVisit(storage.get(POPUP_SAVE)),visit);
});
test('popup restore only accepts its own bounded actions, never earlier checkpoints',()=>{
 const s=restorePopupVisit(JSON.stringify({version:1,stage:3,paid:true,eaten:true,coupon:'used',arrived:true,cart:['tea','tea','__proto__','missing'],popupPayments:{tea:'cash'},gameAttempts:200,gameScore:100,performanceScore:99,finished:true}));
 assert.equal(s.stage,6);assert.equal(s.coupon,'none');assert.equal(s.paid,false);assert.equal(s.arrived,false);assert.deepEqual(s.cart,['tea']);assert.equal(s.popupPayments.tea,'cash');assert.equal(s.gameAttempts,3);assert.equal(s.gameScore,3);assert.equal(s.performanceScore,null);
 for(const raw of [null,'bad','{"version":2}','{}'])assert.deepEqual(restorePopupVisit(raw),createPopupVisit());
 const empty=restorePopupVisit('{"version":1,"finished":true}');assert.equal(empty.finished,false);
});
test('all popup booths and the stage are reachable, while counters and the tuho pot block walking',()=>{
 const layout=popupLayout(),spawn=[layout.stations.entrance.position[0],layout.stations.entrance.position[2]];
 for(const station of Object.values(layout.stations)){
  const end=[station.position[0],station.position[2]],path=planWalk(spawn,end,layout);assert.ok(path,station.name);
  for(let i=1;i<path.length;i++)assert.ok(clearWalk(path[i-1],path[i],layout),station.name);
 }
 for(const b of POPUP_BOOTHS)assert.equal(canStand(b.x,b.z,layout),false);
 assert.equal(canStand(POPUP_TUHO.x,POPUP_TUHO.z,layout),false);
 for(const a of Object.values(layout.stations))for(const b of Object.values(layout.stations))assert.ok(planWalk([a.position[0],a.position[2]],[b.position[0],b.position[2]],layout),a.name+' to '+b.name);
});


test('new popup activities restore independently and only tasting purchased edible items is accepted',()=>{
 let s=createPopupVisit();
 assert.strictEqual(relayReducer(s,{type:'TASTE',id:'tea'}),s);
 s=relayReducer(s,{type:'BUY',id:'craft'});assert.strictEqual(relayReducer(s,{type:'TASTE',id:'craft'}),s);
 s=relayReducer(s,{type:'BUY',id:'grill'});s=relayReducer(s,{type:'TASTE',id:'grill'});
 for(const id of ['moon','bridge','mask'])s=relayReducer(s,{type:'STAMP',id});
 s=relayReducer(s,{type:'PHOTO'});s=relayReducer(s,{type:'FINISH'});
 assert.deepEqual(restorePopupVisit(JSON.stringify(s)),s);
 assert.strictEqual(relayReducer(s,{type:'STAMP',id:'moon'}),s);
 assert.strictEqual(relayReducer(s,{type:'BUY',id:'__proto__'}),s);
 const forged=restorePopupVisit(JSON.stringify({version:1,popupStamps:['moon','moon','bad'],popupPhotos:1000,popupTasted:['tea']}));
 assert.deepEqual(forged.popupStamps,['moon']);assert.equal(forged.popupPhotos,99);assert.deepEqual(forged.popupTasted,[]);
 const tour=createRelayState();for(const type of ['STAMP','TASTE','PHOTO'])assert.strictEqual(relayReducer(tour,{type,id:'moon'}),tour);
});
test('site map uses walkable coordinates and preserves river north orientation',()=>{
 assert.deepEqual(popupMapPoint(-31,-22),{x:0,y:0});assert.deepEqual(popupMapPoint(31,22),{x:100,y:100});
 for(const s of Object.values(popupLayout().stations)){const p=popupMapPoint(s.position[0],s.position[2]);assert.ok(p.x>=0&&p.x<=100&&p.y>=0&&p.y<=100);}
});

test('new activities survive the full relay save without granting or spending a second coupon',()=>{
 let s=createRelayState();
 for(const a of [{type:'START'},{type:'GO',index:1},{type:'ORDER'},{type:'EAT'},{type:'GO',index:2},{type:'PAY',method:'cash'},{type:'SCAN'},{type:'GO',index:3},{type:'REDEEM'},{type:'CRAFT'},{type:'CRAFT'},{type:'CRAFT'},{type:'GO',index:4},{type:'ARRIVE'},{type:'GO',index:5},{type:'WALK'},{type:'GO',index:6},{type:'BUY',id:'sikhye',method:'cash'},{type:'TASTE',id:'sikhye'},{type:'STAMP',id:'moon'},{type:'PHOTO'},{type:'FINISH'}])s=relayReducer(s,a);
 assert.deepEqual(restoreRelayState(JSON.stringify(s)),s);assert.equal(s.coupon,'used');assert.equal(s.popupPayments.sikhye,'cash');
});
