import * as T from 'three';
import {poseHand} from './relay-hands.js';

export const MEAL_BITES = 3;
export const inBiteZone = (x,y,rect) => !!rect && rect.width>0 && rect.height>0 &&
 ((x-rect.left-rect.width/2)/(rect.width/2))**2+((y-rect.top-rect.height/2)/(rect.height/2))**2<=1;

// A bite counts only when a held, uneaten piece reaches the mouth guide.
export function mealInput(state,action){
 if(action.type==='grab')return state.eaten.length<MEAL_BITES&&state.held===null&&!state.eaten.includes(action.id)?{...state,held:action.id}:state;
 if(action.type==='release'&&state.held!==null)return {held:null,eaten:action.inside?[...state.eaten,state.held]:state.eaten};
 return state;
}

export class MealInteraction{
 constructor(scene,{onUpdate,dropBounds,resolve}){
  this.scene=scene;this.onUpdate=onUpdate;this.dropBounds=dropBounds;this.resolve=resolve;this.state={held:null,eaten:[]};this.closed=false;this.motion=null;this.target=new T.Vector3();
  this.food=scene.current.refs.food;this.targets=this.food.children.filter(o=>o.userData.edible);
  this.originals=new Map(this.targets.map(o=>[o,{parent:o.parent,position:o.position.clone(),rotation:o.rotation.clone(),scale:o.scale.clone(),visible:o.visible}]));
  this.camera=scene.camera.position.clone();this.rotation=scene.camera.rotation.clone();
  scene.keys.clear();scene.touchMove={forward:0,side:0};const [x,,z]=scene.current.refs.diningOrigin||[0,0,0];scene.camera.position.set(x,1.22,z+.86);scene.camera.lookAt(x,.87,z);
  scene.rig.visible=true;scene.leftHand.visible=false;scene.chopsticks.visible=true;scene.rightHand.visible=true;poseHand(scene.rightHand,'chopsticks');this.update();
 }
 restore(object){const v=this.originals.get(object);v.parent.add(object);object.position.copy(v.position);object.rotation.copy(v.rotation);object.scale.copy(v.scale);object.visible=v.visible;}
 pointerDown(e){
  if(this.motion||this.state.eaten.length===MEAL_BITES||this.state.held!==null)return;
  const s=this.scene,r=s.renderer.domElement.getBoundingClientRect();s.ray.setFromCamera(new T.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),s.camera);
  const hit=s.ray.intersectObjects(this.targets.filter(o=>o.visible),false)[0];if(!hit)return;
  this.pointerOrigin={x:e.clientX,y:e.clientY};this.grab(this.targets.indexOf(hit.object));this.pointerMove(e);
 }
 grab(id){
  if(this.motion||!this.targets[id])return;const next=mealInput(this.state,{type:'grab',id});if(next===this.state)return;
  this.scene.audio?.cue('dish');this.state=next;const object=this.targets[id];this.scene.camera.updateMatrixWorld();this.scene.camera.attach(object);this.target.copy(object.position);poseHand(this.scene.rightHand,'chopsticks');this.update();
 }
 pointerMove(e){
  if(this.motion||this.state.held===null)return;const s=this.scene,r=s.renderer.domElement.getBoundingClientRect(),depth=.7,h=Math.tan(T.MathUtils.degToRad(s.camera.fov/2))*depth;
  const p=new T.Vector3(((e.clientX-r.left)/r.width*2-1)*h*s.camera.aspect,-((e.clientY-r.top)/r.height*2-1)*h,-depth);
  this.target.copy(p);
  const inside=inBiteZone(e.clientX,e.clientY,this.dropBounds());if(inside!==this.inside){this.inside=inside;this.update();}
 }
 pointerUp(e){if(this.state.held===null)return;const moved=this.pointerOrigin&&Math.hypot(e.clientX-this.pointerOrigin.x,e.clientY-this.pointerOrigin.y)>=8;this.release(!!moved&&inBiteZone(e.clientX,e.clientY,this.dropBounds()));this.pointerOrigin=null;}
 release(inside){
  if(this.motion||this.state.held===null)return;
  const object=this.targets[this.state.held],original=this.originals.get(object);
  original.parent.updateMatrixWorld();const end=inside?new T.Vector3(.02,-.13,-.23):this.scene.camera.worldToLocal(original.parent.localToWorld(original.position.clone()));
  this.motion={inside,from:object.position.clone(),end,scale:object.scale.clone(),elapsed:0,duration:this.scene.reduced?.08:inside?.62:.4};
  this.inside=false;this.update(inside?'한 입을 가져오고 있어요.':'접시에 다시 놓고 있어요.');
 }
 tick(dt){
  if(this.state.held===null)return;const object=this.targets[this.state.held],m=this.motion;
  if(m){m.elapsed+=dt;const p=Math.min(1,m.elapsed/m.duration),ease=p*p*(3-2*p);object.position.lerpVectors(m.from,m.end,ease);object.position.y+=Math.sin(p*Math.PI)*.055;
   if(m.inside)object.scale.copy(m.scale).multiplyScalar(1-Math.max(0,(p-.75)/.25)*.8);
   if(p===1){this.restore(object);this.state=mealInput(this.state,{type:'release',inside:m.inside});if(m.inside)object.visible=false;this.motion=null;this.scene.resetHands();poseHand(this.scene.rightHand,'chopsticks');this.update(m.inside?'한 입을 맛봤어요.':'접시에 다시 놓았어요.');return;}
  }else object.position.lerp(this.target,1-Math.exp(-22*dt));
  const hand=this.scene.rightHand;hand.rotation.set(-.35,-.15,-.6);const tip=new T.Vector3(0,.34,0).applyEuler(hand.rotation);hand.position.copy(object.position).sub(tip);
  this.scene.chopsticks.children.forEach((stick,i)=>{if(stick===this.scene.bite)return;stick.rotation.z=(i===0?1:-1)*.045;});
 }
 // Keyboard and pointer share the same pickup, travel and swallow sequence.
 keyboardBite(){if(this.motion||this.state.held!==null||this.state.eaten.length===MEAL_BITES)return;const id=this.targets.findIndex((o,i)=>o.visible&&!this.state.eaten.includes(i));if(id<0)return;this.grab(id);this.release(true);}
 cancelPointer(){if(this.state.held!==null){this.restore(this.targets[this.state.held]);this.state=mealInput(this.state,{type:'release',inside:false});this.motion=null;this.inside=false;this.scene.resetHands();this.update();}}
 update(message=''){
  const count=this.state.eaten.length,done=count===MEAL_BITES;
  this.onUpdate({count,done,holding:this.state.held!==null,inside:!!this.inside,message:this.motion?(message||'한 입을 맛보는 중이에요.'):done?'세 입을 맛봤어요. 식사를 마치고 영수증을 챙기세요.':this.state.held!==null?'아래 입 모양 안내까지 끌어온 뒤 놓으세요.':message||'접시의 음식 조각을 집어 아래 입 모양 안내로 끌어오세요.'});
 }
 finish(ok){
  if(this.closed)return;this.closed=true;this.cancelPointer();for(const object of this.targets)this.restore(object);
  this.scene.camera.position.copy(this.camera);this.scene.camera.rotation.copy(this.rotation);this.scene.leftHand.visible=true;this.scene.resetHands();this.scene.meal=null;this.resolve(ok&&this.state.eaten.length===MEAL_BITES);
 }
}
