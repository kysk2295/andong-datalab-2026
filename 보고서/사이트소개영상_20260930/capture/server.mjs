// 사이트 소개 영상 촬영 서버: 로컬 andong-atlas(현재 코드)를 띄우고 HTTP로 촬영 명령을 받는다.
import {createServer as httpServer} from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from '../../../andong-atlas/node_modules/vite/dist/node/index.js';
import {chromium} from '/tmp/eodream-capture-tools/node_modules/playwright/index.mjs';
import {recordFrames} from './record.mjs';

const out=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const root=path.resolve(out,'../../andong-atlas');
const vite=await createServer({root,configFile:false,server:{host:'127.0.0.1',port:6286,strictPort:true},plugins:[{
 name:'local-filming-hooks',enforce:'pre',transform(code,id){
  if(id.endsWith('/src/relay-ui.js'))return code.replace("const app=document.createElement('div');",`window.__film={get scene(){return scene},get state(){return state},get busy(){return busy},get journey(){return journey},perform,advanceJourney,moveToStation,popupTaste,next:()=>perform(nextAction(state)),getNext:()=>nextAction(state)};const app=document.createElement('div');`);
  if(id.endsWith('/src/scene.js'))return code.replace('this.data = data;','window.__atlas=this;this.data = data;');
 }
}]});
await vite.listen();
const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--ignore-gpu-blocklist','--use-angle=metal','--autoplay-policy=no-user-gesture-required','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
const context=await browser.newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1});
const page=await context.newPage();
const errors=[];page.on('pageerror',e=>errors.push(e.message));
const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
httpServer(async(req,res)=>{let body='';for await(const chunk of req)body+=chunk;try{
 const fn=new AsyncFunction('page','context','browser','out','fs','errors','recordFrames',body);
 const result=await fn(page,context,browser,out,fs,errors,recordFrames);
 res.setHeader('Content-Type','application/json');res.end(JSON.stringify({ok:true,result}));
 }catch(e){res.statusCode=500;res.end(JSON.stringify({ok:false,error:e.stack}));}
}).listen(6287,'127.0.0.1');
await page.goto('http://127.0.0.1:6286/');
await page.waitForFunction(()=>window.__atlas?.container?.dataset.rendered==='true',{timeout:120000});
console.log(JSON.stringify({ready:true,out,api:'http://127.0.0.1:6287'}));
