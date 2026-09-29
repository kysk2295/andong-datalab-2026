import {createTransitKit} from './transit-cabin.js';
import {transitPerson,animateTransitPerson} from './transit-people.js';

// Metres, with the centre of each circulation route left free. Raised decks retain
// their own foot height during animation; decorative people never move the camera.
export const SCENE_VISITORS={
 market:[
  {p:[-1.65,0,1.5],walk:2.1,phase:0},
  {p:[1.65,0,-5],walk:2.2,phase:2},
  {p:[-1.55,0,-12],walk:1.8,phase:4},
  {p:[1.65,0,-15.8],rotation:-1.1},
 ],
 meal:[
  {p:[3,0,-.64],rotation:Math.PI,seated:true,activity:'eat'},
  {p:[3,0,-2.56],seated:true,activity:'eat'},
 ],
 workshop:[
  {p:[-3.1,.038,-.75],rotation:Math.PI,seated:true,activity:'craft'},
  {p:[3.1,.038,-.75],rotation:Math.PI,seated:true,activity:'craft'},
 ],
 bridge:[
  {p:[1.24,.305,4.6],rotation:Math.PI/2},
  {p:[-1.24,.305,8],walk:1.8,phase:2},
 ],
 popup:[
  {p:[-16.5,0,11.85],rotation:Math.PI,seated:true,activity:'eat'},
  {p:[-15.6,0,10.15],seated:true,activity:'eat'},
  {p:[-21.7,0,16.85],rotation:Math.PI,seated:true,activity:'eat'},
  {p:[13,0,-1.15],rotation:Math.PI,seated:true,activity:'eat'},
  {p:[-4,0,8],walk:2.1,phase:0},
  {p:[7,0,7],walk:2.1,phase:2},
  {p:[-12,0,-18],walk:2.1,axis:'x',phase:4},
 ],
 'link-workshop':[{p:[-1.2,0,4.5],rotation:1.1},{p:[4.35,0,-5],walk:1.4,phase:1}],
 'link-pickup':[{p:[-.85,0,-2.4],seated:true},{p:[1.3,0,2.7],rotation:1.2}],
 'link-arrival':[{p:[-1.45,0,-3],walk:1.6,phase:1},{p:[2.4,0,-6],rotation:-1.1}],
 'link-riverside':[{p:[-1.3,0,-3],walk:1.6,phase:1},{p:[4.5,0,-4.8],rotation:-.7},{p:[3.9,0,-5.1],rotation:.8}],
};

export function addSceneLife(scene,id,{textures=true}={}){
 const specs=SCENE_VISITORS[id];if(!specs)return;
 const kit=createTransitKit({textures}),palette=['#8c7765','#768d8c','#b0a48f','#626f82'];
 const people=specs.map((spec,i)=>{
  const p=transitPerson(kit,{...spec,coat:palette[i%palette.length],variant:i+1});
  p.position.fromArray(spec.p);p.rotation.y=spec.rotation||0;
  p.name=`${id}-visitor-${i}`;scene.group.add(p);return p;
 });
 const life={people,specs,update(time,reduced=false){
  people.forEach((p,i)=>{
   const spec=specs[i],phase=spec.phase??i,t=time*.32+phase;
   animateTransitPerson(p,time,spec.walk&&!reduced?Math.abs(Math.cos(t))*.75:0,reduced);
   if(spec.walk){
    const offset=reduced?0:Math.sin(t)*spec.walk;
    p.position.set(spec.p[0]+(spec.axis==='x'?offset:0),spec.p[1],spec.p[2]+(spec.axis==='x'?0:offset));
    p.rotation.y=reduced?(spec.rotation||0):(spec.axis==='x'?Math.PI/2:0)+(Math.cos(t)>=0?0:Math.PI);
   }
   if(spec.activity){
    p.userData.head.rotation.x=.16;
    p.userData.arms.forEach((arm,j)=>{arm.rotation.x=reduced?0:Math.sin(time*1.5+i+j*1.8)*.045;});
   }
  });
 },dispose:()=>kit.dispose()};
 scene.refs.life=life;life.update(0);return life;
}
