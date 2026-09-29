import { readFile, writeFile } from "node:fs/promises";
import { gzipSync } from "node:zlib";
for (const name of ["map", "district", "buildings", "journey"]) {
  const raw = await readFile(
      new URL(`../public/data/${name}.json`, import.meta.url),
    ),
    compressed = gzipSync(raw, { level: 9 });
  await writeFile(
    new URL(`../public/data/${name}.json.gz`, import.meta.url),
    compressed,
  );
  console.log(
    `${name}: ${(raw.length / 1e6).toFixed(2)} MB → ${(compressed.length / 1e6).toFixed(2)} MB`,
  );
}
