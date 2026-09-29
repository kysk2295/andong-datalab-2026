import * as T from 'three';
import assets from '../public/data/relay-materials.json';
const loaded=new Map();let loading;
const photoSurfaces=[['meal-photo','/assets/relay/document/stage-1-image8.webp'],['market-sign','/assets/relay/document/stage-1-image1.webp']];
export function loadRelayMaterials(){
 return loading??=Promise.allSettled([...photoSurfaces.map(async([id,url])=>{const tx=await new T.TextureLoader().loadAsync(url);tx.colorSpace=T.SRGBColorSpace;loaded.set(id+':diff',tx);}),...assets.filter(a=>a.kind!=='hdri').map(async a=>{
  const tx=await new T.TextureLoader().loadAsync(a.file);tx.wrapS=tx.wrapT=T.RepeatWrapping;tx.anisotropy=4;
  if(a.kind==='diffuse')tx.colorSpace=T.SRGBColorSpace;loaded.set(a.asset+':'+(a.kind==='diffuse'?'diff':a.kind),tx);
 })]);
}
export function materialMaps(asset,repeat,track){
 const result={};for(const [kind,slot] of [['diff','map'],['nor_gl','normalMap'],['rough','roughnessMap'],['alpha','alphaMap']]){
  const source=loaded.get(asset+':'+kind);if(!source)continue;const tx=source.clone();tx.repeat.set(...repeat);track.add(tx);result[slot]=tx;
 }return result;
}
