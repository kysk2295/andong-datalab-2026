(() => {
 const style=document.createElement('style');style.textContent=`
 .relay-play-header,.relay-header,.relay-reticle,#relay-interact,.relay-control,#relay-status,#relay-walking,#relay-popup-return,.relay-mobile-look{visibility:hidden!important;pointer-events:none!important}
 .relay-shade{opacity:.25!important}#relay-trip-progress{visibility:hidden!important}
 body[data-film-task="off"] #relay-work-task,body[data-film-task="off"] #relay-mouth,body[data-film-task="off"] #relay-paint-task{visibility:hidden!important}
 #relay-work-task{left:auto!important;right:56px!important;bottom:50px!important;width:420px!important;max-width:420px!important;transform:none!important;background:rgba(19,32,30,.88)!important}
 #relay-work-controls,.work-task-footer{display:none!important}
 *{cursor:none!important}
 `;document.head.append(style);document.body.dataset.filmTask='off';
 window.__pose=(position,target)=>{const s=__film.scene;s.camera.position.fromArray(position);s.camera.lookAt(...target);s.camera.rotation.order='YXZ';s.yaw=s.camera.rotation.y;s.pitch=s.camera.rotation.x;};
 window.__cam=async({from,to,target,targetTo=target,seconds=8})=>{
  const s=__film.scene;s.cancelNavigation();s.keys.clear();s.touchMove={forward:0,side:0};
  __pose(from,target);const start=performance.now();let last=from;
  await new Promise(resolve=>{function tick(now){const p=Math.min(1,(now-start)/(seconds*1000)),e=p*p*(3-2*p),v=from.map((n,i)=>n+(to[i]-n)*e),t=target.map((n,i)=>n+(targetTo[i]-n)*e);__pose(v,t);s.audio.walk(Math.hypot(v[0]-last[0],v[2]-last[2]));last=v;if(p<1)requestAnimationFrame(tick);else resolve();}requestAnimationFrame(tick);});
 };
 window.__night=()=>{const s=__film.scene;if(!s.current.night)return;s.ambient.intensity=.95;s.ambient.color.set('#a6c2ea');s.ambient.groundColor.set('#343c42');s.sun.intensity=1.35;s.fill.intensity=.42;s.scene.environmentIntensity=.28;s.scene.backgroundIntensity=.13;s.renderer.toneMappingExposure=1.32;s.lighting.bloom.strength=.20;s.renderer.shadowMap.needsUpdate=true;};
 window.__audioStart=async()=>{const a=__film.scene.audio;await a.unlock();a.setEnabled(true);a.setPaused(false);const dest=a.ctx.createMediaStreamDestination();a.master.connect(dest);const recorder=new MediaRecorder(dest.stream,{mimeType:'audio/webm;codecs=opus'});const chunks=[];recorder.ondataavailable=e=>chunks.push(e.data);recorder.start();window.__audio={recorder,chunks,dest,master:a.master};};
 window.__audioStop=()=>new Promise(resolve=>{const a=__audio;a.recorder.onstop=async()=>{a.master.disconnect(a.dest);const blob=new Blob(a.chunks,{type:'audio/webm'});const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.readAsDataURL(blob);};a.recorder.stop();});
})();
