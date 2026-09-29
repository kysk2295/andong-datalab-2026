import {popupZoneAt} from './relay-popup-layout.js';
import {PopupPostcard} from './relay-popup-postcard.js';
import {passageAt} from './relay-passages.js';
import {RelayAudio} from './relay-audio.js';
import * as T from 'three';
import {RectAreaLightUniformsLib} from 'three/addons/lights/RectAreaLightUniformsLib.js';
import {RelayLighting} from './relay-lighting.js';
import {JumpMotion,takeWalkingControl,walkingAllowed,walkingEyeHeight} from './relay-locomotion.js';
import {worldKey,acceptsWorldInput,walkIntent} from './relay-input.js';
import {createKit} from './relay-primitives.js';
import {buildRelaySet} from './relay-sets.js';
import {ReceiptScan} from './relay-scan.js';
import {HDRLoader} from 'three/addons/loaders/HDRLoader.js';
import {canStand,planWalk} from './relay-navigation.js';
import {TuhoInteraction} from './relay-tuho.js';
import {MEALS} from './relay-model.js';
import {PaymentInteraction,createReceiptSlip} from './relay-payment.js';
import {poseHand} from './relay-hands.js';
import {MealInteraction} from './relay-meal.js';
import {WorkshopInteraction} from './relay-workshop.js';
import {advanceRiverWater,riverSurfaceAt} from './relay-water.js';

export class RelayScene{
 constructor(container,{onInteract=()=>{},onFocus=()=>{},onError=()=>{},onTravel=()=>{},onNavigation=()=>{},onGameLook=()=>{},onPassage=()=>false,onLocation=()=>{}}={}){
  let sound=true;try{sound=localStorage.getItem('andong-relay-sound')!=='off';}catch{}this.audio=new RelayAudio({enabled:sound});
  this.onLocation=onLocation;this.onPassage=onPassage;this.onGameLook=onGameLook;this.onNavigation=onNavigation;this.navigation=null;this.station=null;this.onTravel=onTravel;this.mapView=false;this.workshop=null;this.container=container;this.onInteract=onInteract;this.onFocus=onFocus;this.focused=null;this.touchMove={forward:0,side:0};this.kit=createKit();this.reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  this.renderer=new T.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
  this.renderer.setPixelRatio(Math.min(devicePixelRatio,innerWidth<700?1.25:1.7));
  this.renderer.shadowMap.enabled=true;this.renderer.shadowMap.type=T.PCFSoftShadowMap;this.renderer.shadowMap.autoUpdate=false;
  this.renderer.outputColorSpace=T.SRGBColorSpace;this.renderer.toneMapping=T.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.25;
  this.renderer.domElement.setAttribute('aria-label','1인칭 3D 공간. 드래그로 둘러보기, 위아래 방향키 또는 W A S D로 이동, 좌우 방향키로 회전, Space로 점프, Shift로 달리기, R로 시점 복원');this.renderer.domElement.tabIndex=0;
  container.append(this.renderer.domElement);this.scene=new T.Scene();this.scene.background=new T.Color('#c2b9a0');
  this.skies={};for(const [key,file] of [['day','qwantani_sunset_puresky'],['night','qwantani_night_puresky'],['interior','studio_small_09']])new HDRLoader().load('/assets/relay/materials/'+file+'_hdri.hdr',tx=>{if(this.disposed){tx.dispose();return;}tx.mapping=T.EquirectangularReflectionMapping;this.skies[key]=tx;this.updateEnvironment();},undefined,()=>{});
  this.camera=new T.PerspectiveCamera(58,1,.045,220);this.scene.add(this.camera);this.lighting=new RelayLighting(this.renderer,this.scene,this.camera);RectAreaLightUniformsLib.init();this.ceilingLight=new T.RectAreaLight('#fff2da',5,3.5,2);this.ceilingLight.position.set(0,3.3,0);this.ceilingLight.lookAt(0,0,0);this.scene.add(this.ceilingLight);
  this.windowLight=new T.RectAreaLight('#f4f6ee',7,2.5,2.3);this.windowLight.position.set(-3,2.15,1.7);this.windowLight.lookAt(0,.8,0);this.scene.add(this.windowLight);
  this.ambient=new T.HemisphereLight('#fff0c9','#556a5f',2);this.scene.add(this.ambient);
  this.sun=new T.DirectionalLight('#ffdba1',3.5);this.sun.position.set(-5,13,8);this.sun.castShadow=true;this.sun.shadow.mapSize.set(2048,2048);this.sun.shadow.camera.left=-18;this.sun.shadow.camera.right=18;this.sun.shadow.camera.top=18;this.sun.shadow.camera.bottom=-18;this.sun.shadow.normalBias=.04;this.scene.add(this.sun);
  this.fill=new T.DirectionalLight('#c6dce0',1);this.fill.position.set(6,3,-7);this.scene.add(this.fill);
  this.localLight=new T.PointLight('#ffdb9c',18,12,2);this.localLight.position.set(0,2.5,1);this.scene.add(this.localLight);
  this.rig=new T.Group();this.camera.add(this.rig);this.leftHand=this.kit.hand(this.rig,-1);this.rightHand=this.kit.hand(this.rig,1);this.leftHand.position.set(-.35,-.43,-.72);this.rightHand.position.set(.38,-.46,-.71);this.leftHand.rotation.set(-.35,.2,-.4);this.rightHand.rotation.set(-.4,-.2,.4);
  this.chopsticks=new T.Group();this.rightHand.add(this.chopsticks);for(const x of [-.016,.016]){const q=this.kit.box(this.chopsticks,[.007,.3,.007],[x,.19,0],'#6d5039');q.rotation.z=x;}
  this.brush=new T.Group();this.rightHand.add(this.brush);this.kit.cyl(this.brush,.008,.011,.28,[0,.18,0],this.kit.wood);this.kit.cyl(this.brush,.003,.01,.055,[0,.345,0],'#3b2b1e');
  this.phone=new T.Group();this.leftHand.add(this.phone);this.kit.box(this.phone,[.19,.35,.023],[0,.13,-.037],'#1e3531');this.kit.label(this.phone,'이어드림',[0,.18,-.021],.16,'#274f41','#e8dbb9',.23);this.phone.rotation.x=-.22;
  this.receipt=new T.Group();this.rightHand.add(this.receipt);
  this.popupBag=new T.Group();this.rightHand.add(this.popupBag);this.popupBag.visible=false;this.popupBag.position.set(0,.14,-.06);
  this.kit.roundedBox(this.popupBag,[.19,.23,.1],[0,-.16,0],this.kit.mat('#ab8b5e',{roughness:.93}),.005);
  for(const z of [-.035,.035])this.kit.tube(this.popupBag,[[-.05,-.045,z],[-.04,.055,z],[.04,.055,z],[.05,-.045,z]],.004,'#675842');
  this.kit.sign(this.popupBag,'월영 밤마당',[0,-.15,.052],.14,'#504d38','#ab8b5e',.055);

  this.tastingCup=new T.Group();this.rightHand.add(this.tastingCup);this.tastingCup.visible=false;this.tastingCup.position.set(0,.16,-.07);this.kit.cyl(this.tastingCup,.062,.048,.13,[0,.04,0],this.kit.paper);this.tastingLiquid=this.kit.cyl(this.tastingCup,.055,.055,.003,[0,.106,0],this.kit.mat('#bba263',{roughness:.28}));
  this.bite=this.kit.sphere(this.chopsticks,.027,[0,.34,0],'#ba8343');this.bite.visible=false;
  this.jumpMotion=new JumpMotion();this.keys=new Set();this.yaw=0;this.pitch=0;this.action=null;this.cache=new Map();this.clock=0;this.disposed=false;this.paused=false;
  this.ray=new T.Raycaster();this.ray.far=4.5;this.events=new AbortController();const signal=this.events.signal;let drag=null;
  const canvas=this.renderer.domElement;
  window.addEventListener('pointerdown',()=>this.audio.unlock(),{signal});window.addEventListener('keydown',()=>this.audio.unlock(),{signal});
  document.addEventListener('pointerlockchange',()=>{this.keys.clear();this.onGameLook(document.pointerLockElement===canvas);},{signal});
  document.addEventListener('mousemove',e=>{if(document.pointerLockElement===canvas)this.look(-e.movementX*.0025,-e.movementY*.0025);},{signal});
  document.addEventListener('pointerlockerror',()=>onError('마우스 고정을 사용할 수 없어 드래그 조작을 유지합니다.'),{signal});
  canvas.addEventListener('contextmenu',e=>e.preventDefault(),{signal});
  canvas.addEventListener('pointerdown',e=>{canvas.focus({preventScroll:true});if(document.pointerLockElement===canvas){this.interact();return;}drag={x:e.clientX,y:e.clientY,lastX:e.clientX,lastY:e.clientY};if(this.payment)this.payment.pointerDown(e);else if(this.tuho)this.tuho.pointerDown(e);else if(this.meal)this.meal.pointerDown(e);else if(this.scanner)this.scanner.pointerDown(e);else if(this.workshop)this.workshop.pointerDown(e);else if(this.painting)this.paintAt(e);canvas.setPointerCapture(e.pointerId);},{signal});
  canvas.addEventListener('pointermove',e=>{if(!drag||(this.action&&this.action.type!=='travel')||this.mapView||this.navigation)return;if(this.payment){this.payment.pointerMove(e);return;}if(this.tuho){this.tuho.pointerMove(e);return;}if(this.meal){this.meal.pointerMove(e);return;}if(this.scanner){this.scanner.pointerMove(e);return;}if(this.workshop){this.workshop.pointerMove(e);return;}if(this.painting){this.paintAt(e);return;}this.yaw-=(e.clientX-drag.lastX)*.0035;this.pitch=T.MathUtils.clamp(this.pitch-(e.clientY-drag.lastY)*.003,-.68,.55);drag.lastX=e.clientX;drag.lastY=e.clientY;this.orient();},{signal});
  canvas.addEventListener('pointerup',e=>{if(this.payment){this.payment.pointerUp(e);drag=null;return;}if(this.tuho){this.tuho.pointerUp(e);drag=null;return;}if(this.meal){this.meal.pointerUp(e);drag=null;return;}if(this.scanner){this.scanner.pointerUp();drag=null;return;}if(this.workshop){this.workshop.pointerUp(e);drag=null;return;}if(this.painting){drag=null;return;}if(drag&&Math.hypot(e.clientX-drag.x,e.clientY-drag.y)<6&&!this.action){const rect=canvas.getBoundingClientRect();this.ray.setFromCamera(new T.Vector2((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1),this.camera);const hit=this.pickInteraction();if(hit)this.onInteract(hit.userData.action);}drag=null;},{signal});
  canvas.addEventListener('pointercancel',()=>{drag=null;this.scanner?.pointerUp();this.workshop?.cancelPointer();this.meal?.cancelPointer();this.tuho?.cancelPointer();this.payment?.cancelPointer();},{signal});
  window.addEventListener('keydown',e=>{
   if(!acceptsWorldInput(e,{paused:this.paused,cover:this.options?.cover,modal:!!document.querySelector('dialog[open]')}))return;
   const key=worldKey(e),onCanvas=e.target===canvas;
   if(key==='escape'){this.keys.clear();this.cancelNavigation();if(onCanvas){this.payment?.finish(false);this.tuho?.finish(null);}return;}
   // Task arrows belong to the task only while the 3D surface is focused.
   if(this.payment||this.tuho||this.scanner){if(!onCanvas)return;
    if(this.payment&&[' ','enter'].includes(key)){e.preventDefault();if(!e.repeat)this.payment.assist();}
    if(this.tuho){const steps={arrowleft:[-.06,0],arrowright:[.06,0],arrowup:[0,-.06],arrowdown:[0,.06]};if(steps[key]){e.preventDefault();this.tuho.shift(...steps[key]);}if(key===' '&&!e.repeat){e.preventDefault();this.tuho.throw();}}
    if(this.scanner){const steps={arrowleft:[-.025,0],arrowright:[.025,0],arrowup:[0,.025],arrowdown:[0,-.025]};if(steps[key]){e.preventDefault();this.scanner.shift(...steps[key]);}}return;
   }
   if(this.action?.type==='travel'&&this.current?.refs.busCabin){const turn=walkIntent(new Set([key])).turn;if(turn){e.preventDefault();this.look(turn*.075);}return;}
   if(!walkingAllowed(this))return;
   if(key===' '){if(!onCanvas&&e.target?.closest?.('button,a,[role="button"]'))return;e.preventDefault();if(!e.repeat)this.jump();return;}
   if(['w','a','s','d','arrowup','arrowdown','arrowleft','arrowright'].includes(key))this.takeWalkingControl();
   if(['arrowleft','arrowright','arrowup','arrowdown','w','a','s','d','r','e','shift'].includes(key)){
    e.preventDefault();this.keys.add(key);
    if(!e.repeat){const tap=walkIntent(new Set([key]));this.move(tap.forward*.12,tap.side*.12);if(tap.turn)this.look(tap.turn*.045);if(key==='r')this.resetView();if(key==='e')this.interact();}
   }
  },{signal});
  window.addEventListener('keyup',e=>this.keys.delete(worldKey(e)),{signal});
  const clearInput=()=>{this.keys.clear();this.touchMove={forward:0,side:0};this.workshop?.cancelPointer();this.meal?.cancelPointer();this.tuho?.cancelPointer();this.payment?.cancelPointer();};
  window.addEventListener('blur',clearInput,{signal});document.addEventListener('focusin',e=>{if(!acceptsWorldInput(e))this.keys.clear();},{signal});document.addEventListener('visibilitychange',()=>{if(document.hidden)clearInput();this.audio.setPaused(document.hidden||this.paused||!!this.options?.cover);},{signal});
  canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();this.paused=true;this.cancelAction();this.cancelNavigation();this.payment?.finish(false);this.tuho?.finish(null);this.meal?.finish(false);this.scanner?.finish(false);this.workshop?.finish(false);this.cancelPaint();onError('3D 화면 연결이 끊겼습니다. 새로고침하거나 아래 버튼으로 여정을 계속할 수 있습니다.');},{signal});
  this.resizeObserver=new ResizeObserver(()=>this.resize());this.resizeObserver.observe(container);this.resize();this.last=performance.now();this.animate();
 }
 releaseGameLook(){if(document.pointerLockElement===this.renderer.domElement)document.exitPointerLock();}
 async toggleGameLook(){if(document.pointerLockElement===this.renderer.domElement){this.releaseGameLook();return;}try{await this.renderer.domElement.requestPointerLock();this.renderer.domElement.focus();}catch{this.onGameLook(false);}}
 resize(){const w=this.container.clientWidth||innerWidth,h=this.container.clientHeight||innerHeight;this.renderer.setSize(w,h);this.camera.aspect=w/h;this.camera.fov=w<700?68:this.current?.refs.busCabin?64:58;this.camera.updateProjectionMatrix();this.lighting?.resize(w,h);this.payment?.fitCamera();this.resizeWater();}
 setScene(id,options={}){
  this.land();
  const same=(this.id===id||(this.id==='meal'&&id==='receipt')||(this.id==='receipt'&&id==='meal'))&&this.options?.cover===options.cover&&this.options?.journey===options.journey,position=this.camera.position.clone(),yaw=this.yaw,pitch=this.pitch,station=this.station;
  this.payment?.finish(false);this.tuho?.finish(null);this.meal?.finish(false);this.scanner?.finish(false);this.workshop?.finish(false);this.cancelPaint();this.cancelAction();this.cancelNavigation();this.mapView=false;this.id=id;this.options=options;if(options.paid){const receiptKey=options.meal+options.payment;if(receiptKey!==this.receiptKey){this.receiptSlip?.dispose();this.receiptSlip=createReceiptSlip(MEALS[options.meal]||MEALS.jjimdak,options.payment);this.receipt.add(this.receiptSlip.mesh);this.receiptSlip.mesh.position.set(0,.17,-.034);this.receiptKey=receiptKey;}}
  const key=JSON.stringify([id,options.meal,options.seat,options.program,options.craftSteps,options.color,options.maskArt,options.transport,options.cover,options.walked,options.ordered,options.eaten,options.paid,options.journey,options.gameScore,options.gameAttempts,options.cart]);
  if(this.current)this.scene.remove(this.current.group);
  if(!this.cache.has(key)){const kit=createKit();this.cache.set(key,{...buildRelaySet(id,kit,options),kit});}
  this.audio.setLocation(options.cover?'':id);this.audio.setPaused(this.paused||document.hidden||!!options.cover);
  this.busProgress=0;this.current=this.cache.get(key);this.current.refs.busCabin?.reset();this.cache.delete(key);this.cache.set(key,this.current);
  while(this.cache.size>5){const [oldKey,oldSet]=this.cache.entries().next().value;this.disposeSet(oldSet);this.cache.delete(oldKey);}
  this.scene.add(this.current.group);if(this.current.refs.entryDoor)this.current.refs.entryDoor.rotation.y=0;
  const night=this.current.night,interior=['meal','receipt','workshop'].includes(id);this.updateEnvironment();
  this.scene.fog=new T.Fog(night?'#101e2b':'#aeb6b4',night?42:35,night?175:155);
  this.ceilingLight.visible=interior;this.ceilingLight.intensity=id==='workshop'?2.8:2.7;this.windowLight.visible=interior;this.windowLight.intensity=id==='workshop'?4.5:3.3;
  this.useContactShadows=interior||id==='market'||id==='popup';this.scene.environmentIntensity=night?.38:interior?.4:.65;
  const shadowRange=interior?7:id==='popup'?40:18;for(const axis of ['left','bottom'])this.sun.shadow.camera[axis]=-shadowRange;for(const axis of ['right','top'])this.sun.shadow.camera[axis]=shadowRange;this.sun.shadow.camera.updateProjectionMatrix();
  this.ambient.intensity=night?.48:interior?.24:.7;this.ambient.color.set(night?'#a8c3e0':'#eef0e5');this.ambient.groundColor.set(night?'#172021':'#686b60');
  this.sun.color.set(night?'#abc6e3':'#fff0d3');this.sun.intensity=night?1.15:2.1;this.fill.intensity=night?.12:interior?.18:.45;this.localLight.intensity=interior?2.5:night?7:8;
  this.localLight.color.set(id==='market'?'#e5eeef':'#ffe0b3');this.localLight.position.set(0,2.8,id==='bridge'?-14:0);this.renderer.toneMappingExposure=night?1.05:interior?1.08:1.04;
  if(id==='popup'){this.ambient.intensity=.62;this.scene.environmentIntensity=.2;this.sun.intensity=.5;this.fill.intensity=.2;this.scene.fog=new T.Fog('#182d40',55,180);this.renderer.toneMappingExposure=1.12;}
  if(id==='market'){this.ambient.intensity=.32;this.scene.environmentIntensity=.48;this.sun.intensity=1.25;this.fill.intensity=.18;this.localLight.intensity=2;this.renderer.toneMappingExposure=.96;}
  if(this.current.refs.busCabin){this.ambient.intensity=.65;this.scene.environmentIntensity=.65;this.sun.intensity=2.1;this.fill.intensity=.38;this.localLight.intensity=0;this.scene.fog=new T.Fog('#a8b4ad',110,310);this.renderer.toneMappingExposure=1.02;}
  this.camera.fov=this.container.clientWidth<700?68:this.current.refs.busCabin?64:58;this.camera.updateProjectionMatrix();
  this.resizeWater();this.rig.visible=!options.cover;this.chopsticks.visible=id==='meal';this.brush.visible=id==='workshop'&&options.program==='mask';this.phone.visible=id==='receipt';this.receipt.visible=id==='receipt'&&!!options.paid;
  this.resetHands();this.leftHand.visible=['receipt','meal','workshop'].includes(id);this.popupBag.visible=id==='popup'&&!!options.cart?.length;this.rightHand.visible=this.popupBag.visible||!['market','transit','link','bridge','popup'].includes(id);
  this.resetView();if(same){this.camera.position.copy(position);this.yaw=yaw;this.pitch=pitch;this.station=station;this.orient();}else this.station=null;this.syncHands();this.renderer.shadowMap.needsUpdate=true;
 }
 resizeWater(){const water=this.current?.refs.water;if(!water)return;const size=this.lowQuality?256:this.container.clientWidth<700?384:768,target=water.getRenderTarget();if(target.width!==size)target.setSize(size,size);}
 updateEnvironment(){
  if(!this.current)return;const interior=['meal','receipt','workshop'].includes(this.id),key=interior||this.id==='market'?'interior':this.current.night?'night':'day';
  const environment=this.skies[key]||this.skies.day;if(environment)this.scene.environment=environment;
  this.scene.background=(this.id==='popup'?this.skies.night:this.skies.day)||new T.Color(this.current.night?'#101e2b':'#aeb6b4');this.scene.backgroundIntensity=this.current.night?(this.id==='popup'?.085:.06):.75;this.scene.backgroundBlurriness=.015;
 }
 resetView(){if(!this.current)return;this.station=null;this.cancelNavigation();this.jumpMotion.reset();this.keys.clear();this.touchMove={forward:0,side:0};this.camera.position.fromArray(this.current.camera);const target=new T.Vector3(...this.current.target);const direction=target.sub(this.camera.position).normalize();this.yaw=Math.atan2(-direction.x,-direction.z);this.pitch=Math.asin(direction.y);this.orient();this.syncHands();this.onNavigation(null);}
 placeAt({position,target,yaw,pitch}){if(!this.current||!canStand(position[0],position[2],this.current))return false;this.land();this.cancelNavigation();this.keys.clear();this.touchMove={forward:0,side:0};this.station=null;this.camera.position.fromArray(position);const direction=new T.Vector3(...target).sub(this.camera.position).normalize();this.yaw=Number.isFinite(yaw)?yaw:Math.atan2(-direction.x,-direction.z);this.pitch=Number.isFinite(pitch)?pitch:Math.asin(direction.y);this.orient();this.syncHands();return true;}
 tickPassage(){if(!walkingAllowed(this)||this.navigation||this.action)return;const action=passageAt(this.camera.position,this.current?.passages);if(action)this.onPassage(action);}
 orient(){this.camera.rotation.order='YXZ';this.camera.rotation.y=this.yaw;this.camera.rotation.x=this.pitch;this.camera.rotation.z=0;}
 look(dx,dy=0){if(this.paused||this.options?.cover||this.painting||this.payment||this.tuho||this.meal||this.scanner||this.workshop||this.mapView||(this.action&&this.action.type!=='travel')||this.navigation)return;this.yaw+=dx;this.pitch=T.MathUtils.clamp(this.pitch+dy,-.68,.55);this.orient();}
 takeWalkingControl(){return takeWalkingControl(this);}
 land(){if(this.jumpMotion?.airborne)this.camera.position.y-=this.jumpMotion.height;this.jumpMotion?.reset();}
 jump(){
  if(this.id==='transit'||!walkingAllowed(this)||this.jumpMotion.airborne)return false;
  this.takeWalkingControl();this.station=null;this.syncHands();this.onNavigation(null);
  this.camera.position.y=walkingEyeHeight(this.id,this.camera.position.z);
  return this.jumpMotion.start();
 }
 tickJump(dt){if(!this.jumpMotion.airborne||!walkingAllowed(this))return;this.camera.position.y=walkingEyeHeight(this.id,this.camera.position.z)+this.jumpMotion.tick(dt);}
 move(amount,side=0){
  if((!amount&&!side)||!this.takeWalkingControl())return;
  const b=this.current.bounds,p=this.camera.position;const x=T.MathUtils.clamp(p.x-Math.sin(this.yaw)*amount+Math.cos(this.yaw)*side,...b.x),z=T.MathUtils.clamp(p.z-Math.cos(this.yaw)*amount-Math.sin(this.yaw)*side,...b.z);
  if(canStand(x,p.z,this.current))p.x=x;if(canStand(p.x,z,this.current))p.z=z;
  if(this.station){this.station=null;this.syncHands();this.onNavigation(null);}
  if(this.id!=='transit')p.y=walkingEyeHeight(this.id,p.z)+this.jumpMotion.height;
  if(!this.reduced)this.rig.position.y=Math.sin(this.clock*10)*.009;
 }
 syncHands(){this.chopsticks.visible=this.id==='meal'&&this.station==='table';this.brush.visible=this.id==='workshop'&&this.options.program==='mask'&&this.station==='table';const close=['table','counter'].includes(this.station);this.rig.visible=!this.options?.cover&&(!['meal','receipt','workshop'].includes(this.id)||close);}
 pickInteraction(){
  const hits=this.ray.intersectObjects(this.current?.group.children.filter(o=>!o.userData.scenery)||[],true);
  for(const hit of hits){if(hit.distance>4.5)return null;let node=hit.object,visible=true;for(let p=node;p;p=p.parent)if(!p.visible)visible=false;if(!visible)continue;
   if(hit.object.material?.transparent&&hit.object.material.opacity<.5)continue;
   while(node&&!node.userData.action)node=node.parent;return node||null;
  }return null;
 }
 interact(){if(this.focused&&!this.action&&!this.painting&&!this.payment&&!this.tuho&&!this.meal&&!this.workshop&&!this.scanner&&!this.navigation)this.onInteract(this.focused.userData.action);}
 updateFocus(){if(this.paused||this.options?.cover||!this.current||this.action||this.painting||this.payment||this.tuho||this.meal||this.workshop||this.scanner||this.navigation||this.options.cover){this.focused=null;this.onFocus(null);return;}this.ray.setFromCamera(new T.Vector2(0,0),this.camera);this.focused=this.pickInteraction();this.onFocus(this.focused?{name:this.focused.userData.name,action:this.focused.userData.action}:null);}
 cancelNavigation(){if(!this.navigation)return;const n=this.navigation;this.navigation=null;this.station=null;this.syncHands();this.onNavigation(null);n.resolve(false);}
 async approach(key){
  const station=this.current?.stations?.[key];if(!station)return true;this.land();this.cancelNavigation();this.keys.clear();this.touchMove={forward:0,side:0};
  const from=this.camera.position.clone(),to=new T.Vector3(...station.position);
  const aisle=this.current.refs.busCabin&&key==='alight'?station.waypoints:null;
  const path=aisle?[[from.x,from.z],...aisle.map(p=>[p[0],p[2]])]:planWalk([from.x,from.z],[to.x,to.z],this.current);if(!path)return false;
  if(this.station===key&&from.distanceTo(to)<.1)return true;
  const points=path.map((p,i)=>new T.Vector3(p[0],aisle&&i>0?aisle[i-1][1]:i===path.length-1?to.y:this.id==='bridge'?1.94:1.7,p[1]));points[0].copy(from);
  const lengths=points.slice(1).map((p,i)=>p.distanceTo(points[i])),distance=lengths.reduce((a,b)=>a+b,0);
  return new Promise(resolve=>{this.navigation={key,station,points,lengths,distance,elapsed:0,duration:this.reduced?.2:Math.max(.55,distance/2.6),fromYaw:this.yaw,fromPitch:this.pitch,resolve};this.station=null;this.rig.visible=false;this.onNavigation({name:station.name,progress:0});});
 }
 tickNavigation(dt){
  const n=this.navigation;if(!n)return;n.elapsed+=dt;const p=Math.min(1,n.elapsed/n.duration);let travelled=n.distance*p,index=0;
  while(index<n.lengths.length-1&&travelled>n.lengths[index]){travelled-=n.lengths[index];index++;}
  this.camera.position.lerpVectors(n.points[index],n.points[index+1],n.lengths[index]?travelled/n.lengths[index]:1);
  const target=new T.Vector3(...n.station.target),direction=target.sub(this.camera.position).normalize(),goalYaw=Math.atan2(-direction.x,-direction.z),goalPitch=Math.asin(direction.y);
  const turn=Math.min(1,p*2);this.yaw=n.fromYaw+Math.atan2(Math.sin(goalYaw-n.fromYaw),Math.cos(goalYaw-n.fromYaw))*turn;this.pitch=T.MathUtils.lerp(n.fromPitch,goalPitch,turn);this.orient();this.onNavigation({name:n.station.name,progress:p});
  if(p===1){this.station=n.key;this.navigation=null;this.syncHands();this.onNavigation(null);n.resolve(true);}
 }
 postcardTask(options){this.land();this.releaseGameLook();return new Promise(resolve=>{this.workshop=new PopupPostcard(this,{...options,resolve});});}
 paymentTask(options){this.land();this.releaseGameLook();return new Promise(resolve=>{this.payment=new PaymentInteraction(this,{...options,resolve});});}
 tuhoTask(options){this.land();this.releaseGameLook();return new Promise(resolve=>{this.tuho=new TuhoInteraction(this,{...options,resolve});});}
 mealTask(options){this.land();this.releaseGameLook();return new Promise(resolve=>{this.meal=new MealInteraction(this,{...options,resolve});});}
 scanTask(onUpdate){this.land();this.releaseGameLook();return new Promise(resolve=>{this.scanner=new ReceiptScan(this,{onUpdate,resolve});});}
 workshopTask(options){this.land();this.releaseGameLook();if(!this.current?.refs.workTargets?.length)return Promise.resolve(false);return new Promise(resolve=>{this.workshop=new WorkshopInteraction(this,{...options,resolve});});}
 toggleRouteView(){if(this.id!=='transit')return false;this.mapView=!this.mapView;this.current.refs.routeMap.visible=this.mapView;if(this.mapView){this.mapObjects=this.current.group.children.filter(o=>o!==this.current.refs.routeMap).map(o=>[o,o.visible]);for(const [o] of this.mapObjects)o.visible=false;const height=innerWidth<700?36:23;this.camera.position.set(80,height,height);this.camera.lookAt(80,0,0);}else{for(const [o,visible] of this.mapObjects||[])o.visible=visible;this.resetView();}return this.mapView;}
 paintTask({color,step,onProgress}){
  this.land();this.releaseGameLook();
  const face=this.current?.refs.mask?.userData.face;if(!face)return Promise.resolve(false);this.paintView={position:this.camera.position.clone(),rotation:this.camera.rotation.clone()};this.station='table';this.syncHands();this.camera.position.set(0,1.65,1.15);this.camera.lookAt(0,.98,0);this.keys.clear();
  const c=document.createElement('canvas');c.width=c.height=512;const ctx=c.getContext('2d');ctx.fillStyle=face.material.color.getStyle();ctx.fillRect(0,0,512,512);if(face.material.map?.image)ctx.drawImage(face.material.map.image,0,0,512,512);
  const tx=new T.CanvasTexture(c);tx.colorSpace=T.SRGBColorSpace;const originalMaterial=face.material,originalTexture=this.current.refs.paintTexture,originalOwned=this.current.refs.paintMaterial;const material=face.material.clone();material.color.set('#ffffff');material.map=tx;face.material=material;this.current.refs.paintTexture=tx;this.current.refs.paintMaterial=material;
  return new Promise(resolve=>{this.painting={face,ctx,tx,material,originalMaterial,originalTexture,originalOwned,color:step===1?'#be5b48':step===2?'#53392d':color,cells:new Set(),onProgress,resolve};});
 }
 paintAt(e){const p=this.painting;if(!p)return;const r=this.renderer.domElement.getBoundingClientRect();this.ray.setFromCamera(new T.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),this.camera);const hit=this.ray.intersectObject(p.face,false)[0];if(!hit?.uv)return;const brushPoint=this.camera.worldToLocal(hit.point.clone());this.rightHand.position.set(brushPoint.x,brushPoint.y-.3,brushPoint.z+.02);this.rightHand.rotation.set(0,0,0);this.paintUV(hit.uv.x,hit.uv.y);}
 paintUV(u,v){const p=this.painting;if(!p)return;const x=u*512,y=(1-v)*512;p.ctx.fillStyle=p.color;p.ctx.beginPath();p.ctx.arc(x,y,15,0,Math.PI*2);p.ctx.fill();p.tx.needsUpdate=true;p.cells.add(Math.floor(x/18)+','+Math.floor(y/18));const progress=Math.min(1,p.cells.size/14);p.onProgress(progress);if(progress===1){const resolve=p.resolve;this.painting=null;p.originalTexture?.dispose();p.originalOwned?.dispose();this.restorePaintView();resolve(true);}}
 paintAssist(){const p=this.painting;if(!p)return;const row=p.assistRow||0;p.assistRow=row+1;for(let i=0;i<4;i++)this.paintUV(.19+i*.04,.43+(row%5)*.04);}
 restorePaintView(){if(this.paintView){this.camera.position.copy(this.paintView.position);this.camera.rotation.copy(this.paintView.rotation);this.paintView=null;}this.resetHands();}
 maskArtwork(){return this.current?.refs.paintTexture?.image?.toDataURL?.('image/png')||null;}
 cancelPaint(success=false){if(this.painting){const p=this.painting;if(!success){p.face.material=p.originalMaterial;p.tx.dispose();p.material.dispose();this.current.refs.paintTexture=p.originalTexture;this.current.refs.paintMaterial=p.originalOwned;}else{p.originalTexture?.dispose();p.originalOwned?.dispose();}this.painting=null;this.restorePaintView();p.resolve(success);}}
 setPaused(paused){this.paused=paused;this.audio.setPaused(paused||document.hidden||!!this.options?.cover);if(paused){this.releaseGameLook();this.workshop?.cancelPointer();this.meal?.cancelPointer();this.tuho?.cancelPointer();this.payment?.cancelPointer();}this.keys.clear();this.touchMove={forward:0,side:0};}
 setQuality(low){this.lowQuality=low;this.renderer.setPixelRatio(low?1:Math.min(devicePixelRatio,1.7));this.renderer.shadowMap.enabled=!low;this.resize();}
 cancelAction(){if(this.action){if(this.action.type==='serve'&&this.current?.refs.food){this.current.refs.food.position.set(0,.78,0);this.current.refs.food.rotation.y=0;}this.action.resolve(false);this.action=null;}}
 async act(type,payload={}){
  if(this.disposed)return false;this.land();this.cancelAction();this.resetHands();if(type==='travel'&&this.current?.refs.busCabin){this.busProgress=0;this.current.refs.busCabin.reset();this.resetView();}
  return new Promise(resolve=>{const duration=this.reduced ? .25 : ({travel:this.current?.refs.busCabin?34:7,walk:5.5,scan:1.8,enter:1.1,game:1.4,serve:1.8}[type]||1.6);this.action={type,payload,duration,elapsed:0,resolve,from:this.camera.position.clone(),gameOrigin:this.camera.localToWorld(new T.Vector3(.18,-.12,-.55))};});
 }
 resetHands(){if(this.tastingCup)this.tastingCup.visible=false;if(this.popupBag)this.popupBag.visible=this.id==='popup'&&!!this.options?.cart?.length;poseHand(this.rightHand,'relaxed');poseHand(this.leftHand,'relaxed');this.receipt.visible=this.id==='receipt'&&!!this.options?.paid;this.rightHand.position.set(.38,this.id==='workshop'?-.72:-.46,-.71);this.rightHand.rotation.set(-.4,-.2,.4);this.leftHand.position.set(-.35,this.id==='workshop'?-.72:-.43,-.72);this.leftHand.rotation.set(-.35,.2,-.4);this.phone.visible=this.id==='receipt';this.bite.visible=false;if(this.popupBag?.visible){this.rightHand.position.set(.43,-.42,-.9);this.rightHand.rotation.set(0,.2,-.1);poseHand(this.rightHand,'pinch');}}
 tickAction(dt){
  const a=this.action;if(!a)return;a.elapsed+=dt;const p=Math.min(1,a.elapsed/a.duration),ease=p*p*(3-2*p),wave=Math.sin(p*Math.PI);const refs=this.current.refs;
  if(a.type==='serve'&&refs.food){refs.food.position.set((1-ease)*1.15,.78+Math.sin((1-ease)*Math.PI/2)*.25,(1-ease)*-.35);refs.food.rotation.y=(1-ease)*.18;}
  if(a.type==='enter'&&refs.entryDoor){refs.entryDoor.rotation.y=-ease*Math.PI*.47;this.camera.position.z=T.MathUtils.lerp(a.from.z,-21.05,ease);}
  if(a.type==='eat'){this.rightHand.position.set(.2,-.44+wave*.36,-.8+wave*.35);this.rightHand.rotation.z=.4-wave*.8;this.bite.visible=p>.2&&p<.8;}
  if(a.type==='scan'||a.type==='redeem'){this.leftHand.position.y=-.43+wave*.2;this.phone.visible=true;}
  if(a.type==='mask'){this.rightHand.position.set(.15+Math.sin(p*Math.PI*4)*.08,-.4,-.85);this.rightHand.rotation.x=-.65;}
  if(a.type==='tea'&&refs.teapot){const step=this.options.craftSteps;if(step===0&&refs.flowers){refs.flowers.visible=true;refs.flowers.position.y=(1-p)*.22;}else{refs.teapot.rotation.z=-wave*.5;refs.teapot.position.y=.82+wave*.17;if(refs.teaStream)refs.teaStream.visible=p>.25&&p<.85&&step===2;}this.rightHand.position.set(.1,-.35,-.82);}
  if(a.type==='soju'){this.rightHand.position.x=.28-wave*.17;this.rightHand.position.y=-.4+wave*.09;if(refs.bottle&&this.options.craftSteps===2)refs.bottle.rotation.z=Math.sin(p*Math.PI*3)*.12;if(refs.distill)refs.distill.visible=this.options.craftSteps===1&&p>.2&&p<.9;}
  if(a.type==='walk'){this.camera.position.z=T.MathUtils.lerp(a.from.z,-9,ease);}
  if(a.type==='travel'){this.busProgress=p;if(refs.roadside)refs.roadside.position.z=p*40;if(refs.city&&!refs.busCabin)refs.city.position.z=p*40;if(!this.mapView&&!refs.busCabin)this.camera.position.x=a.from.x+(this.reduced?0:Math.sin(p*Math.PI)*.03);if(refs.routeMarker){refs.routeMarker.position.copy(refs.routeCurve.getPointAt(p));refs.routeMarker.position.y+=.5;}this.onTravel(p);}
  if(a.type==='taste'){this.popupBag.visible=false;this.rig.visible=true;this.rightHand.visible=true;this.tastingCup.visible=true;this.rightHand.position.set(.18-wave*.12,-.4+wave*.29,-.67+wave*.31);this.rightHand.rotation.set(-wave*.6,0,-.1);poseHand(this.rightHand,'pinch');}
  if(a.type==='buy'){this.popupBag.visible=true;this.rightHand.visible=true;this.rightHand.position.set(.2,-.45+wave*.14,-.71-wave*.2);}
  if(a.type==='game'&&refs.arrow){refs.arrow.visible=p<1;const end=a.payload.end?new T.Vector3(...a.payload.end):refs.target.clone();if(!a.payload.end&&!a.payload.hit)end.x+=1;refs.arrow.position.lerpVectors(a.gameOrigin,end,p);refs.arrow.position.y+=Math.sin(p*Math.PI)*.8;refs.arrow.rotation.x=p*Math.PI*.9;}
  if(p>=1){if(a.type==='serve')this.audio.cue('dish');if(a.type==='travel'&&this.mapView)this.toggleRouteView();a.resolve(true);this.action=null;this.resetHands();}
 }
 watchPerformance(){if(this.id!=='popup')return;this.rig.visible=false;const s=this.current.stations.performance;this.camera.position.fromArray(s.position);this.camera.lookAt(...s.target);}
 requestBusStop(){if(this.current?.refs.busCabin?.requestStop()){this.audio.cue('bell');return true;}return false;}
 capturePhoto(){this.releaseGameLook();const visible=this.rig.visible;this.rig.visible=false;try{this.lighting.render(this.scene,this.camera,!this.lowQuality&&this.container.clientWidth>=700,this.useContactShadows,!!this.current?.night);return this.renderer.domElement.toDataURL('image/png');}finally{this.rig.visible=visible;}}
 fountain(){if(this.current?.refs.fountain)this.current.refs.fountain.visible=!this.current.refs.fountain.visible;}
 animate(){if(this.disposed)return;this.frame=requestAnimationFrame(()=>this.animate());const now=performance.now(),dt=Math.min((now-this.last)/1000,.045);this.last=now;if(document.hidden||this.paused)return;
  this.clock+=dt;const soundX=this.camera.position.x,soundZ=this.camera.position.z;
  if(this.current&&!this.action&&!this.navigation){const intent=walkIntent(this.keys),speed=this.keys.has('shift')?3.8:2;this.look(intent.turn*dt*.95);this.move((intent.forward+this.touchMove.forward)*dt*speed,(intent.side+this.touchMove.side)*dt*speed);}
  if(this.current?.refs.busCabin){const riding=this.action?.type==='travel',p=this.busProgress||0;this.current.refs.tickBus(this.clock,p,riding&&!this.reduced?Math.sin(p*Math.PI):0,this.reduced);this.audio.setRide(riding?Math.sin(p*Math.PI):0);}
  this.tickJump(dt);this.tickPassage();this.updateFocus();this.tickNavigation(dt);this.tickAction(dt);this.meal?.tick(dt);this.payment?.tick(dt);this.workshop?.tick(dt);this.scanner?.tick(dt);const refs=this.current?.refs;refs?.life?.update(this.clock,this.reduced);refs?.parkedBus?.update(this.clock,{doorOpen:1,reduced:this.reduced});advanceRiverWater(refs?.water,dt,this.reduced);if(refs?.boats&&!this.reduced)refs.boats.forEach((b,i)=>{const surface=riverSurfaceAt(b.position.x,b.position.z,refs.water?.material.uniforms.uTime.value??this.clock);b.userData.floatBaseY??=b.position.y;b.position.y=b.userData.floatBaseY+surface.height;b.rotation.x=surface.slopeZ*.65;b.rotation.z=-surface.slopeX*.65;b.rotation.y=Math.sin(this.clock*.08+i)*.22;});
  if(refs?.mealSteam&&!this.reduced)refs.mealSteam.children.forEach(s=>{s.position.y=((this.clock*.2+s.userData.phase)%1)*.4;s.position.x=Math.sin(this.clock*.5+s.userData.phase)*.15;s.scale.set(.12+s.position.y*.2,.2+s.position.y*.3,1);s.material.opacity=.13*Math.sin(s.position.y/.4*Math.PI);});
  if(refs?.steam&&!this.reduced)refs.steam.children.filter(s=>s.isSprite).forEach(s=>{s.position.y=((this.clock*.12+s.userData.phase)%1)*.3;s.position.x=Math.sin(this.clock*.4+s.userData.phase)*.025;s.scale.set(.07+s.position.y*.1,.11+s.position.y*.28,1);s.material.opacity=.065*Math.sin(s.position.y/.3*Math.PI);});
  if(refs?.marketSteam&&!this.reduced)refs.marketSteam.forEach(s=>{const t=(this.clock*.55+s.userData.phase)%1,[x,y,z]=s.userData.origin;s.position.set(x+Math.sin(t*6+s.userData.phase)*.035,y+t*.4,z);s.scale.set(.13+t*.18,.2+t*.2,1);s.material.opacity=.12*Math.sin(t*Math.PI);});
  if(refs?.dancer&&!this.reduced){refs.dancer.rotation.y=Math.sin(this.clock*1.8)*.25;refs.dancer.position.y=(refs.dancer.userData.baseY??.2)+Math.abs(Math.sin(this.clock*2.2))*.04;refs.dancer.userData.arms?.forEach((arm,i)=>{arm.rotation.z=(i?1:-1)*(.95+Math.sin(this.clock*1.8+i)*.5);arm.rotation.x=-.25+Math.cos(this.clock*1.8+i)*.3;});}
  if(refs?.entryDoor&&this.action?.type!=='enter'){const near=this.camera.position.z<-18.2&&Math.abs(this.camera.position.x)<1.7;const previous=refs.entryDoor.rotation.y;refs.entryDoor.rotation.y=T.MathUtils.damp(previous,near?-Math.PI*.47:0,8,dt);if(Math.abs(previous-refs.entryDoor.rotation.y)>.001)this.renderer.shadowMap.needsUpdate=true;}
  if(refs?.fan&&!this.reduced)refs.fan.rotation.z=this.clock*8;
  if(refs?.people&&!this.reduced)refs.people.forEach((p,i)=>{const t=this.clock+i*1.7;p.userData.head.rotation.y=Math.sin(t*.45)*.15;if(p.userData.torso)p.userData.torso.scale.x=1+Math.sin(t*1.6)*.008;if(p.userData.cooking){p.userData.head.rotation.x=.12;p.userData.arms?.forEach((arm,j)=>{arm.rotation.x=Math.sin(t*1.8+j)*.09;arm.rotation.y=Math.sin(t*1.8+j)*.16;});}});if(this.meal||this.workshop||this.payment||this.painting||(!this.reduced&&refs?.life&&Math.floor(this.clock*8)!==this.lifeShadowFrame)){this.renderer.shadowMap.needsUpdate=true;this.lifeShadowFrame=Math.floor(this.clock*8);}if(this.current){const c=this.renderer.domElement;c.dataset.scene=this.id;c.dataset.position=this.camera.position.toArray().map(n=>n.toFixed(3)).join(',');c.dataset.airborne=String(this.jumpMotion.airborne);if(this.id==='popup'){const zone=popupZoneAt(this.camera.position.x,this.camera.position.z);c.dataset.popupZone=zone;this.onLocation(zone);}}
  this.audio.walk(Math.hypot(this.camera.position.x-soundX,this.camera.position.z-soundZ),this.jumpMotion.airborne);
  this.lighting.render(this.scene,this.camera,!this.lowQuality&&this.container.clientWidth>=700,this.useContactShadows,!!this.current?.night);
 }
 disposeSet(s){s.refs.life?.dispose();s.refs.parkedBus?.dispose();s.refs.busCabin?.dispose();s.refs.paintTexture?.dispose();s.refs.paintMaterial?.dispose();s.refs.water?.userData.dispose?.();s.kit.dispose();}
 dispose(){this.audio.dispose();this.releaseGameLook();this.disposed=true;cancelAnimationFrame(this.frame);this.payment?.finish(false);this.tuho?.finish(null);this.meal?.finish(false);this.scanner?.finish(false);this.workshop?.finish(false);this.cancelPaint();this.cancelAction();this.cancelNavigation();this.receiptSlip?.dispose();Object.values(this.skies).forEach(tx=>tx.dispose());this.events.abort();this.resizeObserver.disconnect();for(const s of this.cache.values())this.disposeSet(s);this.cache.clear();this.kit.dispose();this.lighting.dispose();this.renderer.dispose();this.renderer.domElement.remove();}
}
