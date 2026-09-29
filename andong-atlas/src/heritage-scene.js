import * as THREE from 'three';
import { inRing } from './geo.js';
import { corridorMask } from './footprints.js';
import { Vegetation } from './vegetation.js';

export class HeritageScene {
  constructor(district) {
    this.d = district;
    const detail = district.data.heritageDetail;
    if (!detail) return;
    this.buildWalls(detail.walls);
    this.buildTrees(detail);
  }
  buildWalls(walls) {
    const d=this.d, bodies=[], caps=[], stones=[], barriers=[];
    for (const f of walls) {
      const c=f.geometry.coordinates;
      for(let i=1;i<c.length;i++) {
        const a=d.point(c[i-1]),b=d.point(c[i]),length=Math.hypot(b.x-a.x,b.z-a.z);
        const count=Math.max(1,Math.ceil(length/.008));
        for(let j=0;j<count;j++) {
          const p=a.clone().lerp(b,j/count),q=a.clone().lerp(b,(j+1)/count);
          const x=(p.x+q.x)/2,z=(p.z+q.z)/2;
          // Preserve gaps at mapped walking/vehicle routes rather than sealing entrances.
          if(d.roadBlocked(x,z))continue;
          barriers.push({geometry:{coordinates:[[p.x,p.z],[q.x,q.z]]}});
          const ground=d.point(d.a.project.toGeo(x,z)).y;
          const height=Math.min(.018,Math.max(.006,Number(f.properties.height)*.008 || .008));
          const angle=Math.atan2(q.x-p.x,q.z-p.z),span=Math.hypot(q.x-p.x,q.z-p.z)+.0001;
          const box=(w,h,y)=>{const g=new THREE.BoxGeometry(w,h,span);g.rotateY(angle);g.translate(x,ground+y,z);return g;};
          bodies.push(box(.0016,height,height/2));
          caps.push(box(.0025,.0012,height));
          stones.push(box(.0019,.0016,.0008));
        }
      }
    }
    d.wallBlocked=corridorMask(barriers,c=>c,()=>.0025);
    d.merge(bodies,new THREE.MeshStandardMaterial({color:'#b5a086',roughness:1}));
    d.merge(caps,new THREE.MeshStandardMaterial({color:'#65706b',roughness:1}));
    d.merge(stones,new THREE.MeshStandardMaterial({color:'#939385',roughness:1}));
  }
  buildTrees(detail) {
    const d=this.d, trunks=[], crowns=[], dummy=new THREE.Object3D();
    let seed=6941;
    const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
    for(const grove of detail.groves) {
      const ring=grove.geometry.coordinates[0].map(c=>d.a.project.toWorld(c));
      const xs=ring.map(p=>p[0]),zs=ring.map(p=>p[1]);
      const minX=Math.min(...xs),maxX=Math.max(...xs),minZ=Math.min(...zs),maxZ=Math.max(...zs);
      const target=Math.min(d.a.mobile?130:260,Math.ceil((maxX-minX)*(maxZ-minZ)/.0005));
      let count=0;
      for(let i=0;i<target*8&&count<target;i++) {
        const x=minX+random()*(maxX-minX),z=minZ+random()*(maxZ-minZ);
        if(!inRing([x,z],ring)||d.buildingBlocked(x,z,.008)||d.roadBlocked(x,z,.005)||d.waterBlocked(x,z))continue;
        const y=d.point(d.a.project.toGeo(x,z)).y,size=.018+random()*.01;
        trunks.push({x,y,z,size});count++;
        for(let j=0;j<3;j++) crowns.push({x:x+(random()-.5)*size*.7,y:y+size*(1.45+j*.22),z:z+(random()-.5)*size*.7,size:size*(.65-j*.06)});
      }
    }
    const make=(geometry,color,items,isCrown)=>{
      const mesh=new THREE.InstancedMesh(geometry,new THREE.MeshStandardMaterial({color,roughness:1}),items.length);
      items.forEach((p,i)=>{
        dummy.position.set(p.x,p.y+(isCrown?0:p.size*.7),p.z);
        dummy.scale.set(isCrown?p.size:p.size*.08,isCrown?p.size*.32:p.size*1.4,isCrown?p.size:p.size*.08);
        dummy.updateMatrix();mesh.setMatrixAt(i,dummy.matrix);
      });
      mesh.castShadow=true;d.group.add(mesh);return mesh;
    };
    make(new THREE.CylinderGeometry(1,1.4,1,6),'#79694f',trunks,false);
    this.pines=make(new THREE.IcosahedronGeometry(1,1),'#42634c',crowns,true);
    this.pines.userData.source='Mapped woodland boundary; decorative pine positions';
    const trees=detail.trees.map((t,i)=>{
      const p=d.point(t.coordinates);
      return {x:p.x,y:p.y,z:p.z,size:t.name==="삼신당"?.019:.012,tint:(i*.618)%1};
    });
    this.trees=new Vegetation(d.group,trees);
  }
  update() {this.trees?.setSeason(this.d.a.season);}
}
