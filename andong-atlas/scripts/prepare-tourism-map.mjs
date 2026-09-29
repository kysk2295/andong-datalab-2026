import {readFile,writeFile} from 'node:fs/promises';
import {simplify} from '@turf/simplify';
import {tourismModel} from '../src/tourism-map-model.js';
import {geometryBounds} from '../src/geo.js';
const directory=new URL('../public/data/',import.meta.url);
const read=async name=>JSON.parse(await readFile(new URL(`${name}.json`,directory),'utf8'));
const [journey,research,map]=await Promise.all(['journey','relay-research','map'].map(read));
const model=tourismModel(journey,research.route);
const background=[];
for(const [kind,features] of [['water',map.water],['road',map.transportation]]) {
  for(const feature of features) {
    if(kind==='road' && !['motorway','trunk','primary','secondary','tertiary'].includes(feature.properties.class))continue;
    if(!['Polygon','MultiPolygon','LineString','MultiLineString'].includes(feature.geometry.type))continue;
    const simplified=simplify(feature,{tolerance:.00006,highQuality:true});
    background.push({kind,bbox:geometryBounds(simplified.geometry),geometry:simplified.geometry});
  }
}
const data={...model,background,source:'OpenStreetMap / OpenFreeMap · 기존 수집 지도에서 단순화',sourceUrl:'https://www.openstreetmap.org/copyright',benefitCheckedAt:'2026-09-21'};
const text=JSON.stringify(data);
await writeFile(new URL('tourism-map.json',directory),text);
console.log(`Tourism map: ${model.benefits.length} located + ${model.unlocated.length} unlocated benefits, ${model.stages.length} stages, ${(text.length/1024).toFixed(0)} KB`);
