import * as THREE from "three";
import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js";
import { polygons, inRing } from "./geo.js";
import { Vegetation } from "./vegetation.js";
import { clearRuns } from "./activity.js";
const inside = (p, rings) =>
  inRing(p, rings[0]) && !rings.slice(1).some((r) => inRing(p, r));
const bounds = (r) => [
  Math.min(...r.map((p) => p[0])),
  Math.min(...r.map((p) => p[1])),
  Math.max(...r.map((p) => p[0])),
  Math.max(...r.map((p) => p[1])),
];
const overlap = (a, b) =>
  a[0] <= b[2] && a[2] >= b[0] && a[1] <= b[3] && a[3] >= b[1];
function segmentDistance(x, z, a, b) {
  const dx = b.x - a.x,
    dz = b.z - a.z,
    t = Math.max(
      0,
      Math.min(1, ((x - a.x) * dx + (z - a.z) * dz) / (dx * dx + dz * dz || 1)),
    );
  return Math.hypot(x - a.x - t * dx, z - a.z - t * dz);
}
export class ParkScene {
  constructor(d) {
    this.d = d;
    this.group = new THREE.Group();
    d.group.add(this.group);
    const trees = [],
      wood = [],
      metal = [],
      flowers = [],
      white = [],
      paving = [],
      borders = [],
      project = (c) => d.a.project.toWorld(c);
    let seed = 231;
    const rand = () => {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      return seed / 4294967296;
    };
    const box = (array, w, h, dep, x, y, z, angle = 0) => {
      const g = new THREE.BoxGeometry(w, h, dep);
      g.rotateY(angle);
      g.translate(x, y, z);
      array.push(g);
    };
    for (const feature of d.data.parks || [])
      for (const poly of polygons(feature.geometry)) {
        const rings = poly.map((r) => r.map(project)),
          b = bounds(rings[0]);
        const paths = [...d.walks, ...d.paths].filter((p) =>
          overlap(bounds(p.coordinates.map(project)), b),
        );
        const clear = (x, z, margin = 0.007) =>
          !d.buildingBlocked(x, z, margin);
        // Where OSM has no interior paths, use a clearly disclosed miniature
        // landscape layout clipped to the real park boundary and building mask.
        if (
          feature.properties.leisure === "park" &&
          !paths.some(
            (p) =>
              d.walks.includes(p) &&
              p.curve
                .getSpacedPoints(Math.ceil(p.curve.getLength() / 0.02))
                .some((v) => inside([v.x, v.z], rings)),
          )
        ) {
          const cx = (b[0] + b[2]) / 2,
            cz = (b[1] + b[3]) / 2;
          const layouts = [
            rings[0].map((p) => [
              cx + (p[0] - cx) * 0.7,
              cz + (p[1] - cz) * 0.7,
            ]),
            [
              [b[0], cz],
              [b[2], cz],
            ],
            [
              [cx, b[1]],
              [cx, b[3]],
            ],
          ];
          for (const layout of layouts) {
            const samples = [];
            for (let j = 1; j < layout.length; j++) {
              const a = layout[j - 1],
                b = layout[j],
                n = Math.max(
                  1,
                  Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / 0.003),
                );
              for (let k = 0; k < n; k++)
                samples.push(
                  new THREE.Vector3(
                    a[0] + ((b[0] - a[0]) * k) / n,
                    0,
                    a[1] + ((b[1] - a[1]) * k) / n,
                  ),
                );
            }
            samples.push(
              new THREE.Vector3(layout.at(-1)[0], 0, layout.at(-1)[1]),
            );
            const runs = clearRuns(
              samples,
              (x, z) => !inside([x, z], rings) || !clear(x, z, 0.007),
            );
            for (const run of runs) {
              const coordinates = run.map((p) => d.a.project.toGeo(p.x, p.z));
              const curve = new THREE.CurvePath();
              for (let k = 1; k < run.length; k++)
                curve.add(new THREE.LineCurve3(run[k - 1], run[k]));
              if (curve.getLength() < 0.025) continue;
              const path = {
                coordinates,
                curve,
                width: 0.005,
                decorative: true,
              };
              d.walks.push(path);
              paths.push(path);
              borders.push(d.ribbon(coordinates, 0.0065, 0.0008));
              paving.push(d.ribbon(coordinates, 0.005, 0.0012));
            }
          }
        }
        const roadSegments = paths.flatMap((p) =>
          p.coordinates.slice(1).map((c, i) => {
            const a = project(p.coordinates[i]),
              b = project(c);
            return {
              a: { x: a[0], z: a[1] },
              b: { x: b[0], z: b[1] },
              width: p.width / 2 + 0.009,
            };
          }),
        );
        const onRoad = (x, z) =>
          roadSegments.some((s) => segmentDistance(x, z, s.a, s.b) < s.width);
        if (feature.properties.leisure === "pitch") {
          // Follow the actual pitch boundary; no invented official court dimensions.
          white.push(d.ribbon(poly[0], 0.001, 0.0012));
          continue;
        }
        const step = d.a.mobile ? 0.035 : 0.027;
        let count = 0;
        for (let x = b[0] + step / 2; x < b[2] && count < 220; x += step)
          for (let z = b[1] + step / 2; z < b[3] && count < 220; z += step) {
            const px = x + (rand() - 0.5) * step * 0.55,
              pz = z + (rand() - 0.5) * step * 0.55;
            if (
              !inside([px, pz], rings) ||
              !clear(px, pz) ||
              onRoad(px, pz) ||
              rand() < 0.35
            )
              continue;
            const v = d.point(d.a.project.toGeo(px, pz));
            trees.push({
              x: px,
              y: v.y,
              z: pz,
              size: 0.007 + rand() * 0.007,
              tint: rand(),
            });
            count++;
          }
        for (const path of paths.filter((p) => d.walks.includes(p))) {
          for (const t of [0.2, 0.55, 0.85]) {
            const v = path.curve.getPointAt(t),
              dir = path.curve.getTangentAt(t),
              angle = Math.atan2(dir.x, dir.z);
            v.x -= dir.z * (path.width / 2 + 0.006);
            v.z += dir.x * (path.width / 2 + 0.006);
            if (!inside([v.x, v.z], rings) || !clear(v.x, v.z)) continue;
            v.y = d.point(d.a.project.toGeo(v.x, v.z)).y;
            box(wood, 0.006, 0.002, 0.003, v.x, v.y + 0.005, v.z, angle);
            box(
              wood,
              0.006,
              0.006,
              0.001,
              v.x + dir.z * 0.002,
              v.y + 0.008,
              v.z - dir.x * 0.002,
              angle,
            );
            box(metal, 0.004, 0.005, 0.002, v.x, v.y + 0.0025, v.z, angle);
            // Small planted borders beside the path, clear of the public walkway.
            for (let i = 0; i < 3; i++) {
              const x = v.x - dir.x * (0.016 + i * 0.003),
                z = v.z - dir.z * (0.016 + i * 0.003);
              if (inside([x, z], rings) && clear(x, z))
                box(
                  flowers,
                  0.003,
                  0.002,
                  0.003,
                  x,
                  d.point(d.a.project.toGeo(x, z)).y + 0.002,
                  z,
                );
            }
          }
        }
      }
    for (const f of d.data.mappedTrees || []) {
      const p = d.point(f.coordinates);
      trees.push({ x: p.x, y: p.y, z: p.z, size: 0.01, tint: rand() });
    }
    this.vegetation = new Vegetation(this.group, trees);
    this.treeCount = trees.length;
    const merge = (parts, color) => {
      if (!parts.length) return;
      const g = mergeGeometries(parts),
        m = new THREE.Mesh(
          g,
          new THREE.MeshStandardMaterial({
            color,
            roughness: 0.9,
            side: THREE.DoubleSide,
          }),
        );
      m.castShadow = true;
      m.receiveShadow = true;
      this.group.add(m);
      parts.forEach((p) => p.dispose());
    };
    merge(borders, "#b6b197");
    merge(paving, "#e2d7bd");
    merge(wood, "#997b52");
    merge(metal, "#50665e");
    merge(flowers, "#d29382");
    merge(white, "#f4eee0");
  }
  update() {
    this.vegetation.setSeason(this.d.a.season);
  }
}
