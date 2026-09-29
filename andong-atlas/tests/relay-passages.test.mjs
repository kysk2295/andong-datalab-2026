import test from 'node:test';
import assert from 'node:assert/strict';
import {RESTAURANT_PASSAGES as doors,RESTAURANT_ARRIVALS as arrivals,passageAt,restaurantStage} from '../src/relay-passages.js';
import {diningLayout,DINING_SEATS} from '../src/relay-dining-layout.js';
import {canStand,planWalk,clearWalk} from '../src/relay-navigation.js';
import {createRelayState,relayReducer,restoreRelayState,canEnter} from '../src/relay-model.js';
import {journeyFor} from '../src/relay-journey.js';

test('doorways trigger within the opening, not through walls or on arrival',()=>{
 assert.equal(passageAt({x:0,z:5.45},[doors.dining]),'restaurant:exit');
 assert.equal(passageAt({x:0,z:-21.05},[doors.market]),'restaurant:enter');
 for(const [id,door] of Object.entries(doors)){
  const arrival=arrivals[id].position;
  assert.equal(passageAt({x:arrival[0],z:arrival[2]},[door]),null,'arrival must not bounce back');
  assert.equal(passageAt({x:door.x[1]+.1,z:door.z[0]},[door]),null);
  assert.equal(passageAt({x:0,z:door.z[1]+.1},[door]),null);
 }
});
test('chairs and counter connect to the exit through the open gap, never glass',()=>{
 for(const seat of Object.keys(DINING_SEATS)){
  const layout=diningLayout(seat);
  for(const id of ['table','counter','door']){
   const p=layout.stations[id].position,path=planWalk([p[0],p[2]],[0,5.65],layout);
   assert.ok(path,seat+' '+id);
   for(let i=1;i<path.length;i++)assert.ok(clearWalk(path[i-1],path[i],layout));
  }
  assert.equal(canStand(0,4.4,layout),true);
  for(const x of [-3.5,-2.03,-1.5,1.5,2.03,3.5])assert.equal(canStand(x,4.4,layout),false);
 }
});
test('leaving and re-entering at every dining checkpoint keeps progress and reloads',()=>{
 let state=relayReducer(createRelayState(),{type:'GO',index:1});
 state=relayReducer(state,{type:'SEAT',id:'window'});
 const checkpoints=[null,{type:'ORDER'},{type:'EAT'},{type:'PAY',method:'cash'},{type:'SCAN'}];
 for(const action of checkpoints){
  if(action?.type==='PAY')state=relayReducer(state,{type:'GO',index:2});
  if(action)state=relayReducer(state,action);
  const outside=relayReducer(state,{type:'GO',index:0});
  assert.deepEqual(restoreRelayState(JSON.stringify(outside)),outside);
  const inside=relayReducer(outside,{type:'GO',index:restaurantStage(outside)});
  assert.deepEqual({...inside,stage:state.stage},state);
  assert.equal(inside.stage,state.eaten?2:1);
  assert.equal(inside.seat,'window');
  assert.equal(canEnter(outside,3),state.coupon!=='none');
  state=inside;
 }
 assert.equal(journeyFor(0,3),'workshop');
 assert.equal(canEnter(createRelayState(),3),false,'walking out never grants a coupon');
});
