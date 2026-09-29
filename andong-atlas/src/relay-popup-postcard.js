import * as T from 'three';
import {POPUP_BOOTHS} from './relay-popup-layout.js';
import {POPUP_STAMPS} from './relay-model.js';

export function postcardStampAt(u,v){
 if(!Number.isFinite(u)||!Number.isFinite(v))return null;
 return POPUP_STAMPS.find((_,i)=>Math.hypot((u-(.23+i*.27))*1.5,v-.48)<.17)||null;
}
export function drawPostcard(canvas,stamps=[]){
 const c=canvas.getContext('2d'),w=canvas.width,h=canvas.height;c.fillStyle='#eee5ce';c.fillRect(0,0,w,h);
 c.strokeStyle='#b7aa8b';c.lineWidth=2;c.strokeRect(20,20,w-40,h-40);c.fillStyle='#394d48';c.textAlign='center';c.font='500 34px Pretendard, sans-serif';c.fillText('달빛 아래, 안동',w/2,75);
 c.font='16px Pretendard, sans-serif';c.fillStyle='#756c5a';c.fillText('WOLYEONG · A NIGHT TO REMEMBER',w/2,h-44);
 for(const [i,id] of POPUP_STAMPS.entries()){
  const x=w*(.23+i*.27),y=h*.52,r=63;c.save();c.translate(x,y);c.strokeStyle=stamps.includes(id)?['#a16f36','#4c7972','#aa584c'][i]:'#9b8f74';c.fillStyle=c.strokeStyle;c.lineWidth=4;c.setLineDash(stamps.includes(id)?[]:[5,7]);c.beginPath();c.arc(0,0,r,0,Math.PI*2);c.stroke();c.setLineDash([]);
  if(stamps.includes(id)){
   if(id==='moon'){c.beginPath();c.arc(0,0,37,0,Math.PI*2);c.fill();c.fillStyle='#eee5ce';c.beginPath();c.arc(17,-12,31,0,Math.PI*2);c.fill();}
   if(id==='bridge'){c.strokeRect(-44,-6,88,10);for(let n=-40;n<=40;n+=16){c.beginPath();c.moveTo(n,-20);c.lineTo(n,23);c.stroke();}c.beginPath();c.moveTo(-44,-18);c.lineTo(44,-18);c.stroke();c.beginPath();c.moveTo(-20,-20);c.lineTo(0,-41);c.lineTo(20,-20);c.closePath();c.stroke();}
   if(id==='mask'){c.beginPath();c.ellipse(0,0,32,43,0,0,Math.PI*2);c.stroke();for(const x of [-13,13]){c.beginPath();c.ellipse(x,-7,8,3,0,0,Math.PI*2);c.fill();}c.beginPath();c.arc(0,8,18,.12,Math.PI-.12);c.stroke();}
  }else{c.font='18px Pretendard, sans-serif';c.textAlign='center';c.fillText(['달','다리','탈'][i],0,6);}
  c.restore();
 }
 return canvas;
}
export class PopupPostcard{
 constructor(scene,{stamps=[],onUpdate,resolve}){
  this.scene=scene;this.onUpdate=onUpdate;this.resolve=resolve;this.stamps=new Set(stamps);this.selected=POPUP_STAMPS.find(x=>!this.stamps.has(x))||'moon';this.closed=false;
  this.camera=scene.camera.position.clone();this.rotation=scene.camera.rotation.clone();this.rigVisible=scene.rig.visible;this.handVisible=scene.rightHand.visible;
  this.canvas=document.createElement('canvas');this.canvas.width=900;this.canvas.height=600;drawPostcard(this.canvas,[...this.stamps]);this.texture=new T.CanvasTexture(this.canvas);this.texture.colorSpace=T.SRGBColorSpace;
  this.geometry=new T.PlaneGeometry(.75,.5);this.material=new T.MeshBasicMaterial({map:this.texture,toneMapped:false});this.card=new T.Mesh(this.geometry,this.material);this.card.rotation.x=-Math.PI*.33;
  const b=POPUP_BOOTHS.find(x=>x.id==='print');this.card.position.set(b.x,1.17,b.z+1.13);scene.scene.add(this.card);
  scene.camera.position.set(b.x,1.62,b.z+2.2);scene.camera.lookAt(b.x,1.02,b.z+1.13);scene.keys.clear();scene.touchMove={forward:0,side:0};scene.rig.visible=true;scene.rightHand.visible=true;scene.popupBag.visible=false;this.update();
 }
 update(){this.onUpdate({progress:this.stamps.size/3,selected:this.selected,done:this.stamps.size===3,message:this.stamps.size===3?'내가 찍은 세 개의 도장이 엽서에 남았어요.':'도장을 고른 뒤 엽서의 같은 그림 자리를 눌러 찍으세요.'});}
 select(id){if(POPUP_STAMPS.includes(id)){this.selected=id;this.update();}}
 stamp(id){if(this.closed||id!==this.selected||this.stamps.has(id))return false;this.stamps.add(id);drawPostcard(this.canvas,[...this.stamps]);this.texture.needsUpdate=true;this.scene.audio.cue('dish');this.selected=POPUP_STAMPS.find(x=>!this.stamps.has(x))||id;this.update();return true;}
 pointerDown(e){const s=this.scene,r=s.renderer.domElement.getBoundingClientRect();s.ray.setFromCamera(new T.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),s.camera);const hit=s.ray.intersectObject(this.card)[0];if(hit?.uv){const local=s.camera.worldToLocal(hit.point.clone());s.rightHand.position.set(local.x,local.y+.08,local.z+.07);s.rightHand.rotation.set(0,0,0);this.stamp(postcardStampAt(hit.uv.x,hit.uv.y));}}
 assist(){this.stamp(this.selected);}
 pointerMove(){} pointerUp(){} cancelPointer(){} tick(){}
 finish(success){if(this.closed)return;this.closed=true;const result=success&&this.stamps.size===3?[...this.stamps]:null;this.card.removeFromParent();this.geometry.dispose();this.material.dispose();this.texture.dispose();this.scene.camera.position.copy(this.camera);this.scene.camera.rotation.copy(this.rotation);this.scene.workshop=null;this.scene.resetHands();this.scene.rig.visible=this.rigVisible;this.scene.rightHand.visible=this.handVisible;this.resolve(result);}
}
