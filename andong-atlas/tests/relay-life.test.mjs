import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from 'three';
import {addSceneLife,SCENE_VISITORS} from '../src/relay-life.js';
import {createBusCabin,createTransitKit} from '../src/transit-cabin.js';
import {visitor} from '../src/relay-people.js';
import {JOURNEYS,journeyLayout,journeyVehicle} from '../src/relay-journey.js';
import {diningLayout} from '../src/relay-dining-layout.js';
import {planWalk} from '../src/relay-navigation.js';
import {popupLayout} from '../src/relay-popup-layout.js';

test('existing window diners lower their torso while feet remain grounded',()=>{
 const k=createTransitKit({textures:false}),group=new T.Group();
 k.hand=(parent)=>{const hand=new T.Group();hand.userData.sleeve=new T.Group();parent.add(hand);return hand;};
 const standing=visitor(group,[0,0,0],{},k),seated=visitor(group,[2,0,0],{seated:true},k);
 group.updateMatrixWorld(true);
 assert.ok(standing.userData.head.position.y-seated.userData.head.position.y>.3);
 assert.ok(new T.Box3().setFromObject(seated).max.y<1.45);
 assert.ok(Math.abs(new T.Box3().setFromObject(seated).min.y)<.03);
 k.dispose();
});

test('diners sit at chair height with feet on the floor and hands over the table',()=>{
 const scene={group:new T.Group(),refs:{}},life=addSceneLife(scene,'meal',{textures:false});
 scene.group.updateMatrixWorld(true);
 for(const p of life.people){
  const box=new T.Box3().setFromObject(p),head=p.userData.head.getWorldPosition(new T.Vector3());
  assert.ok(Math.abs(box.min.y)<.025);assert.ok(head.y>1.15&&head.y<1.35);
  assert.ok(box.max.y<1.5,'seated guests do not have a standing torso');
  assert.equal(p.userData.activity,'eat');
 }
 const layout=diningLayout();layout.obstacles.push(...SCENE_VISITORS.meal.map(s=>({x:s.p[0],z:s.p[2],w:.55,d:.63})));
 for(const station of Object.values(layout.stations))assert.ok(planWalk([0,5.1],[station.position[0],station.position[2]],layout));
 life.dispose();
});

test('walkers retain raised-deck foot height and reduced motion freezes their poses',()=>{
 const scene={group:new T.Group(),refs:{}},life=addSceneLife(scene,'bridge',{textures:false}),p=life.people[1];
 life.update(2);const first=p.position.clone();life.update(5);assert.notEqual(p.position.z,first.z);
 assert.equal(p.position.y,.305);assert.ok(p.userData.legs.some(leg=>leg.rotation.x!==0));
 life.update(8,true);const pose=JSON.stringify([p.position.toArray(),p.rotation.toArray(),p.userData.legs.map(l=>l.rotation.toArray())]);
 life.update(28,true);assert.equal(JSON.stringify([p.position.toArray(),p.rotation.toArray(),p.userData.legs.map(l=>l.rotation.toArray())]),pose);
 life.dispose();
});

test('festival diners stay within existing table footprints and every booth remains reachable',()=>{
 const layout=popupLayout();
 for(const guest of SCENE_VISITORS.popup.filter(s=>s.seated))assert.ok(layout.obstacles.some(o=>Math.abs(guest.p[0]-o.x)<o.w/2&&Math.abs(guest.p[2]-o.z)<o.d/2));
 const entrance=layout.stations.entrance.position;
 for(const station of Object.values(layout.stations))assert.ok(planWalk([entrance[0],entrance[2]],[station.position[0],station.position[2]],layout),station.name);
});

test('same full-sized bus is reachable from the pavement at both stops',()=>{
 const bus=createBusCabin({textures:false});
 for(const id of ['pickup','arrival']){
  const placement=journeyVehicle(id),layout=journeyLayout(id),legs=JOURNEYS[id].legs;
  bus.group.position.set(placement.x,0,placement.z);bus.group.rotation.y=Math.PI;bus.group.updateMatrixWorld(true);
  const door=bus.group.localToWorld(new T.Vector3(1.23,.8,-3.89));
  assert.ok(Math.abs(door.z-(id==='pickup'?-4.2:8))<.01);
  assert.ok(door.x<placement.x,'door opens onto the pavement');
  let start=[0,8];for(const leg of legs){const end=[leg.position[0],leg.position[2]];assert.ok(planWalk(start,end,layout),id+' walking leg remains reachable');start=end;}
 }
 bus.dispose();
});

test('open front door has a real opening at knee, waist and head height',()=>{
 const bus=createBusCabin({textures:false});bus.update(0,{doorOpen:1});bus.group.updateMatrixWorld(true);
 for(const y of [.65,1,1.7,2.1]){
  const hits=new T.Raycaster(new T.Vector3(.8,y,-3.89),new T.Vector3(1,0,0),0,.8).intersectObjects(bus.group.children,true);
  assert.equal(hits.length,0,`doorway blocked at ${y}m`);
 }
 bus.dispose();
});
