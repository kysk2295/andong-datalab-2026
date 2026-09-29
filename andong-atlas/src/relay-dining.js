import {addSceneLife} from './relay-life.js';
import * as T from 'three';
import {RESTAURANT_ARRIVALS} from './relay-passages.js';
import {DINING_SEATS,diningSeat,diningLayout} from './relay-dining-layout.js';

// Photo references: supplied stage-1 images 9 / 11 (interior) and 8 / 17 (food).
// A visitor-scale reconstruction; layout and menu prices are illustrative.
export function buildDiningRoom(r,k,o={}){
 const g=r.group,{box,cyl,sphere,tube,sign}=k;
 const spot=(object,action,name)=>{Object.assign(object.userData,{action,name});r.hotspots.push(object);return object;};
 Object.assign(r,diningLayout(o.seat),{camera:RESTAURANT_ARRIVALS.dining.position,target:RESTAURANT_ARRIVALS.dining.target});
 const steel=k.mat('#9a9f9b',{metalness:.88,roughness:.3}),black=k.mat('#292b29',{roughness:.58}),ivory=k.mat('#c7c3b3',{roughness:.9});
 const brick=k.surface('brick_wall_001',[4.5,1.7],'#ab9385');
 const tile=k.surface('square_tiles',[4.05,4.45],'#9b9f99');
 // Large neutral stoneware slabs match image 11; retain only fine scanned grain.
 tile.normalScale.set(.025,.025);tile.roughness=.88;
 tile.onBeforeCompile=shader=>{shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>',`#include <map_fragment>
  #ifdef USE_MAP
  vec2 slabUv=vMapUv*4.;vec2 cell=floor(slabUv);vec2 edge=min(fract(slabUv),1.-fract(slabUv));
  float grout=smoothstep(.006,.014,min(edge.x,edge.y));
  float grain=dot(diffuseColor.rgb,vec3(.2126,.7152,.0722));
  float varied=.96+.07*fract(sin(dot(cell,vec2(12.9898,78.233)))*43758.5453);
  diffuseColor.rgb=diffuse*(.96+grain*.07)*varied*mix(.48,1.,grout);
  #endif`);};
 tile.customProgramCacheKey=()=> 'dining-stoneware-v1';
 const floor=k.mesh(g,new T.PlaneGeometry(9.55,10.5),tile,[0,.005,.6]);floor.rotation.x=-Math.PI/2;
 box(g,[10,.1,11],[0,-.065,.6],k.stone);
 box(g,[10,.12,10],[0,3.24,.4],black);
 // Back wall leaves a real opening onto the stainless kitchen pass.
 for(const x of [-3.37,3.37])box(g,[2.85,3.22,.16],[x,1.61,-4.3],brick);
 box(g,[3.9,.92,.16],[0,.46,-4.3],brick);box(g,[3.9,1.05,.16],[0,2.7,-4.3],brick);
 box(g,[.16,3.22,8.7],[4.78,1.61,.05],brick);
 // A street-facing side window with depth, slender glazing bars and a bench below it.
 for(const z of [-3.4,3.1])box(g,[.16,3.22,1.85],[-4.78,1.61,z],brick);
 box(g,[.16,.95,4.7],[-4.78,.475,-.15],brick);box(g,[.16,.46,4.7],[-4.78,3.0,-.15],brick);
 const glass=k.mat('#bbc9c6',{metalness:.12,roughness:.12,transparent:true,opacity:.1,depthWrite:false});
 box(g,[.016,1.78,4.6],[-4.76,1.86,-.15],glass);
 for(const z of [-2.46,-.9,.66,2.18])box(g,[.09,1.88,.038],[-4.7,1.88,z],black);
 for(const y of [.94,2.8])box(g,[.14,.045,4.7],[-4.71,y,-.15],black);
 box(g,[.38,.07,4.7],[-4.59,.95,-.15],k.wood);
 // The view is modelled beyond the glazing, rather than a photograph blocking the window.
 box(g,[4,.09,10],[-6.7,-.02,0],k.paving);box(g,[.15,4.8,12],[-8.6,2.4,0],k.plaster);
 for(const z of [-3,.1,3.2]){box(g,[.05,1.75,1.8],[-8.49,1.8,z],black);box(g,[.12,.06,2.3],[-8.43,2.85,z],steel);}
 k.plant(g,[-6.6,0,.8],1.2);k.plant(g,[-6.6,0,-3.3],.95);
 const daylight=new T.RectAreaLight('#ecf2ef',3.1,4,1.8);daylight.position.set(-4.5,1.9,-.2);daylight.lookAt(0,1,-.2);g.add(daylight);
 // Slim suspended lights and exposed black ceiling service lines.
 const white=k.mat('#edece4',{emissive:'#fff6e5',emissiveIntensity:1.4});
 for(const x of [-3,0,3])for(const z of [-2.1,1.8]){
  box(g,[.085,.05,1.6],[x,2.97,z],black);box(g,[.065,.015,1.53],[x,2.937,z],white);
  for(const dz of [-.58,.58])cyl(g,.004,.004,.25,[x,3.11,z+dz],black,8);
 }
 for(const x of [-3.6,2.4])tube(g,[[x,3.16,4.3],[x,3.16,-4.15]],.022,black);
 box(g,[.86,.08,.86],[.8,3.15,-.4],ivory);box(g,[.59,.018,.59],[.8,3.1,-.4],black);
 for(let i=0;i<9;i++)box(g,[.55,.009,.018],[.8,3.087,-.63+i*.056],ivory);
 // Upholstered wall bench, seams and warm grazing light from the reference room.
 for(const z of [-3,-2,-1,0,1,2,3]){
  k.roundedBox(g,[.085,.56,.97],[4.62,.89,z],black,.018);
  for(const dz of [-.38,0,.38])tube(g,[[4.563,.68,z+dz-.1],[4.563,.89,z+dz],[4.563,1.1,z+dz-.1]],.0025,'#575954');
 }
 box(g,[.52,.085,7.8],[4.37,.43,0],black);
 box(g,[.045,.025,8],[4.64,1.22,0],k.mat('#c39c6a',{emissive:'#edb878',emissiveIntensity:.75}));
 // Oscillating wall fan with a proper wire cage and separately animated rotor.
 const fan=new T.Group();fan.position.set(4.5,2.3,-1.1);fan.rotation.y=-Math.PI/2;g.add(fan);
 const rotor=new T.Group();fan.add(rotor);r.refs.fan=rotor;
 for(const radius of [.09,.16,.23])k.mesh(fan,new T.TorusGeometry(radius,.003,5,40),steel,[0,0,.05]);
 for(let i=0;i<12;i++){const a=i*Math.PI/6;tube(fan,[[0,0,.07],[Math.cos(a)*.23,Math.sin(a)*.23,0]],.0025,steel);}
 for(let i=0;i<3;i++){const blade=sphere(rotor,[.065,.15,.012],[0,.085,0],ivory);blade.rotation.z=i*Math.PI*2/3;blade.position.set(Math.sin(i*Math.PI*2/3)*.085,Math.cos(i*Math.PI*2/3)*.085,0);}
 sphere(fan,.042,[0,0,.065],black);
 // Entry has a wide walkable threshold; no billboards or floating stage instructions.
 for(const x of [-3.48,3.48])box(g,[2.6,3.22,.15],[x,1.61,4.4],brick);
 for(const x of [-2.12,2.12])box(g,[.07,2.5,.12],[x,1.25,4.4],black);
 box(g,[4.3,.06,.12],[0,2.52,4.4],black);box(g,[4.3,.018,.4],[0,.009,4.4],steel);
 box(g,[9,.05,3],[0,-.02,5.7],k.paving);
 // Open sliding leaves and a real exit sign are usable from either side.
 for(const x of [-2.03,2.03]){
  const leaf=new T.Group();leaf.position.set(x,0,4.4);g.add(leaf);
  box(leaf,[1.38,2.44,.022],[0,1.22,0],glass);
  for(const dx of [-.68,.68])box(leaf,[.035,2.48,.04],[dx,1.24,0],black);
  for(const y of [.03,2.47])box(leaf,[1.39,.04,.04],[0,y,0],black);
  box(leaf,[.025,.38,.05],[-Math.sign(x)*.49,1.18,-.04],steel);
  spot(leaf,'restaurant:exit','문으로 나가기');
 }
 const exitSign=sign(g,'출구 · 찜닭골목',[0,2.73,4.28],1.7,'#eeeadd','#34574a',.26);exitSign.rotation.y=Math.PI;
 spot(exitSign,'restaurant:exit','식당 밖으로 나가기');
 const exitPlate=sign(g,'밖으로',[-1.72,1.48,4.33],.5,'#f2eee4','#34574a',.2);exitPlate.rotation.y=Math.PI;
 spot(exitPlate,'restaurant:exit','식당 밖으로 나가기');
 // Continue the alley sightline beyond the threshold instead of ending at a slab.
 box(g,[6,.08,24],[0,-.06,17],k.paving);
 for(const side of [-1,1])for(const z of [8,13,18,23]){
  const shop=new T.Group();shop.position.set(side*4.3,0,z);shop.rotation.y=side<0?Math.PI/2:-Math.PI/2;g.add(shop);
  box(shop,[4.8,4.5,.15],[0,2.25,0],brick);
  box(shop,[3.3,2.3,.03],[0,1.2,.09],glass);
  for(const x of [-1.68,0,1.68])box(shop,[.045,2.4,.05],[x,1.2,.13],black);
  sign(shop,'안동찜닭',[0,2.9,.16],3.5,'#e6dfca','#3b5046',.45);
  box(shop,[4.3,.12,1.2],[0,3.42,.5],k.mat('#53746b',{roughness:.8}));
 }
 for(const z of [8,15,22]){for(const x of [-3.1,3.1])box(g,[.08,4.4,.08],[x,2.2,z],steel);box(g,[6.3,.09,.09],[0,4.4,z],steel);}

 // Each selectable seat owns its tabletop objects. Food and steam follow the chosen seat.
 const selected=diningSeat(o.seat);
 for(const [id,s] of Object.entries(DINING_SEATS)){
  const setting=new T.Group();setting.position.set(s.x,0,s.z);g.add(setting);
  k.table(setting,[0,0,0],1.75,1.15,.75);
  const chair=k.chair(setting,[0,0,.96],Math.PI);k.chair(setting,[0,0,-.93]);
  if(!o.ordered||s===selected)spot(chair,'seat:'+id,s.name+'에 앉기');
  const menu=new T.Group();menu.position.set(-.63,.797,-.25);menu.rotation.x=-Math.PI*.36;menu.rotation.z=.04;setting.add(menu);
  box(menu,[.27,.35,.008],[0,0,-.008],k.wood);
  sign(menu,'MENU',[0,.108,0],.22,'#413d36','#e1d9bd',.045);
  ['안동찜닭','간고등어','헛제사밥'].forEach((name,i)=>sign(menu,name,[0,.037-i*.054,.001],.22,'#514a3d','#e1d9bd',.037));
  if(!o.ordered||s===selected)spot(menu,'dining-menu:'+id,'메뉴판 보기');
  cyl(setting,.032,.031,.095,[-.7,.841,.32],steel);
  cyl(setting,.046,.047,.2,[.7,.899,-.34],steel);cyl(setting,.043,.043,.018,[.7,1.01,-.34],black);
  k.roundedBox(setting,[.15,.065,.11],[.7,.831,-.1],k.fabric,.012);box(setting,[.09,.008,.025],[.7,.869,-.1],'#e9e7da');
  if(s===selected){
   r.refs.diningOrigin=[s.x,0,s.z];r.refs.food=k.food(setting,o.meal||'jjimdak');r.refs.food.position.set(0,.78,0);
   r.refs.food.visible=o.ordered&&!o.eaten;spot(r.refs.food,'primary','식사 맛보기');
   if(o.ordered)k.sideDishes(setting);
   for(const x of [.665,.689])box(setting,[.005,.005,.255],[x,.801,.18],steel);
   tube(setting,[[.74,.802,.33],[.74,.802,.13]],.003,steel);sphere(setting,[.014,.003,.024],[.74,.804,.109],steel);
   const steam=new T.Group();steam.position.set(0,.93,0);setting.add(steam);r.refs.mealSteam=steam;steam.visible=o.ordered&&!o.eaten;
   for(let i=0;i<9;i++){const s=k.steam(steam,[Math.sin(i*2)*.13,i*.04,Math.cos(i*2)*.14]);s.userData.phase=i*.8;}
  }
 }
 k.table(g,[3,0,-1.6],1.5,1.15,.75);k.chair(g,[3,0,-.64],Math.PI);k.chair(g,[3,0,-2.56]);
 const guests=new T.Group();guests.position.set(3,0,-1.6);g.add(guests);
 const sharedMeal=k.food(guests,'jjimdak');sharedMeal.position.set(0,.78,0);sharedMeal.scale.setScalar(.7);
 for(const z of [-.4,.4]){k.bowl(guests,[-.45,.79,z],.09,'#b5b7ae','#e2d9be');cyl(guests,.032,.032,.09,[.5,.83,z],steel);}
 addSceneLife(r,'meal');
 r.obstacles.push({x:3,z:-.64,w:.55,d:.63},{x:3,z:-2.56,w:.55,d:.63});
 // Open kitchen: an actual room behind the pass, cook, hob, extraction and stacked crockery.
 box(g,[5,.08,2.7],[0,0,-5.6],tile);box(g,[5,3.2,.1],[0,1.6,-6.95],ivory);
 for(const x of [-2.5,2.5])box(g,[.1,3.2,2.7],[x,1.6,-5.6],ivory);
 box(g,[3.85,.055,.6],[0,.98,-4.3],steel);box(g,[4,.09,.8],[0,.86,-6.25],steel);
 box(g,[3.7,.22,.82],[0,2.6,-6.25],steel);cyl(g,.12,.12,.6,[1.2,2.99,-6.3],steel,24);
 for(const x of [-1.3,0,1.3]){k.bowl(g,[x,.92,-6.2],.25,'#282e2b','#68472b');for(let n=0;n<5;n++)k.bowl(g,[x,.99+n*.022,-4.28],.095,'#c8c9bc');}
 k.bowl(g,[-.33,.99,-4.48],.24,'#282e2b','#68472b');
 const cook=k.person(g,[-.6,0,-5.15],{coat:'#d0ccc0',apron:true,cooking:true});r.refs.people.push(cook);
 const kitchenLight=new T.RectAreaLight('#fff4da',3,3,1);kitchenLight.position.set(0,2.9,-5.6);kitchenLight.lookAt(0,0,-5.6);g.add(kitchenLight);
 // Same counter coordinates as the hand-operated card reader and receipt interaction.
 const counter=new T.Group();counter.position.set(3.1,0,2.45);g.add(counter);
 box(counter,[2.45,1.06,.82],[0,.53,0],k.wood);box(counter,[2.58,.06,.93],[0,1.09,0],k.mat('#686c63',{roughness:.36}));
 for(let x=-1.1;x<1.2;x+=.13)box(counter,[.025,.91,.014],[x,.53,.423],k.woodDark);
 sign(counter,'계산',[0,.76,.44],.6,'#ddd3ba','#45463d',.17);
 const terminal=new T.Group();counter.add(terminal);terminal.position.set(.55,1.14,0);
 box(terminal,[.29,.06,.25],[0,0,0],black);box(terminal,[.25,.35,.035],[0,.19,-.03],black);
 sign(terminal,'카드 · 현금',[0,.2,-.007],.21,'#d4d9cd','#233b34',.08);
 const paper=sign(counter,o.paid?'영수증':'감사합니다',[-.45,1.3,.29],.28,'#45483f','#ece7d9',.25);paper.rotation.x=-.17;
 Object.assign(r.refs,{counter,terminal,counterPaper:paper});spot(counter,'station:counter','계산대 이용하기');
 const host=k.person(g,[3.2,0,1.4],{coat:'#656c5d',apron:true});r.refs.people.push(host);spot(host,'talk:host','식당 직원과 이야기하기');
 k.plant(g,[-3.7,0,3.5],1.3);
 // One framed food photograph, like a restaurant menu print, lit by the room.
 box(g,[.88,1.18,.04],[3.1,1.98,-4.18],black);k.photo(g,'meal-photo',[3.1,1.98,-4.15],.82,1.12);
 sign(g,'따뜻하게 차려드립니다',[-3.1,2.48,-4.18],1.9,'#443c31','#bfb49c',.23);
 return r;
}
