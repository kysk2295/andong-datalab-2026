import test from 'node:test';
import assert from 'node:assert/strict';
import {createRiverWater,advanceRiverWater,riverSurfaceAt} from '../src/relay-water.js';

test('river motion is frame-rate independent, freezes in place, and resumes without jumping',()=>{
 const a=createRiverWater(120,52),b=createRiverWater(240,310);
 try{
  for(let i=0;i<60;i++)advanceRiverWater(a,1/60);
  for(let i=0;i<30;i++)advanceRiverWater(b,1/30);
  assert.ok(Math.abs(a.material.uniforms.uTime.value-b.material.uniforms.uTime.value)<1e-12);
  const before=a.material.uniforms.uTime.value;
  advanceRiverWater(a,5,true);assert.equal(a.material.uniforms.uTime.value,before);
  for(const dt of [NaN,Infinity,-1,0])advanceRiverWater(a,dt);
  assert.equal(a.material.uniforms.uTime.value,before);
  advanceRiverWater(a,.25);assert.equal(a.material.uniforms.uTime.value,before+.25);
  assert.notEqual(a.material.uniforms.uTime.value,b.material.uniforms.uTime.value);
 }finally{a.userData.dispose();b.userData.dispose();}
});

test('floating objects follow continuous river heights and the same local slope as the water',()=>{
 for(const [x,z] of [[0,0],[26,-37],[-23,-49],[7,-3],[12,-37]]){
  let changed=false;
  for(let t=0;t<25;t+=.25){
   const s=riverSurfaceAt(x,z,t),next=riverSurfaceAt(x,z,t+.01),eps=.001;
   assert.ok(Object.values(s).every(Number.isFinite));assert.ok(Math.abs(s.height)<.068);
   assert.ok(Math.abs(next.height-s.height)<.002);
   const dx=(riverSurfaceAt(x+eps,z,t).height-riverSurfaceAt(x-eps,z,t).height)/(2*eps);
   const dz=(riverSurfaceAt(x,z+eps,t).height-riverSurfaceAt(x,z-eps,t).height)/(2*eps);
   assert.ok(Math.abs(dx-s.slopeX)<1e-7);assert.ok(Math.abs(dz-s.slopeZ)<1e-7);
   changed ||= Math.abs(next.height-s.height)>.0001;
  }
  assert.ok(changed,'water must move at each visible boat position');
 }
});

test('river wave grid stays bounded and includes wave height in culling bounds',()=>{
 for(const [w,h,p] of [[120,52,[0,-.18,-50]],[240,310,[0,-.3,-20]]]){
  const water=createRiverWater(w,h,p);
  try{
   assert.deepEqual(water.position.toArray(),p);
   assert.ok(water.geometry.attributes.position.count>1000&&water.geometry.attributes.position.count<35000);
   assert.ok(water.geometry.boundingBox.min.z<=-.067&&water.geometry.boundingBox.max.z>=.067);
   assert.ok([...water.geometry.attributes.position.array].every(Number.isFinite));
  }finally{water.userData.dispose();}
 }
});
