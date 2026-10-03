import fs from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {once} from 'node:events';

// Record each actual WebGL frame at its authored camera pose. This avoids
// uneven real-time frame delivery in the dense night scene; no interpolation.
export async function recordFrames(page,out,spec){
 const fps=30,frames=Math.round(spec.duration*fps);
 const encoder=spawn('/opt/homebrew/bin/ffmpeg',['-hide_banner','-loglevel','error','-y','-f','image2pipe','-vcodec','mjpeg','-framerate',String(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',`${out}/clips/${spec.file}`],{stdio:['pipe','ignore','pipe']});
 let error='';encoder.stderr.on('data',d=>error+=d);const done=once(encoder,'close');
 await page.evaluate(spec=>{__film.scene.paused=true;__film.scene.rig.visible=!!spec.hands;},spec);
 const began=Date.now();
 for(let i=0;i<frames;i++){
  await page.evaluate(({i,fps,spec})=>{
   const s=__film.scene,t=i/fps,p=Math.max(0,Math.min(1,(t-(spec.lead||0))/spec.move)),e=p*p*(3-2*p);
   __pose(spec.from.map((n,k)=>n+(spec.to[k]-n)*e),spec.target.map((n,k)=>n+(spec.targetTo[k]-n)*e));
   if(spec.nativeTaste){if(i===30){s.station='tea';void __film.popupTaste('tea');}s.tickAction(1/fps);}
   if(s.current.refs.water)s.current.refs.water.material.uniforms.uTime.value=90+t;
   if(s.current.refs.boats)s.current.refs.boats.forEach((b,k)=>{b.position.y=Math.sin((90+t)*.7+k)*.035;b.rotation.y=Math.sin((90+t)*.08+k)*.22;});
   Object.getPrototypeOf(s.lighting).render.call(s.lighting,s.scene,s.camera,true,false,true);
  },{i,fps,spec});
  const frame=await page.screenshot({type:'jpeg',quality:94,animations:'allow'});
  if(!encoder.stdin.write(frame))await once(encoder.stdin,'drain');
  if([0,Math.floor(frames/2),frames-1].includes(i))await fs.writeFile(`${out}/stills/${spec.id}-${i}.jpg`,frame);
  if(i%30===0)await fs.writeFile(`${out}/production/frame-progress.json`,JSON.stringify({shot:spec.id,frame:i,total:frames,elapsed:(Date.now()-began)/1000}));
 }
 encoder.stdin.end();const [code]=await done;if(code!==0)throw new Error(error);
 const result={...spec,fps,frames,method:'actual WebGL frame capture, no optical-flow interpolation',elapsed:(Date.now()-began)/1000};
 await fs.writeFile(`${out}/production/${spec.id}-capture.json`,JSON.stringify(result,null,2));return result;
}
