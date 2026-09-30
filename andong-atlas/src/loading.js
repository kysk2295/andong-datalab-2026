// A deadline covers the response body/decode too, not just the response headers.
export async function withDeadline(task, {timeoutMs=20000, signal}={}) {
  const controller=new AbortController();
  let timer, rejectAbort;
  const aborted=new Promise((_,reject)=>{rejectAbort=reject;});
  const abort=reason=>{controller.abort(reason);rejectAbort(reason);};
  const onAbort=()=>abort(signal.reason || new DOMException('Aborted','AbortError'));
  if(signal?.aborted)onAbort();
  else signal?.addEventListener('abort',onAbort,{once:true});
  timer=setTimeout(()=>abort(new Error('자료를 불러오는 시간이 길어졌습니다. 다시 시도해 주세요.')),timeoutMs);
  try {
    return await Promise.race([aborted,Promise.resolve().then(()=>{
      controller.signal.throwIfAborted();
      return task(controller.signal);
    })]);
  } finally {
    clearTimeout(timer);signal?.removeEventListener('abort',onAbort);
  }
}

export function loadJSON(url, {compressed=false, timeoutMs=25000, signal, fetcher=fetch}={}) {
  return withDeadline(async requestSignal=>{
    async function read(gzip) {
      const response=await fetcher(url+(gzip?'.gz':''),{signal:requestSignal});
      if(!response.ok)throw new Error(`자료 응답 ${response.status}`);
      if(gzip && !response.headers.get('content-encoding')?.includes('gzip')) {
        return new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).json();
      }
      return response.json();
    }
    if(compressed && typeof DecompressionStream!=='undefined') {
      try {return await read(true);}
      catch(error) {if(requestSignal.aborted)throw error;}
    }
    return read(false);
  },{timeoutMs,signal});
}

// Optional art can keep arriving after the visitor starts moving.
export async function waitForArt(work, {timeoutMs=8000, continueEarly}={}) {
  let timer;
  try {
    return await Promise.race([
      Promise.resolve(work).then(()=>true,()=>false),
      new Promise(resolve=>{timer=setTimeout(()=>resolve(false),timeoutMs);}),
      ...(continueEarly?[continueEarly.then(()=>false)]:[]),
    ]);
  } finally {clearTimeout(timer);}
}

export async function loadPool(items, load, {concurrency=4,onProgress=()=>{}}={}) {
  const results=new Array(items.length);let next=0,done=0;
  await Promise.all(Array.from({length:Math.min(concurrency,items.length)},async()=>{
    while(next<items.length) {
      const index=next++;
      try {results[index]={status:'fulfilled',value:await load(items[index])};}
      catch(reason) {results[index]={status:'rejected',reason};}
      onProgress(++done,items.length);
    }
  }));
  return results;
}

export const yieldToPage=()=>new Promise(resolve=>setTimeout(resolve,0));
