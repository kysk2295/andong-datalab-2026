import * as T from 'three';

// A second camera renders the sample receipt onto the held phone, entirely locally.
export class ReceiptScan{
 constructor(scene,{onUpdate,resolve}){
  this.scene=scene;this.onUpdate=onUpdate;this.resolve=resolve;this.offset={x:.19,y:.08};this.steady=0;this.done=false;this.drag=null;
  this.target=new T.WebGLRenderTarget(256,384,{depthBuffer:true});this.camera=new T.PerspectiveCamera(52,2/3,.02,80);
  this.screen=new T.Mesh(new T.PlaneGeometry(.157,.244),new T.MeshBasicMaterial({map:this.target.texture,toneMapped:false}));this.screen.position.set(0,.13,-.019);scene.phone.add(this.screen);
  this.paper=scene.receipt.clone(true);this.paper.matrixAutoUpdate=false;scene.scene.add(this.paper);this.paper.visible=false;
  this.phoneZ=scene.phone.position.z;this.receiptZ=scene.receipt.position.z;scene.phone.position.z=.1;scene.receipt.position.z=.085;
  this.before={left:scene.leftHand.position.clone(),right:scene.rightHand.position.clone(),lr:scene.leftHand.rotation.clone(),rr:scene.rightHand.rotation.clone()};
  scene.keys.clear();scene.rig.visible=true;scene.phone.visible=true;scene.receipt.visible=true;
  scene.leftHand.position.set(innerWidth<700?-.015:-.1,innerWidth<700?-.03:-.24,innerWidth<700?-.72:-.49);scene.leftHand.rotation.set(0,0,0);scene.rightHand.rotation.set(0,0,0);
  this.update();
 }
 pointerDown(e){this.drag={x:e.clientX,y:e.clientY};}
 pointerMove(e){if(!this.drag||this.done)return;this.shift((e.clientX-this.drag.x)*.0007,-(e.clientY-this.drag.y)*.0007);this.drag={x:e.clientX,y:e.clientY};}
 pointerUp(){this.drag=null;}
 shift(x,y){if(this.done)return;this.offset.x=T.MathUtils.clamp(this.offset.x+x,-.25,.3);this.offset.y=T.MathUtils.clamp(this.offset.y+y,-.18,.2);this.steady=0;this.update();}
 align(){this.offset={x:0,y:0};this.steady=0;this.update();}
 update(){const {x,y}=this.offset;this.scene.rightHand.position.set(x,y-.18,-1.05);const aligned=Math.abs(x)<.035&&Math.abs(y)<.04;this.onUpdate({done:this.done,progress:Math.min(1,this.steady/1.1),aligned,message:this.done?'QR을 확인했어요. 할인권을 받아 다음 체험으로 이어가세요.':aligned?'잘 맞았어요. 잠시 그대로 잡고 있어주세요.':'영수증을 끌어 휴대폰 화면 안에 맞춰주세요.'});}
 tick(dt){
  if(!this.done){if(Math.abs(this.offset.x)<.035&&Math.abs(this.offset.y)<.04)this.steady+=dt;else this.steady=0;if(this.steady>=1.1)this.done=true;this.update();}
  const s=this.scene;s.scene.updateMatrixWorld(true);this.paper.matrix.copy(s.receipt.matrixWorld);this.paper.visible=true;
  this.camera.position.copy(s.camera.localToWorld(new T.Vector3(0,-.045,-.52)));this.camera.quaternion.copy(s.camera.getWorldQuaternion(new T.Quaternion()));
  const rigVisible=s.rig.visible;s.rig.visible=false;const old=s.renderer.getRenderTarget();s.renderer.setRenderTarget(this.target);s.renderer.render(s.scene,this.camera);s.renderer.setRenderTarget(old);s.rig.visible=rigVisible;this.paper.visible=false;
 }
 finish(ok){const s=this.scene;s.phone.remove(this.screen);s.scene.remove(this.paper);this.screen.geometry.dispose();this.screen.material.dispose();this.target.dispose();s.phone.position.z=this.phoneZ;s.receipt.position.z=this.receiptZ;s.scanner=null;s.resetHands();s.syncHands();this.resolve(ok);}
}
