import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {buildingAppearance} from '../src/building-style.js';
import {buildingGeometry} from '../src/building-geometry.js';
import {DistrictScene} from '../src/district-scene.js';
import {createStreetLightPools} from '../src/street-light-pools.js';

const building=(id,x)=>({id,properties:{height:12},geometry:{type:'Polygon',coordinates:[[[x,0],[x+.06,0],[x+.06,.06],[x,.06],[x,0]]]}});
const features=[building('a',0),building('b',1),building('c',2)];

test('merged overview buildings retain stable independent lighting identities on all their faces',()=>{
 const {geometry}=buildingGeometry(features,c=>c,()=>.1),p=geometry.getAttribute('position'),seeds=geometry.getAttribute('facadeSeed');
 assert.equal(seeds.count,p.count);
 assert.equal(new Set(features.map(f=>buildingAppearance(f).lightSeed)).size,features.length);
 for(let i=0;i<p.count;i++){
  const f=features[Math.floor(p.getX(i))],seed=seeds.getX(i);
  assert.ok(seed>=0&&seed<1);assert.ok(Math.abs(seed-buildingAppearance(f).lightSeed)<1e-7);
 }
 const reversed=buildingGeometry([...features].reverse(),c=>c,()=>.1).geometry;
 assert.deepEqual(new Set(reversed.getAttribute('facadeSeed').array),new Set(seeds.array));
 geometry.dispose();reversed.dispose();
});

test('detail building batches supply the same lighting identities as the overview',()=>{
 let facadeCount=0;
 const district={data:{buildings:features},point:([x,z])=>new THREE.Vector3(x,.1,z),materials:[],merge(parts,material){
  if(material.userData.nightIntensity===1.8){
   facadeCount+=parts.length;
   parts.forEach((g,i)=>{
    const seeds=g.getAttribute('facadeSeed');assert.equal(seeds.count,g.getAttribute('position').count);
    assert.ok([...seeds.array].every(s=>Math.abs(s-buildingAppearance(features[i]).lightSeed)<1e-7));
   });
  }
  parts.forEach(g=>g.dispose());material.dispose();
 }};
 DistrictScene.prototype.buildBuildings.call(district);
 assert.equal(facadeCount,features.length);
});

test('street light pools follow fixture height on both terrain and raised roads without extra lights',()=>{
 const lamps=new THREE.InstancedMesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial(),3),matrix=new THREE.Matrix4();
 const heights=[.2,1,4.5];
 heights.forEach((h,i)=>lamps.setMatrixAt(i,matrix.makeTranslation(i,h+.024,2*i)));
 const pools=createStreetLightPools(lamps);assert.equal(pools.count,3);assert.equal(pools.visible,false);
 heights.forEach((h,i)=>{
  pools.getMatrixAt(i,matrix);assert.equal(matrix.elements[12],i);assert.equal(matrix.elements[14],2*i);
  assert.ok(Math.abs(matrix.elements[13]-(h+.0012))<1e-6);
 });
 assert.ok(pools.material.depthTest);assert.equal(pools.material.depthWrite,false);assert.equal(pools.castShadow,false);
 const rgba=pools.material.map.image.data;assert.equal(rgba[3],0);assert.ok(rgba[(16*32+16)*4+3]>100);
 pools.geometry.dispose();pools.material.map.dispose();pools.material.dispose();lamps.geometry.dispose();lamps.material.dispose();
});

test('districts without street fixtures have an empty finite light batch',()=>{
 const lamps=new THREE.InstancedMesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial(),0),pools=createStreetLightPools(lamps);
 assert.equal(pools.count,0);assert.ok(Number.isFinite(pools.boundingSphere.radius));
 pools.geometry.dispose();pools.material.map.dispose();pools.material.dispose();lamps.geometry.dispose();lamps.material.dispose();
});
