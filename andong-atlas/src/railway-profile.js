// Display geometry inferred from mapped track positions and DEM, not surveyed
// rail levels. Shared nodes and a bounded grade keep joined tracks continuous.
export function railwayProfiles(features, project, groundAt) {
  const nodes=[],byKey=new Map(),edges=[],tracks=[];
  const nodeAt=(c,bridge,normal)=>{
    const key=c.map(n=>n.toFixed(9)).join(',');
    let node=byKey.get(key);
    const [x,z]=project.toWorld(c);
    const ground=Math.max(groundAt(x,z),groundAt(x+normal[0]*.005,z+normal[1]*.005),groundAt(x-normal[0]*.005,z-normal[1]*.005));
    const minimum=ground+(bridge?.014:.002);
    if(!node){node={x,z,height:minimum};byKey.set(key,node);nodes.push(node);}
    else node.height=Math.max(node.height,minimum);
    return node;
  };
  for(const feature of features){
    if(feature.properties.tunnel&&feature.properties.tunnel!=='no')continue;
    const bridge=!!feature.properties.bridge&&feature.properties.bridge!=='no';
    const coordinates=[],path=[];
    const source=feature.geometry.coordinates;
    for(let i=1;i<source.length;i++){
      const a=source[i-1],b=source[i],p=project.toWorld(a),q=project.toWorld(b);
      const length=Math.hypot(q[0]-p[0],q[1]-p[1]);if(length<1e-10)continue;
      const normal=[-(q[1]-p[1])/length,(q[0]-p[0])/length],count=Math.ceil(length/.02);
      for(let j=0;j<=count;j++){
        const c=j===0?a:j===count?b:a.map((v,k)=>v+(b[k]-v)*j/count);
        const node=nodeAt(c,bridge,normal),last=path.at(-1);
        if(last===node)continue;
        if(last)edges.push([last,node,Math.hypot(last.x-node.x,last.z-node.z)]);
        path.push(node);coordinates.push(c);
      }
    }
    if(path.length>1)tracks.push({id:String(feature.id),bridge,path,coordinates});
  }
  // Minimal upper envelope with a 0.2 display grade (terrain is shown 4× high).
  // No source DEM is edited and both sides of every shared node have one height.
  for(let pass=0;pass<nodes.length;pass++){
    let changed=false;
    for(const [a,b,distance] of edges){
      const delta=.2*distance;
      if(a.height<b.height-delta-1e-10){a.height=b.height-delta;changed=true;}
      if(b.height<a.height-delta-1e-10){b.height=a.height-delta;changed=true;}
    }
    if(!changed)break;
  }
  for(const track of tracks){
    track.surface=(x,z)=>{
      let nearest=Infinity,height=track.path[0].height;
      for(let i=1;i<track.path.length;i++){
        const a=track.path[i-1],b=track.path[i],dx=b.x-a.x,dz=b.z-a.z;
        const t=Math.max(0,Math.min(1,((x-a.x)*dx+(z-a.z)*dz)/(dx*dx+dz*dz)));
        const distance=(x-a.x-dx*t)**2+(z-a.z-dz*t)**2;
        if(distance<nearest){nearest=distance;height=a.height+(b.height-a.height)*t;}
      }
      return height;
    };
  }
  return tracks;
}
