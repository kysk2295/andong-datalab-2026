import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from 'three';
import { heritageAppearance, heritageLane, visitorWeight, visitorProgress } from '../src/heritage-model.js';
import { heritageRoof } from '../src/heritage-geometry.js';
import { DistrictScene } from '../src/district-scene.js';

test('Heritage streets assemble both narrow village lanes and ordinary roads',()=>{
  const groups=[];
  const scene={data:{heritage:true,roads:[
    {id:'lane',properties:{highway:'service'},geometry:{coordinates:[[0,0],[1,0]]}},
    {id:'road',properties:{highway:'tertiary',surface:'asphalt'},geometry:{coordinates:[[0,1],[1,1]]}},
  ]},bridgeSurfaces:new Map(),walks:[],paths:[],point:c=>new THREE.Vector3(c[0],0,c[1]),
    ribbon:()=>new THREE.PlaneGeometry(1,1),merge:(geometries,material)=>{groups.push(geometries.length);geometries.forEach(g=>g.dispose());material.dispose();}};
  DistrictScene.prototype.buildStreets.call(scene);
  assert.equal(scene.walks.length,1);
  assert.equal(scene.paths.length,1);
  assert.equal(scene.walks[0].lane,true);
  assert.ok(groups[0]>0);
});

test('Named heritage packs retain mapped open walls and source identifiers',()=>{
  for(const [id,count] of [['hahoe',93],['byeongsan',7],['dosan',40],['bongjeong',5]]){
    const data=JSON.parse(fs.readFileSync(new URL(`../public/data/regions/${id}.json`,import.meta.url)));
    assert.equal(data.heritageDetail.walls.length,count);
    for(const wall of data.heritageDetail.walls){
      assert.match(wall.id,/^osm-\d+$/);
      assert.equal(wall.properties.source,'OpenStreetMap API 0.6');
      assert.equal(wall.geometry.type,'LineString');
      assert.ok(wall.geometry.coordinates.every(c=>c.length===2&&c.every(Number.isFinite)));
    }
    assert.ok(data.heritageDetail.walls.some(f=>JSON.stringify(f.geometry.coordinates[0])!==JSON.stringify(f.geometry.coordinates.at(-1))));
  }
});
test('Heritage lane styling does not turn main asphalt roads into pedestrian lanes',()=>{
  assert.equal(heritageLane({highway:'service'},true),true);
  assert.equal(heritageLane({highway:'residential',surface:'asphalt'},true),false);
  assert.equal(heritageLane({highway:'tertiary'},true),false);
  assert.equal(heritageLane({highway:'residential'},false),false);
  const source={id:'osm-4',properties:{name:'북촌댁',visualRoof:'traditional'}};
  const before=JSON.stringify(source);
  assert.equal(heritageAppearance(source,'hahoe').thatch,false);
  assert.equal(JSON.stringify(source),before);
});
test('Visitor parties stay continuous, share direction, and pause without teleporting',()=>{
  const length=.09;
  let rests=0;
  for(let t=0;t<160;t+=.1){
    const a=visitorProgress(t,0,length),b=visitorProgress(t+.1,0,length);
    assert.ok(a.t>=0&&a.t<=1);
    assert.ok(Math.abs(b.t-a.t)<=.002);
    assert.deepEqual(a,visitorProgress(t,2,length));
    if(!a.moving)rests++;
  }
  assert.ok(rests>0);
  assert.ok(visitorWeight(0,0,[0,0],true)>visitorWeight(3,3,[0,0],true)*20);
});
test('Rounded roof refinement preserves the source footprint and courtyard opening',()=>{
  const shape=new THREE.Shape([new THREE.Vector2(0,0),new THREE.Vector2(4,0),new THREE.Vector2(4,2),new THREE.Vector2(0,2)]);
  shape.holes.push(new THREE.Path([new THREE.Vector2(1,.5),new THREE.Vector2(1,1.5),new THREE.Vector2(3,1.5),new THREE.Vector2(3,.5)]));
  const g=heritageRoof(shape,10,1,true),p=g.attributes.position;
  assert.ok(p.count>100);
  for(let i=0;i<p.count;i++)assert.ok(p.getY(i)>=10&&p.getY(i)<=11&&Number.isFinite(p.getY(i)));
  for(let i=0;i<p.count;i+=3){const x=(p.getX(i)+p.getX(i+1)+p.getX(i+2))/3,z=-(p.getZ(i)+p.getZ(i+1)+p.getZ(i+2))/3;assert.ok(!(x>1&&x<3&&z>.5&&z<1.5));}
  g.dispose();
});
