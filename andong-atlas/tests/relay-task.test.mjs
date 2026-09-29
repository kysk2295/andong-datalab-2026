import test from 'node:test';
import assert from 'node:assert/strict';
import {createWorkshopTask,workshopInput,pourInput} from '../src/relay-task-model.js';
import {createRelayState,relayReducer as step,restoreRelayState} from '../src/relay-model.js';
test('ordering, eating, paying and scanning require the previous visitor action',()=>{
 let s=step(createRelayState(),{type:'GO',index:1});assert.equal(step(s,{type:'EAT'}),s);
 s=step(s,{type:'ORDER'});assert.equal(step(s,{type:'MEAL',id:'mackerel'}),s);s=step(s,{type:'EAT'});s=step(s,{type:'GO',index:2});assert.equal(step(s,{type:'SCAN'}),s);assert.equal(step(s,{type:'PAY',method:'invalid'}),s);
 s=step(s,{type:'PAY',method:'cash'});assert.equal(s.receipt,'ready');assert.equal(step(s,{type:'PAY',method:'card'}),s);s=step(s,{type:'SCAN'});assert.equal(s.coupon,'issued');assert.deepEqual(restoreRelayState(JSON.stringify(s)),s);
});
test('existing saved visits migrate while unpaid new visits remain unpaid',()=>{
 const old={version:1,started:true,stage:2,meal:'jjimdak',eaten:true,receipt:'verified',coupon:'issued'};assert.equal(restoreRelayState(JSON.stringify(old)).coupon,'issued');
 const current={...old,ordered:true,paid:false,receipt:'none',coupon:'none'};const s=restoreRelayState(JSON.stringify(current));assert.equal(s.paid,false);assert.equal(s.receipt,'none');
});
test('workshop materials cannot be counted twice and soju order is enforced',()=>{
 let tea=createWorkshopTask('tea',0);for(const id of ['flower-2','flower-2','unknown','flower-0'])tea=workshopInput(tea,id);assert.equal(tea.selected.length,2);assert.equal(tea.done,false);tea=workshopInput(tea,'flower-1');assert.equal(tea.done,true);
 let soju=createWorkshopTask('soju',0);soju=workshopInput(soju,'nuruk');assert.equal(soju.selected.length,0);assert.match(soju.error,/쌀/);for(const id of ['rice','nuruk','water'])soju=workshopInput(soju,id);assert.equal(soju.done,true);
});
test('pouring has real undershoot and overshoot states and an accessible path',()=>{
 let s=createWorkshopTask('tea',1);s=pourInput(s,'tap');s=pourInput(s,'release');assert.equal(s.done,false);assert.match(s.error,/적어요/);s=pourInput(s,'start');s=pourInput(s,'tick',10);s=pourInput(s,'release');assert.equal(s.done,false);assert.equal(s.amount,100);s=pourInput(s,'reset');for(let i=0;i<6;i++)s=pourInput(s,'tap');s=pourInput(s,'release');assert.equal(s.done,true);assert.equal(s.holding,false);
});
test('performance completes the popup without inventing a purchase',()=>{
 let s=createRelayState();for(const a of [{type:'GO',index:1},{type:'ORDER'},{type:'EAT'},{type:'GO',index:2},{type:'PAY',method:'card'},{type:'SCAN'},{type:'GO',index:3},{type:'REDEEM'},{type:'CRAFT'},{type:'CRAFT'},{type:'CRAFT'},{type:'GO',index:4},{type:'ARRIVE'},{type:'GO',index:5},{type:'WALK'},{type:'GO',index:6},{type:'PERFORMANCE',score:2},{type:'FINISH'}])s=step(s,a);
 assert.equal(s.finished,true);assert.equal(step(s,{type:'GO',index:3}).finished,true);assert.equal(s.cart.length,0);assert.equal(s.performanceScore,2);assert.deepEqual(restoreRelayState(JSON.stringify(s)),s);assert.equal(step(s,{type:'PERFORMANCE',score:8}),s);
});
