import * as THREE from 'three';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';
import {POPUP_BOOTHS,POPUP_TABLES,POPUP_STAGE} from './relay-popup-layout.js';
import {popupBoothCoordinate} from './popup-map-layer.js';

// Architectural map models share the metre layout with the first-person market.
export function createPopupMapOverlay(atlas,site,onSelect=()=>{}){
 const group=new THREE.Group();group.name='popup-booth-map-overlay';group.visible=false;atlas.world.add(group);
 const records=[],metre=atlas.project.scale/1000;
 const materials=new Map();
 const mat=(color,glow=false,nightIntensity=glow?2.6:0)=>{const key=color+glow+nightIntensity;if(!materials.has(key)){const material=new THREE.MeshStandardMaterial({color,roughness:.84,emissive:glow?color:'#000000',emissiveIntensity:glow?.35:0});material.userData.nightIntensity=nightIntensity;materials.set(key,material);}return materials.get(key);};
 const box=(parent,size,pos,color,nightIntensity=0)=>{const m=new THREE.Mesh(new THREE.BoxGeometry(...size),mat(color,false,nightIntensity));m.position.set(...pos);m.castShadow=true;m.receiveShadow=true;parent.add(m);return m;};
 const shell=(name,x,z)=>{const g=new THREE.Group();g.name=name;g.scale.set(metre,metre*1.5,metre);group.add(g);records.push({object:g,x,z});return g;};
 const ground=new THREE.Mesh(new THREE.PlaneGeometry(62,44),new THREE.MeshStandardMaterial({color:'#b99b6b',transparent:true,opacity:.28,depthWrite:false,roughness:1,polygonOffset:true,polygonOffsetFactor:-2}));ground.rotation.x=-Math.PI/2;
 const pad=shell('popup-proposal-ground',0,0);pad.add(ground);
 const outlines=[];
 for(const b of POPUP_BOOTHS){
  const booth=shell(b.id,b.x,b.z);booth.userData.boothId=b.id;
  box(booth,[4.8,.22,3.7],[0,.11,0],'#8b7657');
  box(booth,[4.5,2.7,.14],[0,1.57,-1.6],'#e9dfc8',.36);
  for(const x of [-2.18,2.18]){
   box(booth,[.14,2.7,3.2],[x,1.57,0],'#dfd0af',.2);
   for(const z of [-1.52,1.52])box(booth,[.14,3.1,.14],[x,1.74,z],'#765744');
  }
  box(booth,[4.1,1,.14],[0,.72,1.4],b.color);
  box(booth,[4.65,.16,.85],[0,1.3,1.54],'#92765a',.3);
  box(booth,[3.8,.1,.52],[0,1.4,-1.27],'#8c745a');
  box(booth,[2.15,.78,.08],[0,2.1,-1.49],'#354d47');
  for(const x of [-1.25,-.42,.42,1.25]){
   box(booth,[.4,.25,.32],[x,1.51,1.55],b.kind==='kitchen'?'#b78142':'#c8af7f');
   box(booth,[.35,.35,.32],[x,1.62,-1.16],b.color);
  }
  if(b.kind==='tent'){
   const roof=new THREE.Mesh(new THREE.ConeGeometry(3.55,1.6,4),mat(b.color));roof.rotation.y=Math.PI/4;roof.scale.z=.78;roof.position.y=3.7;roof.castShadow=true;booth.add(roof);
  }else{
   for(const side of [-1,1]){const roof=box(booth,[5,.15,2.1],[0,3.48,side*.94],b.color);roof.rotation.x=side*.36;}
   box(booth,[5,.24,3.85],[0,3.08,0],b.color);
  }
  const awning=box(booth,[4.9,.12,.9],[0,2.75,1.97],b.color);awning.rotation.x=.14;
  box(booth,[3.9,.5,.14],[0,2.95,1.77],'#efe1c2',.5);
  box(booth,[3.9,.07,.12],[0,2.62,1.9],'#ffe2a4',2.2);
  for(const x of [-1.6,1.6]){const lamp=new THREE.Mesh(new THREE.SphereGeometry(.13,8,6),mat('#ffcc78',true));lamp.position.set(x,2.68,1.98);booth.add(lamp);}
  const outline=new THREE.Mesh(new THREE.RingGeometry(3.1,3.65,40),new THREE.MeshBasicMaterial({color:'#f5b443',side:THREE.DoubleSide,depthWrite:false,transparent:true}));outline.rotation.x=-Math.PI/2;outline.position.y=.025;outline.visible=false;booth.add(outline);outlines.push({id:b.id,booth,outline});
 }
 for(const [x,z] of POPUP_TABLES){const table=shell('picnic-table',x,z);box(table,[2.5,.15,1],[0,.83,0],'#9b7d57');for(const leg of [-.9,.9])box(table,[.16,.76,.8],[leg,.38,0],'#536559');for(const side of [-1,1])box(table,[2.5,.14,.36],[0,.47,side*.82],'#b39a71');}
 const stage=shell('moonlight-stage',POPUP_STAGE.x,POPUP_STAGE.z);box(stage,[10,.65,5.6],[0,.325,0],'#8d795e');box(stage,[9,3.3,.25],[0,2.3,-2.6],'#686977');for(const x of [-4.7,4.7])box(stage,[.2,4,.2],[x,2,2.5],'#6a5d4b');
 for(const x of [-28,28])for(const z of [-15,14]){const post=shell('market-light',x,z);box(post,[.13,4,.13],[0,2,0],'#716151');const bulb=new THREE.Mesh(new THREE.SphereGeometry(.23,8,6),mat('#ffd393',true));bulb.position.y=4;post.add(bulb);}
 // Batch static pieces by material inside each booth; selection rings stay separate.
 for(const {object} of records){
  const batches=new Map();
  for(const child of [...object.children]){
   if(!child.isMesh||!child.visible)continue;child.updateMatrix();
   const list=batches.get(child.material)||[];list.push(child.geometry.clone().applyMatrix4(child.matrix));batches.set(child.material,list);child.geometry.dispose();object.remove(child);
  }
  for(const [material,geometries] of batches){const merged=mergeGeometries(geometries,false);geometries.forEach(g=>g.dispose());const mesh=new THREE.Mesh(merged,material);mesh.castShadow=true;mesh.receiveShadow=true;object.add(mesh);}
 }
 // Each booth owns its glow materials so a click cannot light up its neighbours.
 for(const r of outlines)r.materials=r.booth.children.filter(m=>m.material?.isMeshStandardMaterial).map(mesh=>{
  mesh.material=mesh.material.clone();
  return mesh.material;
 });
 // A shared soft pool and emissive fixtures keep nighttime lighting inexpensive at map scale.
 const pixels=new Uint8Array(32*32*4);
 for(let y=0;y<32;y++)for(let x=0;x<32;x++){const i=(y*32+x)*4,a=Math.max(0,1-Math.hypot((x-15.5)/15.5,(y-15.5)/15.5));pixels.set([255,255,255,Math.round(a*a*150)],i);}
 const poolTexture=new THREE.DataTexture(pixels,32,32);poolTexture.needsUpdate=true;poolTexture.magFilter=THREE.LinearFilter;
 const poolMaterial=new THREE.MeshBasicMaterial({color:'#ffc568',map:poolTexture,transparent:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-1,toneMapped:false});
 const poolGeometry=new THREE.PlaneGeometry(9,8),lightPools=[];
 for(const r of outlines){const pool=new THREE.Mesh(poolGeometry,poolMaterial);pool.name='booth-light-pool';pool.rotation.x=-Math.PI/2;pool.position.set(0,.03,2);pool.visible=false;r.booth.add(pool);lightPools.push(pool);}
 const lighting=new Map();
 for(const {object} of records)for(const mesh of object.children){const material=mesh.material;if(material?.isMeshStandardMaterial&&!lighting.has(material))lighting.set(material,{material,emissive:material.emissive.clone(),intensity:material.emissiveIntensity});}
 const glow=new THREE.Color('#ffd17a'),reducedMotion=globalThis.matchMedia?.('(prefers-reduced-motion: reduce)');
 let selected=null,flashId=null,flashStart=null,night=atlas.mode==='night';
 function paintGlow(strength){
  for(const base of lighting.values()){
   const lit=night&&base.material.userData.nightIntensity>0;
   base.material.emissive.copy(lit?glow:base.emissive);
   base.material.emissiveIntensity=lit?base.material.userData.nightIntensity:base.intensity;
  }
  for(const pool of lightPools)pool.visible=night;
  for(const r of outlines){
   const active=flashStart!==null&&(flashId===null||r.id===flashId),amount=active?strength:0;
   for(const material of r.materials){material.emissive.lerp(glow,amount);material.emissiveIntensity+=amount*1.65;}
   r.outline.visible=r.id===selected||active;
   r.outline.scale.setScalar(1+amount*.3);
   r.outline.material.opacity=r.id===selected?1:.35+amount*.65;
  }
 }
 function update(now=performance.now()){
  const nextNight=atlas.mode==='night';
  if(nextNight!==night){night=nextNight;paintGlow(0);}
  if(flashStart===null)return;
  const elapsed=Math.max(0,now-flashStart);
  if(elapsed>=2400){flashStart=null;paintGlow(0);return;}
  const wave=reducedMotion?.matches?1:(1+Math.cos(elapsed/800*Math.PI*2))/2;
  paintGlow(wave*Math.min(1,(2400-elapsed)/400));
 }
 function flash(id=null,now=performance.now()){
  if(!group.visible||(id!==null&&!outlines.some(r=>r.id===id)))return;
  flashId=id;flashStart=now;update(now);
 }
 function refresh(){for(const r of records)r.object.position.copy(atlas.point(popupBoothCoordinate(site,r.x,r.z),r.object===pad?.001:.003));atlas.renderer.shadowMap.needsUpdate=true;}
 function select(id){selected=id;if(flashStart===null)paintGlow(0);else update();}
 function setVisible(visible){
  if(group.visible===visible)return;group.visible=visible;atlas.renderer.shadowMap.needsUpdate=true;atlas.container.dataset.popupBoothModels=visible?String(POPUP_BOOTHS.length):'0';
  if(visible)flash();else{flashStart=null;paintGlow(0);}
 }
 const raycaster=new THREE.Raycaster();let down=null;
 const canvas=atlas.renderer.domElement;
 canvas.addEventListener('pointerdown',e=>{down={x:e.clientX,y:e.clientY,id:e.pointerId};});
 canvas.addEventListener('pointercancel',()=>{down=null;});
 canvas.addEventListener('pointerup',e=>{
  const start=down;down=null;if(!group.visible||!start||start.id!==e.pointerId||Math.hypot(e.clientX-start.x,e.clientY-start.y)>6||atlas.journey?.active)return;
  const rect=canvas.getBoundingClientRect();raycaster.setFromCamera(new THREE.Vector2((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1),atlas.camera);
  for(const hit of raycaster.intersectObject(group,true)){let object=hit.object;while(object&&object!==group){if(object.userData.boothId){onSelect(object.userData.boothId);return;}object=object.parent;}}
 });
 paintGlow(0);refresh();return {group,refresh,select,setVisible,flash,update};
}
