import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {GTAOPass} from 'three/addons/postprocessing/GTAOPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {Vector2} from 'three';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';

// The stock normal pass includes transparent meshes, making steam look solid.
class TransparentAwareGTAO extends GTAOPass{
 _overrideVisibility(){super._overrideVisibility();this.scene.traverse(o=>{if(o.visible&&(o.isSprite||(o.material?.transparent&&o.material.opacity<.9))){o.visible=false;this._visibilityCache.push(o);}});}
}

// Contact shading gives curved utensils, chair legs and food a shared surface.
// The inexpensive renderer remains available on small screens and in light mode.
export class RelayLighting{
 constructor(renderer,scene,camera){
  this.renderer=renderer;this.scene=scene;this.camera=camera;
 }
 initialize(){
  if(this.composer)return;
  const {renderer,scene,camera}=this;this.composer=new EffectComposer(renderer);
  this.renderPass=new RenderPass(scene,camera);this.ao=new TransparentAwareGTAO(scene,camera,640,360);
  this.ao.blendIntensity=.65;this.ao.updateGtaoMaterial({radius:.32,thickness:.16,distanceExponent:1.5,distanceFallOff:1,scale:1});
  this.bloom=new UnrealBloomPass(new Vector2(640,360),.16,.38,1.25);this.output=new OutputPass();this.composer.addPass(this.renderPass);this.composer.addPass(this.ao);this.composer.addPass(this.bloom);this.composer.addPass(this.output);
  if(this.size)this.resize(...this.size);
 }
 resize(w,h){this.size=[w,h];if(!this.composer)return;this.composer.setPixelRatio(Math.min(this.renderer.getPixelRatio(),1.25));this.composer.setSize(w,h);this.ao.setSize(Math.round(w*.8),Math.round(h*.8));}
 render(scene,camera,enabled,ao=true,night=false){if(enabled){this.initialize();this.ao.enabled=ao;this.bloom.enabled=night;this.composer.render();}else this.renderer.render(scene,camera);}
 dispose(){this.bloom?.dispose();this.ao?.dispose();this.renderPass?.dispose();this.output?.dispose();this.composer?.dispose();}
}
