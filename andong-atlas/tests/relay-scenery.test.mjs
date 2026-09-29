import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from 'three';
import {batchScenery} from '../src/relay-atmosphere.js';

const kit={mesh(parent,geometry,material){const mesh=new T.Mesh(geometry,material);parent.add(mesh);return mesh;}};
test('batching storefront scenery preserves world geometry beneath rotated parents',()=>{
 const world=new T.Group(),shop=new T.Group(),shelf=new T.Group();world.add(shop);shop.add(shelf);
 shop.position.set(5,0,7);shop.rotation.y=-Math.PI/2;shelf.position.set(.7,1,-.4);shelf.rotation.z=.1;
 const material=new T.MeshStandardMaterial();
 for(const x of [-.3,.3]){const mesh=new T.Mesh(new T.BoxGeometry(.2,.3,.4),material);mesh.position.x=x;mesh.castShadow=true;mesh.receiveShadow=true;shelf.add(mesh);}
 world.updateMatrixWorld(true);const before=new T.Box3().setFromObject(shop);
 batchScenery(shop,kit);world.updateMatrixWorld(true);const after=new T.Box3().setFromObject(shop);
 assert.ok(before.min.distanceTo(after.min)<1e-6);assert.ok(before.max.distanceTo(after.max)<1e-6);
 const rendered=[];shop.traverse(o=>{if(o.isMesh)rendered.push(o);});assert.equal(rendered.length,1);
 assert.equal(rendered[0].castShadow,true);assert.equal(rendered[0].receiveShadow,true);
});
test('scenery batching retains transparent glass, moving steam, hidden props and interactive objects',()=>{
 const group=new T.Group(),material=new T.MeshStandardMaterial();group.userData.action='buy-food';
 const solid=new T.Mesh(new T.BoxGeometry(2,1,1),material);group.add(solid);
 const glass=new T.Mesh(new T.PlaneGeometry(1,1),new T.MeshStandardMaterial({transparent:true,opacity:.15}));group.add(glass);
 const steam=new T.Sprite();group.add(steam);
 const hidden=new T.Group();hidden.visible=false;group.add(hidden);const prop=new T.Mesh(new T.BoxGeometry(),material);hidden.add(prop);
 const action=new T.Group();action.userData.action='photo';group.add(action);const target=new T.Mesh(new T.BoxGeometry(),material);action.add(target);
 const light=new T.PointLight();group.add(light);
 batchScenery(group,kit);
 assert.equal(glass.parent,group);assert.equal(steam.parent,group);assert.equal(prop.parent,hidden);assert.equal(target.parent,action);assert.equal(light.parent,group);
 const ray=new T.Raycaster(new T.Vector3(0,0,3),new T.Vector3(0,0,-1));group.updateMatrixWorld(true);
 const hit=ray.intersectObjects(group.children.filter(o=>o!==glass&&o!==steam&&o!==hidden&&o!==action),true)[0];assert.ok(hit);assert.equal(hit.object.parent.userData.action,'buy-food');
});
