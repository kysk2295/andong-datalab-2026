import {readdir,readFile,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {gzipSync} from 'node:zlib';
const root=fileURLToPath(new URL('../dist/',import.meta.url));
let rawBytes=0,gzipBytes=0;
async function walk(directory) {
  for(const entry of await readdir(directory,{withFileTypes:true})) {
    const path=join(directory,entry.name);
    if(entry.isDirectory()){await walk(path);continue;}
    if(!/\.(?:html|js|css|json|svg)$/.test(entry.name))continue;
    const raw=await readFile(path);if(raw.length<1024)continue;
    const zipped=gzipSync(raw,{level:9});if(zipped.length>=raw.length)continue;
    await writeFile(path+'.gz',zipped);rawBytes+=raw.length;gzipBytes+=zipped.length;
  }
}
await walk(root);
console.log(`Static text: ${(rawBytes/1e6).toFixed(2)} MB → ${(gzipBytes/1e6).toFixed(2)} MB`);
