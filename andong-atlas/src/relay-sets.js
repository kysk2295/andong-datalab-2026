import {buildPopupSet,addDistantPopup} from './relay-popup.js';
import * as T from 'three';
import {createRiverWater} from './relay-water.js';
import research from '../public/data/relay-research.json';
import {marketStreet,pavilion,riverLandscape} from './relay-architecture.js';
import {buildJourneySet} from './relay-journey-set.js';
import {buildDiningRoom} from './relay-dining.js';
import {enrichRelaySet} from './relay-details.js';
import {addSceneLife} from './relay-life.js';
import {buildBusRide} from './relay-bus.js';

export function buildRelaySet(id,k,options={}){
 if(id==='link')return buildJourneySet(k,options);
 if(id==='transit'&&!['taxi','walk'].includes(options.transport))return buildBusRide(k,options,research.route.coordinates);
 const group=new T.Group(),refs={people:[],workTargets:[]},hotspots=[];
 const result={group,refs,hotspots,camera:[0,1.65,5],target:[0,1.4,-3],night:false,bounds:{x:[-2,2],z:[-1,6]}};
 if(id==='meal'||id==='receipt')return buildDiningRoom(result,k,options);
 if(id==='popup')return buildPopupSet(result,k,options);
 const {box,cyl,sphere,tube,label,roof,lamp,table,chair,bowl,plant,pot,mask,food}=k;
 const spot=(object,action,name)=>{object.userData.action=action;object.userData.name=name;hotspots.push(object);return object;};
 const work=(object,id,name)=>{refs.workTargets.push({object,id,label:name});return object;};
 function npc(p,role,coat='#54766a',rotation=0){const person=k.person(group,p,{coat,rotation,apron:role==='host'||role==='teacher'});refs.people.push(person);if(role)spot(person,'talk:'+role,{host:'식당 직원과 이야기하기',teacher:'체험 선생님과 이야기하기',guide:'골목 안내인과 이야기하기',vendor:'부스 운영자와 이야기하기'}[role]);return person;}
 function ground(size=40){box(group,[size,.12,size],[0,-.08,0],k.stone);}
 function lattice(parent,x,y,z,w=2,h=1.5){box(parent,[w,.05,.07],[x,y-h/2,z],k.wood);box(parent,[w,.05,.07],[x,y+h/2,z],k.wood);box(parent,[w,h,.035],[x,y,z-.02],k.paper);for(let a=-w/2;a<=w/2+.01;a+=.25)box(parent,[.022,h,.055],[x+a,y,z+.04],'#694f36');for(let b=-h/2;b<=h/2+.01;b+=.25)box(parent,[w,.023,.055],[x,y+b,z+.04],'#694f36');}
 function hanok(parent,p,w=6,d=4,title=''){const a=new T.Group();a.position.set(...p);parent.add(a);box(a,[w,2.5,d],[0,1.25,0],k.paper);for(const x of [-w/2,w/2])for(const z of [-d/2,d/2])box(a,[.18,2.9,.18],[x,1.45,z],k.wood);roof(a,w+.65,d+.55,[0,2.8,0]);lattice(a,0,1.4,d/2+.03,w*.7,1.6);if(title)label(a,title,[0,2.43,d/2+.08],w*.52,'#f3ddb1','#314b40',.44);return a;}
 function interior(){
  box(group,[10,.12,10],[0,-.07,0],k.floor);
  box(group,[10,3.5,.16],[0,1.75,-4.3],k.plaster);
  for(const x of [-4.8,4.8]){box(group,[.15,3.5,10],[x,1.75,0],k.plaster);box(group,[.16,3.5,.16],[x,1.75,-4.1],k.wood);}
  box(group,[10,.12,10],[0,3.5,0],k.wood);
  for(let z=-4;z<4;z+=2)box(group,[9.8,.2,.2],[0,3.2,z],k.wood);
  for(const x of [-3,0,3]){lamp(group,[x,2.6,-1.5],.8);lattice(group,x,1.55,-4.19,2.2,1.8);}
 }
 function scenery(){riverLandscape(group,k);}
 function water(){refs.water=createRiverWater();group.add(refs.water);}
 function bridge(){water();scenery();
  // A close walkable section and long continuing spans; travel distances are compressed.
  const start=-120,end=90,length=end-start,center=(end+start)/2;
  box(group,[3.6,.24,length],[0,.08,center],k.woodDark);
  const boards=[];for(let z=start;z<end;z+=.24)boards.push({p:[0,.27,z],s:[3.6,.07,.231]});k.instances(group,new T.BoxGeometry(1,1,1),k.woodDark,boards);
  const beams=[],posts=[],caps=[],bolts=[];
  for(const x of [-1.78,1.78]){
   for(let z=start;z<end;z+=2.1){posts.push({p:[x,.91,z],s:[.18,1.22,.18]});caps.push({p:[x,1.61,z],s:[.16,.07,.16],r:[0,Math.PI/4,0]});beams.push({p:[x,1.48,z],s:[.25,.23,.25]});
    for(const y of [.62,1.22])bolts.push({p:[x-Math.sign(x)*.097,y,z],s:[.009,.018,.018]});
    for(let n=1;n<6;n++)beams.push({p:[x,.88,z+n*.35],s:[.055,.89,.055]});
   }
   for(const y of [.43,.84,1.29])box(group,[.105,.115,length],[x,y,center],k.woodDark);
   box(group,[.024,.027,length],[x,1.215,center],k.mat('#dba353',{emissive:'#e8a94c',emissiveIntensity:.8}));
  }
  k.instances(group,new T.BoxGeometry(1,1,1),k.woodDark,posts.concat(beams));k.instances(group,new T.ConeGeometry(1,1,4),k.mat('#303738',{metalness:.5}),caps);k.instances(group,new T.SphereGeometry(1,8,6),k.mat('#888471',{metalness:.8}),bolts);
  const pagoda=pavilion(group,[0,.29,-14],k);spot(pagoda,'primary','월영정 둘러보기');
  for(const x of [-2.1,2.1]){const light=new T.PointLight('#ffd69b',22,11,2);light.position.set(x,2.5,-14);group.add(light);}
  for(const z of [-5,8,-28]){const glow=new T.PointLight('#edc08b',5,7,2);glow.position.set(0,1.1,z);group.add(glow);}
  // Accessible sloped connection to the slightly raised pavilion deck.
  const ramp=box(group,[2.15,.08,2.8],[0,.45,-10.1],k.woodDark);ramp.rotation.x=.1;
  for(const x of [-1.78,1.78])for(let z=-100;z<90;z+=16){cyl(group,.18,.25,2.8,[x,-1.35,z],'#949b8b');}
  const moon=sphere(group,.44,[18,23,-88],k.mat('#f6e4b6',{emissive:'#e7d5a8',emissiveIntensity:.8}));moon.castShadow=false;
  refs.boats=[];
  for(let i=0;i<3;i++){const a=new T.Group();group.add(a);a.position.set([7,12,16][i],-.02,[-3,-37,-10][i]);const crescent=new T.Shape();crescent.absarc(0,0,.95,Math.PI*.25,Math.PI*1.75,false);crescent.bezierCurveTo(-.75,-.5,-.75,.5,Math.SQRT1_2*.95,Math.SQRT1_2*.95);crescent.closePath();k.mesh(a,new T.ExtrudeGeometry(crescent,{depth:.27,bevelEnabled:true,bevelThickness:.04,bevelSize:.03,bevelSegments:2,steps:1}),k.mat(['#edbd57','#84c4b8','#ef9bb2'][i],{emissive:['#d89c30','#469789','#bd607a'][i],emissiveIntensity:1.2}),[0,.66,0]);sphere(a,[.7,.18,.45],[0,-.19,.1],k.mat('#bfb7a6',{roughness:.48}));k.roundedBox(a,[.45,.12,.35],[0,.01,.13],k.mat('#827968'),.035);refs.boats.push(a);}
  const sail=new T.Group();group.add(sail);sail.position.set(-11,0,-21);sphere(sail,[2.3,.3,.65],[0,0,0],'#725035');cyl(sail,.05,.07,3.4,[0,1.65,0],k.wood);const canvas=new T.PlaneGeometry(1.6,2.35,18,18),vertices=canvas.attributes.position;for(let i=0;i<vertices.count;i++){const u=vertices.getX(i)/1.6+.5,v=vertices.getY(i)/2.35+.5;vertices.setZ(i,.22*Math.sin(u*Math.PI)*Math.sin(v*Math.PI));}canvas.computeVertexNormals();k.mesh(sail,canvas,k.mat('#a99263',{side:T.DoubleSide,roughness:.95}),[-.65,1.9,0]);for(const y of [.78,1.17,1.56,1.95,2.34,2.73])tube(sail,[[-1.46,y,.014],[-.7,y,.14],[.17,y,.014]],.012,k.woodDark);
  refs.fountain=new T.Group();group.add(refs.fountain);refs.fountain.visible=false;for(let i=0;i<12;i++)tube(refs.fountain,[[2.35,.2,-i*2.7],[4,2.8,-i*2.7],[6,-.2,-i*2.7]],.025,k.mat('#a3dbe1',{emissive:'#99c6e2',emissiveIntensity:.5,transparent:true,opacity:.65}));
 }
 if(id==='market'){
  marketStreet(result,k,spot);
 }else if(id==='workshop'){
  interior();result.camera=[0,1.44,1.75];result.target=[0,.96,-.32];result.bounds={x:[-.5,.5],z:[1.4,2.2]};
  table(group,[0,0,0],2.5,1.5,.73);label(group,'손끝으로 만나는 안동',[0,2.67,-4.17],3,'#574d35','#e4d5b4',.45);
  for(const side of [-1,1]){const g=new T.Group();group.add(g);g.position.set(side*3.7,0,-2.2);for(const y of [.3,1,1.7]){box(g,[1.2,.1,.75],[0,y,0],k.wood);for(let i=0;i<3;i++)pot(g,[-.4+i*.4,y+.05,0],.48);}for(const x of [-.58,.58])box(g,[.08,2,.08],[x,1,0],k.wood);plant(group,[side*3.4,0,1.4],1.2);}
  for(let i=0;i<3;i++){const m=mask(group,[-2+i*2,1.6,-4.05],.8);m.rotation.z=(i-1)*.12;}
  npc([-1.65,0,-.6],'teacher','#8b7458',.3);
  if(options.program==='tea'){
   refs.teapot=k.teapot(group,[-.27,.805,-.1],.34);refs.teapot.rotation.z=0;refs.teapot.userData.lid.visible=options.craftSteps>=2;

   refs.cup=bowl(group,[.3,.8,.12],.057,'#c4cbb9');
   bowl(group,[-.8,.8,.27],.095,'#9c794f');for(let i=0;i<7;i++)k.flower(group,[-.8+Math.sin(i*2)*.05,.85,.27+Math.cos(i*2)*.04],.75);
   refs.flowers=new T.Group();group.add(refs.flowers);for(let i=0;i<7;i++){k.flower(refs.flowers,[-.27+Math.sin(i*2)*.035,.992,-.1+Math.cos(i*2)*.033],.4);}refs.flowers.visible=options.craftSteps>=1;
   refs.teaStream=cyl(group,.009,.009,.34,[.15,1.04,.09],k.mat('#d2b76a',{transparent:true,opacity:.65}));refs.teaStream.visible=false;refs.steam=new T.Group();refs.steam.position.set(.3,.843,.12);group.add(refs.steam);for(let i=0;i<5;i++){const w=k.steam(refs.steam,[Math.sin(i)*.025,i*.04,Math.cos(i)*.02]);w.userData.phase=i*.74;}refs.steam.visible=options.craftSteps>=3;
   work(refs.teapot,'pour','다관');
   refs.kettle=pot(group,[.62,.805,-.33],.42);tube(refs.kettle,[[-.2,.3,0],[-.45,.45,0],[-.48,.52,0]],.05,'#536e67');refs.kettle.visible=options.craftSteps===1;
   refs.potLiquid=cyl(group,.061,.061,.003,[-.27,.994,-.1],k.mat('#997b30',{roughness:.2}));refs.potLiquid.visible=options.craftSteps>=2;
   refs.cupLiquid=cyl(group,.045,.045,.003,[.3,.834,.12],k.mat('#826423',{roughness:.19}));refs.cupLiquid.visible=options.craftSteps>=3;
   for(let i=0;i<3;i++){const f=new T.Group();f.position.set(-.46+i*.24,.815,.32);group.add(f);k.flower(f,[0,.006,0],1);f.visible=options.craftSteps===0;work(f,'flower-'+i,'국화꽃 '+(i+1));}
   spot(refs.teapot,'primary','차 우리기');
  }else if(options.program==='soju'){
   refs.still=pot(group,[-.22,.8,-.12],1.15);cyl(refs.still,.21,.14,.28,[0,.75,0],'#775f48');const upper=pot(refs.still,[0,1,0],.75);upper.rotation.x=Math.PI;
   tube(group,[[-.02,1.5,-.12],[.33,1.47,-.12],[.42,1.27,-.12]],.031,'#9c7754');bowl(group,[.43,.8,-.12],.14,'#d4c6a3',options.craftSteps>=2?'#dfe4d8':null);
   bowl(group,[-.9,.8,.2],.16,'#a4845d','#e5d5ac');for(let i=0;i<10;i++)sphere(group,[.012,.008,.007],[-.9+Math.sin(i*2)*.09,.9,.2+Math.cos(i*2)*.07],'#f3e6c8');
   refs.bottle=cyl(group,.065,.065,.25,[.83,.95,.2],k.mat('#638c7d',{roughness:.2}));cyl(group,.025,.055,.1,[.83,1.13,.2],'#638c7d');cyl(group,.033,.033,.04,[.83,1.2,.2],'#b49b74');refs.bottleLabel=label(group,'안동소주',[.83,1,.269],.11,'#514936','#e4d3aa',.13);refs.bottleLabel.visible=options.craftSteps>=3;refs.distill=cyl(group,.007,.007,.28,[.42,1.13,-.12],k.mat('#e7ddbf',{transparent:true,opacity:.7}));refs.distill.visible=false;spot(refs.still,'primary','전통주 과정 체험');
   for(const [i,id,name,color] of [[0,'rice','쌀','#eadcc0'],[1,'nuruk','누룩','#ac8a57'],[2,'water','물','#a6c5bc']]){const g=new T.Group();g.position.set(-.75+i*.55,.83,.56);group.add(g);bowl(g,[0,0,0],.16,'#d6c4a1',color);label(g,name,[0,.16,.13],.3,'#f1e5c9','#365146',.13);g.visible=options.craftSteps===0;work(g,id,name);}
   work(pot(group,[-.85,.81,-.4],.7),'ferment','발효 항아리');work(refs.still,'still','소주고리');work(bowl(group,[.47,.82,-.15],.2,'#d5c6aa','#e8e0cc'),'collect','받는 그릇');
   work(refs.bottle,'bottle','완성 술병');const tag=label(group,'나의 안동',[.05,.96,.57],.35,'#55442f','#f0d9aa',.24);tag.visible=options.craftSteps===2;work(tag,'label','표찰');refs.package=box(group,[.25,.25,.25],[-.55,.96,.48],'#a57f4b');refs.package.visible=options.craftSteps>=2;work(refs.package,'package','포장 상자');
  }else{
   refs.mask=mask(group,[0,.9,0],1.15);refs.mask.rotation.x=-Math.PI*.42;
   if(options.craftSteps>=1)refs.mask.userData.face.material=k.mat(options.color||'#c77a48');
   if(options.maskArt){refs.paintTexture=new T.TextureLoader().load(options.maskArt);refs.paintTexture.colorSpace=T.SRGBColorSpace;refs.paintMaterial=k.mat('#ffffff').clone();refs.paintMaterial.map=refs.paintTexture;refs.mask.userData.face.material=refs.paintMaterial;}
   for(let i=0;i<3;i++){cyl(group,.075,.065,.05,[-.8+i*.23,.82,.2],['#b95842','#e0b962','#3e6860'][i]);}
   refs.brush=box(group,[.022,.022,.4],[.8,.82,.2],k.wood);refs.brush.rotation.y=.6;
   spot(refs.mask,'primary','꾸미기');if(options.craftSteps>=2)for(const side of [-1,1])sphere(refs.mask,[.065,.045,.008],[side*.15,-.075,.126],'#bf5747');
   if(options.craftSteps>=3)label(group,'나의 안동 · 완성',[0,1.23,-.45],.85,'#ead8aa','#36584b',.18);
  }
 }else if(id==='transit'){
  result.camera=[.48,1.4,2.15];result.target=[.05,1.6,-8];result.bounds={x:[.2,.7],z:[1.8,2.5]};
  ground(100);scenery();box(group,[8,.03,100],[0,.02,-20],'#64665f');for(let z=-55;z<24;z+=3.5)box(group,[.12,.012,1.8],[0,.047,z],'#e0ce85');
  refs.city=new T.Group();group.add(refs.city);for(let i=0;i<16;i++){hanok(refs.city,[(i%2?1:-1)*(10+i%3*2),0,12-i*7],5,3);}
  refs.roadside=new T.Group();group.add(refs.roadside);for(let i=0;i<18;i++){const x=(i%2?1:-1)*6,z=-i*5;cyl(refs.roadside,.06,.07,4,[x,2,z],'#3d514d');sphere(refs.roadside,.16,[x,4,z],k.mat('#e4ce97',{emissive:'#e4ce97',emissiveIntensity:.7}));}
  refs.vehicle=new T.Group();group.add(refs.vehicle);const bus=refs.vehicle;box(bus,[2.6,.12,5.4],[0,.3,0],'#42554f');box(bus,[2.6,.15,5.5],[0,2.6,0],'#d0c9b4');
  for(const x of [-1.25,1.25]){box(bus,[.12,.95,5.5],[x,.75,0],'#657b6c');for(const z of [-2.65,-1,1,2.65])box(bus,[.1,1.9,.08],[x,1.55,z],'#d0c9b4');}
  for(const x of [-.7,.7])for(const z of [-1.55,.0]){box(bus,[.5,.5,.12],[x,1.15,z],'#7d9276');box(bus,[.5,.1,.5],[x,.88,z+.2],'#7d9276');cyl(bus,.025,.025,1.4,[x,1.25,z-.1],'#b5b39c');}
  box(bus,[2.5,.4,.4],[0,.77,-2.45],'#354840');label(bus,options.transport==='taxi'?'월영교 방향 · 택시':'이어드림 · 월영교 방면',[0,2.22,-2.54],1.9,'#ead9aa','#344e43',.22);
  if(options.transport==='walk'){bus.visible=false;result.camera=[3.2,1.7,5];result.target=[3.2,1.6,-18];result.bounds={x:[2.9,3.5],z:[3,6]};}
  if(options.transport==='taxi'){
   bus.visible=false;const car=new T.Group();group.add(car);box(car,[2.1,.14,4],[0,.33,0],'#2e3938');box(car,[2.1,.1,3.8],[0,1.98,0],'#d0cabc');
   for(const x of [-1,1]){box(car,[.1,.6,4],[x,.63,0],'#727d70');for(const z of [-1.8,1.7])box(car,[.07,1.1,.1],[x,1.45,z],'#c6c3b5');}
   box(car,[2,.32,.6],[0,.95,-1.55],'#3b4340');const wheel=k.mesh(car,new T.TorusGeometry(.21,.025,8,24),k.mat('#292f2b'),[-.5,1.16,-1.3]);wheel.rotation.x=-.35;
   label(car,'월영교 →',[.1,1.12,-1.22],.43,'#d7dabc','#253e36',.19);result.camera=[.4,1.3,.6];result.target=[0,1.15,-8];result.bounds={x:[.25,.6],z:[.45,.9]};
  }
  result.night=true;
  rAlight();
  function rAlight(){const taxi=options.transport==='taxi',walk=options.transport==='walk';if(walk)return;result.bounds.x=[.2,taxi?.9:1.15];result.stations={alight:{name:'차량 출입문',position:taxi?[.85,1.3,.65]:[1.05,1.55,2.15],target:[3.5,1.5,2.2]}};}
  const map=new T.Group();map.position.set(80,0,0);group.add(map);refs.routeMap=map;
  box(map,[28,.35,22],[0,-.2,0],'#36594b');
  const coords=research.route.coordinates,minX=Math.min(...coords.map(c=>c[0])),maxX=Math.max(...coords.map(c=>c[0])),minY=Math.min(...coords.map(c=>c[1])),maxY=Math.max(...coords.map(c=>c[1]));
  refs.routePoints=coords.map(c=>new T.Vector3((c[0]-minX)/(maxX-minX)*22-11,.16,8-(c[1]-minY)/(maxY-minY)*16));
  refs.routeCurve=tube(map,refs.routePoints.map(p=>p.toArray()),.095,'#efcf88').geometry.parameters.path;
  for(const [i,name] of [[0,'원도심 · 식사와 체험'],[coords.length-1,'월영교 · 야간 팝업']]){const p=refs.routePoints[i];cyl(map,.28,.28,.4,[p.x,.38,p.z],'#ead9aa');label(map,name,[p.x,1.3,p.z],5,'#f4e2b4','#29483e',.7).rotation.x=-Math.PI/4;}
  refs.routeMarker=sphere(map,.33,refs.routePoints[0].clone().add(new T.Vector3(0,.5,0)).toArray(),'#f4b55c');
  label(map,'공개 경로 3D 개략도 · 실제 버스 노선 아님',[0,2,-10],17,'#e8d6ad','#28473b',1);
 }else if(id==='bridge'){
  bridge();result.night=true;result.camera=options.cover?[4.7,3.1,15]:[0,1.94,13];result.target=options.cover?[0,1.4,-12]:[0,1.9,-17];result.bounds={x:[-1.42,1.42],z:[-18,14]};
  if(options.walked){result.camera=[0,1.94,-9];result.target=[0,1.8,-19];}
  addDistantPopup(group,k);
  const nightEntry=new T.Group();group.add(nightEntry);nightEntry.position.set(1.1,.28,9);
  box(nightEntry,[.035,1.35,.035],[0,.675,0],k.woodDark);
  spot(k.sign(nightEntry,'야간 팝업존',[0,1.2,.025],.84,'#f0d7a5','#354a40',.24),'night-market','야간 팝업존 들어가기');
  npc([-1.3,.305,-5],null,'#a88861',Math.PI);npc([1.3,.305,-23],null,'#56756b');
 }
 enrichRelaySet(id,result,k,options);
 addSceneLife(result,id);
 return result;
}
