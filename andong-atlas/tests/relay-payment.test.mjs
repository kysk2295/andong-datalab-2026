import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from 'three';
import {PaymentInteraction,paymentInZone,drawReceipt} from '../src/relay-payment.js';
import {poseHand,createVisitorHand} from '../src/relay-hands.js';

function fixture(method='card'){
 const world=new T.Scene(),camera=new T.PerspectiveCamera(58,1.7,.04,200),counter=new T.Group();world.add(camera,counter);counter.position.set(3.1,0,2.45);camera.position.set(3,1.62,3.8);camera.lookAt(3.1,1.15,2.4);
 const scene={camera,current:{refs:{counter,terminal:new T.Group(),counterPaper:new T.Group()}},keys:new Set(),rig:new T.Group(),leftHand:new T.Group(),rightHand:new T.Group(),chopsticks:new T.Group(),receipt:new T.Group(),phone:new T.Group(),resetHands(){},syncHands(){}};
 let disposed=false,result;const updates=[];
 const propsFactory=parent=>{const root=new T.Group();parent.add(root);const card=new T.Mesh(new T.PlaneGeometry(.24,.15)),receipt=new T.Mesh(new T.PlaneGeometry(.25,.46));root.add(card,receipt);card.position.set(-.31,1.25,.38);receipt.position.set(.33,1.51,.068);receipt.visible=false;return {root,card,receipt,ring:new T.Group(),target:new T.Vector3(0,1.4,.3),screenText(){},dispose(){disposed=true;root.removeFromParent();}};};
 const start=camera.position.clone(),rotation=camera.rotation.clone(),payment=new PaymentInteraction(scene,{meal:{name:'안동찜닭',examplePrice:18000},method,onUpdate:u=>updates.push(u),resolve:r=>result=r,propsFactory});scene.payment=payment;
 return {scene,payment,updates,start,rotation,result:()=>result,disposed:()=>disposed};
}
test('terminal requires proximity in both axes',()=>{assert.equal(paymentInZone({x:.03,y:1.45},{x:0,y:1.4}),true);assert.equal(paymentInZone({x:.2,y:1.4},{x:0,y:1.4}),false);assert.equal(paymentInZone({x:0,y:1.6},{x:0,y:1.4}),false);});
for(const method of ['card','cash'])test(`${method}: confirmation alone cannot award a receipt; print, take and collect are required`,()=>{
 const f=fixture(method),p=f.payment;p.present();p.present();assert.equal(p.phase,'approving');p.tick(.8);assert.equal(p.phase,'printing');p.takeReceipt();assert.equal(p.phase,'printing');p.tick(1.1);assert.equal(p.phase,'receipt');assert.equal(f.result(),undefined);
 p.takeReceipt();p.tick(.3);assert.equal(p.phase,'taking');p.tick(.4);assert.equal(p.phase,'held');assert.equal(f.updates.at(-1).done,true);p.finish(true);assert.equal(f.result(),true);assert.equal(f.disposed(),true);assert.equal(f.scene.current.refs.counter.children.length,0);assert.deepEqual(f.scene.camera.position,f.start);assert.deepEqual(f.scene.camera.rotation.toArray(),f.rotation.toArray());
});
for(const phase of ['ready','printing','receipt','taking'])test(`cancel during ${phase} restores camera, props and does not award payment`,()=>{
 const f=fixture(),p=f.payment;if(phase!=='ready'){p.present();p.tick(.8);}if(['receipt','taking'].includes(phase))p.tick(1.1);if(phase==='taking')p.takeReceipt();p.finish(false);p.tick(100);assert.equal(f.result(),false);assert.equal(f.scene.payment,null);assert.equal(f.scene.current.refs.counter.children.length,0);assert.equal(f.scene.camera.children.length,0);assert.equal(f.scene.current.refs.terminal.visible,true);assert.deepEqual(f.scene.camera.position,f.start);
});
test('early confirmation cannot skip the receipt pickup',()=>{const f=fixture();f.payment.finish(true);assert.equal(f.result(),false);});
test('invalid drag and cancelled pointer return the card without starting payment',()=>{const f=fixture(),p=f.payment;p.dragging=true;p.target.set(.5,1.4,.3);p.pointerUp();assert.equal(p.phase,'ready');assert.deepEqual(p.target,p.start);p.dragging=true;p.target.copy(p.props.target);p.cancelPointer();assert.equal(p.phase,'ready');p.finish(false);});
test('articulated grip bends finger joints and mirrors the thumb',()=>{
 const k={mat:color=>new T.MeshBasicMaterial({color}),mesh(g,geo,mat,p=[0,0,0]){const o=new T.Mesh(geo,mat);o.position.set(...p);g.add(o);return o;},sphere(g,scale,p,mat){const o=this.mesh(g,new T.SphereGeometry(1,6,4),mat,p);o.scale.set(...scale);return o;}};
 const parent=new T.Group(),right=createVisitorHand(parent,1,k),left=createVisitorHand(parent,-1,k);poseHand(right,'chopsticks');poseHand(left,'pinch');assert.ok(right.userData.joints.fingers[0].joint.rotation.x>.6);assert.ok(left.userData.joints.thumb.rotation.z>0);assert.ok(right.userData.joints.thumb.rotation.z<0);poseHand(right);assert.ok(right.userData.joints.fingers[0].joint.rotation.x<.2);
 parent.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});
});

test('mobile payment keeps the camera inside the restaurant and the entire cash note in view',()=>{
 const f=fixture('cash'),s=f.scene,p=f.payment;s.camera.aspect=390/844;s.camera.fov=68;s.camera.updateProjectionMatrix();p.fitCamera();s.current.refs.counter.updateMatrixWorld(true);s.camera.updateMatrixWorld(true);
 assert.ok(s.camera.position.z<4.24);
 for(const x of [-.145,.145])for(const y of [-.075,.075]){const ndc=p.props.card.localToWorld(new T.Vector3(x,y,0)).project(s.camera);assert.ok(Math.abs(ndc.x)<.96);assert.ok(ndc.y>-.4&&ndc.y<.5);}
 p.finish(false);
});
test('printed and held receipt template carries the selected meal, amount and payment method',()=>{
 const lines=[],ctx={fillText(t){lines.push(t);},fillRect(){},setLineDash(){},beginPath(){},moveTo(){},lineTo(){},stroke(){}};
 drawReceipt(ctx,512,942,{name:'안동간고등어',examplePrice:12000},'cash');
 for(const line of ['안동간고등어','12,000원','현금 · 시연','QR 인증 → 10% 할인','샘플 QR · 실제 결제 없음'])assert.ok(lines.includes(line));
 assert.ok(!lines.includes('안동찜닭'));
});
