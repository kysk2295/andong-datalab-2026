// A stop inherits the approach surface. In particular, arriving on a bridge
// must not move the traveler back down to the river/terrain elevation.
export function arrivalAnchor(stages, paths, index) {
  const before=stages[index-1],after=stages[index+1];
  if(before?.path&&paths[index-1]?.length)
    return {point:paths[index-1].at(-1),bridge:!!before.path?.bridges?.at(-1)};
  if(after?.path&&paths[index+1]?.length)
    return {point:paths[index+1][0],bridge:!!(after.path?.bridges?.[0]||after.path?.bridges?.[1])};
  return null;
}

// Arc-length look-ahead is stable across densely and sparsely sampled roads.
const pathLengths=new WeakMap();
export function sampleTravel(points, fraction, lookAhead = .012) {
  let lengths=pathLengths.get(points);
  if(!lengths){lengths=[0];for(let i=1;i<points.length;i++) lengths.push(lengths.at(-1)+points[i].distanceTo(points[i-1]));pathLengths.set(points,lengths);}
  const total=lengths.at(-1);
  const at=distance=>{
    let i=1;
    while(i<points.length-1&&lengths[i]<distance)i++;
    return points[i-1].clone().lerp(points[i],Math.max(0,Math.min(1,(distance-lengths[i-1])/(lengths[i]-lengths[i-1]||1))));
  };
  const distance=Math.max(0,Math.min(1,fraction))*total,point=at(distance);
  const next=at(Math.min(total,distance+lookAhead));
  if(next.distanceTo(point)<.0001)next.copy(point).add(point.clone().sub(at(Math.max(0,total-lookAhead))));
  return {point,next};
}

export function transitPhase(fraction, vehicle, duration=null) {
  if(!vehicle)return {phase:'walk',progress:fraction,boarding:0};
  const edge=duration>0?Math.min(.07,1.8/duration):.07;
  if(fraction<edge)return {phase:'boarding',progress:0,boarding:fraction/edge};
  if(fraction>1-edge)return {phase:'alighting',progress:1,boarding:(1-fraction)/edge};
  return {phase:'riding',progress:(fraction-edge)/(1-edge*2),boarding:1};
}
