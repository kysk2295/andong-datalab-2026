import test from 'node:test';
import assert from 'node:assert/strict';
import {canStand,clearWalk,planWalk} from '../src/relay-navigation.js';
const room={bounds:{x:[-4.4,4.4],z:[-3.5,5.9]},obstacles:[{x:0,z:0,w:2.3,d:1.5},...[-3.48,3.48].map(x=>({x,z:4.4,w:2.6,d:.15})),{x:3.1,z:2.45,w:2.5,d:.95},...[-3.3,3.3].flatMap(x=>[-2.4,.6].map(z=>({x,z,w:1.6,d:1.55})))]};
test('walk rejects walls and tables but allows seating and cashier positions',()=>{assert.equal(canStand(0,0,room),false);assert.equal(canStand(5,3,room),false);assert.equal(canStand(0,1.8,room),true);assert.equal(canStand(3,3.8,room),true);});
test('assisted movement finds traversable paths between restaurant visitor places',()=>{for(const [a,b] of [[[0,5.4],[0,1.8]],[[0,1.8],[3,3.8]],[[3,3.8],[0,1.8]],[[0,1.8],[0,-2.4]]]){const path=planWalk(a,b,room);assert.ok(path);assert.deepEqual(path[0],a);assert.deepEqual(path.at(-1),b);for(let i=1;i<path.length;i++)assert.ok(clearWalk(path[i-1],path[i],room));}});
test('unreachable goals are not teleported through furniture',()=>{const blocked={bounds:{x:[-2,2],z:[-2,2]},obstacles:[{x:0,z:0,w:5,d:.5}]};assert.equal(planWalk([0,1],[0,-1],blocked),null);assert.equal(planWalk([0,1],[0,0],blocked),null);});

test('courtyard visitors use the open doorway to reach the reception desk',()=>{const courtyard={...room,bounds:{x:[-4.4,4.4],z:[-3.5,12]}};assert.equal(canStand(3.48,4.4,courtyard),false);const route=planWalk([0,10.8],[3,3.8],courtyard);assert.ok(route);for(let i=1;i<route.length;i++)assert.ok(clearWalk(route[i-1],route[i],courtyard));});
