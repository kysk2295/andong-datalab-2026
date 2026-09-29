import { JourneyNetwork, meters } from './journey-model.js';
import { heritageDescription } from './heritage-content.js';

export const HERITAGE_STOPS={
  hahoe:['삼신당','북촌댁','원지정사','빈연정사','작천고택','영모각'],
  byeongsan:['복례문','만대루','입교당','동재','서재'],
  dosan:['역락서재','농운정사','도산서당','진도문','전교당'],
  bongjeong:['만세루ㅡ','화엄강당','삼층석탑','극락전','대웅전'],
};

export function heritagePlaces(data){
  return (data.heritageDetail?.sites||[]).map(site=>({...site,id:`${data.id}:${site.id}`,kind:'heritage',region:data.id,
    name:site.name==='만세루ㅡ'?'만세루':site.name,sourceName:site.name,
    description:`${data.name.split('·')[0].trim()} 안에서 공개 지도에 이름과 위치가 기록된 장소입니다. 사진과 지도에서 주변 배치를 살펴보세요. 건물 내부 개방 여부는 현장 안내를 확인하세요.`,
    source:'OpenStreetMap · 저장된 장소 좌표',hours:'현장 관람·개방 여부 확인 필요',priceText:'개별 요금 확인 필요',...heritageDescription(data.id,site.name)}));
}

export function heritageNetwork(data) {
  const nodes=[],edges=[],keys=new Map();
  const node=c=>{const key=c.map(n=>n.toFixed(7)).join(',');if(!keys.has(key)){keys.set(key,nodes.length);nodes.push(c);}return keys.get(key);};
  for(const f of data.roads){
    const p=f.properties||{},kind=p.highway;
    if(!kind||['motorway','motorway_link','trunk','trunk_link','construction','proposed'].includes(kind)||p.foot==='no'||(['private','no'].includes(p.access)&&!['yes','designated','permissive'].includes(p.foot)))continue;
    const lines=f.geometry.type==='MultiLineString'?f.geometry.coordinates:[f.geometry.coordinates];
    for(const line of lines)for(let i=1;i<line.length;i++){
      const a=line[i-1],b=line[i],n=Math.max(1,Math.ceil(meters(a,b)/3));let previous=node(a);
      for(let j=1;j<=n;j++){const c=[a[0]+(b[0]-a[0])*j/n,a[1]+(b[1]-a[1])*j/n],next=node(c);edges.push([previous,next,meters(nodes[previous],c),1,0,0,p.bridge&&p.bridge!=='no'?f.id:'',kind]);previous=next;}
    }
  }
  const network=new JourneyNetwork({nodes,edges});
  // Select the connected component at the actual heritage grounds, not a distant main road.
  const center=data.activityCenter||data.center,seen=new Set();let best=null;
  for(let i=0;i<nodes.length;i++){
    if(seen.has(i)||!network.graph.walk[i].length)continue;
    const component=[i];seen.add(i);
    for(let j=0;j<component.length;j++)for(const [v] of network.graph.walk[component[j]])if(!seen.has(v)){seen.add(v);component.push(v);}
    const distance=Math.min(...component.map(k=>meters(nodes[k],center)));
    if(component.length>8&&(!best||distance<best.distance))best={distance,component};
  }
  network.valid.walk=best?.component||[];
  return network;
}

export function makeHeritageTour(data,network=heritageNetwork(data)){
  const places=heritagePlaces(data),targets=(HERITAGE_STOPS[data.id]||[]).map(name=>places.find(p=>p.sourceName===name)).filter(Boolean);
  const stages=[],skipped=[];let previous=null,time=600,distance=0;
  for(const place of targets){
    const snap=network.snap(place.coordinates);
    if(!snap||snap.offset>45){skipped.push(place.name);continue;}
    if(previous){
      const path=network.route(previous.coordinates,place.coordinates);
      if(!path||path.distance>1500){skipped.push(place.name);continue;}
      if(path.coordinates.length<2){stages.push({kind:'sight',place,title:`길에서 ${place.name} 바라보기`,start:time,end:time+3});time+=3;continue;}
      const duration=Math.max(1,Math.ceil(path.distance/65));
      stages.push({kind:'walk',place,title:`${previous.name} → ${place.name}`,path,start:time,end:time+duration});time+=duration;distance+=path.distance;
    }
    stages.push({kind:'sight',place,title:`${place.name} 둘러보기`,start:time,end:time+3});time+=3;previous=place;
  }
  if(!stages.some(s=>s.path)){
    const center=data.activityCenter||data.center;
    const candidates=data.roads.filter(f=>['path','footway','steps'].includes(f.properties.highway)&&f.geometry.type==='LineString'&&!['private','no'].includes(f.properties.access)&&f.properties.foot!=='no').map(f=>({f,d:Math.min(...f.geometry.coordinates.map(c=>meters(c,center)))})).filter(r=>r.d<100).sort((a,b)=>a.d-b.d);
    const road=candidates[0]?.f;
    if(road){
      let coordinates=road.geometry.coordinates;
      if(meters(coordinates[0],center)<meters(coordinates.at(-1),center))coordinates=[...coordinates].reverse();
      let first=coordinates.length-1,length=0;
      while(first>0&&length<250){length+=meters(coordinates[first],coordinates[first-1]);first--;}
      coordinates=coordinates.slice(first);
      const name=data.name.split('·')[0].trim(),startPlace={id:`${data.id}:approach`,name:`${name} 접근 산책길`,kind:'heritage',coordinates:coordinates[0],description:'내려받은 공개 지도에 기록된 보행로입니다.'};
      const endPlace={...startPlace,id:`${data.id}:arrival`,name:`${name} 앞길`,coordinates:coordinates.at(-1)};
      const minutes=Math.max(1,Math.ceil(length/65));
      stages.splice(0,stages.length,{kind:'sight',place:startPlace,start:600,end:601},{kind:'walk',place:endPlace,title:`${name} 앞길 걷기`,start:601,end:601+minutes,path:{coordinates,kinds:coordinates.map(()=>road.properties.highway),bridges:coordinates.map(()=>''),distance:length}},{kind:'sight',place:endPlace,start:601+minutes,end:604+minutes});
      time=604+minutes;distance=length;
    }
  }
  return {kind:'heritage',start:600,end:time,distance,stages,skipped,issues:[],region:data.id};
}
