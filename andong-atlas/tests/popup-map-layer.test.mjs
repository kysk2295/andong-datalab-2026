import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {popupSite,popupBoothCoordinate,popupBoothHref,popupEntryStation} from '../src/popup-map-layer.js';
import {POPUP_BOOTHS,popupLayout} from '../src/relay-popup-layout.js';
import {visibleMapPlaces,layerState,mapPlaceLayer} from '../src/tourism-map-model.js';
import {canStand} from '../src/relay-navigation.js';
const model=JSON.parse(readFileSync(new URL('../public/data/tourism-map.json',import.meta.url)));

test('popup visibility is independent from benefits and the relay route, and old preferences migrate',()=>{
 const old=layerState('{"benefits":true,"route":false}');assert.deepEqual(old,{benefits:true,route:false,booths:false});
 const on={...old,booths:true},off={...on,booths:false};
 assert.deepEqual(visibleMapPlaces(model,off),visibleMapPlaces(model,old));
 const extra=visibleMapPlaces(model,on).filter(p=>mapPlaceLayer(p)==='booths');
 assert.equal(extra.length,1);assert.equal(extra[0].proposed,true);assert.ok(!extra[0].benefit);
 assert.deepEqual(layerState(JSON.stringify(on)),on);assert.equal(layerState('{"booths":"false"}').booths,false);
 assert.deepEqual(visibleMapPlaces(model,{booths:true}),extra);
});
test('proposal anchor and metre-based layout preserve the scene spacing without claiming actual booth locations',()=>{
 const site=popupSite(model);assert.deepEqual(site.coordinates,model.stages[2].coordinates);assert.match(site.note,/미확정/);
 assert.deepEqual(popupBoothCoordinate(site,0,0),site.coordinates);
 const east=popupBoothCoordinate(site,31,0),north=popupBoothCoordinate(site,0,-22);
 assert.ok(east[0]>site.coordinates[0]);assert.ok(north[1]>site.coordinates[1]);
 assert.ok(Math.abs((east[0]-site.coordinates[0])*111320*Math.cos(site.coordinates[1]*Math.PI/180)-31)<1e-7);
 assert.equal(popupSite({...model,stages:[]}),null);assert.deepEqual(visibleMapPlaces({...model,stages:[]},{booths:true}),[]);
});
test('all nine booth links arrive at a walkable station and invalid booth links cannot move another scene',()=>{
 for(const b of POPUP_BOOTHS){const url=new URL(popupBoothHref(b.id),'https://example.test'),s=popupEntryStation(url.searchParams.get('visit'),url.searchParams.get('booth'));
  assert.equal(url.searchParams.get('at'),'popup');assert.equal(s.name,b.name);assert.ok(canStand(s.position[0],s.position[2],popupLayout()));
 }
 for(const id of ['constructor','__proto__','<script>','missing']){assert.equal(popupEntryStation('popup',id),null);assert.ok(!popupBoothHref(id).includes('booth='));}
 assert.equal(popupEntryStation('bridge','tea'),null);
});

test('the map toggle controls nine solid 3D booths with depth and shading, independently of the base city',async()=>{
 const THREE=await import('three'),{createPopupMapOverlay}=await import('../src/popup-map-overlay.js');
 const world=new THREE.Group(),city=new THREE.Mesh(new THREE.BoxGeometry(1,1,1),new THREE.MeshStandardMaterial());world.add(city);
 const atlas={world,project:{scale:2},point:c=>new THREE.Vector3(c[0],.5,c[1]),renderer:{shadowMap:{},domElement:{addEventListener(){}}},container:{dataset:{}}};
 const overlay=createPopupMapOverlay(atlas,popupSite(model));assert.equal(overlay.group.visible,false);
 overlay.setVisible(true);assert.equal(atlas.container.dataset.popupBoothModels,'9');
 for(const b of POPUP_BOOTHS){const object=overlay.group.getObjectByName(b.id);assert.ok(object);assert.equal(object.userData.boothId,b.id);const box=new THREE.Box3().setFromObject(object),size=box.getSize(new THREE.Vector3());assert.ok(size.x>0&&size.y>0&&size.z>0);assert.ok(object.children.some(m=>m.isMesh&&m.material.isMeshStandardMaterial&&m.material.depthTest));}
 overlay.setVisible(false);assert.equal(overlay.group.visible,false);assert.equal(atlas.container.dataset.popupBoothModels,'0');assert.equal(city.visible,true);assert.ok(world.children.includes(city));
});

test('booth flashes stay local, can restart, and restore original lighting after completion or hiding',async()=>{
 const THREE=await import('three'),{createPopupMapOverlay}=await import('../src/popup-map-overlay.js');
 const atlas={world:new THREE.Group(),project:{scale:2},point:c=>new THREE.Vector3(c[0],.5,c[1]),renderer:{shadowMap:{},domElement:{addEventListener(){}}},container:{dataset:{}}};
 const overlay=createPopupMapOverlay(atlas,popupSite(model));
 const booth=id=>overlay.group.getObjectByName(id),ring=id=>booth(id).children.find(m=>m.geometry.type==='RingGeometry');
 const materials=id=>booth(id).children.filter(m=>m.material.isMeshStandardMaterial).map(m=>m.material);
 const original=materials('food').map(m=>({intensity:m.emissiveIntensity,color:m.emissive.getHex()}));
 overlay.setVisible(true);
 assert.ok(POPUP_BOOTHS.every(b=>materials(b.id).every(m=>m.emissiveIntensity>1)));
 overlay.select('food');overlay.flash('food',1000);
 assert.ok(materials('food').every(m=>m.emissiveIntensity>1));
 assert.ok(materials('grill').every(m=>m.emissiveIntensity<=.35));
 overlay.update(1400);assert.deepEqual(materials('food').map(m=>m.emissiveIntensity),original.map(m=>m.intensity));
 overlay.flash('food',1500);assert.ok(materials('food').every(m=>m.emissiveIntensity>1));
 overlay.update(3900);
 assert.deepEqual(materials('food').map(m=>({intensity:m.emissiveIntensity,color:m.emissive.getHex()})),original);
 assert.equal(ring('food').visible,true);assert.equal(ring('grill').visible,false);
 overlay.flash('food',4000);overlay.setVisible(false);overlay.update(4200);
 assert.deepEqual(materials('food').map(m=>({intensity:m.emissiveIntensity,color:m.emissive.getHex()})),original);
});

test('night fixtures remain lit after a flash, follow weather changes, and survive hiding',async()=>{
 const THREE=await import('three'),{createPopupMapOverlay}=await import('../src/popup-map-overlay.js');
 const atlas={mode:'day',world:new THREE.Group(),project:{scale:2},point:c=>new THREE.Vector3(c[0],.5,c[1]),renderer:{shadowMap:{},domElement:{addEventListener(){}}},container:{dataset:{}}};
 const overlay=createPopupMapOverlay(atlas,popupSite(model));
 const materials=[];overlay.group.traverse(m=>{if(m.material?.isMeshStandardMaterial&&!materials.includes(m.material))materials.push(m.material);});
 const state=()=>materials.map(m=>({intensity:m.emissiveIntensity,color:m.emissive.getHex()}));
 const pools=POPUP_BOOTHS.map(b=>overlay.group.getObjectByName(b.id).getObjectByName('booth-light-pool'));
 const day=state();assert.ok(pools.every(p=>!p.visible));
 overlay.setVisible(true);overlay.flash(null,0);overlay.update(2400);
 atlas.mode='night';overlay.update(2500);
 const night=state();assert.notDeepEqual(night,day);assert.ok(pools.every(p=>p.visible));
 for(const b of POPUP_BOOTHS)assert.ok(overlay.group.getObjectByName(b.id).children.some(m=>m.material?.emissiveIntensity>=2));
 for(const m of materials.filter(m=>m.userData.nightIntensity>0))assert.equal(m.emissiveIntensity,m.userData.nightIntensity);
 overlay.select('food');overlay.flash('food',3000);assert.notDeepEqual(state(),night);
 overlay.update(5400);assert.deepEqual(state(),night);
 overlay.update(20000);assert.deepEqual(state(),night);
 overlay.setVisible(false);overlay.update(21000);assert.deepEqual(state(),night);
 overlay.setVisible(true);overlay.flash(null,22000);overlay.update(24400);assert.deepEqual(state(),night);
 overlay.flash('food',25000);atlas.mode='day';overlay.update(27400);assert.deepEqual(state(),day);assert.ok(pools.every(p=>!p.visible));
 atlas.mode='night';overlay.update(28000);assert.deepEqual(state(),night);
 atlas.mode='sunset';overlay.update(29000);assert.deepEqual(state(),day);
 const initialNight=createPopupMapOverlay({...atlas,mode:'night'},popupSite(model));
 assert.ok(initialNight.group.getObjectByName('food').children.some(m=>m.material?.emissiveIntensity>=2));
});
