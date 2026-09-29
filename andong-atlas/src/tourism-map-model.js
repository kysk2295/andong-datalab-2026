import {popupSite} from './popup-map-layer.js';
export const MAP_LAYER_KEY = 'andong-map-layers-v1';
export const validCoordinate = c => Array.isArray(c) && c.length === 2 && c.every(Number.isFinite) && Math.abs(c[0]) <= 180 && Math.abs(c[1]) <= 90;
const distance = (a,b) => Math.hypot((a[0]-b[0])*89300,(a[1]-b[1])*111320);

export function routeMidpoint(coords) {
  const lengths=coords.slice(1).map((c,i)=>distance(c,coords[i]));
  let remaining=lengths.reduce((a,b)=>a+b,0)/2;
  for(let i=0;i<lengths.length;i++) {
    if(remaining<=lengths[i] && lengths[i]>0) {
      const t=remaining/lengths[i];
      return coords[i].map((n,k)=>n+(coords[i+1][k]-n)*t);
    }
    remaining-=lengths[i];
  }
  return coords[0]?.slice();
}

export function tourismModel(journey,route) {
  const coordinates=route.coordinates.filter(validCoordinate);
  const benefits=journey.places.filter(p=>p.benefit && validCoordinate(p.coordinates)).map(p=>({...p}));
  const unlocated=journey.unlocatedBenefits.map((p,i)=>({...p,id:`unlocated-benefit-${i}`,coordinates:null,benefitSource:'디지털 관광주민증 가맹 목록 · 2026.09.21 수집'}));
  const stages=coordinates.length<2?[]:[
    {id:'relay-stage-1',relayStage:1,name:'식음·체험 릴레이',area:'원도심 · 안동구시장',coordinates:coordinates[0],description:'식사 → 영수증 인증 → 전통 체험. 한 끼에서 체험 할인으로 이어집니다.',note:'체험 거점은 권역을 나타내며 설치 지점은 미확정입니다.'},
    {id:'relay-stage-2',relayStage:2,name:'저녁 이동 연결',area:'원도심 → 월영교',coordinates:routeMidpoint(coordinates),description:'원도심에서 월영교로 이동하는 구간입니다. 1단계의 체험과 3단계의 야간 체류를 연결합니다.',note:'2번은 이동 구간의 중간 표식입니다. 정류장이나 업체 위치가 아닙니다.'},
    {id:'relay-stage-3',relayStage:3,name:'월영교 야간 체류',area:'월영교 · 강변 팝업 권역',coordinates:coordinates.at(-1),description:'월영교 야경 산책 → 로컬 음식·공예 팝업 → 놀이와 공연으로 이어집니다.',note:'팝업은 제안 권역이며 부지·운영은 미확정입니다.'},
  ];
  return {benefits,unlocated,stages,route:{...route,coordinates}};
}

export function layerState(value,defaults={}) {
  let p;try{p=typeof value==='string'?JSON.parse(value):value;}catch{}
  return Object.fromEntries(['benefits','route','booths'].map(k=>[k,typeof p?.[k]==='boolean'?p[k]:defaults[k]===true]));
}
export function mapPlaceLayer(place){return place.popupSite?'booths':place.relayStage?'route':'benefits';}
export function layerCoordinates(model,layer){return layer==='booths'?[popupSite(model)?.coordinates].filter(Boolean):layer==='route'?model.route.coordinates:model.benefits.map(p=>p.coordinates);}
export function visibleMapPlaces(model,state) {
  return [...(state.benefits?model.benefits:[]),...(state.route?model.stages:[]),...(state.booths?[popupSite(model)].filter(Boolean):[])];
}
export function fitMapBounds(coords,width,height) {
  const points=coords.filter(validCoordinate);
  if(!points.length)points.push([128.744,36.571]);
  const xs=points.map(c=>c[0]),ys=points.map(c=>c[1]);
  const cx=(Math.min(...xs)+Math.max(...xs))/2,cy=(Math.min(...ys)+Math.max(...ys))/2;
  const ratio=Math.max(1,width)/Math.max(1,height),cos=Math.cos(cy*Math.PI/180);
  let dx=Math.max(.002,Math.max(...xs)-Math.min(...xs))*1.35;
  let dy=Math.max(.002,Math.max(...ys)-Math.min(...ys))*1.35;
  if(dx*cos/dy>ratio)dy=dx*cos/ratio;else dx=dy*ratio/cos;
  return [cx-dx/2,cy-dy/2,cx+dx/2,cy+dy/2];
}
export function projectMapPoint(c,b,width,height) {
  return [(c[0]-b[0])/(b[2]-b[0])*width,(b[3]-c[1])/(b[3]-b[1])*height];
}
export function clusterMapPlaces(places,bounds,width,height,gap=38) {
  const clusters=[];
  for(const place of places){
    const [x,y]=projectMapPoint(place.coordinates,bounds,width,height);
    if(x<16||y<16||x>width-16||y>height-16)continue;
    const near=clusters.filter(c=>c.points.some(p=>Math.hypot(p.x-x,p.y-y)<gap));
    const cluster={points:[{place,x,y},...near.flatMap(c=>c.points)]};
    for(const c of near)clusters.splice(clusters.indexOf(c),1);
    clusters.push(cluster);
  }
  return clusters.map(c=>({...c,x:c.points.reduce((n,p)=>n+p.x,0)/c.points.length,y:c.points.reduce((n,p)=>n+p.y,0)/c.points.length}));
}
