import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from 'three';
import {canStand,clearWalk} from '../src/relay-navigation.js';
import {curvedRoof,pavilion} from '../src/relay-architecture.js';
function kit(){const geometries=[];const k={woodDark:new T.MeshStandardMaterial(),floor:new T.MeshStandardMaterial(),stone:new T.MeshStandardMaterial(),mat:()=>new T.MeshStandardMaterial(),mesh(g,geo,mat,p=[0,0,0]){geometries.push(geo);const m=new T.Mesh(geo,typeof mat==='string'?k.mat():mat);m.position.set(...p);g.add(m);return m;},tube(g,points,r,c){return k.mesh(g,new T.TubeGeometry(new T.CatmullRomCurve3(points.map(p=>new T.Vector3(...p))),20,r,6),c);},sphere(g,s,p,c){return k.mesh(g,new T.SphereGeometry(1,8,6),c,p);},box(g,s,p,c){return k.mesh(g,new T.BoxGeometry(...s),c,p);},cyl(g,a,b,h,p,c,n){return k.mesh(g,new T.CylinderGeometry(a,b,h,n),c,p);},label:()=>new T.Group(),lamp:()=>new T.Group()};return {k,geometries};}
test('curved roof edge samples remain finite despite Float32 rounding beyond the eaves',()=>{for(const [w,d] of [[4.8,4],[7.6,4],[10.7,9.4],[.7,7.2]]){const {k,geometries}=kit();curvedRoof(new T.Group(),w,d,[0,0,0],k);for(const geo of geometries){assert.ok(Array.from(geo.attributes.position.array).every(Number.isFinite),`${w}x${d}`);geo.dispose();}}});
test('pavilion curved panels and tile ribs have finite geometry and normals',()=>{const {k,geometries}=kit();pavilion(new T.Group(),[0,0,0],k);for(const geo of geometries){assert.ok(Array.from(geo.attributes.position.array).every(Number.isFinite));assert.ok(Array.from(geo.attributes.normal.array).every(Number.isFinite));geo.dispose();}});

test('market reconstruction exposes a hinged entrance before creating its interaction label',async()=>{
 const {marketStreet}=await import('../src/relay-architecture.js');const {k}=kit();k.instances=()=>new T.Group();k.grove=()=>new T.Group();k.table=()=>new T.Group();k.chair=()=>new T.Group();k.bowl=()=>new T.Group();k.person=()=>new T.Group();k.wood=k.woodDark;k.plaster=k.stone;k.paving=k.stone;
 k.surface=()=>k.mat();k.sign=k.label;k.photo=(g,id,p,w,h)=>k.mesh(g,new T.PlaneGeometry(w,h),k.mat(),p);
 const r={group:new T.Group(),refs:{people:[]},hotspots:[]};marketStreet(r,k,(object,action)=>{object.userData.action=action;return object;});
 assert.ok(r.refs.entryDoor instanceof T.Group);assert.equal(r.refs.entryDoor.children.length,2);assert.equal(r.refs.entryDoor.position.x,-1.3);
 assert.ok(r.stations.entrance.position[2]>=r.bounds.z[0]);
 assert.equal(canStand(r.camera[0],r.camera[2],r),true);
 for(const x of [-2.25,0,2.25])assert.equal(clearWalk([x,8],[x,-19.9],r),true);
 assert.equal(canStand(2.5,8,r),false);
 r.group.updateMatrixWorld(true);
 assert.ok(new T.Raycaster(new T.Vector3(0,1,18),new T.Vector3(0,-1,0),0,1.5).intersectObjects(r.group.children,true).length,'road continues outside the arcade');
 assert.ok(new T.Raycaster(new T.Vector3(0,1.7,18),new T.Vector3(0,0,1),0,15).intersectObjects(r.group.children,true).length,'return view ends on a street facade, not empty sky');
 r.group.traverse(o=>{if(o.geometry)for(const attr of Object.values(o.geometry.attributes))assert.ok([...attr.array].every(Number.isFinite));});
});
