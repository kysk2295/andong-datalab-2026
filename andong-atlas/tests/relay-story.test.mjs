import test from 'node:test';
import assert from 'node:assert/strict';
import {createRelayState,relayReducer as step} from '../src/relay-model.js';
import {relayProgress} from '../src/relay-story.js';

test('previewing the final scene never awards relay completion',()=>{
 const s=createRelayState(), progress=relayProgress(s,6);
 assert.equal(progress[4].current,true);
 assert.ok(progress.every(p=>!p.completed));
 assert.equal(s.stage,0);
});
test('relay checkpoints follow actual actions and final engagement',()=>{
 let s=createRelayState();
 for(const a of [{type:'GO',index:1},{type:'ORDER'},{type:'EAT'},{type:'GO',index:2},{type:'PAY',method:'card'},{type:'SCAN'},{type:'GO',index:3},{type:'REDEEM'},{type:'CRAFT'},{type:'CRAFT'},{type:'CRAFT'},{type:'GO',index:4},{type:'ARRIVE'},{type:'GO',index:5}])s=step(s,a);
 assert.deepEqual(relayProgress(s).map(p=>p.completed),[true,true,true,true,false]);
 for(const a of [{type:'WALK'},{type:'GO',index:6},{type:'THROW',hit:true},{type:'FINISH'}])s=step(s,a);
 assert.ok(relayProgress(s).every(p=>p.completed));
});

test('carried benefit follows the redeemed program even after selecting another craft',async()=>{
 const {relayCarry}=await import('../src/relay-story.js');let s=createRelayState();assert.equal(relayCarry(s),null);
 for(const a of [{type:'GO',index:1},{type:'ORDER'},{type:'EAT'},{type:'GO',index:2},{type:'PAY',method:'card'}])s=step(s,a);
 assert.equal(relayCarry(s).status,'receipt');s=step(s,{type:'SCAN'});assert.equal(relayCarry(s).status,'issued');s=step(s,{type:'GO',index:3});s=step(s,{type:'REDEEM'});s=step(s,{type:'PROGRAM',id:'soju'});
 assert.match(relayCarry(s).title,/탈 공예/);assert.match(relayCarry(s).value,/1,200/);assert.equal(s.redeemedProgram,'mask');
});
