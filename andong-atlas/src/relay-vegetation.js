import * as T from 'three';

// Only the photographed twig in the top-left of the CC0 pine atlas is used.
// The outline stays inside its black alpha island (the unused atlas is opaque).
export function pineTwigGeometry(){
 const uv=[[.115,.562],[.154,.562],[.19,.64],[.226,.82],[.226,.953],[.048,.953],[.036,.82],[.061,.64]];
 const shape=new T.Shape(uv.map(([u,v])=>new T.Vector2((u-.13)*3.5,(v-.562)*2.85)));
 const geo=new T.ShapeGeometry(shape),p=geo.attributes.position;
 const coords=[];for(let i=0;i<p.count;i++)coords.push(p.getX(i)/3.5+.13,p.getY(i)/2.85+.562);
 geo.setAttribute('uv',new T.Float32BufferAttribute(coords,2));return geo;
}

// A forest shares three draw calls: bark trunks, structural branches and twigs.
// Every tree has irregular whorls and a tapered crown, with no solid canopy balls.
export function pineGrove(parent,trees,k){
 const trunks=[],branches=[],twigs=[];
 const up=new T.Vector3(0,1,0),delta=new T.Vector3(),q=new T.Quaternion(),e=new T.Euler();
 const segment=(a,b,r1,r2)=>{delta.fromArray(b).sub(new T.Vector3(...a));q.setFromUnitVectors(up,delta.clone().normalize());e.setFromQuaternion(q);branches.push({p:a.map((v,i)=>(v+b[i])/2),s:[r1,delta.length(),r2],r:[e.x,e.y,e.z]});};
 for(let i=0;i<trees.length;i++){
  const {x,y=0,z,height=5,seed=i}=trees[i],bend=Math.sin(seed*1.73)*.14;
  trunks.push({p:[x+bend*height*.15,y+height*.45,z],s:[height*.055,height*.9,height*.055],r:[0,seed*.4,bend*.15]});
  const tiers=6;
  for(let row=0;row<tiers;row++){
   const level=.38+row*.105,spread=height*(.29-row*.035),count=row===5?3:5;
   for(let n=0;n<count;n++){
    const a=seed*1.17+n*Math.PI*2/count+row*.87,cx=x+bend*height*level*.3,cy=y+height*level;
    const ex=cx+Math.sin(a)*spread,ez=z+Math.cos(a)*spread,ey=cy+height*(.035+row*.006);
    segment([cx,cy,z],[ex,ey,ez],height*.008,height*.008);
    for(let j=0;j<3;j++){
     const t=.38+j*.29,size=height*(.21-row*.017)*(1-j*.15),tx=T.MathUtils.lerp(cx,ex,t),tz=T.MathUtils.lerp(z,ez,t);
     const angle=a+(j%2?-.48:.37),tilt=.72+Math.sin(seed+row+j)*.22;
     // Crossed, differently tilted cards retain the needle silhouette from all views.
     for(let face=0;face<2;face++)twigs.push({p:[tx,cy+height*.025,tz],s:[size,size,size],r:[tilt,angle,face*Math.PI/2],color:new T.Color().setHSL(.22+(seed%5)*.008,.18,.72+(row%3)*.055)});
    }
   }
  }
  twigs.push({p:[x,y+height*.85,z],s:[height*.15,height*.15,height*.15],r:[0,seed,0]});
 }
 const root=new T.Group();parent.add(root);root.userData.scenery=true;
 k.instances(root,new T.CylinderGeometry(.24,1,1,9,3),k.bark,trunks);
 k.instances(root,new T.CylinderGeometry(.3,1,1,7),k.bark,branches);
 const crown=k.instances(root,pineTwigGeometry(),k.needles,twigs);crown.castShadow=trees.length<12;
 root.userData.treeCount=trees.length;root.userData.twigCount=twigs.length;
 return root;
}
