import * as T from 'three';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';

// Only call for scenery whose mesh transforms will never animate. Keep lights,
// sprites and instanced foliage in place; their transforms/opacity stay live.
export function batchScenery(group,k){
 group.updateWorldMatrix(true,true);
 const inverse=group.matrixWorld.clone().invert(),batches=new Map();
 group.traverse(o=>{
  if(!o.isMesh||o.isInstancedMesh||Array.isArray(o.material)||o.material.transparent)return;
  for(let p=o;p&&p!==group;p=p.parent)if(!p.visible||p.userData.action)return;
  const key=o.material.uuid+Object.keys(o.geometry.attributes).sort().join(',')+o.castShadow+o.receiveShadow;
  const batch=batches.get(key)||{material:o.material,castShadow:o.castShadow,receiveShadow:o.receiveShadow,geometries:[],objects:[]};
  const geometry=o.geometry.index?o.geometry.toNonIndexed():o.geometry.clone();
  geometry.applyMatrix4(inverse.clone().multiply(o.matrixWorld));
  batch.geometries.push(geometry);batch.objects.push(o);batches.set(key,batch);
 });
 for(const {material,castShadow,receiveShadow,geometries,objects} of batches.values()){
  const merged=mergeGeometries(geometries);geometries.forEach(g=>g.dispose());
  if(!merged)continue;
  for(const o of objects)o.removeFromParent();
  const mesh=k.mesh(group,merged,material);mesh.castShadow=castShadow;mesh.receiveShadow=receiveShadow;
 }
}

function paperLanterns(parent,k,positions){
 const bodies=[],ribs=[],caps=[],cords=[];
 for(const [x,y,z,s=1] of positions){
  bodies.push({p:[x,y,z],s:[.28*s,.34*s,.28*s]});
  for(let i=1;i<10;i++){
   const a=i/10*Math.PI,r=Math.sin(a)*.282*s;
   ribs.push({p:[x,y+Math.cos(a)*.34*s,z],s:[r,r,s],r:[Math.PI/2,0,0]});
  }
  for(const side of [-1,1])caps.push({p:[x,y+side*.335*s,z],s:[.083*s,.028*s,.083*s]});
  cords.push({p:[x,y+.59*s,z],s:[.004,.46*s,.004]});
 }
 const paper=k.mat('#ffe7b6',{roughness:.94,emissive:'#ffbb61',emissiveIntensity:1.15});
 k.instances(parent,new T.SphereGeometry(1,28,20),paper,bodies);
 k.instances(parent,new T.TorusGeometry(1,.009,4,32),k.mat('#b39a70',{roughness:.9}),ribs);
 k.instances(parent,new T.CylinderGeometry(1,1,1,16),k.mat('#67583e'),caps);
 k.instances(parent,new T.CylinderGeometry(1,1,1,6),k.mat('#595b4d'),cords);
}

export function dressPopup(parent,k){
 const g=new T.Group();g.name='festival-atmosphere';parent.add(g);
 // Lanterns hang on the existing spans, safely above the pedestrian clearance.
 const lanterns=[];
 for(const z of [8,15])for(let i=0;i<7;i++)lanterns.push([-26+i*3.15,3.5-Math.sin(i/6*Math.PI)*.46,z,i%2?.75:1]);
 for(const z of [-4,4,14])for(let i=0;i<7;i++)lanterns.push([7+i*3.1,3.7-Math.sin(i/6*Math.PI)*.46,z,.78]);
 for(let i=0;i<7;i++)lanterns.push([-27+i*2.75,3.45-Math.sin(i/6*Math.PI)*.4,-4,.83]);
 paperLanterns(g,k,lanterns);
 // A lit river edge links the booths to the bridge. Planting stays outside the
 // walkable boundary, so the existing riverside route remains fully open.
 const leaves=[],stems=[],flowers=[];
 let seed=4821;const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
 for(const x of [-28,-21,-14,-7,0,7,14,21,28]){
  k.box(g,[4.6,.32,.78],[x,.16,-23.75],k.woodDark);
  k.box(g,[4.45,.02,.66],[x,.33,-23.75],'#3e4230');
  for(let n=0;n<28;n++){
   const px=x-2.08+random()*4.16,pz=-23.75+(random()-.5)*.58,h=.25+random()*.33;
   stems.push({p:[px,.33+h/2,pz],s:[.004,h,.004]});
   for(let j=0;j<7;j++)leaves.push({p:[px,.34,pz],s:[.75+random()*.7,.5+random()*.7,1],r:[random()*.12,random()*Math.PI*2,0]});
   if(n%3===0)for(let j=0;j<5;j++)flowers.push({p:[px+Math.sin(j*2.4)*.023,.33+h+Math.cos(j)*.012,pz+Math.cos(j*2.4)*.023],s:[.022,.017,.023],color:n%2?'#c3b391':'#9baca6'});
  }
  k.box(g,[4.3,.022,.024],[x,.27,-23.34],k.mat('#ebc897',{emissive:'#ffc379',emissiveIntensity:1.4}));
 }
 k.instances(g,new T.CylinderGeometry(1,1,1,6),k.mat('#687553'),stems);
 const blade=new T.PlaneGeometry(1,1,1,8),bp=blade.attributes.position;
 for(let i=0;i<bp.count;i++){const t=bp.getY(i)+.5;bp.setXYZ(i,bp.getX(i)*.037*(1-t)+t*t*.21,t*.58,Math.sin(t*Math.PI)*.045);}blade.computeVertexNormals();
 k.instances(g,blade,k.mat('#657854',{roughness:.89,side:T.DoubleSide}),leaves);
 k.instances(g,new T.SphereGeometry(1,8,6),k.mat('#ffffff',{roughness:.94}),flowers);
 for(const [x,z] of [[-30,5],[-30,-7],[30,5],[30,-7]]){
  const l=new T.SpotLight('#dfc69e',65,17,.55,.85,1.5);l.position.set(x,.2,z);l.target.position.set(Math.sign(x)*33,4,z-2);g.add(l,l.target);
 }
 // Large soft sources make faces, fabrics and the food legible, while retaining
 // the warm islands / cool sky contrast rather than exposing the whole night.
 for(const [x,z,w,color] of [[-17,8,19,'#ffdbac'],[-21,-5,14,'#ffe5c7'],[18,-3,16,'#ffe0b2'],[18,9,12,'#dfdceb']]){
  const light=new T.RectAreaLight(color,2.8,w,2.2);light.position.set(x,3.9,z);light.lookAt(x,.2,z+2);g.add(light);
 }
 const moon=k.sphere(g,.6,[16,22,-86],k.mat('#fff1d4',{emissive:'#f3dec0',emissiveIntensity:.8}));moon.castShadow=false;
 batchScenery(g,k);
 // A blue-hour sky with a cool horizon keeps the river readable. The HDR still
 // supplies reflections; this dome only replaces its over-bright brown stars.
 const skyMaterial=k.mat('#ffffff',{side:T.BackSide,depthWrite:false,fog:false});
 skyMaterial.onBeforeCompile=shader=>{
  shader.vertexShader='varying vec3 vSkyDirection;\n'+shader.vertexShader;
  shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\n vSkyDirection=normalize(position);');
  shader.fragmentShader='varying vec3 vSkyDirection;\n'+shader.fragmentShader;
  shader.fragmentShader=shader.fragmentShader.replace('#include <opaque_fragment>','float skyHeight=smoothstep(-.08,.7,vSkyDirection.y);\n outgoingLight=mix(vec3(.023,.044,.064),vec3(.004,.010,.023),skyHeight);\n #include <opaque_fragment>');
 };
 skyMaterial.customProgramCacheKey=()=> 'festival-blue-hour';
 const sky=k.mesh(g,new T.SphereGeometry(185,40,24),skyMaterial);sky.name='festival-sky';sky.castShadow=false;sky.receiveShadow=false;
 return g;
}

export function dressStage(stage,k){
 const g=new T.Group();g.name='moon-stage-scenery';stage.add(g);
 const fabric=k.surface('fabric_pattern_05',[2,2],'#626e75');fabric.map=null;fabric.side=T.DoubleSide;
 // Deep folds catch grazing light around the central moon, like a small outdoor
 // concert set. All of this stays behind the performers and their interaction.
 for(const side of [-1,1]){
  const geo=new T.PlaneGeometry(2.5,4,64,1),p=geo.attributes.position;
  for(let i=0;i<p.count;i++)p.setZ(i,.11*Math.cos((p.getX(i)+1.25)*Math.PI*8));geo.computeVertexNormals();
  k.mesh(g,geo,fabric,[side*3.72,2.35,-2.46]);
 }
 const moon=k.mesh(g,new T.CircleGeometry(1.15,72),k.mat('#e6d5af',{emissive:'#e6bd73',emissiveIntensity:.48}),[0,2.23,-2.49]);moon.castShadow=false;
 for(let i=0;i<4;i++){
  const points=Array.from({length:33},(_,n)=>{const x=-4.35+n*.272;return [x,.57+i*.16+Math.sin(n*.18+i*.6)*.14,-2.29];});
  k.tube(g,points,.016,k.mat('#adac92',{emissive:'#b99960',emissiveIntensity:.15}));
 }
 // Footlights and a warm edge to the platform ground the performers.
 for(const x of [-3.5,-1.8,1.8,3.5]){
  k.box(g,[.28,.13,.18],[x,.42,2.55],'#303b39');
  k.box(g,[.23,.026,.12],[x,.49,2.55],k.mat('#ffe0ac',{emissive:'#ffc071',emissiveIntensity:1.8}));
 }
 k.box(g,[9.8,.025,.035],[0,.27,2.82],k.mat('#deb680',{emissive:'#ffcb8c',emissiveIntensity:1.1}));
 batchScenery(g,k);
}

export function dressFestivalPerformer(person,k){
 const cloth=k.surface('fabric_pattern_05',[2,2],'#ddd6bc');cloth.map=null;cloth.roughness=.95;
 const profile=[[.27,.44],[.28,.48],[.255,.63],[.205,.87],[.17,1.12]].map(p=>new T.Vector2(...p));
 const geo=new T.LatheGeometry(profile,64),positions=geo.attributes.position;
 for(let i=0;i<positions.count;i++){
  const x=positions.getX(i),z=positions.getZ(i),y=positions.getY(i),fold=1+.035*Math.sin(Math.atan2(x,z)*16)*(1.15-y);
  positions.setXYZ(i,x*fold,y,z*fold*.73);
 }geo.computeVertexNormals();k.mesh(person,geo,cloth);
 const sash=k.mat('#a55443',{roughness:.9});
 const belt=k.mesh(person,new T.CylinderGeometry(.17,.18,.085,48),sash,[0,1.085,0]);belt.scale.z=.66;
 for(const side of [-1,1]){
  const ribbon=k.mesh(person,new T.PlaneGeometry(.055,.34,4,10),sash,[side*.035,.89,.151]);ribbon.rotation.z=side*.12;
  const collar=k.box(person,[.04,.24,.023],[side*.06,1.29,.13],cloth);collar.rotation.z=side*.42;
  const arm=person.userData.arms[side<0?0:1];
  const sleeve=k.mesh(arm,new T.CylinderGeometry(.075,.125,.41,32),cloth,[side*.026,-.2,.025]);sleeve.rotation.z=side*.1;
 }
}

export function festivalDrum(parent,k,x){
 const g=new T.Group();g.position.set(x,.97,.3);parent.add(g);
 const shell=k.cyl(g,.33,.33,.32,[0,0,0],k.wood);shell.rotation.x=Math.PI/2;
 for(const side of [-1,1]){
  const skin=k.cyl(g,.315,.315,.015,[0,0,side*.17],k.mat('#d6c7a2',{roughness:.91}));skin.rotation.x=Math.PI/2;
  k.mesh(g,new T.TorusGeometry(.32,.018,8,64),k.woodDark,[0,0,side*.18]);
 }
 for(let n=0;n<16;n++){
  const a=n/16*Math.PI*2,b=a+.12;
  k.tube(g,[[Math.sin(a)*.33,Math.cos(a)*.33,-.17],[Math.sin(b)*.336,Math.cos(b)*.336,.17]],.007,'#c5b58f');
 }
 k.tube(g,[[-.23,.22,0],[-.16,.51,-.12],[.13,.51,-.12],[.23,.22,0]],.02,'#836952');
 batchScenery(g,k);
}

export function dressMarketShop(shop,k,{index,side,accent,front,cx,cz}){
 const g=new T.Group();g.name='market-shop-life';shop.add(g);
 // Photo menu belongs on the restaurant wall, never on top of the 3D view.
 if(index<4){
  k.box(g,[.85,1.18,.035],[1.29,1.55,-2.88],k.woodDark);
  k.photo(g,'meal-photo',[1.29,1.68,-2.854],.78,.73);
  k.sign(g,'오늘의 안동 한 상',[1.29,1.17,-2.85],.73,'#eadbc1','#463f32',.15);
  if(index<3){
   k.box(g,[.75,.8,.025],[-1.04,1.56,front+.055],'#d8c8a6');
   k.photo(g,'meal-photo',[-1.04,1.66,front+.071],.69,.53);
   k.sign(g,'갓 만든 안동찜닭',[-1.04,1.26,front+.074],.68,accent,'#e8d8b4',.13);
  }
  const signLight=new T.RectAreaLight('#ffe2b9',5,2.9,.15);signLight.position.set(0,3.23,2.45);signLight.lookAt(0,2.75,1.95);g.add(signLight);
  const interior=new T.RectAreaLight('#ffdcac',5,2.5,1);interior.position.set(0,2.42,-.25);interior.lookAt(0,.35,-.3);g.add(interior);
  // A meal waiting to be served, with real-sized plates and utensils.
  k.bowl(g,[.1,.8,.25],.2,'#e0d7be','#6b3c20');
  const pieces=[];for(let n=0;n<18;n++){const a=n*2.4,r=.025+Math.sqrt(n/18)*.13;pieces.push({p:[.1+Math.sin(a)*r,.9+(n%3)*.008,.25+Math.cos(a)*r],s:[.027,.016,.024],r:[0,a,0],color:n%4===0?'#ccac69':n%5===0?'#677b3d':'#a57843'});}
  k.instances(g,new T.SphereGeometry(1,12,8),k.mat('#ffffff',{roughness:.42}),pieces);
  for(const x of [-.28,.45]){k.bowl(g,[x,.8,.25],.075,'#d2d8cc','#e1dbc3');for(const dz of [-.014,.014])k.cyl(g,.003,.003,.23,[x,.8,.51+dz],k.mat('#9fa49a',{metalness:.85,roughness:.32}),8).rotation.z=Math.PI/2;}
  // Ingredients and small takeaway packets differ by storefront.
  for(let n=0;n<4;n++){
   const x=cx-.66+n*.18;
   if((index+side)%2===0){k.sphere(g,[.075,.062,.07],[x,.99,cz-.19],n%2?'#c3a161':'#7b925b');}
   else{k.box(g,[.13,.2,.09],[x,1.02,cz-.18],'#cbb99b');k.sign(g,'안동',[x,1.03,cz-.13],.105,accent,'#cbb99b',.06);}
  }
  const curtain=k.surface('fabric_pattern_05',[2,1],index%2?'#c7b38c':'#a8b8a4');curtain.map=null;curtain.side=T.DoubleSide;
  for(let n=0;n<3;n++){
   const geo=new T.PlaneGeometry(.47,.55,12,8),p=geo.attributes.position;
   for(let j=0;j<p.count;j++)p.setZ(j,.025*Math.sin(p.getX(j)*24)+.018*Math.cos(p.getY(j)*13+n));geo.computeVertexNormals();
   k.mesh(g,geo,curtain,[.38+n*.5,1.96,front-.13]);
  }
 }
 batchScenery(g,k);
}
