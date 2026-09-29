import * as T from 'three';
import {createWorkshopTask,workshopInput,pourInput,WORKSHOP_SEQUENCES,WORKSHOP_LABELS} from './relay-task-model.js';

export function workshopDropAccepted(position,destination,moved,hitVessel=false){
 return moved&&(hitVessel||Math.hypot(position.x-destination.x,position.z-destination.z)<=destination.r);
}

export class WorkshopInteraction{
 constructor(scene,{program,step,onUpdate,resolve}){
  this.scene=scene;this.refs=scene.current.refs;this.task=createWorkshopTask(program,step);this.onUpdate=onUpdate;this.resolve=resolve;this.drag=null;
  this.pouring=program==='tea'&&step>0;
  this.targets=(this.refs.workTargets||[]).filter(t=>program==='tea'?(this.pouring?t.id==='pour':t.id.startsWith('flower-')):WORKSHOP_SEQUENCES[step].includes(t.id));
  this.originals=new Map();for(const t of this.refs.workTargets||[])this.remember(t.object);
  for(const object of [this.refs.teapot,this.refs.kettle,this.refs.teaStream,this.refs.cupLiquid,this.refs.potLiquid,this.refs.flowers,this.refs.distill,this.refs.bottleLabel,this.refs.package])if(object)this.remember(object);
  this.camera=scene.camera.position.clone();this.rotation=scene.camera.rotation.clone();scene.camera.position.set(0,innerWidth<700?2.15:1.4,innerWidth<700?2.25:1.05);scene.camera.lookAt(0,.95,0);if(program==='soju'){scene.camera.position.set(0,2.7,3.2);scene.camera.lookAt(0,1.35,0);}scene.keys.clear();scene.touchMove={forward:0,side:0};
  if(program==='tea'&&step===1){this.targets=[{id:'pour',object:this.refs.kettle,label:'주전자'}];this.refs.kettle.visible=true;}
  if(program==='soju'&&step===2){this.refs.package.visible=true;this.refs.bottleLabel.visible=false;}
  this.update();
 }
 remember(object){if(!this.originals.has(object))this.originals.set(object,{position:object.position.clone(),rotation:object.rotation.clone(),scale:object.scale.clone(),visible:object.visible});}
 hit(e){const s=this.scene,r=s.renderer.domElement.getBoundingClientRect();s.ray.setFromCamera(new T.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),s.camera);const hits=s.ray.intersectObjects(this.targets.filter(t=>t.object.visible).map(t=>t.object),true);if(!hits.length)return null;let o=hits[0].object;while(o){const target=this.targets.find(t=>t.object===o);if(target)return target;o=o.parent;}return null;}
 pointerDown(e){if(this.task.done)return;const target=this.hit(e);if(!target)return;if(this.pouring){this.hold(true);return;}if(this.task.selected.includes(target.id))return;this.drag={target,x:e.clientX,y:e.clientY,moved:false};}
 dropTarget(id){if(id.startsWith('flower-'))return {x:this.refs.teapot.position.x,z:this.refs.teapot.position.z,y:this.refs.teapot.position.y+this.refs.teapot.scale.y*.57,object:this.refs.teapot,r:.42,name:'다관'};if(this.task.program==='soju'&&this.task.step===0)return {x:-.85,z:-.4,y:1.2,r:.38,name:'발효 항아리'};if(id==='label')return {x:.83,z:.2,y:1,r:.26,object:this.refs.bottle,name:'술병'};return null;}
 pointerMove(e){if(!this.drag||!this.dropTarget(this.drag.target.id))return;const d=this.drag,destination=this.dropTarget(d.target.id);d.moved ||= Math.hypot(e.clientX-d.x,e.clientY-d.y)>5;if(!d.moved)return;this.hit(e);const p=new T.Vector3();if(this.scene.ray.ray.intersectPlane(new T.Plane(new T.Vector3(0,1,0),-destination.y),p)){d.target.object.position.copy(p);this.scene.rightHand.position.copy(this.scene.camera.worldToLocal(p.clone())).add(new T.Vector3(.08,-.23,.07));}}
 pointerUp(){
  if(this.pouring){if(this.task.holding)this.hold(false);return;}const d=this.drag;this.drag=null;if(!d)return;
  const destination=this.dropTarget(d.target.id);if(destination){const hitVessel=destination.object&&this.scene.ray.intersectObject(destination.object,true).length>0,valid=workshopDropAccepted(d.target.object.position,destination,d.moved,hitVessel);
   d.target.object.position.copy(this.originals.get(d.target.object).position);this.scene.resetHands();if(!valid){this.task={...this.task,error:`${d.target.label||WORKSHOP_LABELS[d.target.id]}을 ${destination.name} 쪽으로 끌어 놓으세요.`};this.update();return;}}
  this.choose(d.target.id);
 }
 choose(id){
  const before=this.task;this.task=workshopInput(this.task,id);if(this.task.selected.length>before.selected.length){
   const target=this.targets.find(t=>t.id===id),count=this.task.selected.length;
   if(id.startsWith('flower-'))target.object.position.set(this.refs.teapot.position.x+(count-2)*.024,this.refs.teapot.position.y+this.refs.teapot.scale.y*.55,this.refs.teapot.position.z);
   if(this.task.program==='soju'){
    if(this.task.step===0&&target){target.object.position.set(-.85+(count-2)*.09,1.2,-.4);target.object.scale.setScalar(.6);}
    if(id==='still')this.refs.distill.visible=true;
    if(id==='collect')this.refs.distill.visible=false;
    if(id==='label'){this.refs.bottleLabel.visible=true;target.object.visible=false;}
    if(id==='package')this.refs.package.position.set(.83,.81,.2);
   }
  }this.update();
 }
 hold(value){this.task=pourInput(this.task,value?'start':'release');this.update();}
 tap(){this.task=pourInput(this.task,'tap');this.update();}
 reset(){this.task=pourInput(this.task,'reset');this.update();}
 tick(dt){if(!this.pouring||!this.task.holding)return;this.task=pourInput(this.task,'tick',dt);this.update();if(this.task.amount>=100)this.hold(false);}
 update(){
  const t=this.task;if(this.pouring){
   const source=t.step===1?this.refs.kettle:this.refs.teapot,origin=this.originals.get(source),liquid=t.step===1?this.refs.potLiquid:this.refs.cupLiquid;
   source.position.copy(origin.position);source.rotation.copy(origin.rotation);this.refs.teaStream.visible=t.holding;
   if(t.holding){source.rotation.z=t.step===1?.65:-.65;const spout=new T.Vector3(...(source.userData.spout||(t.step===1?[-.48,.52,0]:[.5,.48,0]))).multiply(source.scale).applyEuler(source.rotation);
    const end=liquid.position.clone(),start=end.clone().add(new T.Vector3(0,.28,0));source.position.copy(start).sub(spout);
    this.refs.teaStream.position.copy(start).add(end).multiplyScalar(.5);this.refs.teaStream.scale.set(1,start.distanceTo(end)/.34,1);this.refs.teaStream.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),start.clone().sub(end).normalize());
    this.scene.rightHand.position.copy(this.scene.camera.worldToLocal(source.position.clone())).add(new T.Vector3(.14,-.12,.04));
   }else this.scene.resetHands();
   liquid.visible=t.amount>0;liquid.scale.set(Math.max(.05,t.amount/100),1,Math.max(.05,t.amount/100));
  }
  const options=this.pouring?[]:this.targets.map(o=>({id:o.id,label:o.label||WORKSHOP_LABELS[o.id],disabled:t.selected.includes(o.id)}));
  this.onUpdate({done:t.done,progress:this.pouring?t.amount/100:t.selected.length/3,pouring:this.pouring,options,message:t.error||(t.done?'잘했어요. 완성한 모습을 보고 다음 단계로 이어가세요.':this.pouring?`현재 ${Math.round(t.amount)}% · 58–82% 사이에서 놓으세요.`:`${t.selected.length} / 3 완료 · ${t.program==='tea'?'꽃을 다관으로 끌어 담으세요.':t.step===0?'쌀 → 누룩 → 물을 발효 항아리로 끌어 담으세요.':t.step===2?'술병을 고르고, 표찰을 술병으로 끌어 붙인 뒤 포장하세요.':'발효 항아리 → 소주고리 → 받는 그릇을 선택하세요.'}`)});
 }
 cancelPointer(){if(this.drag){const obj=this.drag.target.object;obj.position.copy(this.originals.get(obj).position);this.drag=null;}if(this.pouring){this.task={...this.task,holding:false};this.update();}}
 finish(ok){this.cancelPointer();for(const [o,v] of this.originals){o.position.copy(v.position);o.rotation.copy(v.rotation);o.scale.copy(v.scale);o.visible=v.visible;}this.scene.camera.position.copy(this.camera);this.scene.camera.rotation.copy(this.rotation);this.scene.resetHands();this.scene.workshop=null;this.resolve(ok);}
}
