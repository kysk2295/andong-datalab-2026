import * as T from 'three';

// Wrist-local finger joints let the same hand hold chopsticks, a card and paper.
export function createVisitorHand(parent,side,k){
 const hand=new T.Group();parent.add(hand);const skin=k.skin||k.mat('#c69980',{roughness:.73});
 const sleeve=k.mesh(hand,new T.CapsuleGeometry(.058,.27,8,18),k.fabric||k.mat('#b4b6ad'));
 hand.userData.sleeve=sleeve;
 sleeve.rotation.x=-.65;sleeve.position.set(0,-.18,.1);
 const palm=k.mesh(hand,new T.SphereGeometry(1,40,28),skin,[0,.035,0]);palm.scale.set(.05,.079,.027);
 k.sphere(hand,[.034,.034,.026],[side*.023,.017,.006],skin);
 const fingers=[];
 for(let i=0;i<4;i++){
  const joint=new T.Group();hand.add(joint);joint.position.set((i-1.5)*.023,.098,0);joint.rotation.z=(1.5-i)*.055;
  const length=[.041,.048,.044,.033][i];k.mesh(joint,new T.CapsuleGeometry(.011,length,8,16),skin,[0,length/2,0]);
  const tip=new T.Group();joint.add(tip);tip.position.y=length+.01;k.mesh(tip,new T.CapsuleGeometry(.0105,length*.65,6,12),skin,[0,length*.32,0]);
  k.sphere(tip,[.007,.013,.0018],[0,length*.4,-.0105],k.mat('#c99d87',{roughness:.35}));
  fingers.push({joint,tip});
 }
 const thumb=new T.Group();hand.add(thumb);thumb.position.set(side*.045,.019,.008);thumb.rotation.z=-side*.65;
 k.mesh(thumb,new T.CapsuleGeometry(.015,.045,8,16),skin,[0,.03,0]);
 hand.userData.joints={fingers,thumb,side};poseHand(hand,'relaxed');return hand;
}
export function poseHand(hand,pose='relaxed',amount=1){
 const joints=hand.userData.joints;if(!joints)return;
 const curls=pose==='chopsticks'?[.8,1,1.25,1.35]:pose==='pinch'?[.6,.85,1.1,1.25]:[.17,.22,.27,.32];
 joints.fingers.forEach(({joint,tip},i)=>{joint.rotation.x=curls[i]*amount;tip.rotation.x=(pose==='relaxed'?.18:.85)*amount;});
 joints.thumb.rotation.x=(pose==='relaxed'?.15:.8)*amount;
 joints.thumb.rotation.z=-joints.side*(pose==='relaxed'?.65:1.1);
}
