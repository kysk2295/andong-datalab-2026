import * as T from 'three';
import {createBusCabin, BUS_SEAT, BUS_AISLE_SEAT, BUS_ALIGHT_PATH} from './transit-cabin.js';
import {transitPerson,animateTransitPerson} from './transit-people.js';
import {createRiverWater} from './relay-water.js';

// An illustrative ride, with metre-scale street frontage and separate near/far scenery.
// This is not advertised as an actual scheduled bus or a surveyed street replica.
export function buildBusRide(k,options,route){
 const group=new T.Group(),cab=createBusCabin(),street=new T.Group(),walkers=[],refs={people:[],workTargets:[],busCabin:cab,city:street};
 group.add(street,cab.group);const b=cab.k,asphalt=k.mat('#535956',{roughness:.99}),curb=k.mat('#a5aaa1',{roughness:.9});
 k.box(street,[13,.16,440],[0,-.1,-130],asphalt);
 for(const side of [-1,1]){
  k.box(street,[4,.2,440],[side*8.5,.07,-130],k.paving);
  k.box(street,[.22,.25,440],[side*6.55,.07,-130],curb);
  for(const x of [side*3.3,side*6.1])for(let z=60;z>-330;z-=7)k.box(street,[.12,.012,3.4],[x,.006,z],x===side*3.3?'#d4c8a2':'#dbded1');
 }
 const signs=['안동 찻집','동네 책방','국화차 · 다과','공예 작업실','골목 식탁','따뜻한 빵'];
 for(let i=0;i<18;i++){
  const side=i%2?1:-1,z=32-Math.floor(i/2)*18,shop=new T.Group();shop.position.set(side*12.1,0,z);shop.rotation.y=side<0?Math.PI/2:-Math.PI/2;street.add(shop);
  const h=6.4+(i%3)*2.6;
  k.box(shop,[13.9,h,4.4],[0,h/2,0],i%3===0?k.brick:k.plaster);
  k.box(shop,[14.2,.2,4.7],[0,h,0],curb);k.box(shop,[13.9,.42,.1],[0,3.05,2.24],k.woodDark);
  for(let x=-5.6;x<6;x+=2.2){k.box(shop,[1.85,2.24,.06],[x,1.47,2.25],k.mat('#526361',{metalness:.28,roughness:.26}));k.box(shop,[.045,2.3,.1],[x,1.45,2.31],'#9ba4a1');k.box(shop,[1.85,.05,.1],[x,1.47,2.31],'#9ba4a1');}
  for(let y=4.5;y<h-.4;y+=2.6)for(let x=-5.5;x<6;x+=2.65){k.box(shop,[1.5,1.55,.04],[x,y,2.25],k.mat(i%3?'#687d80':'#9a9581',{metalness:.18,roughness:.4}));k.box(shop,[1.62,.08,.16],[x,y-.79,2.3],curb);}
  const awning=k.box(shop,[12.8,.12,1.2],[0,2.96,2.8],['#797f60','#80765d','#617d78'][i%3]);awning.rotation.x=.13;
  k.sign(shop,signs[i%6],[0,3.35,2.3],4,'#e0dfca','#3b4943',.42);
  for(const x of [-5,5]){k.box(shop,[.9,.64,.65],[x,.43,2.9],k.woodDark);}
 }
 // Pavement occupants travel with the street, always outside the carriageway.
 for(let i=0;i<14;i++){
  const p=transitPerson(b,{coat:['#857868','#62747c','#9c8b77','#6b7b64'][i%4],variant:i});p.position.set((i%2?1:-1)*(7.1+i%3*.52),.18,8-i*10.5);p.userData.origin=p.position.clone();p.rotation.y=i%2?0:Math.PI;street.add(p);walkers.push(p);
 }
 // Oncoming traffic passes on its own lane, away from the bus and pedestrians.
 const traffic=[];
 for(let i=0;i<3;i++){
  const car=new T.Group();car.position.set(-3.4,.04,-38-i*57);street.add(car);traffic.push(car);
  b.roundedBox(car,[1.8,.69,4.3],[0,.69,0],['#c7c9c1','#566970','#b4a795'][i],.2);b.roundedBox(car,[1.6,.58,2.25],[0,1.27,-.22],'#465b61',.15);
  for(const x of [-.9,.9])for(const z of [-1.35,1.35]){const wheel=b.cyl(car,.31,.31,.17,[x,.31,z],'#282e30');wheel.rotation.z=Math.PI/2;}
  for(const x of [-.62,.62])b.roundedBox(car,[.4,.12,.04],[x,.85,2.15],b.mat('#f2e5bb',{emissive:'#f2e5bb',emissiveIntensity:1}),.02);b.batch(car);car.userData.start=car.position.z;
 }
 const trees=[];
 for(let i=0;i<30;i++){const side=i%2?1:-1,z=26-i*10;trees.push({x:side*(9.5+i%3*.2),z,height:5.8+i%3*.6,seed:i+31});
  k.cyl(street,.055,.07,6.1,[side*6.9,3.2,z],k.mat('#545e5a',{metalness:.6}));k.tube(street,[[side*6.9,6.1,z],[side*6.9,6.45,z],[side*5.75,6.45,z]],.055,'#545e5a');k.box(street,[.55,.045,.26],[side*5.75,6.4,z],k.mat('#f1d9ac',{emissive:'#f1d9ac',emissiveIntensity:1.5}));
 }
 k.grove(street,trees);
 // The riverbank becomes visible beyond the shopfronts in the second half of the ride.
 const river=createRiverWater(85,380,[63,-.24,-145]);river.userData.keep=true;street.add(river);refs.water=river;
 k.box(street,[19,.16,200],[20,-.03,-212],k.forest);
 k.grove(street,Array.from({length:22},(_,i)=>({x:24+i%3*2,z:-115-i*9,height:7+i%4,seed:i+99})));
 const back=new T.Group();group.add(back);k.box(back,[400,.25,650],[0,-.35,-160],k.forest);
 for(let i=0;i<11;i++){const hill=k.sphere(back,[27+i%3*8,13+i%4*5,40],[i%2?94:-76,-4,30-i*45],'#526557');hill.castShadow=false;}
 const shelter=new T.Group();street.add(shelter);shelter.position.set(7.75,0,-252);
 for(const z of [-1.4,1.4])k.box(shelter,[.07,2.8,.07],[.7,1.4,z],curb);k.box(shelter,[2,.12,3.7],[0,2.81,0],k.woodDark);k.box(shelter,[.55,.1,2.8],[.5,.53,0],k.woodDark);
 const stopSign=k.sign(shelter,'월영교',[.73,2.3,0],1.6,'#efe9d7','#385b51',.32);stopSign.rotation.y=-Math.PI/2;
 // Static frontage is merged by material; animated people/water stay independent.
 for(const child of street.children)if(child.isGroup&&!child.userData.head&&child!==cab.group)b.batch(child);b.batch(street);b.batch(back);
 const map=new T.Group();map.position.set(80,0,0);group.add(map);map.visible=false;refs.routeMap=map;
 k.box(map,[28,.35,22],[0,-.2,0],'#36594b');const xs=route.map(c=>c[0]),ys=route.map(c=>c[1]);
 refs.routePoints=route.map(c=>new T.Vector3((c[0]-Math.min(...xs))/(Math.max(...xs)-Math.min(...xs))*22-11,.16,8-(c[1]-Math.min(...ys))/(Math.max(...ys)-Math.min(...ys))*16));
 refs.routeCurve=k.tube(map,refs.routePoints.map(p=>p.toArray()),.095,'#efcf88').geometry.parameters.path;
 refs.routeMarker=k.sphere(map,.33,refs.routePoints[0].clone().add(new T.Vector3(0,.5,0)).toArray(),'#f4b55c');
 for(const [i,name] of [[0,'원도심'],[route.length-1,'월영교']]){const p=refs.routePoints[i];k.label(map,name,[p.x,1,p.z],3,'#f4e2b4','#29483e',.5);}
 k.label(map,'이동 경로 · 체험용 개략도',[0,2,-10],14,'#e8d6ad','#28473b',.8);
 refs.tickBus=(time,progress,moving,reduced)=>{
  // Smooth departure/braking while keeping forward speed constant in the middle.
  const p=T.MathUtils.clamp(progress,0,1),distance=reduced?(p===1?260:0):260*(p*p*(3-2*p));street.position.z=distance;
  cab.update(time,{moving,doorOpen:p>.97?(p-.97)/.03:0,reduced});
  for(const person of walkers){animateTransitPerson(person,time,1,reduced);person.position.z=person.userData.origin.z+(reduced?0:Math.sin(time*.15+person.userData.variant)*2.8);}
  for(const car of traffic)car.position.z=car.userData.start+(reduced?0:progress*80);
 };
 return {group,refs,hotspots:[cab.stop],night:false,camera:[...BUS_SEAT],target:[-.22,1.6,-4.6],bounds:{x:[.3,.86],z:[1.8,2.04]},
  stations:{window:{name:'창가 좌석',position:[...BUS_SEAT],target:[4,1.65,-1]},aisle:{name:'통로 쪽 좌석',position:[...BUS_AISLE_SEAT],target:[0,1.6,-5]},alight:{name:'차량 출입문',position:[...BUS_ALIGHT_PATH.at(-1)],target:[3,1.7,-3.9],waypoints:BUS_ALIGHT_PATH}}};
}
