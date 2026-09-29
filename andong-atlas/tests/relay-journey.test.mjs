import test from 'node:test';
import assert from 'node:assert/strict';
import {JOURNEYS,journeyFor,journeyLayout} from '../src/relay-journey.js';
import {planWalk,clearWalk} from '../src/relay-navigation.js';
import {createRelayState,relayReducer} from '../src/relay-model.js';
test('only forward destination changes introduce connected walks',()=>{
 assert.equal(journeyFor(2,3),'workshop');assert.equal(journeyFor(3,4),'pickup');assert.equal(journeyFor(4,5),'arrival');assert.equal(journeyFor(5,6),'riverside');
 for(const pair of [[0,1],[1,2],[3,2],[0,6],[5,5]])assert.equal(journeyFor(...pair),null);
});
test('every link can be walked from spawn through all destinations without crossing props',()=>{
 for(const [id,j] of Object.entries(JOURNEYS)){const layout=journeyLayout(id);let start=[0,8];for(const leg of j.legs){const end=[leg.position[0],leg.position[2]],path=planWalk(start,end,layout);assert.ok(path,id+':'+leg.key);for(let i=1;i<path.length;i++)assert.ok(clearWalk(path[i-1],path[i],layout));start=end;}}
});
test('journey metadata never bypasses the existing coupon and completion gates',()=>{
 const state={...createRelayState(),started:true,stage:2};assert.equal(relayReducer(state,{type:'GO',index:JOURNEYS.workshop.to}),state);
 const issued={...state,coupon:'issued'};assert.equal(relayReducer(issued,{type:'GO',index:3}).stage,3);
 assert.equal(relayReducer({...issued,stage:3},{type:'GO',index:4}).stage,3);
});
test('taxi and walking approaches use the correct vehicle collision footprints',()=>{
 for(const transport of ['shuttle','taxi','walk'])for(const id of ['pickup','arrival']){const layout=journeyLayout(id,transport);let start=[0,8];for(const leg of JOURNEYS[id].legs){const end=[leg.position[0],leg.position[2]];assert.ok(planWalk(start,end,layout),id+transport);start=end;}assert.equal(layout.obstacles.length,transport==='walk'?0:1);}
});
