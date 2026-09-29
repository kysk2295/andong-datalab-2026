import { buildingAppearance } from "./building-style.js";
import * as THREE from "three";
import { polygons } from "./geo.js";
// Assemble all shells in one allocation. Avoid tens of thousands of temporary ExtrudeGeometry objects.
export function buildingGeometry(features, project, elevation) {
  let capacity = 0,
    count = 0;
  for (const f of features)
    for (const rings of polygons(f.geometry)) {
      capacity += rings.reduce((n, r) => n + r.length, 0) * 12;
      count++;
    }
  const positions = new Float32Array(capacity * 3),
    normals = new Float32Array(capacity * 3),
    colors = new Float32Array(capacity * 3),
    lightSeeds = new Float32Array(capacity);
  const color = new THREE.Color();
  let cursor = 0, lightSeed = 0;
  const vertex = (x, y, z, nx, ny, nz) => {
    lightSeeds[cursor] = lightSeed;
    const i = cursor++ * 3;
    positions[i] = x;
    positions[i + 1] = y;
    positions[i + 2] = z;
    normals[i] = nx;
    normals[i + 1] = ny;
    normals[i + 2] = nz;
    colors[i] = color.r;
    colors[i + 1] = color.g;
    colors[i + 2] = color.b;
  };
  for (const f of features)
    for (const source of polygons(f.geometry)) {
      const rings = source.map((r) =>
        r.slice(0, -1).map((c) => {
          const p = project(c);
          const point = new THREE.Vector2(p[0], -p[1]);
          point.ground = elevation(c);
          return point;
        }),
      );
      if (rings[0].length < 3) continue;
      // Orient the outer and inner walls consistently in the shape's x/-z plane.
      if (!THREE.ShapeUtils.isClockWise(rings[0])) rings[0].reverse();
      for (const hole of rings.slice(1))
        if (THREE.ShapeUtils.isClockWise(hole)) hole.reverse();
      const appearance = buildingAppearance(f);
      lightSeed = appearance.lightSeed;
      color.set(appearance.facade);
      const y = Math.max(...rings[0].map((p) => p.ground)) + 0.01,
        h =
          Math.max(3, Math.min(150, Number(f.properties.height) || 6)) * 0.008;
      for (const ring of rings)
        for (let j = 0; j < ring.length; j++) {
          const a = ring[j],
            b = ring[(j + 1) % ring.length],
            dx = b.x - a.x,
            dz = a.y - b.y,
            len = Math.hypot(dx, dz);
          if (!len) continue;
          const nx = dz / len,
            nz = -dx / len;
          for (const p of [
            [a.x, a.ground - 0.002, -a.y],
            [a.x, y + h, -a.y],
            [b.x, b.ground - 0.002, -b.y],
            [b.x, b.ground - 0.002, -b.y],
            [a.x, y + h, -a.y],
            [b.x, y + h, -b.y],
          ])
            vertex(...p, nx, 0, nz);
        }
      color.set(appearance.roof);
      const flat = rings.flat(),
        triangles = THREE.ShapeUtils.triangulateShape(rings[0], rings.slice(1));
      for (const triangle of triangles)
        for (const i of triangle) {
          const p = flat[i];
          vertex(p.x, y + h, -p.y, 0, 1, 0);
        }
    }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute(
    "position",
    new THREE.BufferAttribute(positions.slice(0, cursor * 3), 3),
  );
  geometry.setAttribute(
    "normal",
    new THREE.BufferAttribute(normals.slice(0, cursor * 3), 3),
  );
  geometry.setAttribute(
    "color",
    new THREE.BufferAttribute(colors.slice(0, cursor * 3), 3),
  );
  geometry.setAttribute("facadeSeed", new THREE.BufferAttribute(lightSeeds.slice(0, cursor), 1));
  geometry.computeBoundingSphere();
  return { geometry, count };
}
