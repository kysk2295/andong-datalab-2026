import fs from "node:fs/promises";
import path from "node:path";
import { VectorTile } from "@mapbox/vector-tile";
import Pbf from "pbf";
import { PNG } from "pngjs";
import simplify from "@turf/simplify";

const root = path.resolve(import.meta.dirname, ".."),
  out = path.join(root, "public/data"),
  cache = path.join(root, ".cache");
await fs.mkdir(out, { recursive: true });
await fs.mkdir(cache, { recursive: true });
async function download(url, key) {
  const file = path.join(cache, key);
  try {
    return await fs.readFile(file);
  } catch {}
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const r = await fetch(url, { signal: AbortSignal.timeout(90000) });
      if (!r.ok) throw Error(`${r.status} ${url}`);
      const b = Buffer.from(await r.arrayBuffer());
      await fs.writeFile(file, b);
      return b;
    } catch (e) {
      if (attempt === 2) throw e;
    }
  }
}
const boundaryURL =
  "https://raw.githubusercontent.com/vuski/admdongkor/master/ver20260701/HangJeongDong_ver20260701.geojson";
const all = JSON.parse(await download(boundaryURL, "boundary.json"));
const boundaries = {
  type: "FeatureCollection",
  features: all.features.filter((f) =>
    JSON.stringify(f.properties).includes("안동시"),
  ),
};
if (boundaries.features.length !== 24)
  throw Error(`Expected 24 districts, got ${boundaries.features.length}`);
let points = [];
function collect(a) {
  if (typeof a[0] === "number") points.push(a);
  else a.forEach(collect);
}
boundaries.features.forEach((f) => collect(f.geometry.coordinates));
const bbox = [
  Math.min(...points.map((p) => p[0])) - 0.012,
  Math.min(...points.map((p) => p[1])) - 0.012,
  Math.max(...points.map((p) => p[0])) + 0.012,
  Math.max(...points.map((p) => p[1])) + 0.012,
];
const rounded = (n) => Math.round(n * 1e6) / 1e6;
await fs.writeFile(
  path.join(out, "boundaries.json"),
  JSON.stringify(
    simplify(boundaries, { tolerance: 0.00015, highQuality: true }),
  ),
);
console.log("Boundary", boundaries.features.length, bbox);
const tileXY = (lon, lat, z) => [
  ((lon + 180) / 360) * 2 ** z,
  ((1 - Math.asinh(Math.tan((lat * Math.PI) / 180)) / Math.PI) / 2) * 2 ** z,
];
function tileList(z) {
  const a = tileXY(bbox[0], bbox[3], z),
    b = tileXY(bbox[2], bbox[1], z),
    list = [];
  for (let x = Math.floor(a[0]); x <= Math.floor(b[0]); x++)
    for (let y = Math.floor(a[1]); y <= Math.floor(b[1]); y++)
      list.push({ x, y, z });
  return list;
}
async function pool(items, fn, n = 8) {
  let next = 0;
  await Promise.all(
    Array.from({ length: n }, async () => {
      while (next < items.length) {
        const i = next++;
        await fn(items[i], i);
      }
    }),
  );
}
const tz = 11,
  images = new Map();
await pool(tileList(tz), async ({ x, y, z }) => {
  const png = PNG.sync.read(
    await download(
      `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/${z}/${x}/${y}.png`,
      `e-${z}-${x}-${y}.png`,
    ),
  );
  images.set(`${x}/${y}`, png);
});
const cols = 321,
  rows = 321,
  heights = [];
for (let j = 0; j < rows; j++)
  for (let i = 0; i < cols; i++) {
    const lon = bbox[0] + (i / (cols - 1)) * (bbox[2] - bbox[0]),
      lat = bbox[3] - (j / (rows - 1)) * (bbox[3] - bbox[1]);
    const [tx, ty] = tileXY(lon, lat, tz),
      png = images.get(`${Math.floor(tx)}/${Math.floor(ty)}`);
    const p =
      (Math.min(255, Math.floor((ty % 1) * 256)) * 256 +
        Math.min(255, Math.floor((tx % 1) * 256))) *
      4;
    heights.push(
      Math.round(
        png.data[p] * 256 + png.data[p + 1] + png.data[p + 2] / 256 - 32768,
      ),
    );
  }
const correctedSamples = [];
for (let j = 0; j < rows; j++)
  for (let i = 0; i < cols; i++) {
    const index = j * cols + i;
    if (heights[index] >= 0) continue;
    const neighbors = [];
    for (let dy = -2; dy <= 2; dy++)
      for (let dx = -2; dx <= 2; dx++) {
        const x = i + dx,
          y = j + dy;
        if (
          x >= 0 &&
          x < cols &&
          y >= 0 &&
          y < rows &&
          heights[y * cols + x] >= 0
        )
          neighbors.push(heights[y * cols + x]);
      }
    neighbors.sort((a, b) => a - b);
    if (!neighbors.length)
      throw Error("Cannot repair negative inland DEM sample");
    correctedSamples.push({
      index,
      original: heights[index],
      replacement: neighbors[Math.floor(neighbors.length / 2)],
    });
    heights[index] = correctedSamples.at(-1).replacement;
  }
await fs.writeFile(
  path.join(out, "terrain.json"),
  JSON.stringify({ bbox, cols, rows, heights, correctedSamples }),
);
const tilemeta = JSON.parse(
  await download("https://tiles.openfreemap.org/planet", "tilejson.json"),
);
const vectors = {
  water: [],
  landcover: [],
  transportation: [],
  building: [],
  poi: [],
};
const z = 14,
  tiles = tileList(z);
console.log("Vector tiles", tiles.length);
await pool(tiles, async ({ x, y, z }, index) => {
  const tile = new VectorTile(
    new Pbf(
      await download(
        tilemeta.tiles[0].replace("{z}", z).replace("{x}", x).replace("{y}", y),
        `v-${z}-${x}-${y}.pbf`,
      ),
    ),
  );
  for (const name of Object.keys(vectors)) {
    const layer = tile.layers[name];
    if (!layer) continue;
    for (let i = 0; i < layer.length; i++) {
      const f = layer.feature(i).toGeoJSON(x, y, z);
      if (name === "poi" && !f.properties.name) continue;
      const p = f.properties;
      f.properties = {
        name: p["name:ko"] || p.name,
        en: p["name:en"],
        class: p.class,
        subclass: p.subclass,
        height: p.render_height || p.height,
        brunnel: p.brunnel,
      };
      if (
        name === "transportation" &&
        ![
          "motorway",
          "trunk",
          "primary",
          "secondary",
          "tertiary",
          "minor",
          "service",
          "path",
          "track",
          "rail",
        ].includes(p.class)
      )
        continue;
      vectors[name].push(f);
    }
  }
  if (index % 40 === 0) console.log("Downloaded", index, "/", tiles.length);
});
for (const key of Object.keys(vectors)) {
  const seen = new Set();
  vectors[key] = vectors[key].filter((f) => {
    const id = f.id
      ? `${f.id}-${JSON.stringify(f.geometry.coordinates[0]).slice(0, 70)}`
      : JSON.stringify(f.geometry);
    if (seen.has(id)) return false;
    seen.add(id);
    return true;
  });
}
await fs.writeFile(
  path.join(out, "map.json"),
  JSON.stringify(vectors, (_, v) => (typeof v === "number" ? rounded(v) : v)),
);
const project = path.resolve(root, "..");
const read = async (p) =>
  JSON.parse(await fs.readFile(path.join(project, p), "utf8"));
const numbers = await read("보고서/교수브리핑_20260922/수치.json");
const simulation = await read("보고서/성과도출_20260922/시뮬레이션결과.json");
await fs.writeFile(
  path.join(out, "analysis.json"),
  JSON.stringify(
    {
      scenarios: simulation["시나리오"],
      survey: numbers["월영교조사"],
      bus: numbers["버스"],
      consumption: numbers["체험문화"],
      rail: numbers["철도공사"],
      benefits: numbers["혜택배치"],
      assumptions: simulation["설문보정"],
    },
    null,
    2,
  ),
);
const manifest = {
  accessed: new Date().toISOString(),
  bbox,
  districtCount: 24,
  counts: Object.fromEntries(
    Object.entries(vectors).map(([k, v]) => [k, v.length]),
  ),
  terrain: { cols, rows, samples: heights.length },
  sources: [
    {
      name: "OpenFreeMap / OpenMapTiles / © OpenStreetMap contributors",
      url: tilemeta.tiles[0],
      license: "ODbL 1.0",
      note: "Public vector snapshot; building heights may be source estimates.",
    },
    {
      name: "AWS Terrain Tiles / Mapzen",
      url: "https://registry.opendata.aws/terrain-tiles/",
      license:
        "https://github.com/tilezen/joerd/blob/master/docs/attribution.md",
    },
    {
      name: "통계청 SGIS · 가공 vuski/admdongkor",
      url: boundaryURL,
      license: "공공누리 제1유형(출처표시)",
      date: "2026-07-01",
    },
    {
      name: "안동 이어드림 팀 분석",
      url: "../../보고서/교수브리핑_20260922/수치.json",
      date: "2026-09-28",
      note: "Existing analysis JSON; individual survey responses excluded.",
    },
  ],
};
await fs.writeFile(
  path.join(out, "manifest.json"),
  JSON.stringify(manifest, null, 2),
);
console.log("READY", manifest.counts);
