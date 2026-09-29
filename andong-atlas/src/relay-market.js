import * as T from 'three';
import {RESTAURANT_PASSAGES} from './relay-passages.js';
import {batchScenery,dressMarketShop} from './relay-atmosphere.js';

// Visitor-scale reconstruction from the supplied stage-1 market photographs.
// Store names and their order are illustrative; this is not a cadastral survey.
export function marketStreet(r,k,spot){
 const g=r.group,sign=k.sign||k.label;
 const surface=(asset,repeat,color)=>k.surface?.(asset,repeat,color)||k.plaster;
 const steel=k.mat('#8e9592',{metalness:.88,roughness:.38}),edge=k.mat('#505b59',{metalness:.75,roughness:.42});
 const wall=surface('clay_plaster',[1.6,1.4],'#bdbdb1'),pavers=surface('square_tiles',[2.55,14.47],'#f0f0e8');
 const tile=surface('clay_plaster',[3,2],'#d4d0bc'),brick=surface('brick_wall_001',[3.8,2.2],'#b9b3a6');
 // Neutral painted plaster keeps scanned fine grain without the source clay's orange tint.
 wall.onBeforeCompile=shader=>{shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>','#include <map_fragment>\n float paintedGrey=dot(diffuseColor.rgb,vec3(.2126,.7152,.0722)); diffuseColor.rgb=mix(vec3(paintedGrey*1.55),diffuseColor.rgb,.14);');};wall.customProgramCacheKey=()=> 'market-painted-plaster';
 const dark=k.mat('#253834',{roughness:.78}),glass=k.mat('#abb7b1',{metalness:.12,roughness:.13,transparent:true,opacity:.15,depthWrite:false});
 r.camera=[.15,1.7,8];r.target=[.15,1.67,-10];r.bounds={x:[-2.25,2.25],z:[-21.2,9]};r.obstacles=[{x:-1.72,z:-21.2,w:1.35,d:.6},{x:1.72,z:-21.2,w:1.35,d:.6}];r.passages=[RESTAURANT_PASSAGES.market];
 k.box(g,[18,.16,42],[0,-.11,-7],wall);
 // The 2.35 m scanned square-tile patch keeps the same physical scale on both axes.
 const pavement=k.mesh(g,new T.PlaneGeometry(6,34),pavers,[0,.006,-6]);pavement.rotation.x=-Math.PI/2;
 // Continue the view beyond the arcade mouth. Returning from the restaurant
 // should reveal a street, rather than the sky where the ground used to end.
 const outside=new T.Group();g.add(outside);
 k.box(outside,[72,.12,24],[0,-.085,23],k.mat('#606761',{roughness:.98}));
 const sidewalk=surface('square_tiles',[30.64,1.28],'#bdbeb1');
 for(const z of [13,25]){
  k.box(outside,[72,.1,3],[0,0,z],k.mat('#a3a69c',{roughness:.96}));
  const slabs=k.mesh(outside,new T.PlaneGeometry(72,3),sidewalk,[0,.052,z]);slabs.rotation.x=-Math.PI/2;
  k.box(outside,[72,.14,.2],[0,.02,z+(z===13?1.5:-1.5)],wall);
 }
 for(let x=-2.1;x<=2.1;x+=.7)k.box(outside,[.36,.008,8],[x,-.016,19],k.mat('#d4d2bc',{roughness:.94}));
 for(const [i,x] of [-21,-14,-7,0,7,14,21].entries()){
  const shop=new T.Group();outside.add(shop);shop.position.set(x,0,29);shop.rotation.y=Math.PI;
  const height=6.1+i%3*.65;
  k.box(shop,[6.85,height,5],[0,height/2,0],i%2?brick:wall);
  for(const dx of [-2.05,0,2.05]){
   k.box(shop,[1.55,2.25,.06],[dx,1.2,2.54],dark);
   for(const y of [4.05,5.5])if(y<height-.5){
    k.box(shop,[1.4,.94,.05],[dx,y,2.54],glass);
    for(const sx of [-.71,.71])k.box(shop,[.035,1,.07],[dx+sx,y,2.6],edge);
    k.box(shop,[1.46,.045,.13],[dx,y-.49,2.6],edge);
   }
  }
  sign(shop,['골목상회','동네 찻집','안동 공예'][i%3],[0,2.85,2.58],4.8,'#e1d8c3',['#586963','#8c7663','#616c77'][i%3],.4);
  k.box(shop,[6.6,.12,1.05],[0,3.22,2.88],k.mat('#727e70',{roughness:.85}));
  k.box(shop,[7.05,.18,5.2],[0,height+.06,0],edge);
 }
 for(const x of [-6,6]){k.box(outside,[.045,3.8,.045],[x,1.9,13.2],edge);k.box(outside,[.58,.12,.27],[x,3.82,13.2],dark);}
 k.grove(outside,[-11,11,23].map((x,i)=>({x,z:24.8,height:5.5,seed:i+21})));
 batchScenery(outside,k);
 for(const x of [-2.7,2.7]){
  k.box(g,[.17,.027,34],[x,.024,-6],edge);
  const slots=Array.from({length:170},(_,i)=>({p:[x,.04,10-i*.2]}));k.instances(g,new T.BoxGeometry(.14,.006,.025),dark,slots);
  k.box(g,[.038,.008,34],[x-Math.sign(x)*.22,.017,-6],k.mat('#b3a163',{roughness:.96}));
 }
 // Green arcade steel, narrow translucent roof panels, gutters and exposed conduit.
 const frame=k.mat('#3e665d',{metalness:.46,roughness:.64}),roofMat=k.mat('#b8c5b5',{roughness:.75,side:T.DoubleSide});
 const archY=x=>4.55+1.03*Math.sqrt(Math.max(0,1-(x/3.24)**2));
 for(let z=-22;z<=10;z+=3.9){
  for(const x of [-3.1,3.1])k.box(g,[.12,4.7,.12],[x,2.35,z],frame);
  const points=Array.from({length:17},(_,i)=>{const x=-3.2+i*.4;return[x,archY(x)-.06,z];});k.tube(g,points,.036,frame);
  for(const side of [-1,1]){k.tube(g,[[side*3.08,3.9,z],[side*2.5,4.98,z]],.019,frame);}
 }
 for(let panel=0;panel<12;panel++){
  const x0=-3.24+panel*.54,geo=new T.PlaneGeometry(.535,34,4,1);geo.rotateX(-Math.PI/2);const a=geo.attributes.position;
  for(let i=0;i<a.count;i++)a.setY(i,archY(a.getX(i)+x0+.27));geo.computeVertexNormals();
  k.mesh(g,geo,panel===5||panel===6?k.mat('#718f94',{roughness:.64,side:T.DoubleSide}):roofMat,[x0+.27,0,-6]);
  k.box(g,[.026,.035,34],[x0,archY(x0)-.018,-6],frame);
 }
 for(const x of [-2.9,2.9]){k.box(g,[.14,.1,34],[x,4.39,-6],edge);k.tube(g,[[x,3.3,10],[x,3.32,-22]],.025,dark);}
 const lampMat=k.mat('#dddcd0',{emissive:'#fff3dc',emissiveIntensity:1.2});
 for(let z=-18;z<=8;z+=5.2){k.box(g,[1.14,.055,.16],[0,4.62,z],edge);k.box(g,[1.03,.025,.11],[0,4.58,z],lampMat);}
 const colors=['#6d302d','#2d514b','#c2b68d','#46515b','#7b5140','#706a52'];
 const names=['안동찜닭','골목찜닭','전통찜닭','시장찜닭','옛맛찜닭','한상찜닭'];
 for(const side of [-1,1])for(let i=0;i<8;i++){
  const shop=new T.Group();g.add(shop);shop.position.set(side*5.12,0,7-i*3.9);shop.rotation.y=side<0?Math.PI/2:-Math.PI/2;
  shop.name='market-store-'+side+'-'+i;
  const variant=(i+(side===1?2:0))%6,accent=colors[variant],front=1.95,signY=2.85+(i%3)*.08;
  // Actual recessed room, not an opaque box behind a transparent plane.
  k.box(shop,[3.88,.10,5],[0,.04,-.5],tile);k.box(shop,[3.88,.12,5],[0,2.58,-.5],wall);
  k.box(shop,[3.88,2.5,.15],[0,1.3,-3],wall);
  for(const x of [-1.92,1.92])k.box(shop,[.13,5,5],[x,2.5,-.5],wall);
  k.box(shop,[3.88,2.2,.26],[0,3.77,1.74],i%2?brick:wall);
  if(i===4&&side===1){k.box(shop,[1.4,1.18,.045],[.91,1.68,front+.03],steel);for(let y=1.12;y<2.24;y+=.075)k.box(shop,[1.39,.013,.018],[.91,y,front+.062],edge);}
  // Small restaurant furniture remains correctly sized against a 2.1 m door.
  for(const z of [-1.7,.25]){
   k.table(shop,[.1,0,z],1.15,.72,.74);k.chair(shop,[-.75,0,z],-Math.PI/2);k.chair(shop,[.95,0,z],Math.PI/2);
   k.box(shop,[.1,.14,.07],[.42,.85,z],accent);
  }
  k.box(shop,[2.7,.06,.3],[0,1.5,-2.86],edge);
  for(let n=0;n<9;n++)k.cyl(shop,.045,.046,.09,[-1.1+n*.25,1.58,-2.8],n%2?'#d2cbb8':'#888e82',16);
  k.box(shop,[1.35,.032,.12],[0,2.48,-.7],lampMat);
  // Sliding door is partly open; only the closed leaf carries glass.
  for(const x of [-1.78,-.18,1.78])k.box(shop,[.043,2.2,.075],[x,1.16,front],edge);
  for(const y of [.07,2.25])k.box(shop,[3.6,.045,.075],[0,y,front],edge);
  k.box(shop,[1.5,2.1,.012],[-.98,1.17,front-.01],glass);k.box(shop,[.025,.32,.055],[-.27,1.13,front+.03],steel);
  sign(shop,names[variant],[0,signY,front+.07],3.62,variant===2?'#413930':'#e4dbc6',accent,.68);
  sign(shop,'찜닭  ·  포장됩니다',[.2,2.31,front+.07],2.85,'#514b40','#beb99f',.18);
  // Shallow awning, stained edge and asymmetric upper windows / AC units.
  k.box(shop,[3.84,.085,.62],[0,signY+.44,2.14],steel);k.box(shop,[3.84,.055,.04],[0,signY+.38,2.45],edge);
  for(const x of [-1.12,.62]){
   k.box(shop,[1.1,.9,.035],[x,4.03,1.895],dark);
   for(const dx of [-.54,0,.54])k.box(shop,[.025,.91,.045],[x+dx,4.03,1.925],steel);
   k.box(shop,[1.1,.027,.045],[x,4.04,1.925],steel);
  }
  if(i%2===0){k.box(shop,[.66,.46,.29],[1.28,3.79,2.1],k.mat('#b8b6a8',{roughness:.86}));for(let n=0;n<8;n++)k.box(shop,[.58,.014,.02],[1.28,3.61+n*.044,2.255],edge);k.tube(shop,[[1.55,3.75,2.03],[1.78,3.7,2.02],[1.78,2.6,2.02]],.021,wall);}
  // Working stainless counter: thinner sheet edges, open lower shelf, burners and wok.
  const cx=i%2?-.42:.28,cz=2.23,cw=i%3===2?1.55:2.25;
  k.box(shop,[cw,.04,.73],[cx,.86,cz],steel);
  for(const dx of [-cw/2+.06,cw/2-.06])for(const dz of [-.29,.29])k.cyl(shop,.018,.018,.83,[cx+dx,.435,cz+dz],edge,12);
  k.box(shop,[cw-.05,.025,.58],[cx,.25,cz],steel);
  for(const dx of [-.38,.36]){
   k.cyl(shop,.22,.22,.035,[cx+dx,.9,cz],dark,32);
   k.bowl(shop,[cx+dx,.92,cz],.245,'#303633','#66432d');
   for(const h of [-1,1])k.tube(shop,[[cx+dx+h*.21,1.04,cz],[cx+dx+h*.29,1.06,cz],[cx+dx+h*.29,1.09,cz+.07],[cx+dx+h*.21,1.07,cz+.08]],.012,edge);
   k.cyl(shop,.16,.16,.013,[cx+dx,.28,cz],steel,32);
  }
  // Closer to the reference: broad low hood and round exhaust duct, not square chimneys.
  const hood=k.cyl(shop,.25,.57,.34,[cx,2.04,cz],steel,4);hood.rotation.y=Math.PI/4;hood.scale.set(1.45,1,.8);
  k.cyl(shop,.105,.105,.77,[cx,2.58,cz-.08],steel,24);k.cyl(shop,.117,.117,.035,[cx,2.3,cz-.08],edge,24);
  for(let n=0;n<3;n++){k.cyl(shop,.035,.036,.15,[cx+cw*.38,.96,cz-.22+n*.14],['#63442e','#bba884','#777d60'][n],16);}
  k.box(shop,[.27,.07,.2],[cx-.55,.91,cz+.09],'#b7ad90');
  if(i===1&&side===1&&k.food){const dish=k.food(shop,'jjimdak');dish.position.set(cx+.36,.945,cz);dish.scale.setScalar(.78);}
  if(i%3===0){for(let n=0;n<3;n++)k.cyl(shop,.14,.13,.04,[cx+.6,.94+n*.035,cz+.1],'#c6c1ad',28);}
  else {k.box(shop,[.44,.35,.45],[cx+.45,.45,cz],k.mat('#687663',{roughness:.94}));}
  if(i<3&&k.steam){for(let n=0;n<3;n++){const mist=k.steam(shop,[cx-.38,1.06,cz]);mist.userData.origin=[cx-.38,1.06,cz];mist.userData.phase=n*.31+i*.19;(r.refs.marketSteam??=[]).push(mist);}}
  // Folded cloth, takeaway bags and stacked trays supply familiar size cues.
  if(i%2===0){k.box(shop,[.26,.018,.19],[cx+.6,.89,cz-.12],tile);const bag=k.box(shop,[.2,.27,.13],[cx+.61,1.03,cz+.09],'#b4a986');bag.rotation.y=.15;for(const dx of [-.07,.07])k.tube(shop,[[cx+.61+dx,1.16,cz+.08],[cx+.61+dx,1.24,cz+.08]],.004,edge);}
  // Different service fronts break the repeated shop rhythm visible in early prototypes.
  if(i<4){
   if(variant%3===0){
    k.box(shop,[.68,1.64,.63],[1.31,.87,.65],steel);k.box(shop,[.55,1.28,.014],[1.31,1.01,.974],dark);
    for(let shelf=0;shelf<3;shelf++)for(let n=0;n<4;n++){k.cyl(shop,.039,.039,.19,[1.1+n*.14,.53+shelf*.38,.94],n%2?'#566747':'#bbac75',12);}
    k.box(shop,[.02,.63,.035],[1.57,.93,1.015],steel);
   }else if(variant%3===1){
    for(let n=0;n<3;n++){k.box(shop,[.5,.2,.4],[1.25,.14+n*.21,1.7],'#6a7560');for(let q=0;q<5;q++)k.box(shop,[.055,.012,.01],[1.07+q*.09,.18+n*.21,1.905],dark);}
    for(let n=0;n<6;n++)k.sphere(shop,[.065,.055,.059],[1.11+(n%3)*.12,.69,1.63+Math.floor(n/3)*.12],'#bcb47b');
   }else{
    const board=new T.Group();board.position.set(-1.27,.84,front+.14);board.rotation.y=.08;shop.add(board);
    k.box(board,[.55,.84,.032],[0,0,0],edge);sign(board,'오늘도 정성껏',[0,.27,.02],.46,'#d6d1b6','#34413c',.12);
    sign(board,'찜닭 · 당면',[0,.05,.02],.45,'#d6d1b6','#34413c',.13);sign(board,'포장 주문',[0,-.17,.02],.45,'#d6d1b6','#34413c',.12);
   }
   // Rolled bamboo shade, paper order slips and a hanging strainer near the cook.
   if(variant%2===0)for(let n=0;n<10;n++)k.box(shop,[1.26,.023,.022],[-.95,2.13-n*.031,front-.06],'#837b58');
   for(let n=0;n<3;n++){const slip=k.box(shop,[.09,.16,.002],[cx-.6+n*.13,1.48,front-.1],'#d8d3bc');slip.rotation.z=(n-1)*.08;}
  }
  // Hanging oval shop signs use subdued paint and slender iron brackets.
  if(i%2===0||side===-1){
   const hanging=new T.Group();shop.add(hanging);hanging.position.set(-1.38,3.52,2.5);hanging.rotation.y=side*Math.PI/2;
   const oval=k.cyl(hanging,.32,.32,.045,[0,0,0],steel,48);oval.rotation.x=Math.PI/2;oval.scale.y=1.24;
   sign(hanging,'안동찜닭',[0,.015,.03],.57,'#e2dfc6','#385f65',.37);
   k.tube(shop,[[-1.38,3.76,1.85],[-1.38,3.89,2.5],[-1.38,3.74,2.5]],.014,edge);
  }
  if(k.photo&&i%3===0){k.photo(shop,'market-sign',[1.34,1.38,front+.05],.49,.4);}
  if(i%2===0){sign(shop,'포장',[1.31,.85,front+.055],.45,'#463f36','#b9ac8f',.58);}
  // Dirty skirting, drain hose, service conduit, real seams rather than oversized bevels.
  k.box(shop,[3.7,.15,.08],[0,.15,front-.03],edge);k.tube(shop,[[1.7,.85,2],[1.69,.23,2.1],[1.5,.09,2.45]],.02,'#4a5148');
  batchScenery(shop,k);
  dressMarketShop(shop,k,{index:i,side,accent,front,cx,cz});
 }
 const front=new T.Group();g.add(front);front.position.set(0,0,-21.5);
 for(const x of [-2.15,2.15])k.box(front,[1.7,2.5,.15],[x,1.25,0],wall);
 k.box(front,[6,1.6,.15],[0,3.25,0],wall);k.box(front,[5,3,1],[0,1.5,-1.2],dark);
 const door=new T.Group();front.add(door);door.position.set(-1.3,0,.12);
 k.box(door,[2.6,2.5,.065],[1.3,1.25,0],k.mat('#344b43',{metalness:.16,roughness:.42}));
 k.box(door,[.035,.38,.05],[2.38,1.22,.06],steel);r.refs.entryDoor=door;spot(door,'restaurant:enter','식당으로 들어가기');
 for(const x of [-1.32,1.32])k.box(front,[.045,2.5,.1],[x,1.25,.18],steel);
 spot(sign(front,'이어드림 식당',[0,2.94,.18],4.2,'#e5ddc9','#3b5046',.63),'restaurant:enter','식당으로 들어가기');
 spot(sign(door,'식사 · 포장',[1.3,1.5,.065],1.5,'#cecbb8','#344b43',.27),'restaurant:enter','식당으로 들어가기');
 sign(g,'안동구시장  찜닭골목',[0,4.16,-5],3.5,'#d9ddc4','#3a5d52',.49);
 for(const x of [-1.65,1.65])k.tube(g,[[x,4.4,-5],[x,archY(x),-5]],.009,edge);
 for(const z of [6,-3,-12,-20]){const light=new T.PointLight('#e8ede0',8,10,2);light.position.set(0,4,z);g.add(light);}
 r.stations={entrance:{name:'이어드림 식당 앞',position:[0,1.7,-19.9],target:[0,1.7,-21.5]},exit:{name:'공방으로 가는 골목',position:[0,1.7,-17.8],target:[0,1.65,-8]}};
 // Keep the walking corridor clear; vendors are behind the cooking counters.
 for(const [x,z,rotation] of [[3.35,-.8,-Math.PI/2],[-3.35,-8.7,Math.PI/2]])r.refs.people.push(k.person(g,[x,0,z],{coat:x>0?'#b3b0a1':'#586253',rotation,apron:true,cooking:true}));
 // Customers remain inside the recessed rooms, leaving the walking lane clear.
 const diners=new T.Group();g.add(diners);
 for(const [x,z,rotation,coat] of [[5.9,3.4,-Math.PI/2,'#8d7964'],[-5.9,-4.4,Math.PI/2,'#78928d'],[5.9,-8.4,-Math.PI/2,'#ae9b8a']])k.person(diners,[x,0,z],{rotation,coat,seated:true});
 batchScenery(diners,k);
}
