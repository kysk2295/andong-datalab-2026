import * as THREE from 'three';

// A gabled interpretation clipped to the actual footprint, including courtyards.
// Splitting the source triangles at the ridge preserves concave outlines/holes.
export function heritageRoof(shape, base, rise = .006, rounded = false) {
  const flat=new THREE.ShapeGeometry(shape), pos=flat.attributes.position, idx=flat.index;
  const ring=shape.getPoints();let longest=0,ux=1,uy=0;
  for(let i=1;i<ring.length;i++){const dx=ring[i].x-ring[i-1].x,dy=ring[i].y-ring[i-1].y,d=Math.hypot(dx,dy);if(d>longest){longest=d;ux=dx/d;uy=dy/d;}}
  const vx=-uy,vy=ux, values=ring.map(p=>p.x*vx+p.y*vy),lo=Math.min(...values),hi=Math.max(...values),mid=(lo+hi)/2,half=Math.max(.001,(hi-lo)/2);
  const side=p=>p[0]*vx+p[1]*vy-mid;
  function clip(points,sign){const out=[];for(let i=0;i<points.length;i++){const a=points[i],b=points[(i+1)%points.length],sa=side(a)*sign,sb=side(b)*sign;if(sa>=0)out.push(a);if((sa<0)!==(sb<0)){const t=sa/(sa-sb);out.push([a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t]);}}return out;}
  const vertices=[],local=[];
  const push=p=>{local.push(p[0]*ux+p[1]*uy,p[0]*vx+p[1]*vy);const ratio=Math.min(1,Math.abs(side(p))/half);vertices.push(p[0],base+rise*(rounded?Math.sqrt(Math.max(0,1-ratio*ratio)):1-ratio),-p[1]);};
  const triangle=(a,b,c,level)=>{if(!level){[a,b,c].forEach(push);return;}const mid=(p,q)=>p.map((v,k)=>(v+q[k])/2),ab=mid(a,b),bc=mid(b,c),ca=mid(c,a);triangle(a,ab,ca,level-1);triangle(ab,b,bc,level-1);triangle(ca,bc,c,level-1);triangle(ab,bc,ca,level-1);};
  for(let i=0;i<idx.count;i+=3){const tri=[0,1,2].map(k=>{const j=idx.getX(i+k);return[pos.getX(j),pos.getY(j)];});for(const sign of [-1,1]){const polygon=clip(tri,sign);for(let j=1;j<polygon.length-1;j++)triangle(polygon[0],polygon[j],polygon[j+1],rounded?2:0);}}
  flat.dispose();
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));geometry.setAttribute('roofLocal',new THREE.Float32BufferAttribute(local,2));geometry.computeVertexNormals();return geometry;
}

// Close the exposed gable ends between the wall top and the sloping roof.
export function heritageGables(shape,base,rise=.006,rounded=false){
  const rings=[shape.getPoints(),...shape.holes.map(h=>h.getPoints())].map(r=>r.at(-1).equals(r[0])?r:[...r,r[0].clone()]),ring=rings[0];
  let longest=0,ux=1,uy=0;
  for(let i=1;i<ring.length;i++){const dx=ring[i].x-ring[i-1].x,dy=ring[i].y-ring[i-1].y,d=Math.hypot(dx,dy);if(d>longest){longest=d;ux=dx/d;uy=dy/d;}}
  const vx=-uy,vy=ux,values=ring.map(p=>p.x*vx+p.y*vy),lo=Math.min(...values),hi=Math.max(...values),mid=(lo+hi)/2,half=Math.max(.001,(hi-lo)/2);
  const side=p=>p.x*vx+p.y*vy-mid;
  const height=p=>{const ratio=Math.min(1,Math.abs(side(p))/half);return base+rise*(rounded?Math.sqrt(Math.max(0,1-ratio*ratio)):1-ratio);};
  const vertices=[];
  for(const r of rings)for(let i=1;i<r.length;i++){
    const a=r[i-1],b=r[i],cuts=[0,1],sa=side(a),sb=side(b);
    if(sa*sb<0)cuts.push(sa/(sa-sb));
    if(rounded)cuts.push(.25,.5,.75);
    cuts.sort((a,b)=>a-b);
    for(let j=1;j<cuts.length;j++){
      const p=a.clone().lerp(b,cuts[j-1]),q=a.clone().lerp(b,cuts[j]),ph=height(p),qh=height(q);
      if(Math.max(ph,qh)-base<.00001)continue;
      vertices.push(p.x,base,-p.y,q.x,base,-q.y,q.x,qh,-q.y,p.x,base,-p.y,q.x,qh,-q.y,p.x,ph,-p.y);
    }
  }
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));g.computeVertexNormals();return g;
}

export function heritageRoofMaterial(thatch) {
  const material=new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,side:THREE.DoubleSide});
  material.onBeforeCompile=shader=>{
    shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nattribute vec2 roofLocal; varying vec2 roofPoint;').replace('#include <begin_vertex>','#include <begin_vertex>\nroofPoint=roofLocal;');
    shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>\nvarying vec2 roofPoint;').replace('#include <color_fragment>',`#include <color_fragment>
      float period=${thatch?'.00025':'.0005'};
      float cell=roofPoint.x/period, aa=max(fwidth(cell),.03);
      float seam=1.-smoothstep(.06,.06+aa,min(fract(cell),1.-fract(cell)));
      float band=1.-smoothstep(.04,.04+max(fwidth(roofPoint.y/.0008),.03),fract(roofPoint.y/.0008));
      diffuseColor.rgb*=1.-${thatch?'.1':'.18'}*seam-.08*band;
    `);
  };
  material.customProgramCacheKey=()=>`andong-roof-${thatch?'thatch':'tile'}-v2`;
  return material;
}

// Flat ShapeGeometry has an index/UVs; the clipped ridge mesh does not.
// Normalize before batching both roof types into a single GPU draw call.
export function roofForMerge(geometry) {
  if(geometry.index){const source=geometry;geometry=source.toNonIndexed();source.dispose();}
  geometry.deleteAttribute('uv');
  if(!geometry.getAttribute('roofLocal')){
    const p=geometry.getAttribute('position'),local=[];
    for(let i=0;i<p.count;i++)local.push(p.getX(i),p.getZ(i));
    geometry.setAttribute('roofLocal',new THREE.Float32BufferAttribute(local,2));
  }
  return geometry;
}

export function heritageFacade(material) {
  material.onBeforeCompile=shader=>{
    shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nattribute float facadeHeight; varying float heritageHeight; varying vec3 heritagePosition; varying vec3 heritageNormal;').replace('#include <begin_vertex>','#include <begin_vertex>\nheritagePosition=position; heritageNormal=normal; heritageHeight=facadeHeight;');
    shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>\nvarying float heritageHeight; varying vec3 heritagePosition; varying vec3 heritageNormal;').replace('#include <color_fragment>',`#include <color_fragment>
      float side=1.-step(.5,abs(heritageNormal.y));
      float along=dot(heritagePosition.xz,vec2(heritageNormal.z,-heritageNormal.x));
      float cell=fract(along/.007), aa=max(fwidth(along/.007),.025);
      float post=1.-smoothstep(.025,.025+aa,min(cell,1.-cell));
      float opening=step(.25,heritageHeight)*(1.-step(.82,heritageHeight))*step(.18,cell)*(1.-step(.82,cell));
      diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.39,.37,.29),side*opening*.85);
      float gridX=cell*14.,gridY=heritageHeight*12.;
      float latticeX=1.-smoothstep(.05,.05+max(fwidth(gridX),.025),min(fract(gridX),1.-fract(gridX)));
      float latticeY=1.-smoothstep(.05,.05+max(fwidth(gridY),.025),min(fract(gridY),1.-fract(gridY)));
      float lattice=max(latticeX,latticeY);
      diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.65,.57,.4),side*opening*lattice*.65);
      float rail=1.-step(.06,abs(heritageHeight-.18));
      post=max(post,rail);
      diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.24,.16,.105),side*post*.85);
    `);
  };
  material.customProgramCacheKey=()=> 'andong-heritage-facade-v3';
}
