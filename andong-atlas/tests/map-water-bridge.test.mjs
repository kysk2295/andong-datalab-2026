import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from 'three';
import {animateMapWater,advanceMapWater} from '../src/map-water.js';
import {overviewCutout} from '../src/overview-cutout.js';
import {bridgeDeckProfile,bridgeSurfaces} from '../src/bridge-surface.js';
import {AtlasScene} from '../src/scene.js';
import {projection,sampleHeight} from '../src/geo.js';

test('map water advances continuously across detail views and freezes without resetting',()=>{
  const a={value:0},b={value:0};
  for(let i=0;i<60;i++)advanceMapWater(a,1/60);
  for(let i=0;i<30;i++)advanceMapWater(b,1/30);
  assert.ok(Math.abs(a.value-b.value)<1e-12);
  const before=a.value;
  advanceMapWater(a,1,false);advanceMapWater(a,1,true,true);
  for(const dt of [NaN,Infinity,-1,0])advanceMapWater(a,dt);
  assert.equal(a.value,before);advanceMapWater(a,.1);assert.equal(a.value,before+.1);
});

test('flow reaches the actual surface material and composes with overview clipping',()=>{
  const time={value:12},clip={bounds:{value:new THREE.Vector4()},enabled:{value:1}};
  const detail=animateMapWater(new THREE.MeshStandardMaterial(),time);
  const overview=animateMapWater(new THREE.MeshStandardMaterial(),time,{terrain:true});
  overviewCutout(overview,clip);
  const compile=material=>{
    const shader={uniforms:{},vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader};
    material.onBeforeCompile(shader);return shader;
  };
  const d=compile(detail),o=compile(overview);
  assert.equal(d.uniforms.mapWaterTime,time);assert.equal(o.uniforms.mapWaterTime,time);
  assert.equal(o.uniforms.detailEnabled,clip.enabled);
  assert.match(d.fragmentShader,/float waterMask=1\./);
  assert.match(o.fragmentShader,/if\(detailEnabled/);
  assert.match(o.fragmentShader,/float waterMask=step/);
  assert.notEqual(detail.customProgramCacheKey(),overview.customProgramCacheKey());
  detail.dispose();overview.dispose();
});

const read=n=>JSON.parse(fs.readFileSync(new URL(`../public/data/${n}.json`,import.meta.url)));
const district=read('district'),project=projection(read('terrain').bbox);
const main=district.roads.find(f=>f.properties['bridge:name']==='월영교');
const elevation=c=>sampleHeight(district.terrain,...c)*.008;

test('actual bridge deck and walking surface meet both unequal-height banks and every bend',()=>{
  const atlas={data:{district},project,elevation,landmarkMaterials:[],mode:'day',positionBridge:AtlasScene.prototype.positionBridge};
  const group=new THREE.Group();AtlasScene.prototype.refreshBridge.call(atlas,group);group.updateMatrixWorld(true);
  const profile=bridgeDeckProfile(main,elevation,project);
  const surfaces=bridgeSurfaces(district.roads,elevation,project);
  for(const feature of district.roads.filter(f=>f===main||f.properties.name==='Moonlight Bridge')){
    const cs=feature.geometry.coordinates.map(c=>project.toWorld(c));
    for(let i=1;i<cs.length;i++)for(const t of [0,.001,.25,.5,.75,.999,1]){
      const a=cs[i-1],b=cs[i],x=a[0]+(b[0]-a[0])*t,z=a[1]+(b[1]-a[1])*t;
      const hits=new THREE.Raycaster(new THREE.Vector3(x,3,z),new THREE.Vector3(0,-1,0)).intersectObject(group,true);
      const deck=hits.find(h=>['deck','deck-joint'].includes(h.object.name));
      assert.ok(deck,`${feature.id}:${i}:${t} has a continuous deck`);
      assert.ok(Math.abs(deck.point.y-surfaces.get(String(feature.id))(x,z))<.001,`matching walking height ${feature.id}:${t}`);
    }
  }
  for(const index of [0,main.geometry.coordinates.length-1]){
    assert.ok(Math.abs(profile.heights[index]-elevation(main.geometry.coordinates[index])-.0012)<1e-9);
  }
  const children=group.children.slice();AtlasScene.prototype.refreshBridge.call(atlas,group);
  assert.deepEqual(group.children,children,'same profile does not rebuild resources');
  atlas.elevation=c=>elevation(c)+.2;AtlasScene.prototype.refreshBridge.call(atlas,group);group.updateMatrixWorld(true);
  assert.notEqual(group.children[0],children[0],'a new terrain level rebuilds the bank connections');
  assert.equal(atlas.landmarkMaterials.length,3,'old material references are released');
  const unique=new Set();group.traverse(o=>{o.geometry?.dispose();if(o.material)unique.add(o.material);});unique.forEach(m=>m.dispose());
});
