// Shared by walking and assisted approaches, so both respect the same furniture.
export function canStand(x,z,{bounds,obstacles=[]},radius=.2){
 return x>=bounds.x[0]&&x<=bounds.x[1]&&z>=bounds.z[0]&&z<=bounds.z[1]&&!obstacles.some(o=>Math.abs(x-o.x)<o.w/2+radius&&Math.abs(z-o.z)<o.d/2+radius);
}
export function clearWalk(a,b,layout){
 const n=Math.max(1,Math.ceil(Math.hypot(b[0]-a[0],b[1]-a[1])/.08));
 for(let i=0;i<=n;i++)if(!canStand(a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n,layout))return false;
 return true;
}
export function planWalk(start,end,layout){
 if(!canStand(...start,layout)||!canStand(...end,layout))return null;
 if(clearWalk(start,end,layout))return [start,end];
 const cell=.35,[minX,maxX]=layout.bounds.x,[minZ,maxZ]=layout.bounds.z;
 const width=Math.ceil((maxX-minX)/cell)+1,height=Math.ceil((maxZ-minZ)/cell)+1;
 const point=i=>[minX+(i%width)*cell,minZ+Math.floor(i/width)*cell];
 const heuristic=i=>Math.hypot(point(i)[0]-end[0],point(i)[1]-end[1]);
 const open=[],cost=new Map(),previous=new Map();
 for(let i=0;i<width*height;i++){const p=point(i);if(Math.hypot(p[0]-start[0],p[1]-start[1])<cell*1.6&&clearWalk(start,p,layout)){cost.set(i,Math.hypot(p[0]-start[0],p[1]-start[1]));open.push(i);}}
 const closed=new Set();let found=null;
 while(open.length){
  open.sort((a,b)=>cost.get(a)+heuristic(a)-cost.get(b)-heuristic(b));const id=open.shift();if(closed.has(id))continue;closed.add(id);const p=point(id);
  if(heuristic(id)<cell*1.6&&clearWalk(p,end,layout)){found=id;break;}
  for(const [dx,dz] of [[1,0],[-1,0],[0,1],[0,-1],[1,1],[-1,1],[1,-1],[-1,-1]]){
   const x=id%width+dx,z=Math.floor(id/width)+dz;if(x<0||x>=width||z<0||z>=height)continue;const next=z*width+x;
   if(closed.has(next)||!clearWalk(p,point(next),layout))continue;const c=cost.get(id)+Math.hypot(dx,dz)*cell;
   if(c<(cost.get(next)??Infinity)){cost.set(next,c);previous.set(next,id);open.push(next);}
  }
 }
 if(found===null)return null;
 const route=[end];for(let i=found;i!==undefined;i=previous.get(i))route.unshift(point(i));route.unshift(start);
 const smooth=[start];let from=0;while(from<route.length-1){let to=route.length-1;while(to>from+1&&!clearWalk(route[from],route[to],layout))to--;smooth.push(route[to]);from=to;}return smooth;
}
