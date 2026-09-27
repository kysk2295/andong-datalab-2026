import { polygons, inRing } from "./geo.js";
export function segmentDistance(x, z, a, b) {
  const dx = b[0] - a[0],
    dz = b[1] - a[1];
  const t = Math.max(
    0,
    Math.min(1, ((x - a[0]) * dx + (z - a[1]) * dz) / (dx * dx + dz * dz || 1)),
  );
  return Math.hypot(x - a[0] - t * dx, z - a[1] - t * dz);
}
// Spatial buckets keep park planting and pedestrian clearance affordable.
export function footprintMask(features, project, cellSize = 0.08) {
  const cells = new Map();
  for (const feature of features)
    for (const poly of polygons(feature.geometry)) {
      const rings = poly.map((r) => r.map(project));
      const xs = rings[0].map((c) => c[0]),
        zs = rings[0].map((c) => c[1]);
      const b = [
        Math.min(...xs),
        Math.min(...zs),
        Math.max(...xs),
        Math.max(...zs),
      ];
      const item = { rings, b };
      for (
        let x = Math.floor(b[0] / cellSize);
        x <= Math.floor(b[2] / cellSize);
        x++
      )
        for (
          let z = Math.floor(b[1] / cellSize);
          z <= Math.floor(b[3] / cellSize);
          z++
        ) {
          const key = `${x},${z}`;
          if (!cells.has(key)) cells.set(key, []);
          cells.get(key).push(item);
        }
    }
  return (x, z, margin = 0) => {
    const seen = new Set();
    for (
      let ix = Math.floor((x - margin) / cellSize);
      ix <= Math.floor((x + margin) / cellSize);
      ix++
    )
      for (
        let iz = Math.floor((z - margin) / cellSize);
        iz <= Math.floor((z + margin) / cellSize);
        iz++
      )
        for (const item of cells.get(`${ix},${iz}`) || []) {
          if (seen.has(item)) continue;
          seen.add(item);
          const { b, rings } = item;
          if (
            x < b[0] - margin ||
            x > b[2] + margin ||
            z < b[1] - margin ||
            z > b[3] + margin
          )
            continue;
          if (
            inRing([x, z], rings[0]) &&
            !rings.slice(1).some((r) => inRing([x, z], r))
          )
            return true;
          if (
            margin > 0 &&
            rings.some((r) =>
              r
                .slice(1)
                .some((p, i) => segmentDistance(x, z, r[i], p) < margin),
            )
          )
            return true;
        }
    return false;
  };
}

export function corridorMask(features, project, width, cellSize = 0.1) {
  const cells = new Map();
  for (const f of features) {
    const c = f.geometry.coordinates.map(project),
      half = width(f) / 2;
    for (let i = 1; i < c.length; i++) {
      const a = c[i - 1],
        b = c[i],
        s = { a, b, half };
      for (
        let x = Math.floor((Math.min(a[0], b[0]) - half) / cellSize);
        x <= Math.floor((Math.max(a[0], b[0]) + half) / cellSize);
        x++
      )
        for (
          let z = Math.floor((Math.min(a[1], b[1]) - half) / cellSize);
          z <= Math.floor((Math.max(a[1], b[1]) + half) / cellSize);
          z++
        ) {
          const key = `${x},${z}`;
          if (!cells.has(key)) cells.set(key, []);
          cells.get(key).push(s);
        }
    }
  }
  return (x, z, radius = 0) => {
    const seen = new Set();
    for (
      let ix = Math.floor((x - radius) / cellSize);
      ix <= Math.floor((x + radius) / cellSize);
      ix++
    )
      for (
        let iz = Math.floor((z - radius) / cellSize);
        iz <= Math.floor((z + radius) / cellSize);
        iz++
      )
        for (const s of cells.get(`${ix},${iz}`) || []) {
          if (seen.has(s)) continue;
          seen.add(s);
          if (segmentDistance(x, z, s.a, s.b) < s.half + radius) return true;
        }
    return false;
  };
}
