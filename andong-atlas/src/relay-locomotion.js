// Metres and seconds: the same arc at every render rate, with one impulse per press.
export class JumpMotion {
 constructor(){this.reset();}
 reset(){this.height=0;this.velocity=0;this.airborne=false;}
 start(){if(this.airborne)return false;this.velocity=3.8;this.height=0;this.airborne=true;return true;}
 tick(dt){
  if(!this.airborne||dt<=0)return this.height;
  this.height+=this.velocity*dt-4.9*dt*dt;this.velocity-=9.8*dt;
  if(this.height<=0&&this.velocity<0)this.reset();
  return this.height;
 }
}
export function walkingAllowed(scene){
 return !!scene.current&&!scene.paused&&!scene.options?.cover&&!scene.action&&!scene.painting&&!scene.payment&&!scene.tuho&&!scene.meal&&!scene.workshop&&!scene.scanner&&!scene.mapView;
}
// A manual movement command always takes over from assisted walking.
export function takeWalkingControl(scene){
 if(!walkingAllowed(scene))return false;
 scene.cancelNavigation();return true;
}
export function walkingEyeHeight(id,z){
 if(id==='bridge'){const clamp=x=>Math.min(1,Math.max(0,x));return 1.94+.24*clamp((-z-8.7)/2.8)*clamp((z+19.5)/2.8);}
 return 1.7;
}
