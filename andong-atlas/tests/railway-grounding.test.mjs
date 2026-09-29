import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from 'three';
import {projection,sampleHeight} from '../src/geo.js';
import {railwayProfiles} from '../src/railway-profile.js';
import {railwayBed,railwayPiers} from '../src/railway-structure.js';
import {RailwayScene} from '../src/railways.js';
const read=n=>JSON.parse(fs.readFileSync(new URL(`../public/data/${n}.json`,import.meta.url)));
const station=read('regions/station'),project=projection(read('terrain').bbox);
const groundAt=(x,z)=>sampleHeight(station.terrain,...project.toGeo(x,z))*.008;
const originalTracks=structuredClone(station.railways),tracks=railwayProfiles(station.railways,project,groundAt);
const curveFor=track=>{const curve=new THREE.CurvePath();for(let i=1;i<track.path.length;i++){const p=track.path[i-1],q=track.path[i];curve.add(new THREE.LineCurve3(new THREE.Vector3(p.x,p.height,p.z),new THREE.Vector3(q.x,q.height,q.z)));}return curve;};

test('station rail joints share levels, clear the terrain, and bound the displayed grade',()=>{
  const seen=new Map();let joints=0;
  for(const track of tracks)for(let i=0;i<track.path.length;i++){
    const p=track.path[i],key=track.coordinates[i].map(v=>v.toFixed(9)).join(',');
    if(seen.has(key)){assert.equal(seen.get(key),p.height);joints++;}else seen.set(key,p.height);
    assert.ok(p.height>=groundAt(p.x,p.z)+(track.bridge?.0139:.0019));
    if(i){const a=track.path[i-1],length=Math.hypot(p.x-a.x,p.z-a.z);assert.ok(Math.abs(p.height-a.height)<=length*.2+1e-8);}
  }
  assert.ok(joints>15,'real station junctions are checked');
  assert.deepEqual(station.railways,originalTracks);
  const reversed=railwayProfiles([...station.railways].reverse(),project,groundAt);
  for(const t of reversed)for(const p of t.path)assert.ok(Math.abs(p.height-tracks.find(v=>v.id===t.id).surface(p.x,p.z))<1e-7);
});

test('elevated railways have a solid deck and piers that reach terrain instead of floating ribbons',()=>{
  for(const track of tracks.filter(t=>t.bridge)){
    const geometry=railwayBed(track,groundAt),material=new THREE.MeshBasicMaterial({side:THREE.DoubleSide}),mesh=new THREE.Mesh(geometry,material);mesh.updateMatrixWorld();
    const curve=curveFor(track),p=curve.getPointAt(.53);
    const hits=new THREE.Raycaster(new THREE.Vector3(p.x,p.y+.1,p.z),new THREE.Vector3(0,-1,0)).intersectObject(mesh);
    assert.ok(hits.length>=2,track.id+' has top and underside');
    assert.ok(Math.abs(hits[0].point.y-(p.y+.0006))<1e-5);
    assert.ok(hits.some(h=>Math.abs(h.point.y-(p.y-.006))<1e-5));
    const piers=railwayPiers(curve,groundAt);assert.ok(piers.length>0,track.id+' has supports');
    for(let i=0;i<piers.length;i+=2){
      piers[i].computeBoundingBox();const box=piers[i].boundingBox,centre=box.getCenter(new THREE.Vector3());
      assert.ok(box.min.y<=groundAt(centre.x,centre.z)+1e-6);
      assert.ok(Math.abs(box.max.y-(track.surface(centre.x,centre.z)-.006))<1e-5);
    }
    piers.forEach(g=>g.dispose());geometry.dispose();material.dispose();
  }
});

test('ground beds meet the terrain and underground or duplicate segments do not produce invalid geometry',()=>{
  const identity={toWorld:c=>c},ground=(x,z)=>x*.03+z*.02;
  const feature={id:'g',properties:{railway:'rail'},geometry:{coordinates:[[0,0],[0,0],[.2,0]]}};
  const profiles=railwayProfiles([feature,{...feature,id:'tunnel',properties:{railway:'rail',tunnel:'yes'}}],identity,ground);
  assert.equal(profiles.length,1);
  const geometry=railwayBed(profiles[0],ground),positions=geometry.attributes.position;
  assert.ok([...positions.array].every(Number.isFinite));
  let grounded=0;for(let i=0;i<positions.count;i++)if(positions.getY(i)<=ground(positions.getX(i),positions.getZ(i)))grounded++;
  assert.ok(grounded>0);geometry.dispose();
});

test('train wheels sit on rails and coaches pitch with the rail profile',()=>{
  const track={id:'slope',properties:{railway:'rail'},geometry:{coordinates:[[0,0],[1,0]]}};
  const d={data:{railways:[track],center:[.5,0]},a:{project:{toWorld:c=>c,toGeo:(x,z)=>[x,z]}},group:new THREE.Group(),point:([x,z])=>new THREE.Vector3(x,x*.1,z),ribbon:()=>new THREE.PlaneGeometry(.1,.01),merge(gs,material){gs.forEach(g=>g.dispose());material.dispose();}};
  const scene=new RailwayScene(d);scene.update(3);
  for(const coach of scene.coaches.filter(c=>c.visible)){
    assert.ok(Math.abs(coach.rotation.x)>0.05);coach.updateMatrixWorld();
    const wheels=coach.children.filter(c=>c.name==='train-wheel');assert.equal(wheels.length,4);
    for(const wheel of wheels){
      // The bottom of each wheel follows the same sloped rail plane as the body.
      const bottom=coach.localToWorld(wheel.position.clone().add(new THREE.Vector3(0,-.0015,0)));
      assert.ok(Math.abs(bottom.y-scene.tracks[0].surface(bottom.x,bottom.z)-.0018)<.0002);
    }
  }
  const materials=new Set();d.group.traverse(o=>{o.geometry?.dispose();if(o.material)materials.add(o.material);});materials.forEach(m=>m.dispose());
});
