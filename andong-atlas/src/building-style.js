import * as THREE from "three";
export const facades = [
  "#d3c4aa",
  "#b7c8ca",
  "#d4bda5",
  "#b6bda5",
  "#c8b0a5",
  "#d7d7c7",
  "#a7bfc0",
  "#b6a38d",
];
export const roofs = [
  "#567e77",
  "#637d94",
  "#a46f58",
  "#969884",
  "#718473",
  "#b09a78",
  "#596a73",
  "#8a6e62",
];
export function buildingAppearance(feature) {
  let hash = 2166136261;
  const key = String(
    feature.id || JSON.stringify(feature.geometry.coordinates[0][0]),
  );
  for (const c of key) hash = Math.imul(hash ^ c.charCodeAt(0), 16777619) >>> 0;
  const p = feature.properties || {},
    hex = /^#[0-9a-f]{6}$/i;
  return {
    index: hash % facades.length,
    facade: hex.test(p["building:colour"])
      ? p["building:colour"]
      : facades[hash % facades.length],
    roof: hex.test(p["roof:colour"])
      ? p["roof:colour"]
      : roofs[(hash >>> 4) % roofs.length],
  };
}
export function paintGeometry(geometry, color) {
  const c = new THREE.Color(color),
    colors = new Float32Array(geometry.attributes.position.count * 3);
  for (let i = 0; i < colors.length; i += 3) {
    colors[i] = c.r;
    colors[i + 1] = c.g;
    colors[i + 2] = c.b;
  }
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  return geometry;
}
// Extend walls down to terrain at each edge sample, including courtyard edges.
export function terrainSkirt(rings, point, top) {
  const vertices = [];
  for (const ring of rings)
    for (let i = 1; i < ring.length; i++) {
      const a = point(ring[i - 1]),
        b = point(ring[i]),
        n = Math.max(1, Math.ceil(Math.hypot(b.x - a.x, b.z - a.z) / 0.015));
      for (let j = 0; j < n; j++) {
        const c = ring[i - 1].map((v, k) => v + ((ring[i][k] - v) * j) / n),
          d = ring[i - 1].map((v, k) => v + ((ring[i][k] - v) * (j + 1)) / n),
          p = point(c),
          q = point(d);
        vertices.push(
          p.x,
          top,
          p.z,
          p.x,
          Math.min(top, p.y - 0.001),
          p.z,
          q.x,
          top,
          q.z,
          q.x,
          top,
          q.z,
          p.x,
          Math.min(top, p.y - 0.001),
          p.z,
          q.x,
          Math.min(top, q.y - 0.001),
          q.z,
        );
      }
    }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  g.computeVertexNormals();
  return g;
}
