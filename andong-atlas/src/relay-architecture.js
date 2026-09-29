import * as T from 'three';

// Geometry is drawn from the cited photographs; these are visitor-scale reconstructions.
export function curvedRoof(g,w,d,p,k){
 const a=new T.Group();g.add(a);a.position.set(...p);
 const halfX=w/2,halfZ=d/2,h=Math.min(w,d)*.23;
 const height=(x,z)=>{const nx=Math.abs(x)/halfX,nz=Math.abs(z)/halfZ;const slope=Math.max(nz,Math.max(0,(Math.abs(x)-Math.max(0,halfX-halfZ))/halfZ));return h*Math.pow(Math.max(0,1-slope),1.7)+.22*Math.pow(nx*nz,5);};
 const geo=new T.PlaneGeometry(w,d,40,24);geo.rotateX(-Math.PI/2);const v=geo.attributes.position;
 for(let i=0;i<v.count;i++)v.setY(i,height(v.getX(i),v.getZ(i)));geo.computeVertexNormals();
 k.mesh(a,geo,k.mat('#41494a',{side:T.DoubleSide,roughness:.92}));
 for(let x=-halfX+.06;x<halfX;x+=.19){
  for(const side of [-1,1]){const points=[];for(let i=0;i<=9;i++){const z=side*halfZ*i/9;points.push([x,height(x,z)+.045,z]);}k.tube(a,points,.042,'#596064');
   k.sphere(a,[.048,.045,.028],[x,height(x,halfZ)+.036,side*(halfZ+.012)],'#88877d');}
 }
 for(const side of [-1,1]){
  const eave=[];for(let i=0;i<=16;i++){const x=-halfX+w*i/16;eave.push([x,height(x,halfZ)-.09,side*halfZ]);}k.tube(a,eave,.075,k.woodDark);
  for(const sx of [-1,1]){const ridge=[];for(let i=0;i<=12;i++){const t=i/12,x=sx*halfX*t,z=side*halfZ*t;ridge.push([x,height(x,z)+.09,z]);}k.tube(a,ridge,.08,'#424b4b');}
 }
 for(let x=-halfX+.18;x<halfX;x+=.38)for(const side of [-1,1])k.tube(a,[[x,.04,side*(halfZ-.02)],[x,.14,side*(halfZ-.8)]],.054,k.woodDark);
 k.tube(a,[[-Math.max(.1,halfX-halfZ),h+.12,0],[0,h+.14,0],[Math.max(.1,halfX-halfZ),h+.12,0]],.11,'#444c4c');
 return a;
}

export function pavilion(g,p,k){
 const a=new T.Group();a.position.set(...p);g.add(a);const sides=8,r=3.15,roofR=4.35;
 k.cyl(a,r+.2,r+.2,.23,[0,.12,0],k.woodDark,sides);k.cyl(a,r,r,.08,[0,.27,0],k.floor,sides);
 const perimeter=[];
 for(let i=0;i<sides;i++){
  const angle=Math.PI/8+i*Math.PI/4,x=Math.sin(angle)*r,z=Math.cos(angle)*r;perimeter.push([x,3.05,z]);
  k.cyl(a,.14,.18,2.85,[x,1.65,z],k.woodDark);k.cyl(a,.24,.25,.23,[x,.38,z],k.stone);
  for(const y of [2.75,2.91,3.07]){const bracket=k.box(a,[.78,.095,.42],[x,y,z],i%2?'#546453':'#6b5140');bracket.rotation.y=angle;}
  const next=angle+Math.PI/4,xx=Math.sin(next)*r,zz=Math.cos(next)*r;
  k.tube(a,[[x,2.9,z],[xx,2.9,zz]],.11,k.woodDark);
  // Leave the two axial openings unobstructed for visitors.
  if(i!==3&&i!==7){for(const y of [.62,1.15])k.tube(a,[[x,y,z],[xx,y,zz]],.055,k.woodDark);for(let n=1;n<5;n++)k.cyl(a,.026,.026,.53,[x+(xx-x)*n/5,.88,z+(zz-z)*n/5],k.woodDark,8);}
 }
 const roof=new T.Group();a.add(roof);roof.position.y=3.12;
 const profile=t=>1.55*Math.pow(1-t,2)+.18*Math.pow(t,7);
 for(let side=0;side<sides;side++){
  const ang=Math.PI/8+side*Math.PI/4,positions=[],indices=[];
  for(let row=0;row<=12;row++)for(let col=0;col<=8;col++){const t=row/12,u=col/8,x=(Math.sin(ang)*(1-u)+Math.sin(ang+Math.PI/4)*u)*roofR*t,z=(Math.cos(ang)*(1-u)+Math.cos(ang+Math.PI/4)*u)*roofR*t;positions.push(x,profile(t),z);}
  for(let row=0;row<12;row++)for(let col=0;col<8;col++){const n=row*9+col;indices.push(n,n+9,n+1,n+1,n+9,n+10);}
  const geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(positions,3));geo.setIndex(indices);geo.computeVertexNormals();k.mesh(roof,geo,k.mat('#434d50',{side:T.DoubleSide}));
  for(let col=0;col<=10;col++){const u=col/10,points=[];for(let row=0;row<=12;row++){const t=row/12;points.push([(Math.sin(ang)*(1-u)+Math.sin(ang+Math.PI/4)*u)*roofR*t,profile(t)+.035,(Math.cos(ang)*(1-u)+Math.cos(ang+Math.PI/4)*u)*roofR*t]);}k.tube(roof,points,col===0?.082:.046,col===0?'#8b8c80':'#5a666a');const end=points.at(-1);k.sphere(roof,[.049,.045,.049],end,'#9a9b8b');}
  k.tube(roof,[[Math.sin(ang)*roofR,.04,Math.cos(ang)*roofR],[Math.sin(ang+Math.PI/4)*roofR,.04,Math.cos(ang+Math.PI/4)*roofR]],.075,k.woodDark);
 }
 k.cyl(roof,.035,.16,.42,[0,1.83,0],'#58635c');k.sphere(roof,[.11,.1,.11],[0,1.63,0],'#7c8173');
 k.label(a,'月 映 亭',[0,2.66,r*.924+.03],1.3,'#dbd4c0','#272d27',.42);
 for(const x of [-1.1,1.1])k.lamp(a,[x,2.55,1.8],.36);
 return a;
}

export {marketStreet} from './relay-market.js';

export function riverLandscape(group,k){
 for(const side of [-1,1]){
  const elevation=(x,z)=>{const hill=Math.max(0,15*Math.exp(-(((x-side*89)/48)**2+((z+38)/68)**2))+Math.sin((x-side*89)*.15)*Math.cos((z+38)*.13)*2.7),t=T.MathUtils.smoothstep(Math.abs(x),18,37);return -.7+(hill+.7)*t;};
  const geo=new T.PlaneGeometry(142,150,60,50);geo.rotateX(-Math.PI/2);const a=geo.attributes.position;
  for(let i=0;i<a.count;i++)a.setY(i,elevation(a.getX(i)+side*89,a.getZ(i)-38));geo.computeVertexNormals();k.mesh(group,geo,k.forest,[side*89,0,-38]).userData.scenery=true;
  let seed=side<0?813:257;const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
  const trees=[];for(let i=0;i<320;i++){const x=side*(26+random()*100),z=-108+random()*155;trees.push({x,y:elevation(x,z),z,height:6.2+random()*3.6,seed:i+side*5});}k.grove(group,trees);
 }
}
