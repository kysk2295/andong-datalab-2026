import test from 'node:test';
import assert from 'node:assert/strict';
import {worldKey,acceptsWorldInput,walkIntent,bindWalkButton} from '../src/relay-input.js';
test('arrow keys move forward/backward and turn; diagonal walking is normalized',()=>{
 assert.deepEqual(walkIntent(new Set(['arrowup'])),{forward:1,side:0,turn:0});
 assert.deepEqual(walkIntent(new Set(['arrowdown','arrowleft'])),{forward:-1,side:0,turn:1});
 assert.equal(walkIntent(new Set(['arrowup','w'])).forward,1);
 const d=walkIntent(new Set(['w','d']));assert.ok(Math.abs(Math.hypot(d.forward,d.side)-1)<1e-8);
 assert.equal(walkIntent(new Set(['w','s'])).forward,0);
 assert.equal(worldKey({key:'ㅈ',code:'KeyW'}),'w');
});
test('world controls survive button focus but leave forms, dialogs and shortcuts alone',()=>{
 assert.equal(acceptsWorldInput({target:{tagName:'BUTTON',closest:()=>null}}),true);
 for(const flags of [{paused:true},{cover:true},{modal:true}])assert.equal(acceptsWorldInput({},flags),false);
 assert.equal(acceptsWorldInput({ctrlKey:true}),false);
 assert.equal(acceptsWorldInput({target:{isContentEditable:true}}),false);
 assert.equal(acceptsWorldInput({target:{closest:()=>({tagName:'INPUT'})}}),false);
});
test('tap, hold cancellation and keyboard activation never leave touch walking stuck',()=>{
 const b={setPointerCapture(){}},moves=[],s={touchMove:{forward:0},move:n=>moves.push(n)};
 bindWalkButton(b,1,()=>s);b.onpointerdown({button:0,pointerId:1});assert.equal(s.touchMove.forward,1);
 b.onpointerup();assert.equal(s.touchMove.forward,0);assert.equal(moves[0],.24);
 b.onlostpointercapture();assert.equal(moves.length,1);
 b.onpointerdown({button:0,pointerId:1});b.onpointercancel();assert.equal(s.touchMove.forward,0);assert.equal(moves.length,1);
 b.onkeydown({key:'Enter',preventDefault(){}});assert.equal(moves.length,2);
 b.onpointerdown({button:0,pointerId:1});b.onblur();assert.equal(s.touchMove.forward,0);
});

test('thumbstick has a dead zone and limits diagonal movement to walking speed',async()=>{
 const {thumbstickIntent}=await import('../src/relay-input.js');
 assert.deepEqual(thumbstickIntent(2,1,30),{forward:0,side:0});
 const up=thumbstickIntent(0,-30,30);assert.equal(up.forward,1);assert.equal(up.side,0);
 const diagonal=thumbstickIntent(200,-200,30);assert.ok(Math.abs(Math.hypot(diagonal.forward,diagonal.side)-1)<1e-8);
 assert.ok(thumbstickIntent(-20,0,30).side<0);
});

test('thumbstick releases on cancellation, hidden page and blur; a second finger cannot steal it',async()=>{
 const {bindThumbstick}=await import('../src/relay-input.js');
 const listeners={},docListeners={},pad={style:{setProperty(){}},setPointerCapture(){},getBoundingClientRect:()=>({left:0,top:0,width:80,height:80})};
 const host={addEventListener:(k,v)=>listeners[k]=v,removeEventListener:k=>delete listeners[k],document:{hidden:false,addEventListener:(k,v)=>docListeners[k]=v,removeEventListener:k=>delete docListeners[k]}};
 const scene={touchMove:{forward:0,side:0},paused:false};const release=bindThumbstick(pad,()=>scene,host);
 const down=(pointerId,x,y)=>pad.onpointerdown({button:0,pointerId,clientX:x,clientY:y,preventDefault(){}});
 down(1,40,10);assert.ok(scene.touchMove.forward>.9);
 down(2,70,40);pad.onpointermove({pointerId:2,clientX:70,clientY:40});assert.equal(scene.touchMove.side,0);
 pad.onpointerup({pointerId:2});assert.ok(scene.touchMove.forward>.9);
 pad.onpointercancel({pointerId:1});assert.deepEqual(scene.touchMove,{forward:0,side:0});
 down(3,40,10);listeners.blur();assert.equal(scene.touchMove.forward,0);
 down(4,40,10);host.document.hidden=true;docListeners.visibilitychange();assert.equal(scene.touchMove.forward,0);
 scene.paused=true;down(5,40,10);assert.equal(scene.touchMove.forward,0);
 release();assert.deepEqual(listeners,{});assert.deepEqual(docListeners,{});
});
