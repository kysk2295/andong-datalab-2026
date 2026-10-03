(()=>{
 const s=__atlas;s.controls.maxPolarAngle=Math.PI*.495;s.controls.minDistance=.02;s.controls.enableDamping=false;
 const style=document.createElement('style');style.id='film-style';style.textContent=`
 body.film-clean .atlas-masthead,body.film-clean #explore,body.film-clean .explore,body.film-clean .environment,body.film-clean .toolbar,body.film-clean #atlas-route,body.film-clean .location,body.film-clean .map-scope,body.film-clean .map-label,body.film-clean [class*="label"],body.film-clean .explore-toggle,body.film-clean #detail-status,body.film-clean #district-note,body.film-clean .attribution,body.film-clean .map-attribution,body.film-clean .map-tools,body.film-clean .gis-point-layer,body.film-clean #labels,body.film-clean .gesture-hint,body.film-clean footer,body.film-clean .tourism-info{visibility:hidden!important}
 #film-cursor{position:fixed;left:0;top:0;width:30px;height:30px;z-index:99999;pointer-events:none;transform-origin:4px 3px;filter:drop-shadow(0 2px 3px rgba(0,0,0,.35))}
 *{cursor:none!important}`;document.head.append(style);
 const c=document.createElement('div');c.id='film-cursor';c.hidden=true;c.innerHTML='<svg viewBox="0 0 24 24" width="30" height="30"><path d="M4 2.5v17.2l4.6-4.3 3 6.6 3-1.3-3-6.5h6.3z" fill="#fff" stroke="#1d1d1d" stroke-width="1.4" stroke-linejoin="round"/></svg>';document.body.append(c);
 window.__cursor=(x,y,down)=>{c.hidden=false;c.style.transform=`translate(${x-4}px,${y-3}px) scale(${down?.86:1})`;};
 window.__hideCursor=()=>{c.hidden=true;};
 window.__pose=()=>({p:s.camera.position.toArray(),t:s.controls.target.toArray()});
 window.__mapStep=(p,t,dt,force)=>{s.flight=null;s.autoDetail=false;if(p){s.camera.position.fromArray(p);s.controls.target.fromArray(t);}s.clock.getDelta=()=>dt;s.destroyed=false;s.animate();cancelAnimationFrame(s.frame);s.destroyed=true;if(force&&p){s.camera.position.fromArray(p);s.camera.lookAt(s.controls.target);s.renderer.render(s.scene,s.camera);}};
 window.__live=()=>{delete s.clock.getDelta;s.destroyed=false;s.animate();};
})();
