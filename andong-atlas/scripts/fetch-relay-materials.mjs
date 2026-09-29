import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {dirname} from 'node:path';
const assets=JSON.parse(await readFile(new URL('../public/data/relay-materials.json',import.meta.url),'utf8'));
for(const asset of assets){
 const path=fileURLToPath(new URL('../public'+asset.file,import.meta.url));
 try{const existing=await readFile(path);if(createHash('sha256').update(existing).digest('hex')===asset.sha256){console.log('cached',asset.file);continue;}}catch{}
 const response=await fetch(asset.download,{signal:AbortSignal.timeout(45000)});if(!response.ok)throw new Error(asset.download+': '+response.status);
 const bytes=Buffer.from(await response.arrayBuffer());if(createHash('sha256').update(bytes).digest('hex')!==asset.sha256)throw new Error('Source changed; review before updating '+asset.file);
 await mkdir(dirname(path),{recursive:true});await writeFile(path,bytes);console.log('downloaded',asset.file);
}
