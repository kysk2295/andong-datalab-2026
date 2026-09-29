import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {report,reportSummary,reportComparisonHTML} from '../src/report-effects.js';
import {originDepartures,routeProjection,routeForOrigin} from '../src/transport-model.js';
import {returnDeadline} from '../src/journey-model.js';
import {enrichRestaurant,restaurantInfo,restaurantFactsHTML} from '../src/restaurant-info.js';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../public/data/${name}.json`,import.meta.url)));
const transit=read('transport'),catalog=read('journey').places;

test('exported report is identical to canonical scenarios and records source hashes',()=>{
  for(const s of report.sources){
    const bytes=fs.readFileSync(new URL('../../'+s.path,import.meta.url));
    assert.equal(createHash('sha256').update(bytes).digest('hex'),s.sha256);
    if(s.path.endsWith('시뮬레이션결과.json'))assert.deepEqual(report.scenarios,JSON.parse(bytes).시나리오);
  }
  assert.equal(report.restaurants,83);
  assert.equal((reportSummary().additionalConsumption.P50/1e8).toFixed(2),'1.56');
  assert.equal((reportSummary('흥행').additionalConsumption.P50/1e8).toFixed(2),'2.86');
  assert.equal((reportSummary('목표').additionalConsumption.P50/1e8).toFixed(2),'6.91');
});
test('resident effect is a separate forecast, not multiplied by QR participation',()=>{
  assert.equal(reportSummary('기준').residentMonthly,reportSummary('목표').residentMonthly);
  assert.equal(Math.round(report.resident.currentMonthly),888);
  assert.equal(Math.round(reportSummary().residentMonthly),1155);
  const html=reportComparisonHTML();assert.match(html,/83곳 운영 가정/);assert.match(html,/신뢰구간이 아닙니다/);assert.match(html,/QR 인증과 합산하지 않습니다/);
});
test('BIS variants preserve direction, missing timetables, and origin-only semantics',()=>{
  assert.equal(transit.routes.length,9);assert.equal(transit.live,false);assert.equal(transit.timeBasis,'origin-departure');
  assert.deepEqual(originDepartures(routeForOrigin(transit,'station'),'1'),['08:25','10:30','12:50']);
  assert.deepEqual(originDepartures(routeForOrigin(transit,'station'),'2'),[]);
  assert.equal(routeForOrigin(transit,'hahoe').origin,'하회마을');
  assert.deepEqual(originDepartures(routeForOrigin(transit,'hahoe'),'1'),[]);
  for(const r of transit.routes){
    assert.ok(r.coordinates.length>200);assert.ok(r.stops.length>10);
    assert.ok(r.stops.every((s,i)=>i===0||s.order>r.stops[i-1].order));
    const p=routeProjection(r);assert.ok(p.points.every(c=>c.every(Number.isFinite)));assert.ok(!p.path.includes('NaN'));
  }
});
test('origin departure times cannot produce a false feasible bus return',()=>{
  const result=returnDeadline({train:1290,mode:'bus',departures:['19:00'],timetableBasis:'origin-departure'});
  assert.equal(result.valid,false);assert.equal(result.reason,'origin-times-only');assert.equal(result.arrival,undefined);
  assert.equal(returnDeadline({train:1290,mode:'car'}).valid,true);
});
test('alley hours cannot certify store opening, exact store hours and phone are retained',()=>{
  const unknown=catalog.find(p=>p.name==='총각찜닭'),known=catalog.find(p=>p.name==='중앙찜닭');
  const a=enrichRestaurant({...unknown,open:510,close:1320});
  assert.equal(a.open,undefined);assert.equal(a.close,undefined);assert.match(a.hours,/확인 필요/);
  const b=enrichRestaurant(known);assert.equal(b.open,540);assert.equal(b.close,1230);
  assert.match(restaurantFactsHTML(known),/tel:0548557272/);
  assert.equal(restaurantInfo(known).parking,null);assert.equal(restaurantInfo(known).price,null);
  for(const p of catalog.filter(p=>p.id.startsWith('shop-')&&!restaurantInfo(p).contentId)){
    assert.equal(p.open,undefined,`${p.name} must not inherit alley opening time`);
    assert.equal(p.close,undefined,`${p.name} must not inherit alley closing time`);
  }
});
test('business joins reject namesakes and same-address neighbours but permit reviewed aliases',()=>{
  const script=`from restaurant_identity import same_business
p={'name':'중앙찜닭','address':'경상북도 안동시 번영1길 51'}
assert same_business(p,{'title':'중앙찜닭','addr1':'경북 안동시 번영1길 51 (남문동)'})
assert not same_business(p,{'title':'중앙찜닭','addr1':'경북 안동시 번영1길 53'})
assert not same_business(p,{'title':'현대찜닭','addr1':p['address']})
assert same_business({'name':'신세계찜닭','address':'경북 안동시 번영길 10'},{'title':'안동신세계찜닭','addr1':'경상북도 안동시 번영길 10 (남문동)'})
`;
  execFileSync('python3',['-c',script],{cwd:new URL('../scripts/',import.meta.url)});
});
