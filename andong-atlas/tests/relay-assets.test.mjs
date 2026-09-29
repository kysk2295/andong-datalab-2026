import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const photos=JSON.parse(readFileSync(new URL('../public/data/relay-media.json',import.meta.url)));
const research=JSON.parse(readFileSync(new URL('../public/data/relay-research.json',import.meta.url)));
test('cached reference photos preserve attribution, original bytes and honest unavailable states',()=>{
 const available=photos.filter(p=>p.local);assert.ok(available.length>=6);
 for(const p of photos){assert.match(p.sourceUrl,/^https?:\/\//);assert.ok(p.credit&&p.license&&p.licenseUrl);if(!p.local){assert.ok(p.downloadError);continue;}const bytes=readFileSync(new URL('../public'+p.local,import.meta.url));assert.equal(bytes.length,p.bytes);assert.equal(createHash('sha256').update(bytes).digest('hex'),p.sha256);assert.equal(bytes[0],255);assert.equal(bytes[1],216);}
});
test('every chapter reference resolves and geographic route stays in Andong',()=>{
 const ids=new Set(research.sources.map(s=>s.id));for(const group of Object.values(research.chapters))for(const id of group)assert.ok(ids.has(id),id);
 assert.ok(research.unknowns.length>=8);assert.ok(research.route.coordinates.length>20);
 for(const [lng,lat] of research.route.coordinates){assert.ok(lng>128.7&&lng<128.8);assert.ok(lat>36.5&&lat<36.7);}
});
test('downloaded PBR materials and lighting have a license and match recorded bytes',()=>{
 const assets=JSON.parse(readFileSync(new URL('../public/data/relay-materials.json',import.meta.url)));
 assert.ok(assets.length>=19);
 for(const asset of assets){assert.equal(asset.license,'CC0-1.0');assert.match(asset.source,/^https:\/\/polyhaven.com\/a\//);const bytes=readFileSync(new URL('../public'+asset.file,import.meta.url));assert.equal(bytes.length,asset.bytes);assert.equal(createHash('sha256').update(bytes).digest('hex'),asset.sha256);}
 for(const id of ['wood_floor','clay_plaster','cobblestone_floor_02','wood_table','brick_wall_001','fabric_pattern_05'])assert.deepEqual(assets.filter(a=>a.asset===id).map(a=>a.kind).sort(),['diffuse','nor_gl','rough']);
});

test('document references and scanned props are local, intact and retain provenance',()=>{
 const refs=JSON.parse(readFileSync(new URL('../public/data/relay-document-photos.json',import.meta.url)));
 assert.equal(refs.length,114);assert.equal(new Set(refs.map(p=>p.id)).size,114);
 for(const p of refs){const bytes=readFileSync(new URL('../public'+p.file,import.meta.url));assert.equal(createHash('sha256').update(bytes).digest('hex'),p.sha256);assert.ok(readFileSync(new URL('../public'+p.thumbnail,import.meta.url)).length);assert.ok(p.sourceUrl&&p.credit&&p.license);}
 assert.ok(refs.filter(p=>p.stage===2).every(p=>p.kind==='구성 예시'));
 const models=JSON.parse(readFileSync(new URL('../public/data/relay-model-assets.json',import.meta.url)));
 for(const m of models){assert.equal(m.license,'CC0-1.0');for(const f of m.files){const bytes=readFileSync(new URL('../public'+f.file,import.meta.url));assert.equal(createHash('sha256').update(bytes).digest('hex'),f.sha256);}}
});
