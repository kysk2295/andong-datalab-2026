import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from 'three';
import {createBusCabin,createTransitKit,BUS_SEAT,BUS_AISLE_SEAT,BUS_FLOOR,BUS_ALIGHT_PATH} from '../src/transit-cabin.js';
import {JourneyScene} from '../src/journey-scene.js';
import {transitPhase} from '../src/journey-position.js';

test('passenger cabin has metre-scale proportions, grounded occupants and unobstructed eyes',()=>{
 const bus=createBusCabin({textures:false});bus.group.updateMatrixWorld(true);
 const box=new T.Box3().setFromObject(bus.group),size=box.getSize(new T.Vector3());
 assert.ok(size.x>2.4&&size.x<2.7);assert.ok(size.z>10&&size.z<10.5);assert.ok(size.y>2.6&&size.y<3);
 assert.equal(bus.people.length,7);assert.equal(bus.people.filter(p=>p.userData.driver).length,1);
 for(const person of bus.people){const b=new T.Box3().setFromObject(person);assert.ok(Math.abs(b.min.y-BUS_FLOOR)<.025);assert.ok(b.max.y<1.85&&b.max.y>1.5);}
 for(const eye of [BUS_SEAT,BUS_AISLE_SEAT]){
  for(let i=0;i<8;i++){
   const ray=new T.Raycaster(new T.Vector3(...eye),new T.Vector3(Math.sin(i*Math.PI/4),0,Math.cos(i*Math.PI/4)),0,.15);
   assert.equal(ray.intersectObjects(bus.group.children,true).length,0,'head is clear of seats, passengers and walls');
  }
 }
 let meshes=0;bus.group.traverse(o=>{if(o.isMesh){meshes++;for(const attr of Object.values(o.geometry.attributes))assert.ok([...attr.array].every(Number.isFinite));}});
 assert.ok(meshes<300,'batched cabin is suitable for the shared mobile renderer');bus.dispose();
});

test('passengers and straps animate without drifting, reduced motion stays still, and bell resets per ride',()=>{
 const bus=createBusCabin({textures:false}),origins=bus.people.map(p=>p.position.clone());
 bus.update(2,{moving:1,doorOpen:0});const first=bus.people.map(p=>p.userData.head.rotation.y);bus.update(5,{moving:1});assert.notDeepEqual(bus.people.map(p=>p.userData.head.rotation.y),first);
 bus.update(2,{moving:1});assert.deepEqual(bus.people.map(p=>p.userData.head.rotation.y),first);
 bus.people.forEach((p,i)=>assert.ok(p.position.equals(origins[i])));
 bus.update(8,{moving:1,reduced:true});const frozen=bus.straps.map(p=>p.rotation.toArray());bus.update(18,{moving:1,reduced:true});assert.deepEqual(bus.straps.map(p=>p.rotation.toArray()),frozen);
 assert.equal(bus.requestStop(),true);assert.equal(bus.requestStop(),false);assert.equal(bus.stopDisplay.visible,true);
 bus.setDestination('안동역');assert.equal(bus.destination,'안동역');bus.reset();assert.equal(bus.stopRequested,false);assert.equal(bus.stopDisplay.visible,false);
 bus.update(0,{doorOpen:1});assert.ok(bus.door.position.z>-3.89);bus.reset();assert.equal(bus.door.position.z,-3.89);bus.dispose();
});

test('map height compression preserves cabin proportions and metre-scale eye placement through a turn',()=>{
 const bus=createBusCabin({textures:false}),world=new T.Group();world.scale.y=.25;world.add(bus.group);bus.group.scale.set(.002,.008,.002);bus.group.position.set(4,.8,7);bus.group.rotation.y=1.8;world.updateMatrixWorld(true);
 const eye=bus.group.localToWorld(new T.Vector3(...BUS_SEAT)),floor=bus.group.localToWorld(new T.Vector3(BUS_SEAT[0],BUS_FLOOR,BUS_SEAT[2]));
 assert.ok(Math.abs(eye.distanceTo(floor)-(BUS_SEAT[1]-BUS_FLOOR)*.002)<1e-8);
 const roundTrip=bus.group.worldToLocal(eye.clone());assert.ok(roundTrip.distanceTo(new T.Vector3(...BUS_SEAT))<1e-9);bus.dispose();
});

test('batching preserves instancing, reflective water callbacks and interactive parts',()=>{
 const k=createTransitKit({textures:false}),g=new T.Group(),mat=k.mat('#aaa');
 const instance=new T.InstancedMesh(new T.BoxGeometry(),mat,2);g.add(instance);
 const water=k.box(g,[2,.1,2],[0,0,0],mat);water.userData.keep=true;const callback=()=>{};water.onBeforeRender=callback;
 const button=k.box(g,[.1,.1,.1],[1,1,1],mat);button.userData.keep=true;
 k.box(g,[1,1,1],[2,2,2],mat);k.batch(g);
 assert.equal(instance.parent,g);assert.equal(water.parent,g);assert.equal(water.onBeforeRender,callback);assert.equal(button.parent,g);k.dispose();instance.geometry.dispose();
});

test('map bus speed follows road distance instead of flying kilometres in seconds',()=>{
 const player=Object.create(JourneyScene.prototype);
 for(const distance of [180,3780,8000])assert.ok(player.duration({kind:'bus',path:{distance},start:0,end:10})>=distance/9);
 assert.equal(player.duration({kind:'walk',path:{distance:100},start:0,end:5}),9);
 assert.equal(player.duration({kind:'bus',path:{distance:0},start:0,end:5}),18);
 const duration=player.duration({kind:'bus',path:{distance:3780},start:0,end:10});
 assert.equal(transitPhase(2/duration,true,duration).phase,'riding','boarding does not expand with a long drive');
 assert.equal(transitPhase(1-1/duration,true,duration).phase,'alighting');
});

test('alighting follows the aisle to the front door with clear standing eye space',()=>{
 const bus=createBusCabin({textures:false});bus.group.updateMatrixWorld(true);
 const points=[BUS_SEAT,...BUS_ALIGHT_PATH].map(p=>new T.Vector3(...p));
 for(let i=1;i<points.length;i++)for(let n=0;n<=24;n++){
  const eye=points[i-1].clone().lerp(points[i],n/24);
  for(const dir of [[1,0,0],[-1,0,0],[0,0,1],[0,0,-1]])assert.equal(new T.Raycaster(eye,new T.Vector3(...dir),0,.1).intersectObjects(bus.group.children,true).length,0);
 }
 bus.dispose();
});
