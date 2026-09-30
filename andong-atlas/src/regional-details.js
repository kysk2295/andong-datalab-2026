import { DistrictScene } from './district-scene.js';
import { regionFor } from './region-model.js';
import index from '../public/data/regions.json' with {type:'json'};
import {loadJSON} from './loading.js';

// Keep the city and at most two other GPU scenes. Payloads remain local files,
// loaded only when the visitor approaches a region. No remote runtime map API.
export class RegionalDetails {
  constructor(atlas) {
    this.a=atlas;this.regions=index.regions;this.cache=new Map();this.pending=new Map();this.failed=new Set();this.wanted=null;
    this.status=document.createElement('div');this.status.id='detail-status';this.status.hidden=true;
    this.status.setAttribute('role','status');this.status.setAttribute('aria-live','polite');
    document.body.append(this.status);
  }
  at(c) {return regionFor(c,this.a.data.district.bbox,this.regions);}
  cancel() {this.wanted=null;this.status.hidden=true;}
  async activate(key,{retry=false}={}) {
    this.wanted=key;
    if(retry)this.failed.delete(key);
    if(key==='city') {
      this.status.hidden=true;this.a.useDistrict(this.a.coreDistrict,'city');return true;
    }
    const meta=this.regions.find(r=>r.id===key);
    if(!meta)return false;
    if(this.cache.has(key)) {
      const scene=this.cache.get(key);this.cache.delete(key);this.cache.set(key,scene);
      this.status.hidden=true;this.a.useDistrict(scene,key);return true;
    }
    if(this.failed.has(key))return false;
    this.status.hidden=false;this.status.textContent=`${meta.name} · 상세 지형과 거리를 준비하고 있습니다`;
    if(!this.pending.has(key))this.pending.set(key,this.load(meta));
    try {
      const data=await this.pending.get(key);
      if(this.wanted!==key)return false;
      // Yield one frame before CPU/GPU assembly so the loading state is painted.
      await new Promise(resolve=>requestAnimationFrame(resolve));
      if(this.wanted!==key)return false;
      let scene=this.cache.get(key);
      if(!scene){scene=new DistrictScene(this.a,data);this.cache.set(key,scene);}
      this.a.useDistrict(scene,key);
      this.status.hidden=true;
      while(this.cache.size>2){const oldest=this.cache.keys().next().value;const old=this.cache.get(oldest);if(old===scene)break;old.dispose();this.cache.delete(oldest);}
      return true;
    } catch(error) {
      this.failed.add(key);
      if(this.wanted===key){
        this.status.replaceChildren(document.createTextNode(`${meta.name} 상세 자료를 불러오지 못했습니다. `));
        const retry=document.createElement('button');retry.textContent='다시 시도';
        retry.onclick=()=>{this.failed.delete(key);this.activate(key);};this.status.append(retry);
      }
      console.error('Regional detail',key,error);return false;
    } finally {this.pending.delete(key);}
  }
  async load(meta) {
    return loadJSON(meta.url,{compressed:true});
  }
}
