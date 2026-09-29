export function projection(bbox) {
  const lat = (bbox[1] + bbox[3]) / 2,
    kmX = 111.32 * Math.cos((lat * Math.PI) / 180),
    scale = 2;
  const width = (bbox[2] - bbox[0]) * kmX * scale,
    depth = (bbox[3] - bbox[1]) * 111.32 * scale;
  return {
    width,
    depth,
    scale,
    toWorld: ([lon, lat]) => [
      (lon - (bbox[0] + bbox[2]) / 2) * kmX * scale,
      ((bbox[1] + bbox[3]) / 2 - lat) * 111.32 * scale,
    ],
    toGeo: (x, z) => [
      (bbox[0] + bbox[2]) / 2 + x / kmX / scale,
      (bbox[1] + bbox[3]) / 2 - z / 111.32 / scale,
    ],
  };
}
export function sampleHeight(terrain, lon, lat) {
  const { bbox, cols, rows, heights } = terrain;
  const x = Math.max(
      0,
      Math.min(cols - 1, ((lon - bbox[0]) / (bbox[2] - bbox[0])) * (cols - 1)),
    ),
    y = Math.max(
      0,
      Math.min(rows - 1, ((bbox[3] - lat) / (bbox[3] - bbox[1])) * (rows - 1)),
    );
  const i = Math.floor(x),
    j = Math.floor(y),
    i1 = Math.min(i + 1, cols - 1),
    j1 = Math.min(j + 1, rows - 1),
    fx = x - i,
    fy = y - j;
  const a = heights[j * cols + i],
    b = heights[j1 * cols + i],
    c = heights[j1 * cols + i1],
    d = heights[j * cols + i1];
  // Match PlaneGeometry's a-b-d / b-c-d triangles, including the diagonal.
  return fx + fy <= 1
    ? a + fx * (d - a) + fy * (b - a)
    : c + (1 - fx) * (b - c) + (1 - fy) * (d - c);
}
export const polygons = (g) =>
  g.type === "Polygon"
    ? [g.coordinates]
    : g.type === "MultiPolygon"
      ? g.coordinates
      : [];
export const lines = (g) =>
  g.type === "LineString"
    ? [g.coordinates]
    : g.type === "MultiLineString"
      ? g.coordinates
      : [];
export function geometryBounds(g) {
  const points = [];
  function walk(a) {
    if (typeof a[0] === "number") points.push(a);
    else a.forEach(walk);
  }
  walk(g.coordinates);
  return [
    Math.min(...points.map((p) => p[0])),
    Math.min(...points.map((p) => p[1])),
    Math.max(...points.map((p) => p[0])),
    Math.max(...points.map((p) => p[1])),
  ];
}
export function timeLabel(minutes) {
  return `${String(Math.floor(minutes / 60)).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}`;
}
export function closingState(item, minutes) {
  if (item["상태"] === "폐업") return "폐업";
  const match = /^(\d{1,2}):(\d{2})$/.exec(item["영업종료"] || "");
  if (!match) return "확인 필요";
  const close = Number(match[1]) * 60 + Number(match[2]);
  return minutes >= close ? "조사 기준 종료" : "종료 전 · 개점 미확인";
}
export function remainingDepartures(times, minutes) {
  return times.filter((t) => {
    const [h, m] = t.split(":").map(Number);
    return h * 60 + m >= minutes;
  });
}
export function inRing(point, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const a = ring[i],
      b = ring[j];
    if (
      a[1] > point[1] !== b[1] > point[1] &&
      point[0] < ((b[0] - a[0]) * (point[1] - a[1])) / (b[1] - a[1]) + a[0]
    )
      inside = !inside;
  }
  return inside;
}

export function routeDistance(geometry) {
  let meters = 0;
  for (const line of lines(geometry))
    for (let i = 1; i < line.length; i++) {
      const [a, b] = [line[i - 1], line[i]],
        rad = Math.PI / 180;
      const v =
        Math.sin(((b[1] - a[1]) * rad) / 2) ** 2 +
        Math.cos(a[1] * rad) *
          Math.cos(b[1] * rad) *
          Math.sin(((b[0] - a[0]) * rad) / 2) ** 2;
      meters += 6371008.8 * 2 * Math.asin(Math.sqrt(Math.min(1, v)));
    }
  return meters;
}

// Raise the eye enough to keep the sightline above intervening terrain.
export function terrainSafeEye(target, eye, heightAt, {clearance=.012,rise=.09}={}) {
  let y = eye.y;
  for (let i = 1; i <= 16; i++) {
    const t = i / 16,
      x = target.x + (eye.x - target.x) * t,
      z = target.z + (eye.z - target.z) * t;
    const ground = heightAt(x, z);
    if (Number.isFinite(ground))
      y = Math.max(y, target.y + (ground + clearance + rise * t - target.y) / t);
  }
  return y;
}
