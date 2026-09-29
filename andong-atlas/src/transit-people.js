import * as T from 'three';

// Metre-sized occupants. The seated pelvis, knees and feet remain on the seat/floor.
// Small articulated groups let the passengers look out without animating each mesh.
export function transitPerson(k, {seated=false, driver=false, coat='#66766c', skin='#c69779', hair='#302b28', variant=0, activity='rest'}={}) {
 const root=new T.Group(),body=new T.Group();root.add(body);
 const cloth=k.mat(coat,{roughness:.94}),skinMat=k.mat(skin,{roughness:.7}),dark=k.mat('#30363c',{roughness:.94}),hairMat=k.mat(hair,{roughness:.86});
 const hip=seated?.53:.91,shoulder=hip+.47;
 const segment=(parent,a,b,r1,r2,material)=>{const v=new T.Vector3(...b).sub(new T.Vector3(...a));const m=k.cyl(parent,r2,r1,v.length(),new T.Vector3(...a).addScaledVector(v,.5).toArray(),material,12);m.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),v.normalize());return m;};
 const torso=k.mesh(body,new T.LatheGeometry([[.135,hip-.07],[.165,hip+.05],[.155,hip+.22],[.205,shoulder-.025],[.18,shoulder+.06],[.068,shoulder+.105]].map(p=>new T.Vector2(...p)),24),cloth);torso.scale.z=.67;
 k.sphere(body,[.16,.085,.105],[0,hip,0],dark);
 const legs=[];
 for(const side of [-1,1]){
  const leg=new T.Group();body.add(leg);legs.push(leg);leg.position.set(side*.095,hip,0);
  const knee=seated?[side*.015,-.05,.37]:[side*.012,-.44,.02],ankle=seated?[side*.015,-hip+.095,.39]:[side*.012,-hip+.095,.018];
  segment(leg,[0,0,0],knee,.085,.069,dark);k.sphere(leg,[.071,.075,.073],knee,dark);segment(leg,knee,ankle,.065,.046,dark);
  k.roundedBox(leg,[.135,.085,.27],[ankle[0],ankle[1]-.045,ankle[2]+.052],'#272b2c',.035);
  k.roundedBox(leg,[.14,.018,.275],[ankle[0],ankle[1]-.086,ankle[2]+.052],'#b6b5aa',.007);
 }
 const arms=[];
 for(const side of [-1,1]){
  const arm=new T.Group();arm.position.set(side*.205,shoulder,0);body.add(arm);arms.push(arm);
  const working=seated&&activity!=='rest';
  const elbow=[side*.035,working?-.2:-.25,seated?.14:.02],wrist=working?[side*-.035,-.15,.46]:driver?[side*.02,-.26,.43]:seated?[side*-.035,-.37,.28]:[side*.035,-.49,.055];
  segment(arm,[0,0,0],elbow,.068,.051,cloth);k.sphere(arm,.053,elbow,cloth);segment(arm,elbow,wrist,.053,.037,cloth);
  k.sphere(arm,[.044,.025,.066],[wrist[0],wrist[1]-.012,wrist[2]+.03],skinMat);
  if(working&&side===1){const z=wrist[2]+.06,y=wrist[1];for(const x of activity==='eat'?[-.012,.012]:[0])k.tube(arm,[[wrist[0]+x,y+.035,z-.05],[wrist[0]+x,y-.1,z+.16]],.0035,activity==='eat'?'#ac9b77':'#624b32');}
  for(let f=0;f<4;f++)k.sphere(arm,[.008,.011,.032],[wrist[0]-.026+f*.016,wrist[1]-.013,wrist[2]+.083],skinMat);
 }
 const head=new T.Group();head.position.set(0,shoulder+.23,0);body.add(head);
 k.cyl(body,.048,.056,.12,[0,shoulder+.12,0],skinMat,16);
 k.sphere(head,[.092,.127,.087],[0,0,.004],skinMat);
 const cap=k.mesh(head,new T.SphereGeometry(1,24,14,0,Math.PI*2,0,Math.PI*.55),hairMat,[0,.021,-.006]);cap.scale.set(.096,.115,.09);cap.rotation.x=-.1;
 if(variant%3===1){k.sphere(head,[.098,.09,.06],[0,-.012,-.055],hairMat);k.sphere(head,[.044,.052,.042],[0,-.07,-.096],hairMat);}
 for(const s of [-1,1]){
  k.sphere(head,[.012,.021,.013],[s*.092,-.008,0],skinMat);
  k.sphere(head,[.016,.007,.006],[s*.032,.017,.083],'#ded5c9');k.sphere(head,[.006,.006,.004],[s*.033,.016,.089],'#352e28');
  k.tube(head,[[s*.019,.038,.082],[s*.039,.04,.081],[s*.05,.035,.075]],.003,hairMat);
 }
 k.sphere(head,[.012,.023,.021],[0,-.01,.092],skinMat);k.tube(head,[[-.024,-.05,.077],[0,-.053,.084],[.024,-.05,.077]],.0025,'#835347');
 if(variant%4===2)for(const s of [-1,1]){const ring=k.mesh(head,new T.TorusGeometry(.021,.002,6,18),k.mat('#53504a',{metalness:.6}),[s*.031,.017,.096]);ring.scale.y=.7;}
 for(const s of [-1,1]){const collar=k.roundedBox(body,[.055,.082,.014],[s*.04,shoulder+.055,.078],cloth,.006);collar.rotation.z=s*-.3;}
 for(let i=0;i<4;i++)k.sphere(body,.004,[0,shoulder-.02-i*.086,.113],'#c9ccc1');
 if(seated&&!driver&&activity==='rest'&&variant%2===0){const bag=k.roundedBox(body,[.31,.17,.23],[0,hip+.16,.25],k.mat('#af9877',{roughness:1}),.035);k.tube(body,[[-.09,hip+.22,.25],[-.08,hip+.36,.25],[.08,hip+.36,.25],[.09,hip+.22,.25]],.012,'#826b50');bag.rotation.x=-.12;}
 root.userData={head,torso,arms,legs,seated,driver,variant,activity};
 // Batch the parts that move together. Six occupants stay inexpensive on phones.
 for(const limb of [...arms,...legs,head])k.batch(limb);k.batch(body);
 return root;
}

export function animateTransitPerson(person,time,moving=0,reduced=false){
 const {head,torso,arms,legs,seated,driver,variant}=person.userData,t=reduced?0:time;
 head.rotation.y=reduced?0:Math.sin(t*.32+variant*1.8)*(driver?.025:.16);
 head.rotation.x=driver?.035:Math.sin(t*.23+variant)*.025;
 // Root sway is relative to a stable position and never accumulates.
 person.rotation.z=reduced?0:Math.sin(t*1.3+variant)*.006*moving;
 if(!seated)for(let i=0;i<2;i++){const swing=reduced?0:Math.sin(t*4+i*Math.PI+variant)*.2*moving;legs[i].rotation.x=swing;arms[i].rotation.x=-swing*.65;}
}
