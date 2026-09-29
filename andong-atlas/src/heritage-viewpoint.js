import { polygons } from './geo.js';
import { footprintMask, corridorMask } from './footprints.js';
import { HERITAGE_STOPS } from './heritage-tour.js';

// Computed observation positions, never pedestrian routes or claims of public access.
// Keep both the camera and the sightline to the facade clear of mapped obstacles.
export function heritageViewpoints(data, project, places) {
  const building = footprintMask(data.buildings, project.toWorld);
  const water = footprintMask(data.water || [], project.toWorld);
  const walls = corridorMask(data.heritageDetail?.walls || [], project.toWorld, () => .0018);
  const blocked = (x,z) => building(x,z,.0015) || water(x,z,.0015) || walls(x,z,.001);
  const result = new Map();
  for (const place of places) {
    const feature = data.buildings.find(f => `${data.id}:${f.id}` === place.id);
    if (!feature) continue;
    const candidates = [];
    for (const polygon of polygons(feature.geometry)) {
      const ring = polygon[0].map(project.toWorld);
      for (let i=1; i<ring.length; i++) {
        const a=ring[i-1], b=ring[i], dx=b[0]-a[0], dz=b[1]-a[1], length=Math.hypot(dx,dz);
        if(length<.004) continue;
        const middle=[(a[0]+b[0])/2,(a[1]+b[1])/2];
        for(const sign of [-1,1]) {
          const normal=[-dz/length*sign,dx/length*sign];
          for(const distance of [.024,.018,.012]) {
            const position=[middle[0]+normal[0]*distance,middle[1]+normal[1]*distance];
            let clear=true;
            for(let d=.002;d<=distance+.00001;d+=.0005) {
              if(blocked(middle[0]+normal[0]*d,middle[1]+normal[1]*d)){clear=false;break;}
            }
            if(clear) candidates.push({coordinates:project.toGeo(...position),lookAt:project.toGeo(...middle),score:length+distance+normal[1]*.006});
          }
        }
      }
    }
    candidates.sort((a,b)=>b.score-a.score);
    if(candidates.length) result.set(place.id,candidates[0]);
  }
  return result;
}
export function makeHeritageInspection(data,places,viewpoints,selectedId) {
  const names=HERITAGE_STOPS[data.id]||[];
  const ordered=[...places].sort((a,b)=>{
    const ai=names.indexOf(a.sourceName),bi=names.indexOf(b.sourceName);
    return (ai<0?100:ai)-(bi<0?100:bi);
  }).filter(p=>viewpoints.has(p.id));
  const stages=ordered.map((place,i)=>({kind:'sight',title:`${place.name} 가까이 보기`,place,viewpoint:viewpoints.get(place.id),start:i,end:i+1}));
  return {kind:'heritage-inspection',region:data.id,stages,start:0,end:stages.length,distance:0,initial:Math.max(0,stages.findIndex(s=>s.place.id===selectedId))};
}
