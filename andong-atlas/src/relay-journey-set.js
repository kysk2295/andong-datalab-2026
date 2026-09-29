import * as T from 'three';
import {createRiverWater} from './relay-water.js';
import {riverLandscape} from './relay-architecture.js';
import {createBusCabin} from './transit-cabin.js';
import {addSceneLife} from './relay-life.js';
import {JOURNEYS,journeyLayout,journeyVehicle} from './relay-journey.js';

export function buildJourneySet(k,o){
 const id=o.journey,j=JOURNEYS[id],group=new T.Group(),refs={people:[],workTargets:[]},hotspots=[];
 const r={group,refs,hotspots,...journeyLayout(id,o.transport),camera:[0,1.7,8],target:[0,1.6,-4],night:j.night};
 const {box,cyl,tube,label}=k,metal=k.mat('#8a9691',{metalness:.7,roughness:.3});
 box(group,[19,.14,id==='arrival'?22:40],[0,-.12,id==='arrival'?1:-7],k.paving);box(group,[3.9,.022,23],[.8,.002,-1],k.stone);
 const tag=(object,key,name)=>{object.userData.action='journey:'+key;object.userData.name=name;hotspots.push(object);};
 const board=(p,words,key)=>{const g=new T.Group();g.position.set(...p);group.add(g);box(g,[.09,2,.09],[0,1,0],k.woodDark);tag(label(g,words,[0,1.85,.09],1.5,'#ebdfc0','#305547',.52),key,words);};
 function facade(x,z,w=7){const g=new T.Group();g.position.set(x,0,z);group.add(g);box(g,[w,3.7,3],[0,1.85,0],k.plaster);for(const a of [-w*.36,0,w*.36]){box(g,[1.2,1.7,.03],[a,1.5,1.53],'#48635c');for(let q=-.5;q<=.5;q+=.25)box(g,[.023,1.7,.06],[a+q,1.5,1.56],k.woodDark);}k.roof(g,w+.6,4,[0,3.6,0]);return g;}
 function vehicle(x,z){
  if(o.transport!=='taxi'){const bus=createBusCabin(),placement=journeyVehicle(id,o.transport);bus.group.position.set(placement.x,0,placement.z);bus.group.rotation.y=Math.PI;bus.update(0,{doorOpen:1});group.add(bus.group);refs.parkedBus=bus;return bus.group;}
const g=new T.Group();g.position.set(x,0,z);group.add(g);const taxi=o.transport==='taxi',length=taxi?4.5:7;
  box(g,[2.5,1.65,length],[0,1.28,0],taxi?'#e8e4cf':'#567668');box(g,[2.5,.2,length+.1],[0,2.2,0],taxi?'#dfdfd2':'#c3c5ac');box(g,[2.52,.8,length-.8],[0,1.65,0],k.mat('#304c52',{metalness:.45,roughness:.15}));
  for(const side of [-1,1])for(const a of [-length*.32,length*.32]){const wheel=cyl(g,.4,.4,.18,[side*1.24,.42,a],'#292c2b');wheel.rotation.z=Math.PI/2;const hub=cyl(g,.19,.19,.19,[side*1.25,.42,a],metal);hub.rotation.z=Math.PI/2;}
  for(let a=-length/2+.3;a<length/2;a+=1.1)box(g,[2.56,.84,.065],[0,1.7,a],'#bac2b5');
  // Open door on the pedestrian side, with lit steps visible from outside.
  box(g,[.035,1.88,1.05],[-1.275,1.14,-.4],'#172a2b');for(let n=0;n<3;n++)box(g,[.62,.16,1],[-1.52+n*.15,.18+n*.18,-.4],metal);
  label(g,taxi?'TAXI':'이어드림 연결차량',[0,2.03,length/2+.012],1.95,'#f3e5bd','#254c3f',.25);
  return g;
 }
 if(id==='workshop'){
  const restaurant=facade(0,12,7);restaurant.rotation.y=Math.PI;label(restaurant,'이어드림 식당',[0,2.7,1.58],3.2,'#f1dfb7','#345748',.48);
  for(const side of [-1,1])for(let z=-5;z<=6;z+=5){const wall=facade(side*7.3,z,4.8);wall.rotation.y=side<0?Math.PI/2:-Math.PI/2;}
  const hanok=facade(3,-13,9);label(hanok,'이어드림 공방',[0,2.6,1.59],2.8,'#edddb7','#374c3d',.45);box(hanok,[2.2,2.3,.045],[0,1.15,1.62],'#1e3932');for(const x of [-1.3,1.3])k.lamp(hanok,[x,2.35,1.85],.5);
  box(group,[1.1,.9,3],[-1.55,.45,-5],k.plaster);for(let n=0;n<4;n++)k.plant(group,[-1.55,.93,-6+n*.65],.8);
  board([-1,0,.3],'식사 → 전통 체험 ↗','turn');board([4.6,0,-8.7],'체험권을 챙겨 들어오세요','gate');
 }else if(id==='pickup'){
  facade(0,12,9).rotation.y=Math.PI;
  for(let i=0;i<5;i++){const z=7-i*6;box(group,[4,5.5,5.7],[13,2.75,z],k.plaster);for(const y of [1.6,4]){box(group,[.035,1.2,3.9],[10.98,y,z],'#344946');for(let n=0;n<3;n++)box(group,[.06,1.25,.05],[10.92,y,z-1.5+n*1.5],metal);}}
  facade(-7,-6,7);facade(-7,3,7);box(group,[5,.025,30],[6,.008,-4],'#555d5c');box(group,[.15,.12,29],[3.5,.035,-4],'#b4b7a7');
  if(o.transport!=='walk')vehicle(4.5,-3.8);else{for(let z=-5;z>-17;z-=2)box(group,[1.4,.025,.12],[3.5,.025,z],'#d8d0b8');}
  board([-1.15,0,0],o.transport==='walk'?'월영교 도보 연결 →':'월영교 방면 승차','stop');board([1.25,0,-5.5],o.transport==='walk'?'보행로로 출발':'이곳에서 탑승','board');
  for(const x of [-1.8,1.3])box(group,[.09,2.75,.09],[x,1.38,-1.8],metal);box(group,[3.6,.12,2],[-.25,2.8,-1.8],k.woodDark);
  box(group,[3.25,1.85,.025],[-.25,1.57,-2.68],k.mat('#aec5c0',{transparent:true,opacity:.16,roughness:.18,depthWrite:false}));
  box(group,[2.6,.025,.05],[-.25,2.71,-1.65],k.mat('#eadabb',{emissive:'#f2d8a6',emissiveIntensity:1.2}));
  const light=new T.PointLight('#ffddb5',12,8,2);light.position.set(-.25,2.65,-1.6);group.add(light);
  label(group,'월영교 방면',[-.2,2.32,-2.64],1.1,'#eee2c3','#2f4942',.23);
box(group,[2,.12,.5],[-.25,.42,-2.4],k.woodDark);
 }else{
  refs.water=createRiverWater(95,120,[-25,-.18,-18]);group.add(refs.water);
  for(let z=-19;z<=12;z+=2){box(group,[.11,1.15,.11],[-2.55,.58,z],k.woodDark);for(const y of [.48,1.08])box(group,[.07,.07,2],[-2.55,y,z+.9],k.woodDark);}
  riverLandscape(group,k);
  if(id==='arrival'){
   if(o.transport!=='walk')vehicle(6,8);
   box(group,[3.6,.15,28],[0,.1,-24],k.woodDark);for(const x of [-1.8,1.8])for(let z=-36;z<-10;z+=2){box(group,[.17,1.22,.17],[x,.76,z],k.woodDark);for(const y of [.65,1.23])box(group,[.1,.1,2],[x,y,z+.9],k.woodDark);}
   board([1.5,0,0],'월영교 산책로 ↓','walkway');board([1.6,0,-8.5],'월영교 · 산책 시작','bridge');
  }else{
   for(let i=0;i<3;i++){const g=new T.Group();g.position.set(-1+i*4,0,-14);group.add(g);for(const x of [-1.5,1.5])box(g,[.06,2.7,.06],[x,1.35,0],k.woodDark);k.roof(g,3.7,2.8,[0,2.7,-.7]);label(g,['안동의 맛','월영차회','전통 공예'][i],[0,2.2,.04],2.7,'#eeddb9','#355545',.36);k.table(g,[0,0,0],3,.8,1);}
   board([1.4,0,0],'야간 팝업 장터 ↗','shore');board([4.6,0,-8.5],'음식 · 공예 · 놀이','market');
  }
 }
 for(let z=-9;z<=8;z+=5){cyl(group,.055,.065,3.4,[-2,1.7,z],k.woodDark);k.lamp(group,[-2,3.15,z],.42);k.plant(group,[['pickup','arrival'].includes(id)?9:5,0,z],1.6);}

 addSceneLife(r,'link-'+id);
 return r;
}
