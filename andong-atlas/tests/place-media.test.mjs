import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {placeLinks,photosFor,photoDate} from '../src/place-media-model.js';
const media=JSON.parse(fs.readFileSync(new URL('../public/data/place-media.json',import.meta.url)));
const catalog=JSON.parse(fs.readFileSync(new URL('../public/data/journey.json',import.meta.url))).places;
test('public photographs retain attribution, source, license and truthful date',()=>{
 for(const photo of Object.values(media.photos)) {
  assert.ok(photo.src.startsWith('https://'));assert.ok(photo.sourceUrl.startsWith('https://'));
  assert.ok(photo.credit && photo.license && photo.licenseUrl);
  assert.equal(photo.view,'photo');
  if(!photo.capturedAt)assert.match(photoDate(photo),/촬영일 미확인/);
 }
 assert.equal(media.reviews.length,0);
});
test('photo associations are catalogue identities and do not give proposed venues real photographs',()=>{
 for(const [id,record] of Object.entries(media.records)) {
  const place=catalog.find(p=>p.id===id);assert.ok(place);
  for(const photo of record.photos)assert.ok(media.photos[photo]);
  assert.ok(!place.proposed);
 }
 assert.equal(photosFor({id:'bridge',proposed:true},media).length,0);
 assert.equal(photosFor({id:'unknown'},media).length,0);
});
test('Roadview links use latitude before longitude and correctly escape place names',()=>{
 const links=placeLinks({name:'식당 A&B',coordinates:[128.758961,36.577268]});
 assert.equal(links.roadview,'https://map.kakao.com/link/roadview/36.577268,128.758961');
 assert.ok(links.reviews.includes('A%26B'));
 assert.equal(placeLinks({name:'제안',coordinates:[128,36],proposed:true}).reviews,null);
 assert.equal(placeLinks({name:'오류',coordinates:[Infinity,36]}),null);
});
