import test from 'node:test';
import assert from 'node:assert/strict';
import {mapPointStyle, declutterMapPoints} from '../src/map-point-model.js';

test('Overlapping map symbols preserve selection and added benefits without moving source anchors', () => {
  const points=[{id:'food',x:100,y:100,z:0,priority:10},{id:'chosen',x:105,y:105,z:0,priority:100},{id:'benefit',x:200,y:100,z:0,priority:80},{id:'nearby',x:203,y:100,z:0,priority:10}];
  const raw=structuredClone(points);
  assert.deepEqual(declutterMapPoints(points,{width:500,height:400}).map(p=>p.id),['chosen','benefit']);
  assert.deepEqual(points,raw);
  const spread=points.map(p=>({...p,x:p.x*6,y:p.y*3}));
  assert.equal(declutterMapPoints(spread,{width:2000,height:1000,gap:16}).length,4);
});

test('GIS points hidden by panels, behind the camera or off screen cannot cover the map UI', () => {
  const points=[{id:'visible',x:300,y:100,z:0,priority:10},{id:'panel',x:100,y:100,z:0,priority:100},{id:'behind',x:450,y:100,z:2,priority:10},{id:'edge',x:2,y:100,z:0,priority:10},{id:'invalid',x:NaN,y:100,z:0,priority:10}];
  assert.deepEqual(declutterMapPoints(points,{width:500,height:400,obstacles:[{left:0,top:0,right:200,bottom:400}]}).map(p=>p.id),['visible']);
});

test('Selection does not erase a place benefit type, and added benefits take display priority', () => {
  const place={kind:'restaurant',benefit:'10%'};
  assert.equal(mapPointStyle(place,{selected:true}).type,'benefit');
  assert.equal(mapPointStyle(place,{selected:true}).priority,100);
  assert.equal(mapPointStyle(place,{added:true}).type,'added');
  assert.equal(mapPointStyle({kind:'experience'}).type,'experience');
  assert.equal(mapPointStyle({kind:'stop'}).type,'stop');
  assert.match(mapPointStyle({kind:'experience',proposed:true}).label,/제안/);
});
