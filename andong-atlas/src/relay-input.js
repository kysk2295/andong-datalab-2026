// Physical keys work with both Korean and English input methods.
export function worldKey(event){
 const codes={KeyW:'w',KeyA:'a',KeyS:'s',KeyD:'d',KeyE:'e',KeyR:'r',ShiftLeft:'shift',ShiftRight:'shift',Space:' '};
 const key=(event.key||'').toLowerCase();
 return codes[event.code]||({'ㅈ':'w','ㅉ':'w','ㅁ':'a','ㄴ':'s','ㅇ':'d','ㄷ':'e','ㄸ':'e','ㄱ':'r','ㄲ':'r',spacebar:' '})[key]||key;
}
export function acceptsWorldInput(event,{paused=false,cover=false,modal=false}={}){
 if(paused||cover||modal||event.altKey||event.ctrlKey||event.metaKey)return false;
 const target=event.target;
 return !target?.isContentEditable&&!target?.closest?.('input,textarea,select,[contenteditable],[role="dialog"]');
}
export function walkIntent(keys){
 let forward=Number(keys.has('w')||keys.has('arrowup'))-Number(keys.has('s')||keys.has('arrowdown'));
 let side=Number(keys.has('d'))-Number(keys.has('a'));
 const length=Math.hypot(forward,side);if(length>1){forward/=length;side/=length;}
 return {forward,side,turn:Number(keys.has('arrowleft'))-Number(keys.has('arrowright'))};
}
// A short tap still moves even when pointerdown/up occur between animation frames.
export function bindWalkButton(button,direction,scene){
 let started=null;
 const stop=(tap=false)=>{const s=scene();if(s)s.touchMove.forward=0;if(tap&&started!==null&&performance.now()-started<140)s?.move(direction*.24);started=null;};
 button.onpointerdown=e=>{if(e.button!==0)return;started=performance.now();button.setPointerCapture(e.pointerId);const s=scene();if(s)s.touchMove.forward=direction;};
 button.onpointerup=()=>stop(true);button.onpointercancel=()=>stop();button.onlostpointercapture=()=>stop();button.onblur=()=>stop();
 button.onkeydown=e=>{if(e.key==='Enter'||e.code==='Space'){e.preventDefault();scene()?.move(direction*.24);}};
 button.onclick=e=>{if(e.detail===0)scene()?.move(direction*.24);};
 return ()=>stop();
}

export function thumbstickIntent(x,y,radius){
 const length=Math.hypot(x,y);
 if(radius<=0||length<radius*.14)return {forward:0,side:0};
 const strength=Math.min(1,(length/radius-.14)/.86);
 return {forward:-y/length*strength,side:x/length*strength};
}

// Capture one finger only; cancellation, blur and a hidden page release movement.
export function bindThumbstick(pad,getScene,host=window){
 let pointer=null;
 const stop=()=>{pointer=null;const scene=getScene();if(scene)scene.touchMove={forward:0,side:0};pad.style.setProperty('--stick-x','0px');pad.style.setProperty('--stick-y','0px');};
 const update=e=>{
  const scene=getScene();if(!scene||scene.paused){stop();return;}
  const rect=pad.getBoundingClientRect(),radius=rect.width*.35,x=e.clientX-rect.left-rect.width/2,y=e.clientY-rect.top-rect.height/2;
  const scale=Math.min(1,radius/(Math.hypot(x,y)||1));
  const intent=thumbstickIntent(x,y,radius);
  if(intent.forward||intent.side)scene.takeWalkingControl?.();
  scene.touchMove=intent;
  pad.style.setProperty('--stick-x',`${x*scale}px`);pad.style.setProperty('--stick-y',`${y*scale}px`);
 };
 pad.onpointerdown=e=>{if(e.button!==0||pointer!==null)return;e.preventDefault();pointer=e.pointerId;pad.setPointerCapture(pointer);update(e);};
 pad.onpointermove=e=>{if(e.pointerId===pointer)update(e);};
 pad.onpointerup=pad.onpointercancel=pad.onlostpointercapture=e=>{if(e.pointerId===pointer)stop();};
 pad.onblur=stop;
 const visibility=()=>{if(host.document.hidden)stop();};
 host.addEventListener('blur',stop);host.document.addEventListener('visibilitychange',visibility);
 return ()=>{stop();host.removeEventListener('blur',stop);host.document.removeEventListener('visibilitychange',visibility);};
}
