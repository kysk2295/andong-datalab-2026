import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {tourismModel,routeMidpoint,visibleMapPlaces,layerState,fitMapBounds,projectMapPoint,clusterMapPlaces} from '../src/tourism-map-model.js';
import {mapPointStyle} from '../src/map-point-model.js';
const read=name=>JSON.parse(readFileSync(new URL(`../public/data/${name}.json`,import.meta.url)));
const model=tourismModel(read('journey'),read('relay-research').route);

test('only geolocated resident-card merchants become clickable geographic pins',()=>{
  assert.equal(model.benefits.length,6);assert.equal(model.unlocated.length,21);
  assert.ok(model.benefits.every(p=>p.benefit&&p.coordinates.length===2&&!p.proposed));
  assert.ok(model.unlocated.every(p=>p.coordinates===null));
  const pins=visibleMapPlaces(model,{benefits:true,route:false});
  assert.equal(pins.length,6);assert.ok(!pins.some(p=>p.id==='workshop'));
});
test('three numbered stages preserve route endpoints and locate transfer by distance',()=>{
  const coords=model.route.coordinates;
  assert.deepEqual(model.stages.map(p=>p.relayStage),[1,2,3]);
  assert.deepEqual(model.stages[0].coordinates,coords[0]);
  assert.deepEqual(model.stages[2].coordinates,coords.at(-1));
  assert.deepEqual(routeMidpoint([[128,36],[128.001,36],[128.01,36]]),[128.005,36]);
  assert.equal(mapPointStyle(model.stages[1]).type,'relay');
});
test('independent layers do not introduce unlocated or synthetic benefit markers',()=>{
  assert.equal(visibleMapPlaces(model,{benefits:false,route:false}).length,0);
  assert.equal(visibleMapPlaces(model,{benefits:false,route:true}).length,3);
  assert.equal(visibleMapPlaces(model,{benefits:true,route:true}).length,9);
  assert.deepEqual(layerState('{oops',{benefits:false,route:true}),{benefits:false,route:true,booths:false});
  assert.deepEqual(layerState('{"benefits":"false","route":true}'),{benefits:false,route:true,booths:false});
});
test('map framing preserves geographic aspect and keeps markers within desktop and mobile bounds',()=>{
  for(const [w,h] of [[850,380],[340,300]]) {
    for(const coords of [model.route.coordinates,model.benefits.map(p=>p.coordinates),[model.benefits[0].coordinates]]) {
      const b=fitMapBounds(coords,w,h),cos=Math.cos((b[1]+b[3])/2*Math.PI/180);
      assert.ok(Math.abs((b[2]-b[0])*cos/(b[3]-b[1])-w/h)<1e-8);
      for(const c of coords){const [x,y]=projectMapPoint(c,b,w,h);assert.ok(x>=16&&x<=w-16&&y>=16&&y<=h-16);}
    }
  }
});
test('published small map is derived from the existing benefit and route sources',()=>{
  const data=read('tourism-map');
  assert.deepEqual(data.benefits,model.benefits);assert.deepEqual(data.unlocated,model.unlocated);
  assert.deepEqual(data.route,model.route);assert.deepEqual(data.stages,model.stages);
  assert.ok(data.background.some(f=>f.kind==='water'));
  assert.ok(data.background.some(f=>f.kind==='road'));
});
test('overlapping pins form selectable clusters without losing or moving the source places',()=>{
  const all=visibleMapPlaces(model,{benefits:true,route:true}),bounds=fitMapBounds(all.map(p=>p.coordinates),850,380);
  const clusters=clusterMapPlaces(all,bounds,850,380);
  assert.equal(clusters.flatMap(c=>c.points).length,all.length);
  assert.ok(clusters.some(c=>c.points.length>1));
  assert.deepEqual(new Set(clusters.flatMap(c=>c.points.map(p=>p.place.id))),new Set(all.map(p=>p.id)));
});
