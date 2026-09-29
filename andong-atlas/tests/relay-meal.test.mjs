import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from 'three';
import {MealInteraction,mealInput,inBiteZone} from '../src/relay-meal.js';

const zone={left:100,top:100,width:200,height:80};
test('a bite needs a held piece and a drop inside the visible mouth ellipse',()=>{
 assert.equal(inBiteZone(200,140,zone),true);assert.equal(inBiteZone(101,101,zone),false);assert.equal(inBiteZone(400,140,zone),false);assert.equal(inBiteZone(200,140,{...zone,width:0}),false);
 let s={held:null,eaten:[]};assert.equal(mealInput(s,{type:'release',inside:true}),s);
 s=mealInput(s,{type:'grab',id:0});s=mealInput(s,{type:'release',inside:false});assert.equal(s.eaten.length,0);
 for(const id of [0,1,2]){s=mealInput(s,{type:'grab',id});s=mealInput(s,{type:'release',inside:true});}
 assert.deepEqual(s.eaten,[0,1,2]);assert.equal(mealInput(s,{type:'grab',id:3}),s);
});
test('duplicate food cannot be counted twice or replaced during a grab',()=>{
 let s=mealInput({held:null,eaten:[0]},{type:'grab',id:0});assert.equal(s.held,null);
 s=mealInput(s,{type:'grab',id:1});assert.equal(mealInput(s,{type:'grab',id:2}),s);
});
function fixture(origin){
 const food=new T.Group(),camera=new T.PerspectiveCamera(58,1,.045,220);camera.position.set(0,1.43,1.8);camera.lookAt(0,.93,0);camera.updateMatrixWorld();
 for(let i=0;i<3;i++){const p=new T.Mesh(new T.SphereGeometry(.1),new T.MeshBasicMaterial());p.userData.edible=true;p.position.set(i*.2,.1,0);food.add(p);}
 const scene={current:{refs:{food,diningOrigin:origin}},camera,keys:new Set(),rig:new T.Group(),leftHand:new T.Group(),rightHand:new T.Group(),chopsticks:new T.Group(),resetHands(){}};
 let result,updates=[];const meal=new MealInteraction(scene,{onUpdate:u=>updates.push(u),dropBounds:()=>zone,resolve:ok=>result=ok});scene.meal=meal;return {scene,meal,food,updates,result:()=>result};
}
test('cancel restores held and eaten objects plus the original first-person camera',()=>{
 const f=fixture(),before=f.meal.camera.clone(),items=[...f.food.children];f.meal.keyboardBite();f.meal.tick(.7);f.meal.grab(1);assert.equal(items[1].parent,f.scene.camera);
 f.meal.finish(false);assert.equal(f.result(),false);assert.equal(f.scene.meal,null);assert.deepEqual(f.scene.camera.position,before);
 for(const item of items){assert.equal(item.parent,f.food);assert.equal(item.visible,true);}
});
test('keyboard path requires three individual bites, with explicit completion',()=>{
 const f=fixture();f.meal.keyboardBite();f.meal.tick(.7);assert.equal(f.updates.at(-1).done,false);f.meal.keyboardBite();f.meal.tick(.7);f.meal.keyboardBite();f.meal.tick(.7);assert.equal(f.updates.at(-1).done,true);assert.equal(f.result(),undefined);f.meal.finish(true);assert.equal(f.result(),true);
 const early=fixture();early.meal.finish(true);assert.equal(early.result(),false);
});

test('tuho scores the actual landing point in both axes',async()=>{
 const {tuhoHit}=await import('../src/relay-tuho.js');const target={x:3,z:-4};assert.equal(tuhoHit({x:3.08,z:-3.93},target),true);assert.equal(tuhoHit({x:3,z:-3.8},target),false);assert.equal(tuhoHit({x:3.2,z:-4},target),false);assert.equal(tuhoHit({x:3.12,z:-3.88},target),false);
});


test('a bite is awarded after the hand reaches the mouth; cancellation during motion awards nothing',()=>{
 const f=fixture();f.meal.keyboardBite();assert.equal(f.meal.state.eaten.length,0);f.meal.tick(.2);assert.equal(f.meal.state.eaten.length,0);f.meal.keyboardBite();assert.equal(f.meal.state.held,0);
 f.meal.cancelPointer();f.meal.tick(1);assert.equal(f.meal.state.eaten.length,0);assert.equal(f.food.children.length,3);f.meal.finish(false);
});
test('invalid drop returns the same piece to its exact plate position',()=>{
 const f=fixture(),piece=f.food.children[1],before=piece.position.clone();f.meal.grab(1);f.meal.target.set(.4,.1,-.6);f.meal.tick(.1);f.meal.release(false);f.meal.tick(.5);
 assert.equal(piece.parent,f.food);assert.deepEqual(piece.position,before);assert.equal(f.meal.state.eaten.length,0);f.meal.finish(false);
});

test('window-seat eating uses that table and restores the camera when cancelled',()=>{
 const f=fixture([-3,0,-1.55]);assert.ok(f.scene.camera.position.distanceTo(new T.Vector3(-3,1.22,-.69))<1e-8);
 f.meal.grab(0);f.meal.finish(false);assert.equal(f.food.children.length,3);assert.deepEqual(f.scene.camera.position,f.meal.camera);
});
