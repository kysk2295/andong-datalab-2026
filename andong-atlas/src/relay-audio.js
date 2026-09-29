// Quiet synthesized cooking / footstep / crockery sounds, not field recordings.
// No context is created until a user gesture. Failure leaves the experience usable.
export class RelayAudio{
 constructor({AudioContext=globalThis.AudioContext||globalThis.webkitAudioContext,enabled=true}={}){
  this.AudioContext=AudioContext;this.enabled=enabled;this.paused=false;this.location='';this.distance=0;this.closed=false;this.ride=0;
 }
 async unlock(){
  if(this.closed||!this.enabled||!this.AudioContext)return;
  try{
   if(!this.ctx){
    const ctx=this.ctx=new this.AudioContext();this.master=ctx.createGain();this.master.gain.value=0;this.master.connect(ctx.destination);
    this.noise=ctx.createBuffer(1,ctx.sampleRate*2,ctx.sampleRate);const data=this.noise.getChannelData(0);let last=0;
    for(let i=0;i<data.length;i++){last=(last+.04*(Math.random()*2-1))/1.04;data[i]=last*4;}
    this.ambient=ctx.createBufferSource();this.ambient.buffer=this.noise;this.ambient.loop=true;
    const filter=ctx.createBiquadFilter();filter.type='highpass';filter.frequency.value=750;this.ambient.connect(filter);
    this.room=ctx.createGain();filter.connect(this.room);this.room.connect(this.master);this.ambient.start();
    this.motor=ctx.createOscillator();this.motor.type='sine';this.motor.frequency.value=48;this.motorGain=ctx.createGain();this.motorGain.gain.value=0;this.motor.connect(this.motorGain);this.motorGain.connect(this.master);this.motor.start();
   }
   if(!this.paused&&this.ctx.state==='suspended')await this.ctx.resume();this.apply();
  }catch{this.setEnabled(false);}
 }
 setEnabled(value){this.enabled=!!value;this.apply();}
 setPaused(value){this.paused=!!value;this.apply();}
 setLocation(value){this.location=value;this.distance=0;if(value!=='transit')this.ride=0;this.apply();}
 setRide(value){const ride=this.location==='transit'?Math.max(0,Math.min(1,value)):0;if(ride===this.ride||(Math.abs(ride-this.ride)<.015&&ride!==0))return;this.ride=ride;this.apply();}
 apply(){
  if(!this.ctx||this.closed)return;const now=this.ctx.currentTime;
  this.master.gain.setTargetAtTime(this.enabled&&!this.paused?.36:0,now,.08);
  this.room.gain.setTargetAtTime(this.location==='market'?.075:['meal','receipt','popup'].includes(this.location)?.035:0,now,.35);
  this.motorGain?.gain.setTargetAtTime(this.ride*.025,now,.25);this.motor?.frequency.setTargetAtTime(48+this.ride*28,now,.35);
 }
 get audible(){return !this.closed&&this.enabled&&!this.paused&&this.ctx?.state==='running';}
 walk(distance,airborne=false){
  if(!this.audible||airborne||!Number.isFinite(distance)||distance<=0||distance>.8)return;
  this.distance+=distance;if(this.distance<.78)return;this.distance%=.78;this.step();
 }
 step(){
  if(!this.audible)return;const c=this.ctx,t=c.currentTime,s=c.createBufferSource(),filter=c.createBiquadFilter(),gain=c.createGain();
  s.buffer=this.noise;filter.type='lowpass';filter.frequency.value=this.location==='bridge'?420:900;
  s.connect(filter);filter.connect(gain);gain.connect(this.master);gain.gain.setValueAtTime(.22,t);gain.gain.exponentialRampToValueAtTime(.001,t+.105);
  s.start(t,Math.random());s.stop(t+.12);s.onended=()=>{s.disconnect();filter.disconnect();gain.disconnect();};
 }
 cue(kind='dish'){
  if(!this.audible)return;const c=this.ctx,t=c.currentTime,osc=c.createOscillator(),gain=c.createGain();
  osc.type='sine';osc.frequency.setValueAtTime(kind==='bell'?660:kind==='payment'?880:2350,t);osc.frequency.exponentialRampToValueAtTime(kind==='bell'?520:kind==='payment'?740:1700,t+.12);
  gain.gain.setValueAtTime(kind==='payment'?.025:.016,t);gain.gain.exponentialRampToValueAtTime(.0001,t+.16);
  osc.connect(gain);gain.connect(this.master);osc.start();osc.stop(t+.18);osc.onended=()=>{osc.disconnect();gain.disconnect();};
 }
 dispose(){this.closed=true;this.ambient?.stop();this.motor?.stop();this.master?.disconnect();this.ctx?.close().catch(()=>{});}
}
