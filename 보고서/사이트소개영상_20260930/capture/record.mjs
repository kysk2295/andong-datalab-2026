// 지도 장면을 카메라 경로의 각 프레임마다 실제 WebGL로 렌더해 기록한다(보간 없음).
// 경로는 베지어 제어점(p: 카메라, t: 바라보는 점)과 사인 가속으로 드론처럼 부드럽게 움직인다.
import fs from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {once} from 'node:events';

export async function recordFrames(page,out,spec){
 const fps=30,frames=Math.round(spec.duration*fps);
 const encoder=spawn('/opt/homebrew/bin/ffmpeg',['-hide_banner','-loglevel','error','-y','-f','image2pipe','-vcodec','mjpeg','-framerate',String(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',`${out}/clips/${spec.file}`],{stdio:['pipe','ignore','pipe']});
 let error='';encoder.stderr.on('data',d=>error+=d);const done=once(encoder,'close');
 const began=Date.now();
 for(let i=0;i<frames;i++){
  for(const ev of spec.events||[])if(ev.frame===i){
   if(ev.click)await page.click(ev.click,{force:true});
   if(ev.js)await page.evaluate(ev.js);
   if(ev.wait)await page.waitForTimeout(ev.wait);
  }
  await page.evaluate(({i,fps,spec})=>{
   const bez=(pts,u)=>{let q=pts.map(p=>p.slice());while(q.length>1)q=q.slice(1).map((p,k)=>p.map((n,j)=>q[k][j]+(n-q[k][j])*u));return q[0];};
   const t=i/fps,raw=Math.max(0,Math.min(1,(t-(spec.lead||0))/(spec.move||spec.duration)));
   const e=spec.ease==='linear'?raw:spec.ease==='out'?Math.sin(raw*Math.PI/2):(1-Math.cos(raw*Math.PI))/2;
   if(spec.orbit){const o=spec.orbit,a=(o.a0+(o.a1-o.a0)*e)*Math.PI/180,r=o.r0+(o.r1-o.r0)*e,h=o.h0+(o.h1-o.h0)*e;__mapStep([o.c[0]+Math.cos(a)*r,o.c[1]+h,o.c[2]+Math.sin(a)*r],o.c,1/fps,spec.force);}else if(spec.p)__mapStep(bez(spec.p,e),bez(spec.t,e),1/fps,spec.force);else __mapStep(null,null,1/fps);
   if(spec.cursor){const c=spec.cursor;let a=c[0],b=c[c.length-1];for(let k=0;k<c.length-1;k++)if(i>=c[k].f&&i<=c[k+1].f){a=c[k];b=c[k+1];}
    const u=b.f===a.f?1:Math.max(0,Math.min(1,(i-a.f)/(b.f-a.f))),s=(1-Math.cos(u*Math.PI))/2;__cursor(a.x+(b.x-a.x)*s,a.y+(b.y-a.y)*s,!!b.down&&u>.9);}
  },{i,fps,spec});
  const frame=await page.screenshot({type:'jpeg',quality:93,animations:'allow'});
  if(!encoder.stdin.write(frame))await once(encoder.stdin,'drain');
  if([0,Math.floor(frames/2),frames-1].includes(i))await fs.writeFile(`${out}/stills/${spec.id}-${i}.jpg`,frame);
 }
 encoder.stdin.end();const [code]=await done;if(code!==0)throw new Error(error);
 const result={id:spec.id,file:spec.file,fps,frames,method:'actual WebGL frame capture',elapsed:(Date.now()-began)/1000};
 await fs.writeFile(`${out}/capture/${spec.id}.json`,JSON.stringify({...spec,...result},null,1));return result;
}
