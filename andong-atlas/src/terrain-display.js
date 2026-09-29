import { inRing, polygons, sampleHeight } from './geo.js';

// Interpolation weights of the same triangles used by sampleHeight/PlaneGeometry.
function weightsAt(t, [lon, lat]) {
  const {bbox:b, cols, rows}=t;
  const x=Math.max(0,Math.min(cols-1-1e-9,(lon-b[0])/(b[2]-b[0])*(cols-1)));
  const y=Math.max(0,Math.min(rows-1-1e-9,(b[3]-lat)/(b[3]-b[1])*(rows-1)));
  const i=Math.floor(x),j=Math.floor(y),fx=x-i,fy=y-j;
  return fx+fy<=1
    ? [[j*cols+i,1-fx-fy],[(j+1)*cols+i,fy],[j*cols+i+1,fx]]
    : [[(j+1)*cols+i+1,fx+fy-1],[(j+1)*cols+i,1-fx],[j*cols+i+1,1-fy]];
}

// Nearby terraces share DEM vertices. Balance their actual interpolated contact
// points together instead of letting independently blended pads tilt each other.
// This is a bounded display correction, never a change to the downloaded DEM.
export function balanceFootings(terrain, buildings) {
  const {bbox:b,cols,rows}=terrain,dx=(b[2]-b[0])/(cols-1),dy=(b[3]-b[1])/(rows-1);
  const original=terrain.heights,heights=[...original],groups=[];
  for(const f of [...buildings].sort((a,b)=>String(a.id).localeCompare(String(b.id)))) {
    if(f.properties.visualRoof!=='traditional')continue;
    for(const poly of polygons(f.geometry)) {
      const samples=[];
      for(const ring of poly)for(let k=1;k<ring.length;k++) {
        const a=ring[k-1],c=ring[k],steps=Math.max(1,Math.ceil(Math.max(Math.abs(c[0]-a[0])/dx,Math.abs(c[1]-a[1])/dy)*2));
        for(let n=0;n<=steps;n++)samples.push([a[0]+(c[0]-a[0])*n/steps,a[1]+(c[1]-a[1])*n/steps]);
      }
      const xs=poly[0].map(p=>(p[0]-b[0])/dx),ys=poly[0].map(p=>(b[3]-p[1])/dy);
      for(let j=Math.max(1,Math.floor(Math.min(...ys)));j<=Math.min(rows-2,Math.ceil(Math.max(...ys)));j++)
        for(let i=Math.max(1,Math.floor(Math.min(...xs)));i<=Math.min(cols-2,Math.ceil(Math.max(...xs)));i++){
          const p=[b[0]+i*dx,b[3]-j*dy];
          if(inRing(p,poly[0])&&!poly.slice(1).some(r=>inRing(p,r)))samples.push(p);
        }
      if(samples.length)groups.push(samples.map(p=>weightsAt(terrain,p)));
    }
  }
  const value=w=>w.reduce((sum,[i,k])=>sum+heights[i]*k,0);
  for(let pass=0;pass<128;pass++) {
    let largest=0;
    for(const group of groups) {
      let low=group[0],high=group[0],lo=value(low),hi=lo;
      for(const p of group){const h=value(p);if(h<lo){lo=h;low=p;}if(h>hi){hi=h;high=p;}}
      const excess=hi-lo-.35;largest=Math.max(largest,excess);
      if(excess<=0)continue;
      const gradient=new Map();
      for(const [i,k] of high)gradient.set(i,(gradient.get(i)||0)+k);
      for(const [i,k] of low)gradient.set(i,(gradient.get(i)||0)-k);
      // Boundary vertices remain fixed so a regional tile keeps its seam.
      for(const [i] of gradient)if(i%cols===0||i%cols===cols-1||i<cols||i>=cols*(rows-1))gradient.delete(i);
      const norm=[...gradient.values()].reduce((sum,k)=>sum+k*k,0);
      if(norm<1e-9)continue;
      for(const [i,k] of gradient)heights[i]=Math.max(original[i]-4,Math.min(original[i]+4,heights[i]-.7*excess*k/norm));
    }
    if(largest<.01)break;
  }
  return {...terrain,heights};
}

// DEM cells are wider than many traditional houses. A display-only terrace
// avoids turning that unresolved slope into a multi-storey foundation wall.
// Raw downloaded elevations and building coordinates remain untouched.
export function terraceTerrain(terrain, buildings) {
  const {bbox:b,cols,rows}=terrain, dx=(b[2]-b[0])/(cols-1),dy=(b[3]-b[1])/(rows-1);
  const sums=new Float64Array(cols*rows),weights=new Float64Array(cols*rows),strength=new Float32Array(cols*rows);
  for(const f of buildings){
    if(f.properties.visualRoof!=='traditional')continue;
    const ring=f.geometry.coordinates[0];
    const xs=ring.map(p=>p[0]),ys=ring.map(p=>p[1]);
    const west=Math.min(...xs),east=Math.max(...xs),south=Math.min(...ys),north=Math.max(...ys);
    const cx=(west+east)/2,cy=(south+north)/2,level=sampleHeight(terrain,cx,cy);
    const hx=(east-west)/2+dx*.75,hy=(north-south)/2+dy*.75;
    for(let j=Math.max(0,Math.floor((b[3]-north)/dy)-3);j<=Math.min(rows-1,Math.ceil((b[3]-south)/dy)+3);j++)
      for(let i=Math.max(0,Math.floor((west-b[0])/dx)-3);i<=Math.min(cols-1,Math.ceil((east-b[0])/dx)+3);i++){
        const x=b[0]+i*dx,y=b[3]-j*dy;
        const d=Math.max(0,(Math.abs(x-cx)-hx)/dx,(Math.abs(y-cy)-hy)/dy);
        const t=Math.max(0,1-d/1.5),w=t*t*(3-2*t),k=j*cols+i;
        sums[k]+=level*w;weights[k]+=w;strength[k]=Math.max(strength[k],w);
      }
  }
  const softened={...terrain,heights:terrain.heights.map((h,i)=>weights[i]?h*(1-strength[i])+sums[i]/weights[i]*strength[i]:h)};
  return balanceFootings(softened,buildings);
}
