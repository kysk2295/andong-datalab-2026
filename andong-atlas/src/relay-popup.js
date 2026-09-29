import {addSceneLife} from './relay-life.js';
import * as T from 'three';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';
import {createRiverWater} from './relay-water.js';
import {riverLandscape,pavilion} from './relay-architecture.js';
import {POPUP_BOOTHS,POPUP_STAGE,POPUP_TABLES,POPUP_BENCHES,POPUP_TUHO,popupLayout} from './relay-popup-layout.js';
import {batchScenery,dressPopup,dressStage,dressFestivalPerformer,festivalDrum} from './relay-atmosphere.js';

// Zoning follows the supplied night-festival references. This is a proposed venue,
// not a claim that these merchants, prices or facilities currently exist on site.
export function popupStall(parent,k,index,{distant=false,placement}={}){
 const b=POPUP_BOOTHS[index],g=new T.Group();parent.add(g);g.position.set(...(placement||[b.x,0,b.z]));
 const cloth=k.surface('fabric_pattern_05',[3,2],b.color),iron=k.mat('#414740',{metalness:.65,roughness:.43});cloth.side=T.DoubleSide;
 const w=4.5,d=3.3;
 for(const x of [-2.1,2.1])for(const z of [-1.5,1.5]){k.cyl(g,.036,.036,2.85,[x,1.425,z],iron,12);k.box(g,[.19,.04,.19],[x,.02,z],iron);}
 if(b.kind==='kitchen'){
  k.box(g,[w,2.45,.09],[0,1.25,-1.5],cloth);
  for(const x of [-2.2,2.2])k.box(g,[.07,2.45,d],[x,1.25,0],cloth);
  k.box(g,[4.85,.12,3.65],[0,2.86,0],iron);
  const awning=k.box(g,[4.95,.045,1.5],[0,2.6,1.96],cloth);awning.rotation.x=.17;
  k.sign(g,'LOCAL KITCHEN',[0,2.56,1.53],2.8,'#eee2c5',b.color,.26);
  for(const z of [-1.1,-.6])k.box(g,[4.3,.012,.016],[0,2.1,z],iron);
  // Stainless worktop, extractor, oven and stocked shelves.
  const steel=k.mat('#a5aaa2',{metalness:.78,roughness:.29});
  k.box(g,[1.7,.7,.7],[-.7,1.95,-.98],steel);k.box(g,[.35,.85,.35],[-.7,2.6,-1],steel);
  k.box(g,[1.4,.85,.6],[1.2,.43,-1],steel);
  for(let n=0;n<4;n++){k.box(g,[.8,.03,.28],[-1.35,.6+n*.37,-1.34],k.wood);for(let j=0;j<3;j++)k.cyl(g,.07,.07,.18,[-1.6+j*.24,.71+n*.37,-1.31],n%2?'#97976a':'#b2a99b');}
 }else if(b.kind==='market'){
  // A timber pavilion interrupts the tent rhythm, as in courtyard pop-up markets.
  for(const side of [-1,1]){const roof=k.box(g,[2.85,.075,3.9],[side*1.19,3.17,0],k.woodDark);roof.rotation.z=side*-.36;}
  k.tube(g,[[-2.26,2.8,1.72],[0,3.64,1.72],[2.26,2.8,1.72]],.055,k.wood);
  k.box(g,[4.4,2.55,.08],[0,1.27,-1.5],k.wood);
  const boards=[];for(let x=-2.1;x<=2.1;x+=.16)boards.push({p:[x,1.4,-1.44],s:[.06,2.3,.04]});k.instances(g,new T.BoxGeometry(1,1,1),k.woodDark,boards);
  for(const side of [-1,1]){k.box(g,[.07,1.2,3],[side*2.12,.6,0],k.wood);k.box(g,[.07,.07,3],[side*2.12,2.7,0],k.wood);}
 }else{
  // Four tensioned roof faces, with a curved fabric edge and raised central peak.
  const vertices=[];const corners=[[-2.45,2.77,-1.9],[2.45,2.77,-1.9],[2.45,2.77,1.9],[-2.45,2.77,1.9]];
  for(let n=0;n<4;n++){const a=corners[n],b=corners[(n+1)%4],m=[(a[0]+b[0])/2,2.7,(a[2]+b[2])/2];vertices.push(...a,...m,0,4,0,...m,...b,0,4,0);}
  const geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(vertices,3));geo.computeVertexNormals();k.mesh(g,geo,cloth);
  for(let n=0;n<4;n++)k.tube(g,[corners[n],[0,4.015,0],corners[(n+1)%4]],.014,iron);
  k.box(g,[4.9,.3,.025],[0,2.64,1.9],cloth);
  k.box(g,[4.4,2.2,.025],[0,1.2,-1.49],cloth);
  for(const x of [-2.11,2.11]){const curtain=k.box(g,[.3,2.1,3],[x,1.12,0],cloth);curtain.scale.x=.1;}
 }
 k.table(g,[0,0,1.15],4.3,.72,.94);
 k.box(g,[4.27,.8,.035],[0,.51,1.53],k.wood);
 const slats=[];for(let x=-2.1;x<2.1;x+=.14)slats.push({p:[x,.53,1.557],s:[.065,.78,.025]});k.instances(g,new T.BoxGeometry(1,1,1),k.woodDark,slats);
 k.sign(g,b.name,[0,2.22,1.57],3.35,'#f2e7cc',b.color,.47);
 k.sign(g,String(index+1).padStart(2,'0'),[-1.88,1.66,1.58],.32,'#e8d8b6','#3e443e',.26);
 for(const x of [-1.65,1.65]){k.lamp(g,[x,2.04,1.5],.38,'#ffdd9f');k.tube(g,[[x,2.5,1.45],[x,2.3,1.5]],.01,iron);}
 if(!distant){
  for(const side of [-1,1]){const crate=new T.Group();g.add(crate);crate.position.set(side*1.75,.1,-.6);for(let n=0;n<3;n++){k.box(crate,[.64,.09,.5],[0,.04+n*.13,0],k.wood);for(const x of [-.27,.27])k.box(crate,[.05,.42,.5],[x,.2,0],k.woodDark);}}
  const light=new T.RectAreaLight('#ffe5bc',5,3.5,1);light.position.set(0,2.53,1.5);light.lookAt(0,.3,2.6);g.add(light);}
 batchScenery(g,k);
 return g;
}
export function addDistantPopup(parent,k){
 const bank=new T.Group();parent.add(bank);bank.position.set(24,-.22,-17);bank.rotation.y=-.3;
 k.box(bank,[34,.45,19],[0,-.2,0],k.stone);
 for(let i=0;i<5;i++)popupStall(bank,k,i,{distant:true,placement:[-12+i*6,0,-3]});
 stringLights(bank,k,[-15,4,2],[15,4,2]);return bank;
}
function stringLights(g,k,a,b){
 const mid=[(a[0]+b[0])/2,a[1]-.65,(a[2]+b[2])/2];k.tube(g,[a,mid,b],.016,'#34392f');
 const lights=[];for(let i=0;i<=24;i++){const t=i/24;lights.push({p:[T.MathUtils.lerp(a[0],b[0],t),a[1]-Math.sin(t*Math.PI)*.65-.1,T.MathUtils.lerp(a[2],b[2],t)],s:[.045,.063,.045]});}
 k.instances(g,new T.SphereGeometry(1,12,8),k.mat('#ffe6b1',{emissive:'#ffd08b',emissiveIntensity:3.2}),lights);
 for(const p of [a,b])k.cyl(g,.045,.06,p[1],[p[0],p[1]/2,p[2]],'#454e43',12);
}
function bench(g,k,x,z,rotation=0){const a=new T.Group();g.add(a);a.position.set(x,0,z);a.rotation.y=rotation;
 for(const x of [-1,1])k.box(a,[.08,.43,.48],[x,.215,0],'#343d37');
 for(const z of [-.19,-.065,.065,.19])k.box(a,[2.5,.07,.105],[0,.47,z],k.wood);
 for(const y of [.75,.91])k.box(a,[2.5,.12,.05],[0,y,-.26],k.wood);
}
// Static spectators are batched by material so a larger festival does not multiply
// the hundreds of draw calls used by every articulated close-up visitor.
function spectators(g,k,positions){
 const prototype=new T.Group(),person=k.person(prototype,[0,0,0],{coat:'#9b9382'});prototype.updateMatrixWorld(true);const groups=new Map();
 person.traverse(o=>{if(!o.isMesh||Array.isArray(o.material))return;const key=o.material.uuid+Object.keys(o.geometry.attributes).sort().join(',');const entry=groups.get(key)||{material:o.material,geos:[]};const geometry=o.geometry.index?o.geometry.toNonIndexed():o.geometry.clone();entry.geos.push(geometry.applyMatrix4(o.matrixWorld));groups.set(key,entry);});
 const palette=['#b4997a','#829a92','#87929f','#b09288','#bab49b','#707c6a'];
 for(const {material:mat,geos} of groups.values()){const merged=mergeGeometries(geos);geos.forEach(x=>x.dispose());const clothing=mat===person.userData.torso.material;if(merged)k.instances(g,merged,clothing?k.mat('#ffffff',{roughness:.95}):mat,positions.map(([x,z,rotation=0,s=1],i)=>({p:[x,0,z],r:[0,rotation,0],s:[s*(.96+i%3*.04),s*(.94+i%4*.025),s],...(clothing?{color:palette[i%palette.length]}:{})})));}
}
function festivalBridge(g,k,refs){
 const landscape=new T.Group();landscape.scale.x=1.9;g.add(landscape);riverLandscape(landscape,k);refs.water=createRiverWater(120,52,[0,-.18,-50]);g.add(refs.water);
 const bridge=new T.Group();bridge.position.set(0,.25,-37);g.add(bridge);k.box(bridge,[69,.2,3.8],[0,0,0],k.woodDark);
 const planks=[];for(let x=-34.5;x<34.5;x+=.24)planks.push({p:[x,.13,0],s:[.232,.055,3.8]});k.instances(bridge,new T.BoxGeometry(1,1,1),k.wood,planks);
 const glow=k.mat('#e4b974',{emissive:'#f5bd76',emissiveIntensity:1.7});
 for(const z of [-1.85,1.85]){
  for(let x=-34;x<35;x+=2){k.box(bridge,[.14,1.3,.14],[x,.78,z],k.woodDark);k.sphere(bridge,.06,[x,1.46,z],glow);}
  for(const y of [.52,1.2])k.box(bridge,[69,.075,.075],[0,y,z],k.woodDark);
  k.box(bridge,[69,.025,.022],[0,1.03,z],glow);
 }
 pavilion(bridge,[7,.16,0],k).rotation.y=Math.PI/2;
 const light=new T.PointLight('#ffd6a0',55,19,2);light.position.set(7,3,0);bridge.add(light);
 const boats=[];for(let i=0;i<3;i++){
  const boat=new T.Group();boat.position.set(-23+i*21,0,-49-i%2*8);g.add(boat);
  const crescent=[];for(let t=0;t<=28;t++){const a=t/28*Math.PI;crescent.push([Math.cos(a)*1.4,Math.sin(a)*.9+.13,0]);}k.tube(boat,crescent,.11,k.mat('#d7dcb3',{emissive:i%2?'#c1bb70':'#91b5cb',emissiveIntensity:1.4}));
  k.sphere(boat,[1,.1,.6],[0,.05,0],k.mat('#4c655f',{roughness:.45}));boats.push(boat);
 }refs.boats=boats;
}
export function buildPopupSet(r,k,o={}){
 const g=r.group,refs=r.refs,{box,cyl,sphere,tube,sign}=k;
 const spot=(object,action,name)=>{Object.assign(object.userData,{action,name});r.hotspots.push(object);return object;};
 const layout=popupLayout();Object.assign(r,layout,{night:true,camera:layout.stations.entrance.position,target:layout.stations.entrance.target});
 box(g,[72,.2,51],[0,-.13,1],k.stone);
 const paving=k.surface('cobblestone_floor_02',[25,19],'#a9a79a');paving.roughness=.64;paving.normalScale.set(.65,.65);
 const ground=k.mesh(g,new T.PlaneGeometry(68,48),paving,[0,.002,0]);ground.rotation.x=-Math.PI/2;
 // Broad pedestrian avenues; timber islands define dining and river terraces.
 for(const [x,z,w,d] of [[-17,12,21,14],[18,-2,21,7],[0,-5,21,8],[0,-20,64,5]]){
  const deck=k.mesh(g,new T.PlaneGeometry(w,d),k.surface('wood_floor',[w/2,d/2],'#9c8e72'),[x,.013,z]);deck.rotation.x=-Math.PI/2;
 }
 festivalBridge(g,k,refs);
 dressPopup(g,k);
 for(let x=-32;x<=32;x+=2){box(g,[.08,1.12,.08],[x,.56,-23],k.woodDark);for(const y of [.5,1.05])box(g,[2,.055,.045],[x+1,y,-23],k.woodDark);}
 refs.marketSteam=[];
 for(const [i,b] of POPUP_BOOTHS.entries()){
  const stall=popupStall(g,k,i);spot(stall,b.action,b.name);
  const vendor=k.person(stall,[.35,0,.1],{coat:i%2?'#aa967e':'#6c817b',apron:true,cooking:['food','grill'].includes(b.id)});refs.people.push(vendor);
  const steam=(x,z)=>{for(let n=0;n<3;n++){const s=k.steam(stall,[x,1.1,z]);s.userData.origin=[x,1.1,z];s.userData.phase=n*.31;refs.marketSteam.push(s);}};
  if(['food','grill'].includes(b.id)){
   const food=k.food(stall,b.id==='grill'?'mackerel':'jjimdak');food.position.set(-.95,.99,1.1);food.scale.setScalar(.76);steam(-.95,1.1);
   for(let n=0;n<4;n++){cyl(stall,.085,.058,.13,[.1+n*.32,1.02,1.2],'#ceb084');for(let q=0;q<4;q++)sphere(stall,[.035,.024,.03],[.075+n*.32+q*.015,1.115,1.2],'#9d5f30');}
   sign(stall,b.id==='food'?'찜닭 컵  7,000':'간고등어 한 접시  6,000',[0,.65,1.59],2.1,'#e8d8b6',b.color,.24);
  }else if(b.id==='apple'){
   for(let n=0;n<3;n++){box(stall,[.95,.16,.6],[-1.3+n*1.25,1.02,1.13],k.wood);for(let j=0;j<12;j++){const x=-1.65+n*1.25+j%4*.21,z=.94+Math.floor(j/4)*.17;sphere(stall,[.088,.081,.079],[x,1.17,z],n%2?'#b88743':'#a04a36');cyl(stall,.005,.005,.04,[x,1.25,z],'#5c4c2f',8);}}
   sign(stall,'사과 한 컵  3,000',[0,.65,1.59],1.9,'#e8d8b6',b.color,.24);
  }else if(b.id==='craft'){
   for(let n=0;n<5;n++)k.mask(stall,[-1.6+n*.78,1.36,1.17],.68);
   for(let n=0;n<4;n++){k.mask(stall,[-1.4+n*.95,1.65,-1.43],.72);}
   sign(stall,'작은 탈  5,000',[0,.65,1.59],1.9,'#e8d8b6',b.color,.24);
  }else if(b.id==='print'){
   for(let n=0;n<5;n++){box(stall,[.28,.014,.38],[-1.5+n*.7,1.01,1.15],k.paper);cyl(stall,.055,.045,.09,[-1.4+n*.7,1.07,.85],['#8c5848','#768779','#9d8962'][n%3]);}
   sign(stall,'달 · 다리 · 탈  /  나만의 엽서',[0,.65,1.59],2.8,'#e8d8b6',b.color,.24);
  }else if(['tea','sikhye'].includes(b.id)){
   k.teapot(stall,[-1.25,.99,1.1],.44);k.pot(stall,[1.3,.99,.9],.44);
   for(let n=0;n<5;n++){k.bowl(stall,[-.6+n*.35,1.01,1.22],.1,'#ced1bd',b.id==='tea'?'#b39a56':'#bd8b61');if(b.id==='tea')k.flower(stall,[-.6+n*.35,1.07,1.22],.34);}steam(-.25,1.2);
   sign(stall,b.id==='tea'?'국화차  4,000':'안동 식혜  4,000',[0,.65,1.59],1.9,'#e8d8b6',b.color,.24);
  }else if(b.id==='game'){
   const z=POPUP_TUHO.z-b.z;refs.tuhoJar=k.pot(stall,[0,.08,z],.95);refs.tuhoJar.userData.lid.visible=false;cyl(stall,.18,.18,.018,[0,.61,z],'#29281f');
   for(let n=0;n<(o.gameScore||0);n++)cyl(stall,.009,.009,.7,[-.07+n*.07,.8,z],'#a38c55');
   for(let n=0;n<(o.gameAttempts||0)-(o.gameScore||0);n++)cyl(stall,.009,.009,.7,[.5+n*.16,.035,z+.4],'#a38c55').rotation.x=Math.PI/2;
   for(let n=0;n<5;n++)cyl(stall,.009,.009,.7,[-1.6+n*.16,1.02,1.15],k.woodDark).rotation.z=.2;
   refs.target=new T.Vector3(POPUP_TUHO.x,.08+.57*.95,POPUP_TUHO.z);
   sign(stall,'세 번의 도전',[0,.65,1.59],1.9,'#e8d8b6',b.color,.24);
   box(g,[2.4,.008,.07],[b.x,.012,10.4],'#c8b37d');
  }else{sign(stall,'먹거리 · 공예 · 무대 · 강변',[0,1.28,1.22],3.4,'#e2d9bd','#3d5145',.3);}
  if(o.cart?.includes(b.id))sign(stall,'수령한 부스',[1.44,1.16,1.57],.74,'#3f4e39','#d9d4b9',.15);
 }
 // Bunting above the dining aisle, fabric pennants and pool lights at seat height.
 for(const z of [10,17])for(let i=0;i<14;i++){
  const x=-27+i*1.55,geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute([-.25,0,0,.25,0,0,0,-.42,.025],3));geo.computeVertexNormals();k.mesh(g,geo,k.mat(['#ad654d','#d2b56d','#6f897b'][i%3],{side:T.DoubleSide,roughness:.94}),[x,3.8,z]);
 }
 for(const [x,z] of POPUP_TABLES){k.table(g,[x,0,z],2.5,.8,.75);for(const dz of [-.85,.85]){bench(g,k,x,z+dz,dz>0?Math.PI:0);}k.bowl(g,[x-.6,.81,z],.09,'#c8bd9e','#a18b52');cyl(g,.065,.085,.2,[x+.75,.89,z],'#494e43');sphere(g,[.056,.03,.056],[x+.75,1,z],k.mat('#ffe9bc',{emissive:'#ffd290',emissiveIntensity:2}));}
 for(const [x,z] of POPUP_BENCHES)bench(g,k,x,z,z<-18?0:Math.PI);
 for(const z of [8,15])stringLights(g,k,[-28,4.4,z],[-5,4.4,z]);
 for(const z of [-4,4,14])stringLights(g,k,[5,4.6,z],[28,4.6,z]);
 stringLights(g,k,[-28,4.4,-4],[-9,4.4,-4]);
 for(const [x,z] of [[-17,11],[18,-2],[17,12]]){const l=new T.PointLight('#ffcf96',24,20,2);l.position.set(x,3.6,z);g.add(l);}
 const stage=new T.Group();stage.position.set(POPUP_STAGE.x,0,POPUP_STAGE.z);g.add(stage);box(stage,[10,.32,5.6],[0,.16,0],k.woodDark);
 box(stage,[10,4.4,.12],[0,2.35,-2.65],k.mat('#293e43',{roughness:.85}));
 dressStage(stage,k);
 sign(stage,'달빛 무대',[0,3.92,-2.31],3.3,'#eadabb','#293e43',.4);
 for(const x of [-4.65,4.65]){box(stage,[.65,1.6,.7],[x,1.05,1.55],'#252c2c');for(const y of [.65,1.3]){const speaker=cyl(stage,.2,.2,.025,[x,y,1.914],'#121817');speaker.rotation.x=Math.PI/2;}cyl(stage,.06,.06,4.4,[x,2.5,-2.4],'#777f79');}
 tube(stage,[[-4.65,4.55,-2.4],[4.65,4.55,-2.4]],.06,'#777f79');
 refs.dancer=k.person(stage,[0,.33,.7],{coat:'#dbcead'});refs.dancer.userData.baseY=.33;k.mask(refs.dancer,[0,1.5,.15],.62);
 dressFestivalPerformer(refs.dancer,k);
 for(const x of [-2.2,2.2]){const performer=k.person(stage,[x,.33,0],{coat:x<0?'#a96a55':'#668b8f'});refs.people.push(performer);festivalDrum(stage,k,x);}
 spot(stage,'performance','달빛 무대 · 장단 따라하기');
 for(const x of [-3,3]){const l=new T.SpotLight(x<0?'#f6dab3':'#a9d8e1',90,19,.68,.7,1.5);l.position.set(x,4.3,-1.4);l.target.position.set(0,.7,.7);stage.add(l,l.target);}
 // Outdoor craft exhibition, separate from the sales counters.
 const gallery=new T.Group();gallery.position.set(-27,0,-16);g.add(gallery);
 box(gallery,[5,2.35,.1],[0,1.22,0],k.woodDark);for(let n=0;n<4;n++){k.mask(gallery,[-1.8+n*1.2,1.6,.17],1.1);sign(gallery,['웃음','풍자','몸짓','장단'][n],[-1.8+n*1.2,.73,.08],.8,'#e3d7b9','#3a4540',.2);}spot(gallery,'gallery','하회탈 야외 전시');
 const exhibitionLight=new T.RectAreaLight('#ffdda5',7,4,1);exhibitionLight.position.set(-27,2.7,-14);exhibitionLight.lookAt(-27,1,-16);g.add(exhibitionLight);
 const photoBoard=sign(g,'월영교 야경',[27,1.35,-16],2.7,'#eedfba','#384e49',.4);spot(photoBoard,'photo','월영교 야경 사진 찍기');
 for(const x of [-5,5])box(g,[.24,3.45,.24],[x,1.725,21],k.woodDark);
 box(g,[10.6,.5,.22],[0,3.25,21],k.woodDark);sign(g,'월영 밤마당',[0,3.26,21.13],6,'#eee0ba','#38483f',.4);
 const guide=sign(g,'밤마당 안내도',[7,1.3,20.2],1.45,'#e9dcc0','#43534b',.6);spot(guide,'popup-map','밤마당 안내도 보기');
 // People at human scale provide depth cues, with open paths between every zone.
 spectators(g,k,[[-14,8,2.8],[-20,8,3.4],[-24,13,1.1],[-8,10,-1.7],[-20,-5,2.8],[-23,-6,3.3],[12,-5,2.7],[23,-5,3.5],[15,10,.7],[21,11,-.8],[-4,-6,3.1],[4,-6,3.2],[-5,-2,3.1],[3,-2,3.4],[10,-21,0],[22,-21,-.4]]);
 addSceneLife(r,'popup');
 for(const x of [-33,33])k.grove(g,[-18,-5,10,24].map((z,i)=>({x,z,height:6+i*.5,seed:i+Math.abs(x)})));
 for(const [x,z] of [[-29,18],[-7,19],[28,17],[-30,-11],[28,-11]])k.plant(g,[x,0,z],1.7);
 refs.arrow=cyl(g,.014,.014,.65,[0,1.2,5],'#b18d52');refs.arrow.visible=false;
 return r;
}
