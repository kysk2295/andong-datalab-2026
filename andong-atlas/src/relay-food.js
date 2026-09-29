import * as T from 'three';

// Actual metre dimensions: the shared pan is 56 cm across and food stays bite-sized.
// Edible objects remain direct children so pointer pickup uses the rendered mesh.
export function chickenGeometry(seed=0){
 const geo=new T.SphereGeometry(1,36,24),p=geo.attributes.position;
 for(let i=0;i<p.count;i++){
  const x=p.getX(i),y=p.getY(i),z=p.getZ(i);
  const lobes=1+.14*Math.sin(x*5+seed)*Math.sin(z*6+y*3)+.055*Math.sin(y*15+z*10)+.018*Math.cos(x*39+z*31);
  const taper=.79+.26*(1+x)/2;p.setXYZ(i,x*lobes,y*lobes*taper,z*lobes*taper);
 }geo.computeVertexNormals();return geo;
}

export function potatoGeometry(){
 const shape=new T.Shape();shape.moveTo(-.038,-.02);shape.lineTo(.032,-.024);shape.lineTo(.021,.035);shape.quadraticCurveTo(-.016,.045,-.038,-.02);
 const geo=new T.ExtrudeGeometry(shape,{depth:.041,bevelEnabled:true,bevelThickness:.003,bevelSize:.004,bevelSegments:3,steps:1});geo.center();
 // Extrusion's default UVs use metre coordinates, which made each cut face sample
 // just one colour from the photograph. Give the caps and sides a full surface.
 geo.computeBoundingBox();const size=geo.boundingBox.getSize(new T.Vector3()),p=geo.attributes.position,n=geo.attributes.normal,uv=geo.attributes.uv;
 for(let i=0;i<p.count;i++){const side=Math.abs(n.getX(i))>.6;uv.setXY(i,(side?p.getZ(i)/size.z:p.getX(i)/size.x)+.5,p.getY(i)/size.y+.5);}
 return geo;
}

function ribbon(k,parent,points,width,material){
 const curve=new T.CatmullRomCurve3(points.map(p=>new T.Vector3(...p))),positions=[],uv=[],indices=[];
 for(let i=0;i<=24;i++){const t=i/24,p=curve.getPoint(t),tangent=curve.getTangent(t),side=new T.Vector3(-tangent.z,0,tangent.x).normalize(),w=width*Math.sin(Math.PI*(.04+t*.92));for(const sign of [-1,1]){const v=p.clone().addScaledVector(side,sign*w/2);positions.push(...v);uv.push((sign+1)/2,t);}if(i<24){const n=i*2;indices.push(n,n+2,n+1,n+1,n+2,n+3);}}
 const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(positions,3));g.setAttribute('uv',new T.Float32BufferAttribute(uv,2));g.setIndex(indices);g.computeVertexNormals();return k.mesh(parent,g,material);
}

export function cookedMeal(parent,kind,k){
 const a=new T.Group();parent.add(a);
 const steel=k.mat('#b6bdbb',{roughness:.24,metalness:.9}),ceramic=k.mat('#e5e7e1',{roughness:.3}),sauce=k.mat('#482310',{roughness:.2});
 if(kind==='jjimdak'){
  const points=[[0,.008],[.245,.008],[.261,.022],[.283,.101],[.284,.108],[.278,.108],[.275,.10],[.254,.029],[0,.029]].map(p=>new T.Vector2(...p));
  k.mesh(a,new T.LatheGeometry(points,96),k.mat('#242520',{roughness:.49,metalness:.55}));
  const rim=k.mesh(a,new T.TorusGeometry(.281,.0028,10,96),steel,[0,.105,0]);rim.rotation.x=Math.PI/2;
  for(const side of [-1,1]){k.tube(a,[[side*.272,.066,-.075],[side*.331,.09,-.054],[side*.345,.096,0],[side*.331,.09,.054],[side*.272,.066,.075]],.006,steel);for(const z of [-.06,.06]){const rivet=k.sphere(a,[.003,.005,.005],[side*.274,.08,z],steel);}}
  k.cyl(a,.271,.271,.003,[0,.077,0],sauce,96);
  const skin=k.foodSkin;
  for(let i=0;i<17;i++){
   const t=i*2.39996,r=.065+Math.sqrt((i+.5)/17)*.15;
   const piece=k.mesh(a,chickenGeometry(i),skin,[Math.sin(t)*r,.09+(i%3)*.012,Math.cos(t)*r]);
   piece.scale.set(.037+(i%3)*.009,.029+(i%4)*.003,.031+(i%2)*.007);piece.rotation.set(.2*Math.sin(i),t,.35*Math.cos(i));piece.userData.edible=true;
   if(i%4===0){const bone=k.cyl(piece,.12,.17,.5,[.83,0,0],k.mat('#d9c8a8',{roughness:.56}),16);bone.rotation.z=Math.PI/2;k.sphere(piece,[.17,.2,.17],[1.07,0,0],'#d2bb95');}
  }
  for(let i=0;i<7;i++){const t=i*2.399+.8,r=.19;const wedge=k.mesh(a,potatoGeometry(),k.potato,[Math.sin(t)*r,.111,Math.cos(t)*r]);wedge.rotation.set(i*.3,t,i%2?.4:0);wedge.userData.edible=true;}
  const noodle=k.mat('#60421d',{roughness:.21,transparent:true,opacity:.85,depthWrite:true});
  // Loosely coiled, sauce-darkened glass noodles follow varied paths over the mound.
  for(let i=0;i<110;i++){
   const angle=i*2.39996,r=.015+Math.sqrt((i%19)/19)*.104,x=Math.sin(angle)*r,z=Math.cos(angle)*r,points=[];
   for(let n=0;n<9;n++){const t=n/8,a=angle+t*Math.PI*(1.3+(i%5)*.23),radius=.015+.024*Math.sin(t*Math.PI);points.push([x+Math.cos(a)*radius,.126+Math.sin(t*Math.PI)*.018+(i%4)*.004,z+Math.sin(a)*radius*.66]);}
   k.tube(a,points,.0011+(i%3)*.00014,noodle);
  }
  const green=k.mat('#356a25',{roughness:.39,side:T.DoubleSide}),pale=k.mat('#889652',{roughness:.43,side:T.DoubleSide});
  for(let i=0;i<16;i++){const t=i*2.399,r=.075+(i%4)*.043,x=Math.sin(t)*r,z=Math.cos(t)*r;
   const leaf=ribbon(k,a,[[-.057,.129,-.023],[-.022,.151,0],[.042,.146,.024],[.071,.12,.034]],.0105+(i%3)*.002,i%4===0?pale:green);leaf.position.set(x,0,z);leaf.rotation.y=t;
  }
  for(let i=0;i<5;i++){const t=i*2.4+.3,slice=k.cyl(a,.024,.027,.009,[Math.sin(t)*.18,.116,Math.cos(t)*.18],k.mat('#b96829',{roughness:.46}),32);slice.rotation.set(.17,t,.36);}
  const chilli=k.mat('#bc351b',{roughness:.35});for(let i=0;i<6;i++){const t=i*2.3;const ring=k.mesh(a,new T.TorusGeometry(.010,.0024,8,20),chilli,[Math.sin(t)*.186,.147,Math.cos(t)*.177]);ring.rotation.set(1.1,t,.4);ring.scale.y=1.6;}
  const seeds=[];for(let i=0;i<56;i++){const t=i*2.399,r=.02+Math.sqrt(i/56)*.2;seeds.push({p:[Math.sin(t)*r,.146+(i%3)*.004,Math.cos(t)*r],s:[.0023,.0008,.0013],r:[0,t,0]});}k.instances(a,new T.SphereGeometry(1,8,6),k.mat('#dcc8a0',{roughness:.74}),seeds);
 }else if(kind==='mackerel'){
  const plate=k.cyl(a,.25,.25,.017,[0,.01,0],ceramic,72);plate.scale.z=.64;
  const fish=k.mesh(a,chickenGeometry(5),k.mat('#9d8964',{roughness:.52}),[0,.049,0]);fish.scale.set(.218,.023,.07);
  const flakes=[];for(let i=0;i<45;i++){const x=-.18+i*.008;flakes.push({p:[x,.072+.006*Math.sin(i),.005],s:[.003,.001,.048],r:[0,.22,0],color:i%4===0?'#49423b':'#bea977'});}k.instances(a,new T.SphereGeometry(1,10,8),k.mat('#ffffff'),flakes);
  for(const x of [-.1,0,.1]){const bite=k.mesh(a,chickenGeometry(2),k.mat('#dcd1ae',{roughness:.54}),[x,.071,.033]);bite.scale.set(.032,.014,.024);bite.userData.edible=true;}
  const lemon=k.cyl(a,.033,.033,.006,[.18,.028,.078],k.mat('#e4c25f',{roughness:.56}),40);lemon.rotation.z=.25;
 }else{
  k.bowl(a,[0,0,0],.2,'#8a8471');rice(k,a,[0,.095,0],.16);
  const colors=['#547340','#bb6633','#5a4630','#e0c892'];for(let n=0;n<4;n++)for(let i=0;i<15;i++){const t=n*Math.PI/2,rad=.07+i*.004,x=Math.sin(t)*rad,z=Math.cos(t)*rad;k.tube(a,[[x-.012,.131,z-.035],[x,.144+(i%2)*.004,z],[x+.023,.139,z+.029]],.003,k.mat(colors[n],{roughness:.47}));}
  k.sphere(a,[.039,.018,.039],[0,.16,0],k.mat('#db9b2c',{roughness:.3}));
  for(let i=0;i<3;i++){const t=i*2.1;const bite=k.mesh(a,chickenGeometry(i),k.mat('#d9c8a1',{roughness:.52}),[Math.sin(t)*.105,.151,Math.cos(t)*.105]);bite.scale.set(.031,.016,.025);bite.userData.edible=true;}
 }
 return a;
}

export function rice(k,parent,p,r=.092){
 k.sphere(parent,[r,.027,r],p,k.mat('#d3d3c3',{roughness:.6}));
 let seed=375;const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
 const grains=[];for(let i=0;i<690;i++){const t=random()*Math.PI*2,rad=Math.sqrt(random())*r,h=Math.sqrt(Math.max(0,1-(rad/r)**2))*.028;
  grains.push({p:[p[0]+Math.sin(t)*rad,p[1]+h+(i%3)*.001,p[2]+Math.cos(t)*rad],s:[.0018,.0018,.0042],r:[.2*Math.sin(i),t,.3*Math.cos(i)],color:i%7===0?'#c8c7b4':'#dedfd0'});
 }return k.instances(parent,new T.SphereGeometry(1,8,6),k.mat('#ffffff',{roughness:.49}),grains);
}

export function diningSides(parent,k){
 for(const x of [-.47,.47]){const bowl=k.bowl(parent,[x,.799,.22],.105,'#c6cdcd');bowl.material=k.mat('#bfc5c3',{metalness:.86,roughness:.33});rice(k,parent,[x,.872,.22]);}
 k.bowl(parent,[-.5,.8,-.20],.095,'#e4e5da');
 for(let i=0;i<13;i++){const t=i*2.4,x=-.5+Math.sin(t)*.046,z=-.2+Math.cos(t)*.043;
  ribbon(k,parent,[[x-.027,.842,z-.01],[x,.862,z+.014],[x+.031,.85,z-.003]],.029,k.mat(i%3===0?'#d0b289':'#aa4b26',{roughness:.41,side:T.DoubleSide}));}
 k.bowl(parent,[.5,.8,-.20],.095,'#e4e5da','#c6b884');
 for(let i=0;i<8;i++){const t=i*2.4;const radish=k.roundedBox(parent,[.027,.025,.03],[.5+Math.sin(t)*.052,.851,-.2+Math.cos(t)*.05],k.mat('#e3dec0',{roughness:.39}),.004);radish.rotation.y=t;}
}
