import fs from "node:fs/promises";
import { PNG } from "pngjs";
const dir = new URL("../public/data/", import.meta.url),
  d = JSON.parse(await fs.readFile(new URL("district.json", dir))),
  b = d.bbox,
  z = 13;
const tile = (lon, lat) => [
  ((lon + 180) / 360) * 2 ** z,
  ((1 - Math.asinh(Math.tan((lat * Math.PI) / 180)) / Math.PI) / 2) * 2 ** z,
];
const a = tile(b[0], b[3]),
  v = tile(b[2], b[1]),
  images = new Map();
for (let x = Math.floor(a[0]); x <= Math.floor(v[0]); x++)
  for (let y = Math.floor(a[1]); y <= Math.floor(v[1]); y++) {
    const path = new URL(
      `../.cache/detail/e-${z}-${x}-${y}.png`,
      import.meta.url,
    );
    let raw;
    try {
      raw = await fs.readFile(path);
    } catch {
      const r = await fetch(
        `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/${z}/${x}/${y}.png`,
      );
      if (!r.ok) throw Error(r.status);
      raw = Buffer.from(await r.arrayBuffer());
      await fs.writeFile(path, raw);
    }
    images.set(`${x}/${y}`, PNG.sync.read(raw));
  }
const cols = 321,
  rows = 201,
  heights = [];
for (let j = 0; j < rows; j++)
  for (let i = 0; i < cols; i++) {
    const [tx, ty] = tile(
        b[0] + (i / (cols - 1)) * (b[2] - b[0]),
        b[3] - (j / (rows - 1)) * (b[3] - b[1]),
      ),
      im = images.get(`${Math.floor(tx)}/${Math.floor(ty)}`),
      idx = (Math.floor((ty % 1) * 256) * 256 + Math.floor((tx % 1) * 256)) * 4;
    heights.push(
      Math.max(
        0,
        Math.round(
          im.data[idx] * 256 +
            im.data[idx + 1] +
            im.data[idx + 2] / 256 -
            32768,
        ),
      ),
    );
  }
d.terrain = {
  bbox: b,
  cols,
  rows,
  heights,
  source: "AWS Terrarium z13 · native elevation, sampled onto local grid",
};
await fs.writeFile(new URL("district.json", dir), JSON.stringify(d));
console.log("local elevation samples", heights.length);
