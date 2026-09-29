import * as T from 'three';
import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';
import {transitPerson,animateTransitPerson} from './transit-people.js';

export const BUS_SEAT = Object.freeze([.62,1.69,1.90]);
export const BUS_AISLE_SEAT = Object.freeze([.32,1.69,1.90]);
export const BUS_FLOOR = .36;
export const BUS_ALIGHT_PATH = Object.freeze([[0,2.03,1.9],[0,2.03,-3.9],[.83,2.03,-3.9]].map(Object.freeze));

// A self-contained metre-scale vehicle, shared by the map and relay scenes.
// No dashboard overlay: the camera lives inside the same shell as its occupants.
export function createTransitKit({textures=true}={}){
 const geometries=new Set(),materials=new Map(),ownedTextures=new Set();
 const mat=(color,options={})=>{const key=color+JSON.stringify(options);if(!materials.has(key))materials.set(key,new T.MeshStandardMaterial({color,roughness:.78,...options}));return materials.get(key);};
 function mesh(parent,geometry,material,position=[0,0,0]){geometries.add(geometry);const m=new T.Mesh(geometry,typeof material==='string'?mat(material):material);m.position.fromArray(position);m.castShadow=m.receiveShadow=true;parent.add(m);return m;}
 const k={mat,mesh,box:(g,s,p,m)=>mesh(g,new T.BoxGeometry(...s),m,p),roundedBox:(g,s,p,m,r=.025)=>mesh(g,new RoundedBoxGeometry(...s,2,r),m,p),cyl:(g,a,b,h,p,m,n=20)=>mesh(g,new T.CylinderGeometry(a,b,h,n),m,p),sphere:(g,s,p,m)=>{const o=mesh(g,new T.SphereGeometry(1,20,14),m,p);o.scale.set(...(Array.isArray(s)?s:[s,s,s]));return o;},tube:(g,points,r,m)=>mesh(g,new T.TubeGeometry(new T.CatmullRomCurve3(points.map(p=>new T.Vector3(...p))),Math.max(8,points.length*5),r,8),m)};
 k.label=(g,text,p,w,h,bg='#171d22',color='#ffe8aa')=>{
  let m=mat(bg,{emissive:bg,emissiveIntensity:.4});
  if(textures&&typeof document!=='undefined'){
   const canvas=document.createElement('canvas');canvas.width=1024;canvas.height=Math.round(1024*h/w);const c=canvas.getContext('2d');
   const draw=value=>{c.fillStyle=bg;c.fillRect(0,0,canvas.width,canvas.height);c.textAlign='center';c.textBaseline='middle';c.fillStyle=color;c.font=`500 ${Math.min(canvas.height*.62,920/(value.length*.62))}px sans-serif`;c.fillText(value,512,canvas.height/2);};draw(text);
   const tx=new T.CanvasTexture(canvas);tx.colorSpace=T.SRGBColorSpace;ownedTextures.add(tx);m=new T.MeshBasicMaterial({map:tx,toneMapped:false});materials.set('label'+materials.size,m);
   m.userData.setText=value=>{draw(value);tx.needsUpdate=true;};
  }
  return mesh(g,new T.PlaneGeometry(w,h),m,p);
 };
 k.batch=group=>{
  const buckets=new Map();group.updateMatrix();
  for(const child of [...group.children])if(child.isMesh&&!child.isInstancedMesh&&!child.userData.keep){child.updateMatrix();let copy=child.geometry.clone().applyMatrix4(child.matrix);if(copy.index){const plain=copy.toNonIndexed();copy.dispose();copy=plain;}const bucket=buckets.get(child.material)||[];bucket.push(copy);buckets.set(child.material,bucket);group.remove(child);}
  for(const [m,parts] of buckets){const merged=mergeGeometries(parts);if(merged){const object=mesh(group,merged,m);if(m.transparent)object.castShadow=false;}for(const part of parts)part.dispose();}
 };
 k.dispose=()=>{for(const geo of geometries)geo.dispose();for(const m of materials.values())m.dispose();for(const tx of ownedTextures)tx.dispose();};
 return k;
}

export function createBusCabin({textures=true,destination='월영교',occupants=true}={}){
 const k=createTransitKit({textures}),group=new T.Group(),shell=new T.Group(),people=[],straps=[],wheels=[];group.name='passenger-bus';group.add(shell);
 const metal=k.mat('#aeb7b7',{metalness:.78,roughness:.3}),cream=k.mat('#d9d9d0',{roughness:.64}),black=k.mat('#252c30',{roughness:.7}),upholstery=k.mat('#526f81',{roughness:.93}),yellow=k.mat('#d7aa49',{metalness:.22,roughness:.42});
 const glass=k.mat('#91aaa8',{transparent:true,opacity:.075,metalness:.15,roughness:.12,depthWrite:false,side:T.DoubleSide});
 k.roundedBox(shell,[2.48,.18,10.2],[0,.27,0],'#3c4246',.08);
 k.box(shell,[2.36,.035,10.04],[0,BUS_FLOOR-.018,0],'#555957');
 // Rubber aisle, aluminum edges, and wheel arches establish scale at the feet.
 k.box(shell,[.78,.008,9.2],[0,BUS_FLOOR+.005,.25],'#3c4446');
 for(const x of [-.4,.4])k.box(shell,[.016,.01,9.2],[x,BUS_FLOOR+.01,.25],metal);
 for(let z=-4.8;z<5;z+=.055)k.box(shell,[.73,.001,.007],[0,BUS_FLOOR+.011,z],'#485152');
 k.roundedBox(shell,[2.52,.16,10.25],[0,2.65,0],cream,.065);
 for(const side of [-1,1]){
  // Leave a real doorway in the shell; opening the leaf must also open the wall.
  const spans=side===1?[[-5.05,-4.55],[-3.23,5.05]]:[[-5.05,5.05]];
  for(const [start,end] of spans){const length=end-start,z=(start+end)/2;
   k.roundedBox(shell,[.105,.86,length],[side*1.22,.79,z],'#71887d',.035);
   k.box(shell,[.035,.73,length],[side*1.15,.84,z],'#b5b9b2');
   k.box(shell,[.09,.075,length],[side*1.18,1.24,z],black);
  }
  for(let z=-4.85;z<4;z+=1.62){k.box(shell,[.082,1.28,.07],[side*1.2,1.94,z],cream);if(side===1&&z< -3.23&&z+1.55> -4.55)continue;const window=k.box(shell,[.014,1.18,1.49],[side*1.21,1.92,z+.8],glass);window.castShadow=false;}
  k.box(shell,[.16,.11,9.7],[side*1.12,2.51,.04],cream);
  k.box(shell,[.052,.022,8.2],[side*.84,2.548,.45],k.mat('#fff5d6',{emissive:'#fff0c5',emissiveIntensity:1.8}));
  for(let z=-3.2;z<4.9;z+=1.02){
   // Seats face the front (-Z); their backs are behind the knees and heads.
   const x=side*.79,seat=new T.Group();seat.position.set(x,BUS_FLOOR,z);shell.add(seat);
   k.cyl(seat,.045,.045,.43,[0,.215,0],metal);k.roundedBox(seat,[.6,.1,.54],[0,.47,0],upholstery,.055);
   const back=k.roundedBox(seat,[.61,.65,.105],[0,.82,.255],upholstery,.055);back.rotation.x=-.07;
   k.roundedBox(seat,[.54,.15,.075],[0,1.13,.27],upholstery,.04);
   k.tube(seat,[[-.23,1.1,.28],[-.25,1.22,.28],[.25,1.22,.28],[.23,1.1,.28]],.016,metal);
   k.box(seat,[.37,.19,.024],[0,.79,.32],'#344955');
   for(let n=-2;n<=2;n++)k.box(seat,[.006,.47,.008],[n*.086,.82,.191],'#748995');
   k.batch(seat);
  }
  k.tube(shell,[[side*.42,.4,-2.55],[side*.42,2.36,-2.55],[side*.42,2.4,4.75]],.025,yellow);
  for(let z=-2;z<=4;z+=1.05){const strap=new T.Group();strap.position.set(side*.42,2.39,z);group.add(strap);k.box(strap,[.025,.22,.02],[0,-.11,0],'#414a4e');const ring=k.mesh(strap,new T.TorusGeometry(.074,.012,8,24),black,[0,-.265,0]);ring.scale.y=1.14;straps.push(strap);k.batch(strap);}
 }
 // Front glazing and a proper driver's station, all visible from the passenger seat.
 k.box(shell,[2.42,.65,.1],[0,.78,-5.02],'#6c857d');k.box(shell,[2.43,.25,.13],[0,2.46,-5.02],cream);
 const exteriorSign=k.label(shell,'이어드림 · 월영교',[0,2.46,-5.095],1.85,.16);exteriorSign.rotation.y=Math.PI;
 for(const x of [-.94,.94]){k.roundedBox(shell,[.27,.16,.035],[x,.79,-5.08],k.mat('#f4e9c6',{emissive:'#fff1c6',emissiveIntensity:.55}),.03);k.box(shell,[.16,.27,.02],[x,.8,5.07],k.mat('#883f34',{emissive:'#883f34',emissiveIntensity:.35}));}
 const windshield=k.box(shell,[2.29,1.3,.012],[0,1.73,-5.045],glass);windshield.castShadow=false;
 for(const x of [-1.18,1.18])k.box(shell,[.11,1.7,.15],[x,1.75,-4.97],cream);
 for(const x of [-.7,.25])k.tube(shell,[[x,.99,-4.98],[x+.22,1.26,-4.98],[x+.25,1.45,-4.98]],.011,black);
 k.roundedBox(shell,[1.4,.27,.64],[-.47,1.03,-4.64],black,.055);
 k.roundedBox(shell,[.67,.1,.45],[-.64,.81,-4.03],upholstery,.05);k.roundedBox(shell,[.63,.65,.13],[-.64,1.12,-3.8],upholstery,.05);
 const steering=k.mesh(shell,new T.TorusGeometry(.215,.025,12,32),black,[-.65,1.19,-4.48]);steering.rotation.x=-.55;
 k.cyl(shell,.035,.045,.44,[-.65,.96,-4.52],black);k.roundedBox(shell,[.35,.17,.07],[-.66,1.17,-4.77],'#121f24',.025);
 k.label(shell,'28  ·  km/h',[-.66,1.17,-4.73],.28,.07,'#121f24','#b2dcdf');
 k.roundedBox(shell,[.29,.4,.2],[.64,1.02,-4.05],black,.035);k.label(shell,'교통카드',[.64,1.1,-3.945],.23,.1,'#24393a','#d7e7d6');
 const destinationSign=k.label(shell,`이번 정류장  ${destination}`,[0,2.36,-4.72],1.7,.21);
 k.label(shell,'안전하게 앉아 주세요',[.55,2.14,-4.73],.71,.1,'#d4d7cf','#475850');
 // Rear wall closes the cabin. Side doors split open at stops.
 k.box(shell,[2.4,1.3,.12],[0,1.93,5],cream);k.box(shell,[1.98,.87,.015],[0,1.91,4.93],glass);
 const door=new T.Group();door.position.set(1.23,.38,-3.89);group.add(door);
 for(const z of [-.32,.32]){k.box(door,[.055,2.08,.62],[0,1.04,z],black);k.box(door,[.06,1.56,.49],[0,1.25,z],glass);}
 k.box(shell,[.7,.12,.99],[.85,.26,-3.89],black);for(const z of [-4.37,-3.42])k.box(shell,[.7,.025,.035],[.85,.33,z],yellow);
 const stopMaterial=k.mat('#993d2c',{emissive:'#b53019',emissiveIntensity:.12});
 k.tube(shell,[[.43,BUS_FLOOR,.63],[.43,2.38,.63]],.025,yellow);
 const stop=k.roundedBox(group,[.08,.16,.09],[.48,1.22,.63],stopMaterial,.025);stop.userData.keep=true;stop.userData.action='transit:stop';stop.userData.name='하차 벨 누르기';
 k.label(shell,'STOP',[.48,1.225,.682],.065,.026,'#993d2c','#ffe8d3');
 const stopDisplay=k.label(group,'하차합니다',[0,2.12,-4.7],.63,.15,'#632b23','#ffbd6c');stopDisplay.visible=false;
 for(const side of [-1,1])for(const z of [-3.25,3.3]){const wheel=k.cyl(group,.44,.44,.18,[side*1.18,.44,z],black,32);wheel.rotation.z=Math.PI/2;wheels.push(wheel);const hub=k.cyl(shell,.22,.22,.19,[side*1.2,.44,z],metal,24);hub.rotation.z=Math.PI/2;}
 if(occupants){
  const positions=[[-.64,BUS_FLOOR,-4.04,true],[-.79,BUS_FLOOR,-3.2], [.79,BUS_FLOOR,-2.18],[-.79,BUS_FLOOR,-1.16],[-.79,BUS_FLOOR,.88],[.79,BUS_FLOOR,2.92],[-.79,BUS_FLOOR,3.94]];
  positions.forEach(([x,y,z,driver],i)=>{const person=transitPerson(k,{seated:true,driver:!!driver,coat:['#728892','#9d8066','#778875','#677384','#b59579','#697a83','#a3a297'][i],variant:i,hair:i===4?'#777571':'#302c2a'});person.position.set(x,y,z);person.rotation.y=Math.PI;people.push(person);group.add(person);});
 }
 // A soft interior fill, avoiding one shadow-casting light per fitting.
 const light=new T.PointLight('#fff3dc',9,10,2);light.position.set(0,2.42,-.8);group.add(light);
 k.batch(shell);k.batch(door);
 let stopped=false;
 return {group,k,people,straps,stop,stopDisplay,door,light,eye:[...BUS_SEAT],
  get stopRequested(){return stopped;},
  get destination(){return destination;},
  setDestination(value){if(!value||value===destination)return;destination=value;destinationSign.material.userData.setText?.(`이번 정류장  ${value}`);},
  requestStop(){const changed=!stopped;stopped=true;stopDisplay.visible=true;stopMaterial.emissiveIntensity=1.5;return changed;},
  reset(){stopped=false;stopDisplay.visible=false;stopMaterial.emissiveIntensity=.12;door.position.z=-3.89;},
  update(time,{moving=0,doorOpen=0,reduced=false}={}){
   for(const p of people)animateTransitPerson(p,time,moving,reduced);
   for(let i=0;i<straps.length;i++){straps[i].rotation.x=reduced?0:Math.sin(time*1.7+i*.13)*.035*moving;straps[i].rotation.z=reduced?0:Math.sin(time*.95)*.026*moving;}
   door.position.z=-3.89+doorOpen*1.35;
   for(const wheel of wheels)wheel.rotation.x=reduced?0:-time*moving*4;
  },dispose(){k.dispose();}};
}
