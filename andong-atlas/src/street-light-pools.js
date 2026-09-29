import * as THREE from 'three';

// Reuse the mapped street fixtures; one draw call replaces hundreds of point lights.
export function createStreetLightPools(lamps){
 const pixels=new Uint8Array(32*32*4);
 for(let y=0;y<32;y++)for(let x=0;x<32;x++){
  const falloff=Math.max(0,1-Math.hypot((x-15.5)/15.5,(y-15.5)/15.5));
  pixels.set([255,255,255,Math.round(falloff*falloff*130)],(y*32+x)*4);
 }
 const texture=new THREE.DataTexture(pixels,32,32);texture.needsUpdate=true;texture.magFilter=THREE.LinearFilter;
 const material=new THREE.MeshBasicMaterial({color:'#ffd08a',map:texture,transparent:true,depthWrite:false,toneMapped:false,polygonOffset:true,polygonOffsetFactor:-1});
 const geometry=new THREE.PlaneGeometry(.046,.046);geometry.rotateX(-Math.PI/2);
 const pools=new THREE.InstancedMesh(geometry,material,lamps.count),matrix=new THREE.Matrix4();
 pools.name='street-light-pools';pools.visible=false;
 for(let i=0;i<lamps.count;i++){
  lamps.getMatrixAt(i,matrix);matrix.elements[13]-=.0228;
  pools.setMatrixAt(i,matrix);
 }
 pools.instanceMatrix.needsUpdate=true;
 pools.computeBoundingSphere();
 return pools;
}
