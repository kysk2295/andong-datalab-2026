import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import assets from '../public/data/relay-model-assets.json';
const models=new Map();let loading;
export function loadRelayProps(){
 return loading??=Promise.allSettled(assets.map(async a=>{const {scene}=await new GLTFLoader().loadAsync(a.file);models.set(a.id,scene);}));
}
// Source resources are shared; each set owns and disposes its cloned resources.
export function scannedProp(id,parent,position,width,track){
 const source=models.get(id);if(!source)return null;
 const object=source.clone(true),bounds=new T.Box3().setFromObject(object),size=bounds.getSize(new T.Vector3()),center=bounds.getCenter(new T.Vector3());
 const scale=width/Math.max(size.x,size.z);object.scale.multiplyScalar(scale);object.position.set(-center.x*scale,-bounds.min.y*scale,-center.z*scale);
 object.traverse(o=>{if(!o.isMesh)return;o.geometry=o.geometry.clone();track.geometries.add(o.geometry);o.material=o.material.clone();track.materials.set('scan'+track.materials.size,o.material);o.castShadow=o.receiveShadow=true;});
 const group=new T.Group();group.position.fromArray(position);group.add(object);parent.add(group);return group;
}
