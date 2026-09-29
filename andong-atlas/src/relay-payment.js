import * as T from 'three';
import {poseHand} from './relay-hands.js';

export const paymentInZone=(point,target)=>Math.hypot(point.x-target.x,point.y-target.y)<=.115;
const smooth=t=>t*t*(3-2*t);
export function drawReceipt(ctx,w,h,meal,method){const text=(ctx,line,x,y,size=32,color='#234b3c')=>{ctx.fillStyle=color;ctx.font=`600 ${size}px Pretendard, sans-serif`;ctx.textAlign='center';ctx.fillText(line,x,y);};ctx.fillStyle='#fff8df';ctx.fillRect(0,0,w,h);text(ctx,'이어드림 시연 영수증',w/2,80,31);text(ctx,'ED-DEMO-001',w/2,134,23);ctx.strokeStyle='#9aa58b';ctx.setLineDash([8,6]);ctx.beginPath();ctx.moveTo(35,171);ctx.lineTo(w-35,171);ctx.stroke();text(ctx,meal.name,w/2,239,36);text(ctx,meal.examplePrice.toLocaleString('ko-KR')+'원',w/2,306,42);text(ctx,method==='cash'?'현금 · 시연':'카드 · 시연',w/2,357,26);text(ctx,'다음은 전통 체험',w/2,440,29);text(ctx,'QR 인증 → 10% 할인',w/2,490,32);for(let y=0;y<13;y++)for(let x=0;x<13;x++)if((x*7+y*3+x*y)%5<2){ctx.fillStyle='#234b3c';ctx.fillRect(165+x*14,536+y*14,12,12);}text(ctx,'샘플 QR · 실제 결제 없음',w/2,h-65,23);}
export function createReceiptSlip(meal,method){
 const canvas=document.createElement('canvas');canvas.width=512;canvas.height=942;drawReceipt(canvas.getContext('2d'),512,942,meal,method);
 const tx=new T.CanvasTexture(canvas);tx.colorSpace=T.SRGBColorSpace;const mesh=new T.Mesh(new T.PlaneGeometry(.21,.386),new T.MeshBasicMaterial({map:tx,side:T.DoubleSide,toneMapped:false}));
 return {mesh,dispose(){mesh.removeFromParent();mesh.geometry.dispose();mesh.material.dispose();tx.dispose();}};
}
export function createPaymentProps(parent,{meal,method}){
 const root=new T.Group();parent.add(root);const owned=[];
 const mesh=(geometry,material,p)=>{owned.push(geometry,material);const o=new T.Mesh(geometry,material);o.position.set(...p);root.add(o);return o;};
 const box=(size,p,color)=>mesh(new T.BoxGeometry(...size),new T.MeshStandardMaterial({color,roughness:.6}),p);
 function surface(w,h,p,draw){const canvas=document.createElement('canvas');canvas.width=512;canvas.height=Math.round(512*h/w);const ctx=canvas.getContext('2d');draw(ctx,canvas.width,canvas.height);const tx=new T.CanvasTexture(canvas);tx.colorSpace=T.SRGBColorSpace;owned.push(tx);const o=mesh(new T.PlaneGeometry(w,h),new T.MeshBasicMaterial({map:tx,side:T.DoubleSide,toneMapped:false}),p);return {object:o,ctx,canvas,tx};}
 const text=(ctx,line,x,y,size=32,color='#234b3c')=>{ctx.fillStyle=color;ctx.font=`600 ${size}px Pretendard, sans-serif`;ctx.textAlign='center';ctx.fillText(line,x,y);};
 box([.35,.08,.34],[0,1.18,.06],'#34483e');box([.32,.34,.075],[0,1.37,.13],'#233b33');
 const screen=surface(.28,.24,[0,1.4,.171],()=>{});
 const screenText=phase=>{const {ctx,canvas,tx}=screen;ctx.fillStyle='#e4efda';ctx.fillRect(0,0,canvas.width,canvas.height);text(ctx,'이어드림 · 계산 시연',256,64,29);text(ctx,meal.examplePrice.toLocaleString('ko-KR')+'원',256,155,58);text(ctx,phase,256,240,33);text(ctx,'실제 청구 없음',256,315,25,'#687d66');tx.needsUpdate=true;};
 const target=new T.Vector3(0,1.4,.3);
 const ring=mesh(new T.RingGeometry(.085,.093,44),new T.MeshBasicMaterial({color:'#e7bb61',side:T.DoubleSide}),[0,1.39,.178]);
 box([.29,.13,.3],[.33,1.2,-.07],'#334339');box([.23,.013,.022],[.33,1.272,.065],'#101e18');
 const card=surface(method==='cash'?.29:.24,.15,[-.31,1.25,.38],(ctx,w,h)=>{ctx.fillStyle=method==='cash'?'#9eaf86':'#365b4b';ctx.fillRect(0,0,w,h);ctx.strokeStyle='#d6c98d';ctx.strokeRect(14,14,w-28,h-28);text(ctx,method==='cash'?'시연용 현금':'EODREAM',w/2,90,39,'#eee1b7');text(ctx,'DEMO · 실제 사용 불가',w/2,h-37,22,'#e2dbbc');if(method==='card'){ctx.fillStyle='#cbb477';ctx.fillRect(42,133,60,43);}}).object;
 const receipt=surface(.25,.46,[.33,1.51,.068],(ctx,w,h)=>drawReceipt(ctx,w,h,meal,method)).object;receipt.visible=false;
 return {root,card,receipt,ring,target,screenText,dispose(){root.removeFromParent();for(const item of owned)item.dispose();}};
}

export class PaymentInteraction{
 constructor(scene,{meal,method,onUpdate,resolve,propsFactory=createPaymentProps}){
  this.scene=scene;this.onUpdate=onUpdate;this.resolve=resolve;this.method=method;this.phase='ready';this.elapsed=0;this.closed=false;this.dragging=false;
  this.camera=scene.camera.position.clone();this.rotation=scene.camera.rotation.clone();this.props=propsFactory(scene.current.refs.counter,{meal,method});
  this.originalTerminal=scene.current.refs.terminal;this.originalPaper=scene.current.refs.counterPaper;this.terminalWasVisible=this.originalTerminal.visible;this.paperWasVisible=this.originalPaper.visible;this.originalTerminal.visible=false;this.originalPaper.visible=false;
  scene.keys.clear();scene.touchMove={forward:0,side:0};this.fitCamera();
  scene.rig.visible=true;scene.leftHand.visible=false;scene.rightHand.visible=false;scene.chopsticks.visible=false;scene.receipt.visible=false;scene.phone.visible=false;
  this.start=this.props.card.position.clone();this.target=this.start.clone();this.props.screenText(method==='cash'?'현금을 건네주세요':'카드를 대주세요');this.update();
 }
 fitCamera(){const camera=this.scene.camera,scale=camera.aspect<.85?.78:1;this.props.root.scale.setScalar(scale);this.props.root.position.y=1.15*(1-scale);camera.position.set(3.1,1.66,4.08);camera.lookAt(3.1,1.35,2.65);camera.updateMatrixWorld();if(this.phase==='held')this.props.receipt.scale.setScalar(scale);}
 receiptEnd(){return this.scene.camera.aspect<.85?new T.Vector3(0,.07,-.86):new T.Vector3(.04,-.04,-.72);}
 update(message){this.onUpdate({phase:this.phase,done:this.phase==='held',progress:({ready:0,approving:.25,printing:.5,receipt:.75,taking:.85,held:1})[this.phase],message:message||({ready:this.method==='cash'?'왼쪽 시연용 현금을 단말기 앞 금색 원으로 건네세요.':'왼쪽 카드를 집어 단말기의 금색 원까지 끌어다 놓으세요.',approving:'단말기에서 결제를 확인하고 있어요. (시연)',printing:'영수증이 출력되고 있어요.',receipt:'출력된 영수증을 눌러 직접 받아보세요.',taking:'영수증을 손으로 가져오고 있어요.',held:'한 끼의 영수증을 받았어요. 챙긴 뒤 QR로 다음 체험 혜택을 받으세요.'})[this.phase]});}
 hit(e,object){const s=this.scene,r=s.renderer.domElement.getBoundingClientRect();s.ray.setFromCamera(new T.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),s.camera);return s.ray.intersectObject(object,false).length>0;}
 pointerDown(e){if(this.phase==='receipt'&&this.hit(e,this.props.receipt)){this.takeReceipt();return;}if(this.phase!=='ready'||!this.hit(e,this.props.card))return;this.dragging=true;this.scene.rightHand.visible=true;poseHand(this.scene.rightHand,'pinch');this.pointerMove(e);}
 pointerMove(e){if(!this.dragging)return;const s=this.scene,r=s.renderer.domElement.getBoundingClientRect();s.ray.setFromCamera(new T.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),s.camera);
  const planePoint=this.props.root.localToWorld(new T.Vector3(0,0,.3)),point=s.ray.ray.intersectPlane(new T.Plane(new T.Vector3(0,0,1),-planePoint.z),new T.Vector3());if(!point)return;
  this.target.copy(this.props.root.worldToLocal(point));this.target.x=T.MathUtils.clamp(this.target.x,-.6,.6);this.target.y=T.MathUtils.clamp(this.target.y,1.15,1.8);this.target.z=.3;
 }
 pointerUp(){if(!this.dragging)return;this.dragging=false;if(paymentInZone(this.target,this.props.target))this.present();else{this.target.copy(this.start);this.update('금색 원에 닿지 않았어요. 다시 집어 단말기에 가져다 대세요.');}}
 present(){if(this.phase!=='ready')return;this.dragging=false;this.target.copy(this.props.target);this.phase='approving';this.elapsed=0;this.scene.rightHand.visible=true;poseHand(this.scene.rightHand,'pinch');this.props.screenText('확인 중…');this.update();}
 takeReceipt(){if(this.phase!=='receipt')return;this.phase='taking';this.elapsed=0;const {receipt}=this.props;this.scene.camera.attach(receipt);this.receiptStart=receipt.position.clone();this.scene.rightHand.visible=true;poseHand(this.scene.rightHand,'pinch');this.update();}
 assist(){if(this.phase==='ready')this.present();else if(this.phase==='receipt')this.takeReceipt();}
 cancelPointer(){if(!this.dragging)return;this.dragging=false;this.target.copy(this.start);this.update('카드를 다시 놓았어요.');}
 tick(dt){
  if(this.closed)return;const {card,receipt,ring}=this.props,s=this.scene;this.elapsed+=dt;
  card.position.lerp(this.target,1-Math.exp(-18*dt));ring.visible=this.phase==='ready';
  if(this.phase==='approving'&&this.elapsed>=.75){this.phase='printing';this.elapsed=0;card.visible=false;s.rightHand.visible=false;receipt.visible=true;this.scene.audio?.cue('payment');this.props.screenText('시연 결제 확인');this.update();}
  if(this.phase==='printing'){const p=Math.min(1,this.elapsed/(s.reduced?.1:1));receipt.scale.y=Math.max(.015,p);receipt.position.y=1.28+.23*p;if(p===1){this.phase='receipt';this.elapsed=0;this.update();}}
  if(this.phase==='taking'){const p=Math.min(1,this.elapsed/(s.reduced?.1:.65));receipt.position.lerpVectors(this.receiptStart,this.receiptEnd(),smooth(p));receipt.quaternion.slerp(new T.Quaternion(),Math.min(1,dt*12));if(p===1){this.phase='held';this.update();}}
  if(this.phase==='held')receipt.position.copy(this.receiptEnd());
  if(this.dragging||this.phase==='approving'||this.phase==='taking'||this.phase==='held'){
   const object=this.phase==='taking'||this.phase==='held'?receipt:card,p=object.getWorldPosition(new T.Vector3());s.camera.worldToLocal(p);s.rightHand.rotation.set(0,.1,-.25);s.rightHand.position.copy(p).add(new T.Vector3(.08,-.19,.015));
  }else s.rightHand.visible=false;
 }
 finish(ok){if(this.closed)return;this.closed=true;const success=ok&&this.phase==='held';this.props.receipt.removeFromParent();this.props.dispose();this.originalTerminal.visible=this.terminalWasVisible;this.originalPaper.visible=this.paperWasVisible;const s=this.scene;s.camera.position.copy(this.camera);s.camera.rotation.copy(this.rotation);s.leftHand.visible=true;s.rightHand.visible=true;s.resetHands();s.syncHands();s.payment=null;this.resolve(success);}
}
