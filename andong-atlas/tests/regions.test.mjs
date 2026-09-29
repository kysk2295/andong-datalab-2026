import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import * as THREE from 'three';
import {regionFor,contains,regionBudgets} from '../src/region-model.js';
import {heritageRoof,roofForMerge} from '../src/heritage-geometry.js';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';
import {Vegetation} from '../src/vegetation.js';
import {terraceTerrain,balanceFootings} from '../src/terrain-display.js';
import {sampleHeight} from '../src/geo.js';
const root=new URL('../public/data/',import.meta.url);
const read=n=>JSON.parse(fs.readFileSync(new URL(n,root)));
const index=read('regions.json'),core=read('district.json');
test('Core has priority and every named outer destination resolves to its own detail region',()=>{
 assert.equal(regionFor([128.731,36.566],core.bbox,index.regions),'city');
 for(const id of ['station','hahoe','byeongsan','dosan','bongjeong']){const r=index.regions.find(r=>r.id===id);assert.equal(regionFor(r.center,core.bbox,index.regions),id);assert.equal(r.osmDetail,true);}
 assert.equal(regionFor([0,0],core.bbox,index.regions),null);
});
test('Every regional package has consistent elevation, compressed parity, and connected source geometry',()=>{
 for(const region of index.regions){
  const file=new URL(`regions/${region.id}.json`,root),raw=fs.readFileSync(file),data=JSON.parse(raw);
  assert.deepEqual(gunzipSync(fs.readFileSync(new URL(file.href+'.gz'))),raw);
  assert.equal(data.terrain.heights.length,data.terrain.cols*data.terrain.rows);
  assert.ok(data.terrain.heights.every(v=>Number.isFinite(v)&&v>=0&&v<2000));
  assert.ok(data.roads.every(f=>f.properties.highway&&f.geometry.coordinates.length>=2));
  assert.ok(data.roads.flatMap(f=>f.geometry.coordinates).every(c=>contains(data.bbox,c)));
  assert.ok(data.buildings.every(f=>f.geometry.type==='Polygon'&&f.geometry.coordinates[0].length>=4));
 }
});
test('Regional density stays within mobile budgets rather than copying metropolitan traffic totals',()=>{
 const r=index.regions.find(r=>r.id==='dosan');
 assert.ok(regionBudgets(r,true).cars<regionBudgets(r,false).cars);
 assert.ok(regionBudgets(r,false).people<regionBudgets(core,false).people);
});
test('Heritage roof preserves a courtyard hole and does not project beyond its footprint',()=>{
 const shape=new THREE.Shape([new THREE.Vector2(0,0),new THREE.Vector2(4,0),new THREE.Vector2(4,2),new THREE.Vector2(0,2)]);
 shape.holes.push(new THREE.Path([new THREE.Vector2(1,.5),new THREE.Vector2(1,1.5),new THREE.Vector2(3,1.5),new THREE.Vector2(3,.5)]));
 const g=heritageRoof(shape,10,1),p=g.attributes.position;
 for(let i=0;i<p.count;i++){assert.ok(p.getX(i)>=0&&p.getX(i)<=4);assert.ok(p.getZ(i)<=0&&p.getZ(i)>=-2);assert.ok(p.getY(i)>=10&&p.getY(i)<=11);}
 for(let i=0;i<p.count;i+=3){const x=(p.getX(i)+p.getX(i+1)+p.getX(i+2))/3,z=-(p.getZ(i)+p.getZ(i+1)+p.getZ(i+2))/3;assert.ok(!(x>1&&x<3&&z>.5&&z<1.5));}
 g.dispose();
});
test('Flat roofs and heritage roofs can share one geometry batch',()=>{
 const shape=new THREE.Shape([new THREE.Vector2(0,0),new THREE.Vector2(4,0),new THREE.Vector2(4,2),new THREE.Vector2(0,2)]);
 const parts=[roofForMerge(new THREE.ShapeGeometry(shape)),roofForMerge(heritageRoof(shape,1))];
 const combined=mergeGeometries(parts);
 assert.ok(combined?.attributes.position.count>0);
 parts.forEach(g=>g.dispose());combined.dispose();
});
test('A rural region with no mapped park trees can load and change seasons',()=>{
 const trees=new Vegetation(new THREE.Group(),[]);
 for(const season of ['spring','autumn','winter','summer']) assert.doesNotThrow(()=>trees.setSeason(season));
 trees.group.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});
});
test('Display terraces reduce unresolved building slopes without changing raw elevation',()=>{
 const terrain={bbox:[0,0,1,1],cols:11,rows:11,heights:Array.from({length:121},(_,i)=>20+i%11*2)};
 const raw=[...terrain.heights],ring=[[.46,.46],[.54,.46],[.54,.54],[.46,.54],[.46,.46]];
 const next=terraceTerrain(terrain,[{properties:{visualRoof:'traditional'},geometry:{type:'Polygon',coordinates:[ring]}}]);
 const span=t=>{const v=ring.map(p=>sampleHeight(t,...p));return Math.max(...v)-Math.min(...v);};
 assert.deepEqual(terrain.heights,raw);assert.ok(span(next)<span(terrain));assert.equal(next.heights[0],raw[0]);
});
test('Shared footing correction is bounded, preserves tile edges, and does not alter source terrain',()=>{
 const terrain={bbox:[0,0,1,1],cols:11,rows:11,heights:Array.from({length:121},(_,i)=>20+i%11*2)};
 const buildings=[{id:'a',properties:{visualRoof:'traditional'},geometry:{type:'Polygon',coordinates:[[[.36,.4],[.54,.4],[.54,.6],[.36,.6],[.36,.4]]]}}];
 const original=structuredClone(terrain),out=balanceFootings(terrain,buildings);
 assert.deepEqual(terrain,original);
 for(let i=0;i<out.heights.length;i++){
  assert.ok(Math.abs(out.heights[i]-original.heights[i])<=4+1e-9);
  if(i%11===0||i%11===10||i<11||i>=110)assert.equal(out.heights[i],original.heights[i]);
 }
 const samples=buildings[0].geometry.coordinates[0].map(p=>sampleHeight(out,...p));
 assert.ok(Math.max(...samples)-Math.min(...samples)<.4);
 assert.deepEqual(balanceFootings(terrain,[]),terrain);
});
test('Named heritage building edges no longer need tall DEM-induced foundations',()=>{
 for(const id of ['hahoe','byeongsan','dosan','bongjeong']){
  const data=read(`regions/${id}.json`),original=structuredClone(data),out=terraceTerrain(data.terrain,data.buildings);
  for(const f of data.buildings.filter(f=>f.properties.visualRoof==='traditional')){
   const heights=f.geometry.coordinates.flatMap(r=>r.map(p=>sampleHeight(out,...p)));
   assert.ok(Math.max(...heights)-Math.min(...heights)<.55,`${id}/${f.id} has an excessive footing slope`);
  }
  assert.deepEqual(data,original);
 }
});
