import test from 'node:test';
import assert from 'node:assert/strict';
import {JumpMotion,walkingAllowed,takeWalkingControl,walkingEyeHeight} from '../src/relay-locomotion.js';
import {worldKey} from '../src/relay-input.js';

test('jump has a human-sized arc, returns to ground, and is independent of frame rate',()=>{
 for(const fps of [30,60,144]){
  const jump=new JumpMotion();assert.equal(jump.start(),true);let peak=0,time=0;
  while(jump.airborne){jump.tick(1/fps);peak=Math.max(peak,jump.height);time+=1/fps;assert.ok(time<1);}
  assert.ok(peak>.72&&peak<.75);assert.ok(time>.77&&time<.82);assert.equal(jump.height,0);assert.equal(jump.velocity,0);
 }
});
test('held/repeated jump cannot add midair impulses; landing permits a fresh jump',()=>{
 const jump=new JumpMotion();jump.start();jump.tick(.2);const velocity=jump.velocity;
 assert.equal(jump.start(),false);assert.equal(jump.velocity,velocity);jump.tick(1);assert.equal(jump.start(),true);
 jump.reset();assert.equal(jump.airborne,false);assert.equal(jump.height,0);
});
test('walking while airborne preserves vertical arc on flat floors and bridge slope',()=>{
 const jump=new JumpMotion();jump.start();jump.tick(.3);const offset=jump.height;
 assert.equal(walkingEyeHeight('market',7)+offset,walkingEyeHeight('market',-4)+offset);
 assert.equal(walkingEyeHeight('bridge',0),1.94);assert.ok(walkingEyeHeight('bridge',-13)>2.1);
 assert.equal(jump.height,offset);jump.tick(0);assert.equal(jump.height,offset);
});
test('WASD takes control from assisted movement, while dialogs and activities keep their controls',()=>{
 const scene={current:{},navigation:{},options:{},cancelNavigation(){this.navigation=null;this.cancelled=(this.cancelled||0)+1;}};
 assert.equal(takeWalkingControl(scene),true);assert.equal(scene.navigation,null);assert.equal(scene.cancelled,1);
 for(const state of ['paused','action','painting','payment','tuho','meal','workshop','scanner','mapView']){
  const blocked={...scene,[state]:true};assert.equal(walkingAllowed(blocked),false);assert.equal(takeWalkingControl(blocked),false);assert.equal(blocked.cancelled,1);
 }
 assert.equal(takeWalkingControl({...scene,options:{cover:true}}),false);
});
test('physical WASD, Korean-key fallback and Space all work without changing keyboard language',()=>{
 for(const [code,key,want] of [['KeyW','ㅈ','w'],['KeyA','ㅁ','a'],['KeyS','ㄴ','s'],['KeyD','ㅇ','d'],['Space',' ',' '],['','ㅈ','w'],['','ㅉ','w'],['','ㅁ','a'],['','ㄴ','s'],['','ㅇ','d'],['','Spacebar',' ']])assert.equal(worldKey({code,key}),want);
});
