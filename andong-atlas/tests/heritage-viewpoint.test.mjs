import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {heritageViewpoints,makeHeritageInspection} from '../src/heritage-viewpoint.js';
import {heritagePlaces} from '../src/heritage-tour.js';
import {heritageVisit} from '../src/heritage-visit.js';
import {projection} from '../src/geo.js';
import {footprintMask,corridorMask} from '../src/footprints.js';
import {clearRuns} from '../src/activity.js';

for(const id of ['hahoe','byeongsan','dosan','bongjeong'])test(`${id}: observation views keep camera and sightline outside source obstacles`,()=>{
  const data=JSON.parse(fs.readFileSync(new URL(`../public/data/regions/${id}.json`,import.meta.url)));
  const original=JSON.stringify(data),project=projection(data.bbox),places=heritagePlaces(data),views=heritageViewpoints(data,project,places);
  assert.ok(views.size>=3,`${id}: ${views.size} views`);
  const buildings=footprintMask(data.buildings,project.toWorld),water=footprintMask(data.water||[],project.toWorld),walls=corridorMask(data.heritageDetail.walls,project.toWorld,()=>.0018);
  for(const v of views.values()){
    const from=project.toWorld(v.coordinates),to=project.toWorld(v.lookAt),distance=Math.hypot(from[0]-to[0],from[1]-to[1]);
    assert.ok(distance>=.0119&&distance<=.0241);
    for(let d=.002;d<distance;d+=.0005){const x=to[0]+(from[0]-to[0])*d/distance,z=to[1]+(from[1]-to[1])*d/distance;assert.ok(!buildings(x,z,.0014)&&!water(x,z)&&!walls(x,z,.0009));}
  }
  const selected=[...views.keys()].at(-1),tour=makeHeritageInspection(data,places,views,selected);
  assert.equal(tour.stages[tour.initial].place.id,selected);
  assert.equal(tour.distance,0);
  assert.ok(tour.stages.every(s=>!s.path&&s.viewpoint));
  assert.equal(JSON.stringify(data),original);
});
test('A fully enclosed or obstructed facade does not get a fabricated observation point',()=>{
  const box=(id,a,b)=>({id,geometry:{type:'Polygon',coordinates:[[[a,a],[b,a],[b,b],[a,b],[a,a]]]}});
  const data={id:'example',buildings:[box('1',0,.02)],water:[box('water',-.1,.1)],heritageDetail:{walls:[]}};
  assert.equal(heritageViewpoints(data,{toWorld:c=>c,toGeo:(x,y)=>[x,y]},[{id:'example:1'}]).size,0);
});
test('Walking runs cannot bridge a thin wall between clear sample endpoints',()=>{
  const points=[0,.004,.008,.012].map(x=>({x,z:0}));
  const runs=clearRuns(points,x=>x>.0055&&x<.0065,0);
  assert.deepEqual(runs.map(r=>r.map(p=>p.x)),[[0,.004],[.008,.012]]);
});
test('Official visit and VR information is scoped to the right heritage site',()=>{
  assert.equal(heritageVisit({id:'dosan:osm-123'}).vr.url,'https://my.matterport.com/show/?m=1wW24pkKSh3');
  assert.equal(heritageVisit({id:'bongjeong'}).vr,undefined);
  assert.equal(heritageVisit({id:'hahoe'}),null);
  assert.equal(heritageVisit({id:'dosan:popup',proposed:true}),null);
  assert.match(heritageVisit({region:'dosan'}).price,/2,000/);
});
test('Inspection camera observes each stop directly, without snapping to an unrelated road or animating a traveler',async()=>{
  const THREE=await import('three'),{JourneyScene}=await import('../src/journey-scene.js');
  const player=Object.create(JourneyScene.prototype);
  const stage={kind:'sight',place:{coordinates:[20,20]},viewpoint:{coordinates:[2,3],lookAt:[2,3.1]},start:0,end:1};
  Object.assign(player,{group:new THREE.Group(),decor:new THREE.Group(),active:true,playing:false,view:'first',elapsed:0,index:0,yaw:0,pitch:0,
    person:new THREE.Group(),bus:new THREE.Group(),car:new THREE.Group(),network:{snap:()=>{throw new Error('Inspection must not snap to a road');}},onTick:()=>{},journey:{stages:[stage]},paths:[[]],
    a:{point:c=>new THREE.Vector3(c[0],1,c[1]),project:{toGeo:(x,z)=>[x,z]},elevation:()=>1,focusDetail:()=>{},camera:new THREE.PerspectiveCamera(),controls:{target:new THREE.Vector3()},container:{dataset:{}}}});
  player.update(0);
  assert.equal(player.a.camera.position.x,2);assert.equal(player.a.camera.position.z,3);
  assert.equal(player.person.visible,false);assert.equal(player.bus.visible,false);assert.equal(player.car.visible,false);
  assert.ok(player.a.controls.target.z>3);
});
test('Roof tile coordinates follow a rotated building axis rather than global north',async()=>{
  const THREE=await import('three'),{heritageRoof}=await import('../src/heritage-geometry.js');
  const angle=.61,points=[[0,0],[.06,0],[.06,.02],[0,.02]].map(([x,y])=>new THREE.Vector2(x*Math.cos(angle)-y*Math.sin(angle),x*Math.sin(angle)+y*Math.cos(angle)));
  const g=heritageRoof(new THREE.Shape(points),1),p=g.getAttribute('position'),local=g.getAttribute('roofLocal');
  assert.equal(local.count,p.count);
  for(let i=0;i<p.count;i++)assert.ok(Math.abs(local.getX(i)-(p.getX(i)*Math.cos(angle)-p.getZ(i)*Math.sin(angle)))<1e-6);
  g.dispose();
});
test('Traditional roofs close the triangular ends above the facade',async()=>{
  const THREE=await import('three'),{heritageGables}=await import('../src/heritage-geometry.js');
  const shape=new THREE.Shape([new THREE.Vector2(0,0),new THREE.Vector2(.06,0),new THREE.Vector2(.06,.02),new THREE.Vector2(0,.02)]);
  const g=heritageGables(shape,1,.012),p=g.getAttribute('position');
  let area=0;
  for(let i=0;i<p.count;i+=3){const a=new THREE.Vector3().fromBufferAttribute(p,i),b=new THREE.Vector3().fromBufferAttribute(p,i+1),c=new THREE.Vector3().fromBufferAttribute(p,i+2);area+=b.sub(a).cross(c.sub(a)).length()/2;}
  assert.ok(Math.abs(area-2*.02*.012/2)<1e-8);
  g.dispose();
});
