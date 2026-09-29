import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from 'three';
import {cookedMeal} from '../src/relay-food.js';
import {pineTwigGeometry,pineGrove} from '../src/relay-vegetation.js';
import {createRiverWater} from '../src/relay-water.js';
import {MealInteraction} from '../src/relay-meal.js';
import {bowlGeometry} from '../src/relay-vessels.js';

function kit(){
 const k={mat:color=>new T.MeshStandardMaterial({color}),foodSkin:new T.MeshStandardMaterial(),potato:new T.MeshStandardMaterial(),bark:new T.MeshStandardMaterial(),needles:new T.MeshStandardMaterial()};
 k.mesh=(g,geo,mat,p=[0,0,0])=>{const m=new T.Mesh(geo,typeof mat==='string'?k.mat(mat):mat);m.position.fromArray(p);g.add(m);return m;};
 k.sphere=(g,s,p,c)=>{const m=k.mesh(g,new T.SphereGeometry(1,12,10),c,p);m.scale.set(...(Array.isArray(s)?s:[s,s,s]));return m;};
 k.cyl=(g,a,b,h,p,c,n)=>k.mesh(g,new T.CylinderGeometry(a,b,h,n),c,p);
 k.tube=(g,p,r,c)=>k.mesh(g,new T.TubeGeometry(new T.CatmullRomCurve3(p.map(v=>new T.Vector3(...v))),20,r,6),c);
 k.bowl=(g,p,r,c)=>k.mesh(g,bowlGeometry(r),c,p);
 k.roundedBox=(g,s,p,c)=>k.mesh(g,new T.BoxGeometry(...s),c,p);
 k.instances=(g,geo,mat,items)=>{const m=new T.InstancedMesh(geo,mat,items.length),d=new T.Object3D();items.forEach((v,i)=>{d.position.fromArray(v.p);d.scale.fromArray(v.s||[1,1,1]);d.rotation.set(...(v.r||[0,0,0]));d.updateMatrix();m.setMatrixAt(i,d.matrix);});g.add(m);return m;};
 return k;
}

test('photographic twig UVs stay in the intended atlas island, without non-finite vertices',()=>{
 const geo=pineTwigGeometry();for(const name of ['position','normal','uv'])assert.ok([...geo.attributes[name].array].every(Number.isFinite));
 const uv=geo.attributes.uv;for(let i=0;i<uv.count;i++){assert.ok(uv.getX(i)>=.035&&uv.getX(i)<=.227);assert.ok(uv.getY(i)>=.56&&uv.getY(i)<=.954);}
});
test('forest stays batched as density increases, instead of one draw call per twig',()=>{
 const grove=pineGrove(new T.Group(),Array.from({length:180},(_,i)=>({x:i%12*5,z:Math.floor(i/12)*5,height:4+i%3,seed:i})),kit());
 assert.equal(grove.children.length,3);assert.ok(grove.children.every(o=>o.isInstancedMesh));assert.ok(grove.userData.twigCount<40000);
 for(const batch of grove.children)assert.ok([...batch.instanceMatrix.array].every(Number.isFinite));
});
test('all menu portions are finite, human scale and still reachable by the meal raycaster',()=>{
 for(const kind of ['jjimdak','mackerel','heotjesabap']){
  const food=cookedMeal(new T.Group(),kind,kit());food.updateMatrixWorld(true);const bounds=new T.Box3().setFromObject(food),size=bounds.getSize(new T.Vector3());
  assert.ok(size.x<.8&&size.z<.65&&size.y<.3,kind);const targets=food.children.filter(o=>o.userData.edible);assert.ok(targets.length>=3,kind);
  for(const target of targets){assert.equal(target.parent,food);const point=new T.Box3().setFromObject(target).getCenter(new T.Vector3());const ray=new T.Raycaster(point.clone().add(new T.Vector3(0,1,0)),new T.Vector3(0,-1,0));assert.ok(ray.intersectObject(target,false).length,kind);}
  food.traverse(o=>{if(o.geometry)for(const a of Object.values(o.geometry.attributes))assert.ok([...a.array].every(Number.isFinite));});
 }
});
test('water disposes its owned reflection target and material when its cached scene is evicted',()=>{
 const water=createRiverWater();assert.equal(water.material.uniforms.color.value.getHexString(),'10282d');let targets=0,materials=0,geometry=0;
 water.getRenderTarget().addEventListener('dispose',()=>targets++);water.material.addEventListener('dispose',()=>materials++);water.geometry.addEventListener('dispose',()=>geometry++);
 water.userData.dispose();assert.deepEqual([targets,materials,geometry],[1,1,1]);
});
test('a pointer bite requires movement into the mouth, while a stationary click returns the food',()=>{
 const calls=[],meal={state:{held:0},pointerOrigin:{x:50,y:50},dropBounds:()=>({left:0,top:0,width:100,height:100}),release:inside=>calls.push(inside)};
 MealInteraction.prototype.pointerUp.call(meal,{clientX:50,clientY:50});assert.equal(calls.pop(),false);
 meal.pointerOrigin={x:50,y:10};MealInteraction.prototype.pointerUp.call(meal,{clientX:50,clientY:50});assert.equal(calls.pop(),true);
 meal.pointerOrigin={x:50,y:10};MealInteraction.prototype.pointerUp.call(meal,{clientX:150,clientY:50});assert.equal(calls.pop(),false);
});
test('small teacups keep their inner floor below the liquid and rim',()=>{
 for(const r of [.045,.057,.092,.105,.18,.3]){
  const g=bowlGeometry(r),points=g.parameters.points,rim=points[5].y;
  assert.ok(points[7].y<r*.55&&points[8].y<r*.55);assert.ok(r*.55<rim);assert.ok(Math.abs(rim-r*.75)<1e-8);
  assert.ok([...g.attributes.position.array,...g.attributes.normal.array].every(Number.isFinite));g.dispose();
 }
});
