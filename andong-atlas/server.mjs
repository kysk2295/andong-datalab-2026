import http from 'node:http';
import {createReadStream, existsSync, statSync} from 'node:fs';
import {resolve, extname, sep} from 'node:path';
const root=resolve('dist');
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.gz':'application/gzip'};
http.createServer((req,res)=>{
 if(!['GET','HEAD'].includes(req.method)){res.writeHead(405);return res.end();}
 let path;try{path=decodeURIComponent(new URL(req.url,'http://localhost').pathname);}catch{res.writeHead(400);return res.end();}
 const file=resolve(root,'.'+(path==='/'?'/index.html':path));
 if(!file.startsWith(root+sep)||!existsSync(file)||!statSync(file).isFile()){res.writeHead(404);return res.end('Not found');}
 res.setHeader('Content-Type',mime[extname(file)]||'application/octet-stream');
 res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Cache-Control',path.startsWith('/assets/')?'public,max-age=31536000,immutable':'no-cache');
 res.setHeader('Content-Length',statSync(file).size);
 if(req.method==='HEAD')return res.end();createReadStream(file).pipe(res);
}).listen(Number(process.env.PORT)||8080,'0.0.0.0');
