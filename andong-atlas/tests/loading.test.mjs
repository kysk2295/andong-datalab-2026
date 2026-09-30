import test from 'node:test';
import assert from 'node:assert/strict';
import {gzipSync} from 'node:zlib';
import {loadJSON,withDeadline,waitForArt,loadPool} from '../src/loading.js';

test('a request that never returns headers times out and aborts the underlying request',async()=>{
  let signal;
  await assert.rejects(loadJSON('/missing',{timeoutMs:20,fetcher:(_,options)=>{signal=options.signal;return new Promise(()=>{});}}),/다시 시도/);
  assert.equal(signal.aborted,true);
});
test('a response with a stalled body is bounded by the same deadline',async()=>{
  let signal;
  await assert.rejects(loadJSON('/stalled',{timeoutMs:20,fetcher:async(_,options)=>{signal=options.signal;return new Response(new ReadableStream({start(c){c.enqueue(new TextEncoder().encode('{'));}}));}}),/다시 시도/);
  assert.equal(signal.aborted,true);
});
test('gzip data, browser-decoded gzip and missing/corrupt gzip all resolve correctly',async()=>{
  const value={name:'안동',places:[1,2,3]},json=JSON.stringify(value);
  assert.deepEqual(await loadJSON('/map.json',{compressed:true,fetcher:async()=>new Response(gzipSync(json))}),value);
  assert.deepEqual(await loadJSON('/map.json',{compressed:true,fetcher:async()=>new Response(json,{headers:{'content-encoding':'gzip'}})}),value);
  for(const response of [()=>new Response('',{status:404}),()=>new Response('broken gzip')]) {
    const calls=[];
    const actual=await loadJSON('/map.json',{compressed:true,fetcher:async url=>{calls.push(url);return url.endsWith('.gz')?response():new Response(json);}});
    assert.deepEqual(actual,value);assert.deepEqual(calls,['/map.json.gz','/map.json']);
  }
});
test('cancellation does not launch a fallback request and a later retry can succeed',async()=>{
  const controller=new AbortController();let calls=0;
  const loading=loadJSON('/map.json',{compressed:true,signal:controller.signal,fetcher:()=>{calls++;return new Promise(()=>{});}});
  await new Promise(resolve=>setTimeout(resolve,5));controller.abort();
  await assert.rejects(loading);assert.equal(calls,1);
  assert.deepEqual(await loadJSON('/map.json',{fetcher:async()=>new Response('{"ready":true}')}),{ready:true});
});
test('optional art never blocks entry forever and can finish after entry',async()=>{
  let finish;const art=new Promise(resolve=>{finish=resolve;});
  assert.equal(await waitForArt(art,{timeoutMs:15}),false);
  finish();assert.equal(await waitForArt(art),true);
  assert.equal(await waitForArt(new Promise(()=>{}),{continueEarly:Promise.resolve()}),false);
  assert.equal(await waitForArt(Promise.reject(Error('image unavailable'))),false);
});
test('asset loading limits parallel decodes, reports progress and isolates failures',async()=>{
  let active=0,maximum=0;const progress=[];
  const results=await loadPool([0,1,2,3,4,5],async value=>{
    maximum=Math.max(maximum,++active);await new Promise(resolve=>setTimeout(resolve,5));active--;
    if(value===2)throw Error('unavailable');return value;
  },{concurrency:2,onProgress:(done,total)=>progress.push([done,total])});
  assert.equal(maximum,2);assert.equal(results[2].status,'rejected');assert.equal(results[5].value,5);
  assert.deepEqual(progress.at(-1),[6,6]);
});
test('an already cancelled load never starts work',async()=>{
  const controller=new AbortController();controller.abort();let calls=0;
  await assert.rejects(withDeadline(()=>{calls++;},{signal:controller.signal}));assert.equal(calls,0);
});
