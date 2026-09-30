import test from 'node:test';
import assert from 'node:assert/strict';
import {Texture} from 'three';
import {replaceTextureImage} from '../src/progressive-texture.js';

test('late high-resolution images replace placeholder GPU storage and update every live clone',()=>{
  const original=new Texture({width:32,height:32}),oldSource=original.source;
  const first=original.clone(),second=original.clone(),clients=new Set([first,second]);
  first.repeat.set(3,4);second.offset.set(.3,.2);let releases=0;
  for(const texture of [original,first,second])texture.addEventListener('dispose',()=>{releases++;clients.delete(texture);});
  const image={width:2048,height:2048},version=first.version;
  replaceTextureImage(original,clients,image);
  assert.equal(releases,3);assert.notEqual(original.source,oldSource);
  assert.equal(first.source,original.source);assert.equal(second.source,original.source);
  assert.equal(first.image,image);assert.ok(first.version>version);assert.equal(clients.size,2);
  assert.deepEqual(first.repeat.toArray(),[3,4]);assert.deepEqual(second.offset.toArray(),[.3,.2]);
  first.dispose();assert.equal(clients.size,1);
  const next={width:1024,height:1024};replaceTextureImage(original,clients,next);
  assert.equal(second.image,next);assert.equal(first.image,image);
});
