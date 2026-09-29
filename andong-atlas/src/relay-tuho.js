import * as T from 'three';

export const tuhoHit=(aim,target)=>Math.hypot(aim.x-target.x,aim.z-target.z)<=.16;

export class TuhoInteraction{
 constructor(scene,{onUpdate,resolve}){
  this.scene=scene;this.onUpdate=onUpdate;this.resolve=resolve;this.closed=false;this.flying=false;this.dragging=false;
  this.target=scene.current.refs.target.clone();this.aim=this.target.clone().add(new T.Vector3(.5,0,.35));
  this.camera=scene.camera.position.clone();this.rotation=scene.camera.rotation.clone();scene.camera.lookAt(this.target);scene.keys.clear();scene.touchMove={forward:0,side:0};
  this.bagVisible=scene.popupBag?.visible;if(scene.popupBag)scene.popupBag.visible=false;
  this.handVisible=scene.rightHand.visible;scene.rightHand.visible=true;scene.rig.visible=true;scene.current.refs.arrow.visible=true;scene.current.refs.arrow.position.copy(scene.camera.localToWorld(new T.Vector3(.18,-.12,-.55)));
  this.geometry=new T.RingGeometry(.08,.105,32);this.material=new T.MeshBasicMaterial({color:'#f0d289',side:T.DoubleSide,depthTest:false});this.marker=new T.Mesh(this.geometry,this.material);this.marker.rotation.x=-Math.PI/2;this.marker.renderOrder=3;scene.scene.add(this.marker);this.update();
 }
 update(){this.marker.position.copy(this.aim);this.marker.position.y+=.015;this.onUpdate({flying:this.flying,message:this.flying?'화살이 날아가고 있어요.':this.dragging?'입구에 조준한 뒤 놓아 던지세요.':'항아리 입구를 누른 채 조준하고, 놓아 던지세요. 금색 원이 도착 지점이에요.'});}
 pointerDown(e){if(this.flying)return;this.dragging=true;this.pointerMove(e);}
 pointerMove(e){
  if(!this.dragging||this.flying)return;const s=this.scene,r=s.renderer.domElement.getBoundingClientRect();s.ray.setFromCamera(new T.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),s.camera);
  const point=new T.Vector3();if(s.ray.ray.intersectPlane(new T.Plane(new T.Vector3(0,1,0),-this.target.y),point)){this.aim.set(T.MathUtils.clamp(point.x,this.target.x-1.2,this.target.x+1.2),this.target.y,T.MathUtils.clamp(point.z,this.target.z-1.2,this.target.z+1.2));}this.update();
 }
 pointerUp(e){if(!this.dragging||this.flying)return;this.pointerMove(e);this.dragging=false;this.throw();}
 shift(x,z){if(this.flying)return;this.aim.x=T.MathUtils.clamp(this.aim.x+x,this.target.x-1.2,this.target.x+1.2);this.aim.z=T.MathUtils.clamp(this.aim.z+z,this.target.z-1.2,this.target.z+1.2);this.update();}
 async throw(){if(this.flying||this.closed)return;this.flying=true;this.update();const hit=tuhoHit(this.aim,this.target),end=this.aim.toArray();const ok=await this.scene.act('game',{hit,end});if(!this.closed)this.finish(ok?{hit}:null);}
 cancelPointer(){this.dragging=false;}
 finish(result){if(this.closed)return;this.closed=true;this.scene.cancelAction();this.marker.removeFromParent();this.geometry.dispose();this.material.dispose();this.scene.current.refs.arrow.visible=false;this.scene.camera.position.copy(this.camera);this.scene.camera.rotation.copy(this.rotation);this.scene.rightHand.visible=this.handVisible;if(this.scene.popupBag)this.scene.popupBag.visible=this.bagVisible;this.scene.tuho=null;this.resolve(result);}
}
