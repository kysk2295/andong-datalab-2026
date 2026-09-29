import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from 'three';
import {heritagePlaces,heritageNetwork,makeHeritageTour} from '../src/heritage-tour.js';
import {scenarioSummary,benefitPaths} from '../src/scenario-model.js';
import {sampleTravel,transitPhase,arrivalAnchor} from '../src/journey-position.js';
import {terrainSafeEye} from '../src/geo.js';
import {photosFor} from '../src/place-media-model.js';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../public/data/${name}.json`,import.meta.url)));

test('Each heritage grounds has a walking course only along recorded roads',()=>{
 for(const id of ['hahoe','byeongsan','dosan','bongjeong']){
  const data=read('regions/'+id),before=JSON.stringify(data),network=heritageNetwork(data),tour=makeHeritageTour(data,network);
  assert.ok(tour.stages.some(s=>s.kind==='walk'),id);
  assert.ok(tour.stages.every((s,i)=>s.end>s.start&&(!i||s.start===tour.stages[i-1].end)));
  assert.ok(tour.distance>10&&tour.distance<2000);
  for(const stage of tour.stages.filter(s=>s.path))for(const point of stage.path.coordinates){
   // Every route sample lies on an original segment; no straight-line shortcut through courtyards.
   const onRoad=data.roads.some(f=>{
    const lines=f.geometry.type==='MultiLineString'?f.geometry.coordinates:[f.geometry.coordinates];
    return lines.some(line=>line.slice(1).some((b,i)=>{const a=line[i],dx=b[0]-a[0],dy=b[1]-a[1],t=((point[0]-a[0])*dx+(point[1]-a[1])*dy)/(dx*dx+dy*dy||1);return t>=-1e-6&&t<=1+1e-6&&Math.hypot(point[0]-a[0]-t*dx,point[1]-a[1]-t*dy)<1e-7;}));
   });assert.ok(onRoad,`${id}: route stays on source road`);
  }
  assert.equal(JSON.stringify(data),before);
  assert.equal(new Set(heritagePlaces(data).map(p=>p.id)).size,data.heritageDetail.sites.length);
 }
});
test('Heritage routing excludes private and pedestrian-prohibited roads',()=>{
 const line=(a,b,p)=>({properties:{highway:'footway',...p},geometry:{type:'LineString',coordinates:[a,b]}});
 const n=heritageNetwork({center:[128,36],roads:[line([128,36],[128.001,36],{}),line([128.001,36],[128.002,36],{access:'private'}),line([128,36],[128,36.001],{foot:'no'})]});
 assert.ok(n.nodes.every(c=>c[0]<=128.001&&c[1]===36));
});
test('Scenario summaries preserve source values and do not turn the current case into zero tourism',()=>{
 const data=read('solution'),before=JSON.stringify(data);
 for(const plan of ['기본안','확대안']){const s=scenarioSummary(data,plan);assert.equal(s.additionalConsumption,data.plans[plan].추가소비합.P50);assert.equal(s.popups,data.plans[plan].입력.n3);assert.equal(s.annualExperiences,data.plans[plan].체험결제합.P50);}
 const current=scenarioSummary(data,'현재');assert.equal(current.additionalConsumption,null);assert.equal(current.residentMonthly,data.resident.currentMonthly);
 assert.equal(JSON.stringify(data),before);
});
test('Before/after map routes only include available reachable benefits',()=>{
 const rows=[{place:{id:'existing',coordinates:[1,0]},before:{type:'기존 주민증'},after:{type:'기존 주민증'}},{place:{id:'added',coordinates:[2,0]},before:null,after:{type:'추가 제안'}},{place:{id:'closed',coordinates:[3,0]},before:null,after:null}];
 const network={route:(a,b)=>({coordinates:[a,b]})};assert.equal(benefitPaths({rows},network,[0,0],false).length,1);const after=benefitPaths({rows},network,[0,0],true);assert.equal(after.length,2);assert.equal(after[1].added,true);assert.equal(benefitPaths({rows},{route:()=>null},[0,0]).length,0);
});
test('Travel look ahead crosses vertex boundaries without looking backwards at arrival',()=>{
 const points=[[0,0,0],[.002,0,0],[.1,0,0],[.1,0,.1]].map(p=>new THREE.Vector3(...p));
 for(const t of [0,.009,.01,.5,.99,1]){const s=sampleTravel(points,t);assert.ok(s.next.distanceTo(s.point)>0);assert.ok(s.next.x>=s.point.x&&s.next.z>=s.point.z);}
 const last=sampleTravel(points,1);assert.ok(last.next.z>last.point.z);
});
test('Transit stops moving while boarding and alighting; arrivals inherit the bus endpoint',()=>{
 assert.equal(transitPhase(.03,true).progress,0);assert.equal(transitPhase(.97,true).progress,1);assert.equal(transitPhase(.5,true).phase,'riding');
 let last=-1;for(let t=0;t<=1;t+=.01){const p=transitPhase(t,true);assert.ok(p.progress>=last);last=p.progress;assert.ok(p.boarding>=0&&p.boarding<=1);}
 const endpoint=new THREE.Vector3(1,2,3);assert.equal(arrivalAnchor([{kind:'bus',path:{bridges:['']}},{}],[[endpoint],[]],1).point,endpoint);
});
test('Human-scale follow camera stays near the traveler on flat ground',()=>{
 const target=new THREE.Vector3(0,.25075,0),eye=new THREE.Vector3(0,.26,.022);
 const y=terrainSafeEye(target,eye,()=>.25,{clearance:.001,rise:.003});assert.ok(y<.27);assert.ok(y>=eye.y);
 const hill=terrainSafeEye(target,eye,(x,z)=>z>.01?.28:.25,{clearance:.001,rise:.003});assert.ok(hill>.28);
});
test('Heritage photos retain license and clearly distinguish region images from specific buildings',()=>{
 const extra=read('heritage-media'),base=read('place-media'),media={photos:{...base.photos,...extra.photos},records:extra.records};
 for(const p of Object.values(extra.photos)){assert.ok(p.credit&&p.license&&p.licenseUrl.startsWith('https://'));assert.ok(p.sourceUrl.startsWith('https://commons.wikimedia.org/'));}
 for(const [id,r]of Object.entries(extra.records)){const ps=photosFor({id},media);assert.ok(ps.length);if(r.photoScope==='region')assert.match(ps[0].caption,/개별 건물의 사진은 아닙니다/);}
 assert.ok(photosFor({id:'bongjeong:osm-691112449'},media)[0].caption==='봉정사 극락전');
});
