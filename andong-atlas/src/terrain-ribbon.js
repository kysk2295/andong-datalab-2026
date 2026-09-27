// Clip a ground ribbon to the exact DEM triangles before lifting it. Merely
// sampling the ribbon corners cuts through ridges between terrain cells.
export function terrainGrid(terrain, project) {
  const [x, z] = project.toWorld([terrain.bbox[0], terrain.bbox[3]]);
  const [right, bottom] = project.toWorld([terrain.bbox[2], terrain.bbox[1]]);
  return {
    x,
    z,
    dx: (right - x) / (terrain.cols - 1),
    dz: (bottom - z) / (terrain.rows - 1),
    cols: terrain.cols,
    rows: terrain.rows,
  };
}
const cross = (a, b, p) =>
  (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]);
function clip(poly, triangle) {
  const sign = Math.sign(cross(triangle[0], triangle[1], triangle[2]));
  for (let i = 0; i < 3 && poly.length; i++) {
    const a = triangle[i],
      b = triangle[(i + 1) % 3],
      result = [];
    for (let j = 0; j < poly.length; j++) {
      const p = poly[j],
        q = poly[(j + 1) % poly.length],
        dp = sign * cross(a, b, p),
        dq = sign * cross(a, b, q);
      if (dp >= -1e-11) result.push(p);
      if (dp >= -1e-11 !== dq >= -1e-11) {
        const t = dp / (dp - dq);
        result.push([p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])]);
      }
    }
    poly = result;
  }
  return poly;
}
export function drapePolygon(poly, grid, height, lift) {
  const xs = poly.map((p) => p[0]),
    zs = poly.map((p) => p[1]);
  const minX = Math.max(0, Math.floor((Math.min(...xs) - grid.x) / grid.dx)),
    maxX = Math.min(
      grid.cols - 2,
      Math.floor((Math.max(...xs) - grid.x) / grid.dx),
    );
  const minZ = Math.max(0, Math.floor((Math.min(...zs) - grid.z) / grid.dz)),
    maxZ = Math.min(
      grid.rows - 2,
      Math.floor((Math.max(...zs) - grid.z) / grid.dz),
    );
  const vertices = [];
  for (let i = minX; i <= maxX; i++)
    for (let j = minZ; j <= maxZ; j++) {
      const x = grid.x + i * grid.dx,
        z = grid.z + j * grid.dz,
        a = [x, z],
        b = [x, z + grid.dz],
        c = [x + grid.dx, z + grid.dz],
        d = [x + grid.dx, z];
      for (const triangle of [
        [a, b, d],
        [b, c, d],
      ]) {
        const polygon = clip(poly, triangle);
        for (let k = 1; k < polygon.length - 1; k++) {
          if (Math.abs(cross(polygon[0], polygon[k], polygon[k + 1])) < 1e-12)
            continue;
          for (const p of [polygon[0], polygon[k], polygon[k + 1]])
            vertices.push(p[0], height(...p) + lift, p[1]);
        }
      }
    }
  return vertices;
}
