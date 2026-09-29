import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import * as THREE from "three";
import { createWalkingBridge } from "../src/bridge-model.js";
import { JourneyScene } from "../src/journey-scene.js";
import {
  JourneyNetwork,
  makeJourney,
  appendReturn,
  returnDeadline,
  parseTime,
  benefitAt,
  placementComparison,
} from "../src/journey-model.js";
const read = (n) =>
  JSON.parse(
    fs.readFileSync(new URL(`../public/data/${n}.json`, import.meta.url)),
  );
const data = read("journey"),
  analysis = read("analysis"),
  network = new JourneyNetwork(data.network),
  food = data.places.find((p) => p.kind === "restaurant").id;
const make = (options = {}) =>
  makeJourney({
    catalog: data.places,
    network,
    analysis,
    stops: data.stops,
    restaurant: food,
    ...options,
  });
test('Temporary map fallback restores the chosen view on the next clear stage',()=>{
  const player=Object.create(JourneyScene.prototype);
  player.preferredView='first';player.view='first';player.index=0;
  player.journey={stages:[{cameraClear:false},{cameraClear:true}]};
  player.setView=(view,options)=>{assert.equal(options.automatic,true);player.view=view;};
  player.restorePreferredView();assert.equal(player.view,'map');
  player.index=1;player.restorePreferredView();assert.equal(player.view,'first');
  player.preferredView='map';player.restorePreferredView();assert.equal(player.view,'map');
});
test('Standing at a bridge arrival keeps the traveler and first-person eye on the deck',()=>{
 for(const bridge of [true,false]){
  const player=Object.create(JourneyScene.prototype),place={coordinates:[2,0]};
  Object.assign(player,{group:new THREE.Group(),decor:new THREE.Group(),active:true,playing:false,view:'first',elapsed:0,index:1,yaw:0,pitch:0,
   person:new THREE.Group(),bus:new THREE.Group(),network:{snap:()=>null},onTick:()=>{},
   journey:{stages:[{kind:'walk',path:{bridges:bridge?['deck','deck']:['','']}},{kind:'place',place,start:0,end:5}]},
   paths:[[new THREE.Vector3(0,4,0),new THREE.Vector3(2,4,0)],[]],
   a:{point:()=>new THREE.Vector3(2,1,0),project:{toGeo:(x,z)=>[x,z]},elevation:()=>1,focusDetail:()=>{},
    camera:new THREE.PerspectiveCamera(),controls:{target:new THREE.Vector3()},container:{dataset:{}}}
  });
  player.update(0);
  const surface=bridge?4:1.0014;
  assert.ok(Math.abs(player.person.position.y-surface)<1e-9);
  assert.ok(Math.abs(player.a.camera.position.y-(surface+.014)*.25)<1e-9);
  assert.equal(player.a.container.dataset.journeyView,'first');
 }
});
test('KTX exit uses the mapped station entrance and a nearby station bus stop',()=>{
  const station=data.places.find(p=>p.id==='station');
  assert.match(station.source,/출입구/);
  const walk=make({origin:'station'}).stages.find(s=>s.kind==='walk');
  assert.match(walk.place.name,/안동역/);
  assert.ok(walk.path.distance>50&&walk.path.distance<450,'station approach should not circle the entire station block');
});
test("journeys connect all four origins to the bridge on road graph", () => {
  for (const origin of ["downtown", "station", "terminal", "hahoe"]) {
    const j = make({ origin });
    assert.ok(j.stages.some((s) => s.kind === "popup"));
    assert.ok(
      j.stages
        .filter((s) => s.path)
        .every((s) => s.path.coordinates.length > 0),
    );
    assert.ok(!j.issues.some((s) => s.includes("연결 도로")));
    assert.ok(
      j.stages.every(
        (s, i) => s.end >= s.start && (!i || s.start === j.stages[i - 1].end),
      ),
    );
  }
});
test("current plan has no proposed workshop or popup; both plans retain stages", () => {
  assert.ok(make({ plan: "현재" }).stages.every((s) => !s.place.proposed));
  for (const plan of ["기본안", "확대안"]) {
    const j = make({ plan });
    assert.ok(j.stages.some((s) => s.kind === "experience"));
    assert.ok(j.stages.some((s) => s.kind === "popup"));
  }
});
test("return railway deadline subtracts walking, waiting and station buffer", () => {
  const r = returnDeadline({
    train: 1290,
    buffer: 20,
    drive: 35,
    transfer: 10,
    walk: 8,
  });
  assert.equal(r.leave, 1217);
  assert.equal(r.arrival, 1270);
});
test("112 return selects latest feasible departure inclusively", () => {
  const base = {
    train: 1200,
    buffer: 20,
    drive: 25,
    transfer: 15,
    walk: 8,
    mode: "bus",
    departures: ["18:25", "19:00"],
  };
  assert.equal(returnDeadline(base).departure, 1140);
  assert.equal(returnDeadline({ ...base, train: 1199 }).departure, 1105);
  assert.equal(returnDeadline({ ...base, train: 1000 }).valid, false);
});
test("invalid and previous-day times are rejected", () => {
  assert.equal(parseTime("24:00"), null);
  assert.equal(parseTime("19:80"), null);
  assert.equal(parseTime(""), null);
  assert.equal(returnDeadline({ train: 20 }).valid, false);
  assert.equal(returnDeadline({ train: NaN }).valid, false);
});
test("missed return bus does not animate an invented later departure", () => {
  const j = make(),
    r = returnDeadline({
      train: 1100,
      mode: "bus",
      departures: ["16:40"],
      drive: 25,
      transfer: 10,
    });
  const full = appendReturn(j, {
    catalog: data.places,
    network,
    deadline: r,
    mode: "bus",
  });
  assert.equal(full.late, true);
  assert.ok(full.issues.some((s) => s.includes("놓치는")));
  assert.equal(full.stages.length, j.stages.length);
});
test("return mileage includes the route to the station", () => {
  const j = make();
  const full = appendReturn(j, {
    catalog: data.places,
    network,
    deadline: returnDeadline({ train: 1290 }),
    mode: "car",
  });
  const returning = full.stages.find((s) => s.kind === "return");
  assert.equal(full.distance, j.distance + returning.path.distance);
});
test("benefit hours, deduplication and underlying resident benefit are independent", () => {
  const p = { id: "p", open: 600, close: 1200, benefit: "기존 할인" },
    a = [{ id: "p", discount: 10, start: 1000, end: 1100 }];
  assert.equal(benefitAt(p, a, 1050).type, "추가 제안");
  assert.equal(benefitAt(p, a, 1100).type, "기존 주민증");
  assert.equal(benefitAt(p, a, 1200), null);
  assert.equal(benefitAt(p, [], 1050).type, "기존 주민증");
});
test("placement measures reachable sites, not money or straight-line coverage", () => {
  const p = data.places.find((p) => p.id === food),
    base = data.places.find((p) => p.id === "downtown"),
    a = [{ id: p.id, discount: 10, start: 1000, end: 1300 }];
  const r = placementComparison(
    data.places,
    a,
    base.coordinates,
    1110,
    network,
  );
  assert.ok(r.after >= r.before);
  assert.ok(r.rows.some((r) => r.place.id === p.id));
  assert.ok(r.rows.every((r) => r.walk <= 10));
  assert.equal(r.revenue, undefined);
});
test("unreachable route remains absent rather than a straight-line fallback", () => {
  assert.equal(network.route([0, 0], data.places[0].coordinates, "walk"), null);
});
test("source place records have unique IDs and uncertain prices stay null", () => {
  assert.equal(new Set(data.places.map((p) => p.id)).size, data.places.length);
  assert.ok(
    data.places
      .filter((p) => p.kind === "restaurant")
      .every((p) => p.price === null),
  );
  assert.ok(data.places.find((p) => p.id === "workshop").proposed);
  assert.ok(data.unlocatedBenefits.length > 0);
});

import { clearCameraPath } from "../src/journey-clearance.js";
import { footprintMask } from "../src/footprints.js";
import { projection } from "../src/geo.js";
import { meters } from "../src/journey-model.js";
test("camera corridor avoids an obstructing shell continuously and rejects impossible corridors", () => {
  const points = Array.from({ length: 21 }, (_, i) => ({
    x: i * 0.002,
    y: 0,
    z: 0,
  }));
  const blocked = (x, z) => x > 0.014 && x < 0.026 && Math.abs(z) < 0.005;
  const clear = clearCameraPath(points, blocked);
  assert.ok(clear);
  for (let i = 1; i < clear.length; i++) {
    const a = clear[i - 1],
      b = clear[i];
    for (let k = 0; k <= 20; k++)
      assert.ok(
        !blocked(a.x + ((b.x - a.x) * k) / 20, a.z + ((b.z - a.z) * k) / 20),
      );
  }
  assert.equal(
    clearCameraPath(points, () => true),
    null,
  );
});
test("default road journey can render at eye level without passing through mapped buildings", () => {
  const projectionMap = projection(read("terrain").bbox),
    mask = footprintMask(read("district").buildings, (c) =>
      projectionMap.toWorld(c),
    );
  const safeNetwork = new JourneyNetwork(data.network, (c) =>
    mask(...projectionMap.toWorld(c), 0.001),
  );
  const j = makeJourney({
    catalog: data.places,
    network: safeNetwork,
    analysis,
    stops: data.stops,
    restaurant: food,
  });
  const renderer = Object.create(JourneyScene.prototype);
  renderer.a = {
    project: projectionMap,
    elevation: () => 0,
    point: (c, lift = 0) => {
      const [x, z] = projectionMap.toWorld(c);
      return new THREE.Vector3(x, lift, z);
    },
    district: {
      buildingBlocked: mask,
      waterBlocked: () => false,
      bridgeSurfaces: new Map(),
    },
  };
  for (const s of j.stages.filter((s) => s.path)) {
    const cameraPoints = renderer.pathPoints(s);
    assert.ok(s.cameraClear, `actual camera path: ${s.title}`);
    assert.ok(clearCameraPath(cameraPoints, mask), s.title);
    const ps = [];
    for (let i = 1; i < s.path.coordinates.length; i++) {
      const a = s.path.coordinates[i - 1],
        b = s.path.coordinates[i],
        n = Math.ceil(meters(a, b) / 2);
      for (let k = 0; k < n; k++) {
        const [x, z] = projectionMap.toWorld([
          a[0] + ((b[0] - a[0]) * k) / n,
          a[1] + ((b[1] - a[1]) * k) / n,
        ]);
        ps.push({ x, y: 0, z });
      }
    }
    assert.ok(clearCameraPath(ps, mask), s.title);
    assert.ok(
      s.path.distance < 10000,
      "routing penalties must not inflate physical distance",
    );
  }
});

test("bridge supports and open pavilion do not block the walking corridor", () => {
  const { group } = createWalkingBridge();
  const deck = group.getObjectByName("deck");
  const deckTop = deck.position.y + deck.geometry.parameters.height / 2;
  group.traverse((mesh) => {
    if (mesh.name === "support")
      assert.ok(
        mesh.position.y + mesh.geometry.parameters.height / 2 < deckTop,
      );
    if (mesh.name === "pavilion-column")
      assert.ok(
        Math.abs(mesh.position.z) - mesh.geometry.parameters.depth / 2 > 0.001,
      );
  });
  const ray = new THREE.Raycaster(
    new THREE.Vector3(-0.38, deckTop + 0.014, 0),
    new THREE.Vector3(1, 0, 0),
    0,
    0.76,
  );
  group.updateMatrixWorld(true);
  assert.equal(ray.intersectObjects(group.children).length, 0);
});
test("bridge deck follows all bends in the downloaded walking route", async () => {
  const { AtlasScene } = await import("../src/scene.js");
  const district = read("district"),
    project = projection(read("terrain").bbox);
  const feature = district.roads.find(
    (f) => f.properties["bridge:name"] === "월영교",
  );
  const group = new THREE.Group();
  AtlasScene.prototype.positionBridge.call(
    { data: { district }, project, elevation: () => 1 },
    group,
  );
  group.updateMatrixWorld(true);
  const points = feature.geometry.coordinates.map((c) => {
    const [x, z] = project.toWorld(c),
      p = group.worldToLocal(new THREE.Vector3(x, group.position.y, z));
    return [p.x, p.z];
  });
  group.add(createWalkingBridge(points).group);
  group.updateMatrixWorld(true);
  for (let i = 1; i < feature.geometry.coordinates.length; i++) {
    const a = project.toWorld(feature.geometry.coordinates[i - 1]),
      b = project.toWorld(feature.geometry.coordinates[i]);
    for (const t of [0.1, 0.5, 0.9]) {
      const ray = new THREE.Raycaster(
        new THREE.Vector3(
          a[0] + (b[0] - a[0]) * t,
          2,
          a[1] + (b[1] - a[1]) * t,
        ),
        new THREE.Vector3(0, -1, 0),
      );
      const hit = ray
        .intersectObject(group, true)
        .find((h) => h.object.name === "deck");
      assert.ok(hit, `segment ${i}, fraction ${t}`);
      assert.ok(Math.abs(hit.point.y - 1.043) < 1e-8);
    }
  }
});

test("proposed return connection obeys its evening operating window", () => {
  assert.equal(returnDeadline({ train: 1100, mode: "proposal" }).valid, false);
  assert.equal(
    returnDeadline({ train: 1410, mode: "proposal" }).departure,
    1260,
  );
});
test("station course contains walking to a real stop, waiting, boarding and walking after alighting", () => {
  const j = make({ origin: "station", stops: data.stops });
  assert.ok(
    j.stages.some(
      (s) => s.title === "정류장까지 걸어가기" && s.kind === "walk",
    ),
  );
  assert.ok(j.stages.some((s) => s.kind === "wait" && s.place.kind === "stop"));
  assert.ok(
    j.stages.some((s) => s.kind === "alight" && s.place.id.startsWith("stop-")),
  );
  assert.ok(j.stages.some((s) => s.title === "하차 후 식당까지 걷기"));
});

test('Return vehicle follows the chosen car or bus mode',()=>{
 for(const mode of ['car','proposal','bus']){
  const j=make({start:900}),deadline=returnDeadline({train:1320,mode,departures:['19:00']});
  const full=appendReturn(j,{catalog:data.places,network,deadline,mode});
  const stage=full.stages.find(s=>s.title.startsWith('안동역 복귀'));
  if(stage)assert.equal(stage.vehicleType,mode==='car'?'car':'bus');
  else assert.ok(full.late&&mode==='bus');
 }
});
