import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from 'three';
import {WorkshopInteraction} from '../src/relay-workshop.js';

globalThis.innerWidth=1280;
function setup(step){
 const refs={workTargets:[]};for(const key of ['teapot','kettle','teaStream','cupLiquid','potLiquid','flowers'])refs[key]=new T.Group();
 refs.teapot.position.set(-.35,.82,-.05);refs.teapot.scale.setScalar(.64);refs.kettle.position.set(.75,.82,-.45);refs.kettle.scale.setScalar(.75);refs.potLiquid.position.set(-.35,1.19,-.05);refs.cupLiquid.position.set(.4,.85,.12);refs.workTargets=[{id:'pour',object:refs.teapot}];
 const scene={current:{refs},camera:new T.PerspectiveCamera(58,1,.045,220),rightHand:new T.Group(),keys:new Set(),resetHands(){}};let finished;
 const task=new WorkshopInteraction(scene,{program:'tea',step,onUpdate(){},resolve:ok=>finished=ok});return {refs,task,scene,finished:()=>finished};
}
test('water and tea streams connect the moving spout to the destination vessel',()=>{
 for(const step of [1,2]){const {refs,task}=setup(step),source=step===1?refs.kettle:refs.teapot,end=step===1?refs.potLiquid:refs.cupLiquid;
  task.hold(true);task.tick(2.5);source.updateMatrixWorld();const spout=source.localToWorld(new T.Vector3(...(step===1?[-.48,.52,0]:[.5,.48,0])));
  assert.ok(spout.distanceTo(end.position.clone().add(new T.Vector3(0,.28,0)))<1e-10);assert.equal(refs.teaStream.visible,true);assert.ok(Math.abs(task.task.amount-65)<1e-8);
  task.hold(false);assert.equal(task.task.done,true);assert.equal(refs.teaStream.visible,false);
 }
});
test('cancel restores the kettle, liquid, stream, and original viewing position',()=>{
 const {refs,task,scene,finished}=setup(1),original=task.originals.get(refs.kettle),camera=task.camera.clone();task.hold(true);task.tick(1);task.finish(false);
 assert.equal(finished(),false);assert.deepEqual(refs.kettle.position,original.position);assert.deepEqual(refs.teaStream.scale,new T.Vector3(1,1,1));assert.deepEqual(scene.camera.position,camera);assert.equal(scene.workshop,null);
});

test('flower drag follows the actual vessel opening on desktop and mobile cameras',()=>{
 for(const width of [1280,390]){
  globalThis.innerWidth=width;const {task,scene,refs}=setup(0);const d=task.dropTarget('flower-0');
  assert.ok(Math.abs(d.y-(.82+.64*.57))<1e-8);
  scene.camera.aspect=width/(width===390?844:720);scene.camera.updateProjectionMatrix();scene.camera.updateMatrixWorld();
  const destination=new T.Vector3(d.x,d.y,d.z),screen=destination.clone().project(scene.camera),ray=new T.Raycaster();ray.setFromCamera(new T.Vector2(screen.x,screen.y),scene.camera);
  const drop=new T.Vector3();ray.ray.intersectPlane(new T.Plane(new T.Vector3(0,1,0),-d.y),drop);
  assert.ok(drop.distanceTo(destination)<1e-9);assert.equal(d.object,refs.teapot);
 }
 globalThis.innerWidth=1280;
});
test('dragging onto a visible vessel is accepted, while clicks and distant drops are rejected',async()=>{
 const {workshopDropAccepted}=await import('../src/relay-workshop.js'),d={x:-.35,z:-.05,r:.42};
 assert.equal(workshopDropAccepted({x:2,z:2},d,true,false),false);
 assert.equal(workshopDropAccepted({x:2,z:2},d,true,true),true);
 assert.equal(workshopDropAccepted({x:d.x,z:d.z},d,false,true),false);
});
test('a modeled spout overrides the generic pouring offset',()=>{
 const {task,refs}=setup(2);refs.teapot.userData.spout=[.515,.526,0];task.hold(true);refs.teapot.updateMatrixWorld();
 const tip=refs.teapot.localToWorld(new T.Vector3(...refs.teapot.userData.spout));
 assert.ok(tip.distanceTo(refs.cupLiquid.position.clone().add(new T.Vector3(0,.28,0)))<1e-10);
});
