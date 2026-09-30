import * as T from 'three';
import assets from '../public/data/relay-materials.json';
import {loadPool,withDeadline} from './loading.js';
import {replaceTextureImage} from './progressive-texture.js';
const loaded=new Map();let loading;
const photoSurfaces=[['meal-photo','/assets/relay/document/stage-1-image8.webp'],['market-sign','/assets/relay/document/stage-1-image1.webp']];
const clients=new Map();
function placeholder(kind){
 const canvas=document.createElement('canvas');canvas.width=canvas.height=32;const ctx=canvas.getContext('2d');
 ctx.fillStyle=kind==='nor_gl'?'#8080ff':kind==='alpha'?'#000000':'#ffffff';ctx.fillRect(0,0,32,32);
 if(kind==='alpha'){ctx.fillStyle='#ffffff';ctx.beginPath();ctx.ellipse(16,16,7,15,0,0,Math.PI*2);ctx.fill();}
 const tx=new T.Texture(canvas);tx.wrapS=tx.wrapT=T.RepeatWrapping;tx.anisotropy=4;
 if(kind==='diff')tx.colorSpace=T.SRGBColorSpace;tx.needsUpdate=true;return tx;
}
async function imageFor(url,signal){
 const response=await fetch(url,{signal});if(!response.ok)throw Error(`Texture ${response.status}`);
 const blob=await response.blob();signal.throwIfAborted();const objectURL=URL.createObjectURL(blob);
 try{return await new Promise((resolve,reject)=>{
  const image=new Image();
  const clean=()=>{image.onload=image.onerror=null;signal.removeEventListener('abort',abort);};
  const abort=()=>{clean();image.src='';reject(signal.reason);};
  image.onload=()=>{clean();resolve(image);};image.onerror=()=>{clean();reject(Error('Texture decode failed'));};
  signal.addEventListener('abort',abort,{once:true});image.src=objectURL;
 });}finally{URL.revokeObjectURL(objectURL);}
}
export function loadRelayMaterials(onProgress){
 if(loading)return loading;
 // Diffuse color and cutout silhouettes first; normal/roughness maps can follow.
 const files=[...photoSurfaces.map(([asset,file])=>({asset,file,kind:'diff'})),...assets.filter(a=>a.kind!=='hdri').map(a=>({...a,kind:a.kind==='diffuse'?'diff':a.kind}))].sort((a,b)=>Number(!['diff','alpha'].includes(a.kind))-Number(!['diff','alpha'].includes(b.kind)));
 for(const a of files){const key=a.asset+':'+a.kind;loaded.set(key,placeholder(a.kind));clients.set(key,new Set());}
 loading=loadPool(files,async a=>{
  const image=await withDeadline(signal=>imageFor(a.file,signal));
  const key=a.asset+':'+a.kind;
  replaceTextureImage(loaded.get(key),clients.get(key),image);
 },{onProgress});return loading;
}
export function materialMaps(asset,repeat,track){
 const result={};for(const [kind,slot] of [['diff','map'],['nor_gl','normalMap'],['rough','roughnessMap'],['alpha','alphaMap']]){
  const key=asset+':'+kind,source=loaded.get(key);if(!source)continue;const tx=source.clone();tx.repeat.set(...repeat);track.add(tx);result[slot]=tx;
  clients.get(key)?.add(tx);tx.addEventListener('dispose',()=>clients.get(key)?.delete(tx));
 }return result;
}
