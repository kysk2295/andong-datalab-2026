import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import {
  projection,
  sampleHeight,
  closingState,
  remainingDepartures,
} from "../src/geo.js";
const read = (n) =>
  JSON.parse(
    fs.readFileSync(new URL(`../public/data/${n}.json`, import.meta.url)),
  );
test("projection preserves geographic positions", () => {
  const p = projection(read("terrain").bbox),
    c = [128.7609, 36.5765];
  const v = p.toGeo(...p.toWorld(c));
  assert.ok(Math.abs(v[0] - c[0]) < 1e-9);
  assert.ok(Math.abs(v[1] - c[1]) < 1e-9);
});
test("terrain inventory and all 24 districts are valid", () => {
  const t = read("terrain");
  assert.equal(t.heights.length, t.cols * t.rows);
  assert.equal(read("boundaries").features.length, 24);
  assert.ok(t.heights.every((h) => Number.isFinite(h) && h > -50 && h < 2500));
  assert.ok(sampleHeight(t, 128.7609, 36.5765) > 0);
});
test("closing time does not imply known opening time", () => {
  assert.equal(closingState({ 영업종료: "20:00" }, 1200), "조사 기준 종료");
  assert.equal(
    closingState({ 영업종료: "20:00" }, 1199),
    "종료 전 · 개점 미확인",
  );
  assert.equal(closingState({}, 1200), "확인 필요");
  assert.equal(closingState({ 상태: "폐업" }, 1200), "폐업");
});
test("last bus boundary is inclusive and subsequent time has none", () => {
  assert.deepEqual(remainingDepartures(["17:55", "18:45"], 1125), ["18:45"]);
  assert.deepEqual(remainingDepartures(["17:55", "18:45"], 1140), []);
});
test("scenarios exactly match existing analysis", () => {
  const original = JSON.parse(
    fs.readFileSync(
      new URL(
        "../../보고서/성과도출_20260922/시뮬레이션결과.json",
        import.meta.url,
      ),
    ),
  );
  assert.deepEqual(read("analysis").scenarios, original["시나리오"]);
  assert.deepEqual(
    Object.values(read("analysis").scenarios).map((s) => s["참여율"]),
    [0.02, 0.04, 0.1],
  );
});
test("manifest counts equal downloaded vector features", () => {
  const m = read("manifest"),
    map = read("map");
  for (const [k, v] of Object.entries(m.counts)) assert.equal(map[k].length, v);
});
test("basic and expanded outcomes retain the latest source and resident effects stay separate", () => {
  const solution = read("solution");
  const source = JSON.parse(
    fs.readFileSync(
      new URL(
        "../../보고서/성과도출_20260922/시뮬레이션결과.json",
        import.meta.url,
      ),
    ),
  );
  for (const name of ["기본안", "확대안"])
    assert.deepEqual(solution.plans[name], source[name]);
  assert.equal(
    solution.resident.addedMonthlyExpanded,
    source["p근거"]["하한_주민증GLM"] * source["고정값"]["중구동_월방문"],
  );
  assert.ok(
    solution.resident.addedMonthlyExpanded <
      solution.plans["확대안"]["인증_월"].P50,
  );
  assert.equal(solution.plans["기본안"]["입력"].T, 12);
});
test("animated vehicle path uses downloaded road segments", () => {
  const route = read("solution").route,
    map = read("district"),
    segments = new Set();
  const key = (a, b) => JSON.stringify([a, b]);
  for (const f of map.roads) {
    if (
      [
        "path",
        "footway",
        "pedestrian",
        "cycleway",
        "steps",
        "bridleway",
      ].includes(f.properties.highway)
    )
      continue;
    const lines =
      f.geometry.type === "LineString"
        ? [f.geometry.coordinates]
        : f.geometry.coordinates;
    for (const line of lines)
      for (let i = 1; i < line.length; i++) {
        segments.add(key(line[i - 1], line[i]));
        segments.add(key(line[i], line[i - 1]));
      }
  }
  assert.ok(route.length > 2);
  // The source road coordinates are retained to seven decimal degrees.
  const rounded = new Set(
    [...segments].map((s) =>
      JSON.stringify(JSON.parse(s).map((c) => c.map((x) => +x.toFixed(7)))),
    ),
  );
  for (let i = 1; i < route.length; i++)
    assert.ok(
      rounded.has(
        JSON.stringify(
          [route[i - 1], route[i]].map((c) => c.map((x) => +x.toFixed(7))),
        ),
      ),
    );
});
test("height sampling follows the rendered terrain triangles", () => {
  const terrain = {
    bbox: [0, 0, 1, 1],
    cols: 2,
    rows: 2,
    heights: [0, 0, 0, 100],
  };
  assert.equal(sampleHeight(terrain, 0.5, 0.5), 0);
  assert.equal(sampleHeight(terrain, 0.75, 0.25), 50);
});
test("water animation stays inside mapped water and honors reduced motion", async () => {
  const THREE = await import("three"),
    { CityDetail } = await import("../src/city-detail.js"),
    { inRing, polygons, routeDistance } = await import("../src/geo.js");
  const map = read("map"),
    atlas = {
      world: new THREE.Group(),
      data: { map, solution: read("solution") },
      point: (c) => new THREE.Vector3(c[0], 0, c[1]),
      project: { toGeo: (x, z) => [x, z] },
      elevation: () => 0,
      reduced: true,
      solution: { group: { visible: false } },
    };
  const life = new CityDetail(atlas),
    water = map.water.flatMap((f) => polygons(f.geometry));
  assert.equal(life.boats.length, 4);
  for (let i = 0; i < 300; i++) {
    const p = life.waterPath.getPointAt(i / 300);
    assert.ok(
      water.some(
        (r) =>
          inRing([p.x, p.z], r[0]) &&
          !r.slice(1).some((h) => inRing([p.x, p.z], h)),
      ),
    );
  }
  life.update(1);
  assert.equal(life.time, 0);
  atlas.reduced = false;
  life.update(1);
  assert.equal(life.time, 1);
  life.running = false;
  life.update(1);
  assert.equal(life.time, 1);
  assert.ok(
    Math.abs(
      routeDistance({
        type: "LineString",
        coordinates: [
          [0, 0],
          [0, 1],
        ],
      }) - 111195,
    ) < 5,
  );
});

test("district preserves raw roads, closed footprints, provenance and dense terrain", () => {
  const d = read("district"),
    t = d.terrain;
  assert.equal(
    d.buildings.length,
    d.counts.osmBuildings + d.counts.tileSupplement + d.counts.gbaSupplement,
  );
  assert.equal(d.counts.gbaSupplement, 1253);
  assert.equal(d.counts.osmBuildings, 753);
  assert.equal(d.roads.length, 835);
  assert.equal(t.heights.length, t.cols * t.rows);
  assert.equal(t.heights.length, 64521);
  assert.deepEqual(t.bbox, d.bbox);
  assert.ok(t.heights.every((h) => Number.isFinite(h) && h >= 0 && h < 2500));
  for (const f of d.buildings) {
    const r = f.geometry.coordinates[0];
    assert.deepEqual(r[0], r.at(-1));
    assert.ok(r.length >= 4);
  }
  for (const f of d.roads) {
    assert.ok(f.geometry.coordinates.length >= 2);
    for (const [x, y] of f.geometry.coordinates)
      assert.ok(
        x >= d.bbox[0] && x <= d.bbox[2] && y >= d.bbox[1] && y <= d.bbox[3],
      );
  }
  assert.ok(d.roads.some((f) => f.properties.oneway === "yes"));
  assert.match(d.note, /추정/);
});

test("supplementary building research retains geographic coordinates, estimated height and license", () => {
  const d = read("buildings");
  assert.equal(d.features.length, 54640);
  assert.equal(d.source.license, "CC BY-NC 4.0");
  const ids = new Set();
  for (const f of d.features) {
    assert.ok(!ids.has(f.id));
    ids.add(f.id);
    assert.ok(f.properties.height >= 2.5 && f.properties.height <= 150);
    assert.equal(f.properties.heightMethod, "satellite-derived estimate");
    const [x, y] = f.geometry.coordinates[0][0];
    assert.ok(x > 127 && x < 130 && y > 35 && y < 38);
  }
});

test("traffic continues at connected nodes, respects one-way and stops at an unconnected end", async () => {
  const { roadNetwork, vehicleState, advanceVehicle, vehiclePosition } =
    await import("../src/traffic.js");
  const f = (id, c, oneway) => ({
    id,
    properties: { highway: "residential", oneway },
    geometry: { coordinates: c },
  });
  const net = roadNetwork(
    [
      f(
        "a",
        [
          [0, 0],
          [1, 0],
        ],
        "yes",
      ),
      f(
        "b",
        [
          [1, 0],
          [1, 1],
        ],
        "yes",
      ),
      f(
        "c",
        [
          [3, 0],
          [2, 0],
        ],
        "-1",
      ),
    ],
    (c) => c,
  );
  assert.equal(net.edges.length, 3);
  assert.ok(net.edges.some((e) => e.a.x === 2 && e.b.x === 3));
  const state = vehicleState(net, 0);
  state.speed = 1;
  advanceVehicle(state, 1.1);
  assert.equal(state.edge.id, "b");
  assert.ok(Math.abs(state.distance - 0.1) < 1e-8);
  const before = vehiclePosition(state);
  advanceVehicle(state, 0);
  assert.deepEqual(vehiclePosition(state), before);
  advanceVehicle(state, 4);
  assert.equal(state.stopped, true);
  assert.equal(state.edge.b.z, 1);
  assert.equal(state.distance, state.edge.length);
});

test("camera sightline clears an intervening bank when focusing river boats", async () => {
  const { terrainSafeEye } = await import("../src/geo.js");
  const target = { x: 0, y: 1, z: 0 },
    eye = { x: 1, y: 1.3, z: 1 },
    height = (x) => (x > 0.3 && x < 0.8 ? 1.8 : 0.9);
  const y = terrainSafeEye(target, eye, height);
  assert.ok(y > eye.y);
  for (let i = 1; i <= 16; i++) {
    const t = i / 16;
    assert.ok(
      target.y + (y - target.y) * t >= height(t) + 0.012 + 0.09 * t - 1e-9,
    );
  }
});

test("batched building mesh preserves shell dimensions and outward faces", async () => {
  const THREE = await import("three"),
    { buildingGeometry } = await import("../src/building-geometry.js");
  const { geometry: g, count } = buildingGeometry(
    [
      {
        properties: { height: 8 },
        geometry: {
          type: "Polygon",
          coordinates: [
            [
              [0, 0],
              [1, 0],
              [1, 1],
              [0, 1],
              [0, 0],
            ],
          ],
        },
      },
    ],
    (c) => c,
    () => 2,
  );
  assert.equal(count, 1);
  g.computeBoundingBox();
  assert.ok(Math.abs(g.boundingBox.max.y - 2.074) < 1e-5);
  for (let i = 0; i < g.attributes.position.count; i += 3) {
    const a = new THREE.Vector3().fromBufferAttribute(g.attributes.position, i),
      b = new THREE.Vector3().fromBufferAttribute(g.attributes.position, i + 1),
      c = new THREE.Vector3().fromBufferAttribute(g.attributes.position, i + 2),
      n = new THREE.Vector3().fromBufferAttribute(g.attributes.normal, i);
    assert.ok(b.sub(a).cross(c.sub(a)).dot(n) > 0);
  }
});

test("proposal platform clears sloped terrain and reconnects its skirt after elevation changes", async () => {
  const THREE = await import("three"),
    { SolutionScene } = await import("../src/solution-scene.js");
  let rise = 0;
  const site = { id: "popup", coordinates: [0, 0], group: new THREE.Group() };
  site.group.scale.setScalar(0.4);
  const context = {
    sites: [site],
    atlas: {
      point: () => new THREE.Vector3(0, 2, 0),
      project: { toGeo: (x, z) => [x, z] },
      elevation: ([x, z]) => 2 + x + z + rise,
    },
    material: () => new THREE.MeshStandardMaterial(),
  };
  SolutionScene.prototype.positionSites.call(context);
  assert.ok(site.group.position.y > 2 + 0.84 * 0.2 + 0.6 * 0.2);
  const top = site.group.position.y,
    firstGeometry = site.plinth.geometry;
  assert.ok(firstGeometry.attributes.position.count > 4);
  rise = 1;
  SolutionScene.prototype.positionSites.call(context);
  assert.ok(Math.abs(site.group.position.y - top - 1) < 1e-8);
  assert.notEqual(site.plinth.geometry, firstGeometry);
  assert.equal(site.group.children.length, 1);
});

test("bridge model follows the downloaded crossing endpoints", async () => {
  const THREE = await import("three"),
    { AtlasScene } = await import("../src/scene.js");
  const d = read("district"),
    t = read("terrain"),
    project = projection(t.bbox);
  const bridge = d.roads.find((f) => f.properties["bridge:name"] === "월영교");
  const group = new THREE.Group();
  AtlasScene.prototype.positionBridge.call(
    { data: { district: d }, project, elevation: () => 1 },
    group,
  );
  group.updateMatrixWorld();
  for (const [x, c] of [
    [-0.39, bridge.geometry.coordinates[0]],
    [0.39, bridge.geometry.coordinates.at(-1)],
  ]) {
    const p = group.localToWorld(new THREE.Vector3(x, 0, 0)),
      expected = project.toWorld(c);
    assert.ok(
      Math.abs(p.x - expected[0]) < 1e-8 && Math.abs(p.z - expected[1]) < 1e-8,
    );
    assert.equal(p.y, 1.035);
  }
});

test("building foundations meet sloping terrain along outer and courtyard edges", async () => {
  const { terrainSkirt } = await import("../src/building-style.js");
  const rings = [
    [
      [0, 0],
      [0.06, 0],
      [0.06, 0.06],
      [0, 0.06],
      [0, 0],
    ],
    [
      [0.02, 0.02],
      [0.04, 0.02],
      [0.04, 0.04],
      [0.02, 0.04],
      [0.02, 0.02],
    ],
  ];
  const ground = (x, z) => 0.1 + x * 2 + z;
  const g = terrainSkirt(rings, ([x, z]) => ({ x, z, y: ground(x, z) }), 0.3);
  const p = g.attributes.position;
  assert.ok(p.count > rings.flat().length * 6, "long edges are subdivided");
  for (let i = 0; i < p.count; i++) {
    const y = p.getY(i);
    assert.ok(
      Math.abs(y - 0.3) < 1e-6 ||
        Math.abs(y - (ground(p.getX(i), p.getZ(i)) - 0.001)) < 1e-6,
    );
  }
  assert.ok(
    Array.from({ length: p.count }, (_, i) => [p.getX(i), p.getZ(i)]).some(
      ([x, z]) => Math.abs(x - 0.02) < 1e-6 && Math.abs(z - 0.02) < 1e-6,
    ),
  );
  g.dispose();
});

test("building colors are stable, varied, and preserve explicit source colors", async () => {
  const { buildingAppearance } = await import("../src/building-style.js");
  const f = (id) => ({
    id,
    properties: {},
    geometry: { coordinates: [[[0, 0]]] },
  });
  const colors = Array.from({ length: 30 }, (_, i) =>
    buildingAppearance(f(`building-${i}`)),
  );
  assert.ok(new Set(colors.map((c) => c.roof)).size >= 5);
  assert.ok(new Set(colors.map((c) => c.facade)).size >= 5);
  assert.deepEqual(buildingAppearance(f("building-1")), colors[1]);
  assert.deepEqual(
    buildingAppearance({
      ...f("x"),
      properties: { "building:colour": "#abcdef", "roof:colour": "#123456" },
    }),
    { ...buildingAppearance(f("x")), facade: "#abcdef", roof: "#123456" },
  );
});

test("footprint clearance detects walls but leaves courtyards open", async () => {
  const { footprintMask } = await import("../src/footprints.js");
  const blocked = footprintMask(
    [
      {
        geometry: {
          type: "Polygon",
          coordinates: [
            [
              [0, 0],
              [1, 0],
              [1, 1],
              [0, 1],
              [0, 0],
            ],
            [
              [0.3, 0.3],
              [0.7, 0.3],
              [0.7, 0.7],
              [0.3, 0.7],
              [0.3, 0.3],
            ],
          ],
        },
      },
    ],
    (c) => c,
    0.1,
  );
  assert.equal(blocked(0.1, 0.5), true);
  assert.equal(blocked(0.5, 0.5), false);
  assert.equal(blocked(1.005, 0.5, 0.01), true);
  assert.equal(blocked(1.03, 0.5, 0.01), false);
  assert.equal(blocked(0.305, 0.5, 0.01), true);
});

test("pedestrians turn back continuously and avoid building-obstructed walkway spans", async () => {
  const { clearRuns, walkingProgress, distributedIndices, urbanWeight } =
    await import("../src/activity.js");
  const runs = clearRuns(
    Array.from({ length: 11 }, (_, i) => ({ x: i, z: 0 })),
    (x) => x >= 4 && x <= 6,
  );
  assert.deepEqual(
    runs.map((r) => r.map((p) => p.x)),
    [
      [0, 1, 2, 3],
      [7, 8, 9, 10],
    ],
  );
  const before = walkingProgress(499.99, 0, 1),
    after = walkingProgress(500.01, 0, 1);
  assert.ok(Math.abs(before.t - after.t) < 1e-7);
  assert.equal(before.direction, 1);
  assert.equal(after.direction, -1);
  const sample = distributedIndices([1, 9, 0], 100, (x) => x);
  assert.equal(sample.filter((i) => i === 0).length, 10);
  assert.equal(sample.filter((i) => i === 1).length, 90);
  assert.equal(sample.includes(2), false);
  assert.ok(urbanWeight(0, 0, [0, 0]) > urbanWeight(5, 5, [0, 0]));
});

test("public park boundaries and mapped trees retain local geometry and provenance", () => {
  const d = read("district"),
    [west, south, east, north] = d.terrain.bbox;
  assert.match(JSON.stringify(d.parkSource), /OpenStreetMap|OSM/);
  assert.ok(d.parks.some((p) => p.properties.name === "웅부공원"));
  assert.ok(d.parks.some((p) => p.properties.leisure === "pitch"));
  for (const feature of d.parks)
    for (const ring of feature.geometry.coordinates) {
      assert.deepEqual(ring[0], ring.at(-1));
      for (const [lon, lat] of ring)
        assert.ok(lon >= west && lon <= east && lat >= south && lat <= north);
    }
  for (const tree of d.mappedTrees) {
    assert.equal(tree.coordinates.length, 2);
    assert.ok(tree.coordinates.every(Number.isFinite));
  }
});

test("a distant long cycleway does not suppress an unmapped park interior layout", async () => {
  const THREE = await import("three"),
    { ParkScene } = await import("../src/parks.js"),
    { inRing } = await import("../src/geo.js");
  const { footprintMask } = await import("../src/footprints.js");
  const park = {
    properties: { leisure: "park" },
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [0, 0],
          [0.2, 0],
          [0.2, 0.2],
          [0, 0.2],
          [0, 0],
        ],
      ],
    },
  };
  const curve = new THREE.CurvePath();
  // Its bounding box intersects the park, but the line itself misses it.
  curve.add(
    new THREE.LineCurve3(
      new THREE.Vector3(-0.2, 0, 0.15),
      new THREE.Vector3(0.15, 0, 0.5),
    ),
  );
  const outside = {
    coordinates: [
      [-0.2, 0.15],
      [0.15, 0.5],
    ],
    width: 0.005,
    curve,
  };
  const d = {
    a: {
      project: { toWorld: (c) => c, toGeo: (x, z) => [x, z] },
      mobile: false,
      season: "summer",
    },
    data: { parks: [park], buildings: [], mappedTrees: [] },
    group: new THREE.Group(),
    walks: [outside],
    paths: [],
    buildingBlocked: footprintMask([], (c) => c),
    point: (c) => new THREE.Vector3(c[0], 0, c[1]),
    ribbon: () => new THREE.PlaneGeometry(0.01, 0.01),
  };
  const scene = new ParkScene(d);
  const created = d.walks.filter((p) => p.decorative);
  assert.ok(created.length > 0);
  assert.ok(scene.treeCount > 0);
  for (const path of created)
    for (const c of path.coordinates)
      assert.ok(inRing(c, park.geometry.coordinates[0]));
  scene.group.traverse((o) => {
    o.geometry?.dispose();
    o.material?.dispose();
  });
});

test("fleet waits behind a leading vehicle and resumes without crossing it", async () => {
  const { roadNetwork, vehicleState, advanceTraffic } =
    await import("../src/traffic.js");
  const n = roadNetwork(
    [
      {
        id: "a",
        properties: { highway: "residential", oneway: "yes" },
        geometry: {
          coordinates: [
            [0, 0],
            [1, 0],
          ],
        },
      },
    ],
    (c) => c,
  );
  const a = vehicleState(n, 0),
    b = vehicleState(n, 1);
  a.distance = 0.3;
  b.distance = 0.28;
  const before = b.distance;
  advanceTraffic([a, b], 1);
  assert.equal(b.distance, before);
  assert.ok(a.distance > 0.3);
  advanceTraffic([a, b], 1);
  assert.ok(b.distance > before);
  assert.ok(a.distance - b.distance >= 0.02);
});

test("bridge walkers share the elevated deck instead of following the water terrain", async () => {
  const { bridgeSurfaces } = await import("../src/bridge-surface.js");
  const THREE = await import("three"),
    { DistrictScene } = await import("../src/district-scene.js");
  const features = [
    {
      id: "moon",
      properties: { bridge: "yes", "bridge:name": "월영교" },
      geometry: {
        coordinates: [
          [0, 0],
          [1, 0],
        ],
      },
    },
    {
      id: "entry",
      properties: { bridge: "yes", name: "Moonlight Bridge" },
      geometry: {
        coordinates: [
          [1, 0],
          [1.1, 0],
        ],
      },
    },
    {
      id: "road",
      properties: { highway: "residential" },
      geometry: {
        coordinates: [
          [0, 0],
          [1, 1],
        ],
      },
    },
  ];
  const surfaces = bridgeSurfaces(features, (c) => (c[0] === 0 ? 0.8 : 1));
  assert.equal(surfaces.has("road"), false);
  assert.ok(Math.abs(surfaces.get("moon")(0.5, 0) - 1.043) < 1e-9);
  assert.equal(surfaces.get("entry")(), surfaces.get("moon")());
  const d = Object.create(DistrictScene.prototype);
  d.dummy = new THREE.Object3D();
  d.a = { project: { toGeo: (x, z) => [x, z] } };
  d.point = () => new THREE.Vector3(0, 0.1, 0);
  const mesh = new THREE.InstancedMesh(
    new THREE.BoxGeometry(1, 1, 1),
    new THREE.MeshBasicMaterial(),
    1,
  );
  d.place(
    mesh,
    0,
    new THREE.Vector3(0.5, 0, 0),
    0.002,
    0,
    0.001,
    surfaces.get("moon"),
  );
  const m = new THREE.Matrix4();
  mesh.getMatrixAt(0, m);
  assert.ok(Math.abs(m.elements[13] - 1.046) < 1e-6);
  mesh.geometry.dispose();
  mesh.material.dispose();
});

test("tree crown clearance protects the whole road corridor, not just its centreline", async () => {
  const { corridorMask } = await import("../src/footprints.js");
  const mask = corridorMask(
    [
      {
        geometry: {
          coordinates: [
            [0, 0],
            [1, 0],
          ],
        },
      },
    ],
    (c) => c,
    () => 0.02,
  );
  assert.equal(mask(0.5, 0.025, 0.02), true);
  assert.equal(mask(0.5, 0.035, 0.02), false);
  assert.equal(mask(1.005, 0, 0.01), true);
  assert.equal(mask(2, 0, 0.01), false);
});

test("road triangles conform to terrain ridges even between the road corner samples", async () => {
  const { drapePolygon } = await import("../src/terrain-ribbon.js");
  const grid = { x: 0, z: 0, dx: 1, dz: 1, cols: 3, rows: 2 };
  const height = (x, z) => (x <= 1 ? 2 * x : 4 - 2 * x);
  const vertices = drapePolygon(
    [
      [0.2, 0.2],
      [1.8, 0.2],
      [1.8, 0.8],
      [0.2, 0.8],
    ],
    grid,
    height,
    0.01,
  );
  let area = 0;
  for (let i = 0; i < vertices.length; i += 9) {
    const a = vertices.slice(i, i + 3),
      b = vertices.slice(i + 3, i + 6),
      c = vertices.slice(i + 6, i + 9);
    area +=
      Math.abs((b[0] - a[0]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[0] - a[0])) /
      2;
    const x = (a[0] + b[0] + c[0]) / 3,
      z = (a[2] + b[2] + c[2]) / 3,
      y = (a[1] + b[1] + c[1]) / 3;
    assert.ok(
      Math.abs(y - height(x, z) - 0.01) < 1e-8,
      "triangle interior stays above the actual terrain",
    );
  }
  assert.ok(
    Math.abs(area - 1.6 * 0.6) < 1e-8,
    "clipping preserves the full road footprint",
  );
});
