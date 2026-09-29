export function originDepartures(route, dayCode) {
  return [...new Set(route.schedules.filter(s=>s.dayCode===dayCode).flatMap(s=>s.times))].sort();
}
export function routeForOrigin(data, origin) {
  const id=origin==='hahoe'?'354300008':origin==='downtown'?'354300004':origin==='bridge'?'354300005':'354300002';
  return data.routes.find(r=>r.id===id);
}
export function routeProjection(route) {
  const coords=route.coordinates;
  if(!coords.length)return {path:'',points:[]};
  const xs=coords.map(c=>c[0]*Math.cos(36.57*Math.PI/180)),ys=coords.map(c=>-c[1]);
  const minX=Math.min(...xs),minY=Math.min(...ys),w=Math.max(...xs)-minX,h=Math.max(...ys)-minY;
  const scale=Math.min(540/(w||1),240/(h||1)),ox=30+(540-w*scale)/2,oy=30+(240-h*scale)/2;
  const point=c=>[ox+(c[0]*Math.cos(36.57*Math.PI/180)-minX)*scale,oy+(-c[1]-minY)*scale];
  return {path:coords.map((c,i)=>(i?'L':'M')+point(c).map(n=>n.toFixed(1)).join(',')).join(' '),points:route.stops.map(s=>point(s.coordinates))};
}
