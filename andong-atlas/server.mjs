import http from 'node:http';
import {createReadStream, statSync} from 'node:fs';
import {resolve, extname, sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {pipeline} from 'node:stream';

const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.woff2':'font/woff2','.gz':'application/gzip'};
const stat=file=>{try{const info=statSync(file);return info.isFile()?info:null;}catch{return null;}};
function acceptsGzip(header='') {
  return header.split(',').some(value=>{
    const [encoding,...options]=value.trim().split(';');
    const quality=options.find(x=>x.trim().startsWith('q='));
    return encoding==='gzip' && (!quality||Number(quality.trim().slice(2))>0);
  });
}
export function createStaticServer(directory=resolve('dist')) {
  const root=resolve(directory);
  return http.createServer((req,res)=>{
    if(!['GET','HEAD'].includes(req.method)){res.writeHead(405,{Allow:'GET, HEAD'});return res.end();}
    let path;try{path=decodeURIComponent(new URL(req.url,'http://localhost').pathname);}catch{res.writeHead(400);return res.end();}
    let file=resolve(root,'.'+(path==='/'?'/index.html':path)),info;
    if(!file.startsWith(root+sep)||!(info=stat(file))){res.writeHead(404);return res.end('Not found');}
    const type=mime[extname(file)]||'application/octet-stream';
    let gzip=false;
    if(/\.(?:html|js|css|json|svg)$/.test(file)) {
      res.setHeader('Vary','Accept-Encoding');
      const compressed=stat(file+'.gz');
      if(compressed&&acceptsGzip(req.headers['accept-encoding'])){file+='.gz';info=compressed;gzip=true;res.setHeader('Content-Encoding','gzip');}
    }
    const tag=`W/"${info.size.toString(16)}-${Math.trunc(info.mtimeMs).toString(16)}-${gzip?'gz':'raw'}"`;
    // Only Vite's fingerprinted bundles are immutable; public assets keep stable names.
    const immutable=/^\/assets\/[^/]+-[\w-]{8}\.(?:js|css|woff2)$/.test(path);
    res.setHeader('Content-Type',type);res.setHeader('X-Content-Type-Options','nosniff');
    res.setHeader('Cache-Control',immutable?'public,max-age=31536000,immutable':'no-cache');
    res.setHeader('ETag',tag);res.setHeader('Last-Modified',info.mtime.toUTCString());
    const matches=req.headers['if-none-match'];
    const unchanged=matches?matches==='*'||matches.split(',').some(x=>x.trim().replace(/^W\//,'')===tag.replace(/^W\//,'')):
      req.headers['if-modified-since']&&Math.floor(info.mtimeMs/1000)*1000<=Date.parse(req.headers['if-modified-since']);
    if(unchanged){res.writeHead(304);return res.end();}
    res.setHeader('Content-Length',info.size);
    if(req.method==='HEAD')return res.end();
    pipeline(createReadStream(file),res,error=>{if(error&&!res.destroyed)res.destroy(error);});
  });
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  createStaticServer().listen(Number(process.env.PORT)||8080,'0.0.0.0');
}
