import * as T from 'three';
import {visitor} from './relay-people.js';
import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';
import {scannedProp} from './relay-scanned-props.js';
import {createVisitorHand} from './relay-hands.js';
import {curvedRoof} from './relay-architecture.js';
import {cookedMeal,diningSides} from './relay-food.js';
import {pineGrove} from './relay-vegetation.js';
import {materialMaps} from './relay-materials.js';
import {bowlGeometry} from './relay-vessels.js';
export function createKit(){
 const materials=new Map(),textures=new Set(),geometries=new Set();
 function texture(kind){
  const c=document.createElement('canvas');c.width=c.height=256;const x=c.getContext('2d');
  x.fillStyle=kind==='wood'?'#99734f':kind==='plaster'?'#ded1b5':'#827d71';x.fillRect(0,0,256,256);
  let seed=54;const rand=()=>{seed=(1664525*seed+1013904223)>>>0;return seed/4294967296;};
  for(let i=0;i<1400;i++){x.fillStyle=`rgba(${rand()>.5?'255,245,213':'30,24,17'},${rand()*.1})`;if(kind==='wood')x.fillRect(rand()*256,rand()*256,rand()*170,1);else x.fillRect(rand()*256,rand()*256,rand()*3+1,rand()*3+1);}
  if(kind==='stone'){x.strokeStyle='#666257';x.lineWidth=2;for(let y=0;y<256;y+=64){x.beginPath();x.moveTo(0,y);x.lineTo(256,y);x.stroke();for(let a=(y/64%2)*64;a<256;a+=128)x.strokeRect(a,y,128,64);}}
  const tx=new T.CanvasTexture(c);tx.colorSpace=T.SRGBColorSpace;tx.wrapS=tx.wrapT=T.RepeatWrapping;tx.repeat.set(kind==='wood'?2:3,3);textures.add(tx);return tx;
 }
 const wood=texture('wood'),plaster=texture('plaster'),stone=texture('stone');
 function pbr(asset,repeat,color){const m=new T.MeshStandardMaterial({color,roughness:.8,...materialMaps(asset,repeat,textures),normalScale:new T.Vector2(.45,.45)});materials.set(asset+materials.size,m);return m;}
 const floor=pbr('wood_floor',[3,3],'#b9a58b'),paving=pbr('cobblestone_floor_02',[5,6],'#b3b3a5'),wall=pbr('clay_plaster',[2,2],'#eee0c2');
 function mat(color='#e4d6bf',opts={}){const k=color+JSON.stringify(opts);if(!materials.has(k))materials.set(k,new T.MeshStandardMaterial({color,roughness:.82,...opts}));return materials.get(k);}
 const woodMat=pbr('wood_table',[1,1],'#d4c9bc');woodMat.roughness=.39;woodMat.normalScale.set(.07,.07);
 woodMat.onBeforeCompile=shader=>{shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>','#include <map_fragment>\n diffuseColor.rgb=mix(vec3(.21,.105,.043),diffuseColor.rgb,.32);').replace('#include <roughnessmap_fragment>','#include <roughnessmap_fragment>\n roughnessFactor=max(.34,roughnessFactor);');};woodMat.customProgramCacheKey=()=> 'dining-varnish';
 const bark=pbr('pine_bark',[1,2],'#c5bdaf'),forest=pbr('forest_ground_04',[17,20],'#69705c');
 const needles=pbr('pine_needles',[1,1],'#c4c9b3');needles.alphaTest=.46;needles.side=T.DoubleSide;needles.roughness=.88;needles.normalScale.set(.22,.22);
 const distantNeedles=new T.MeshLambertMaterial({map:needles.map,alphaMap:needles.alphaMap,color:'#c4c9b3',alphaTest:.46,side:T.DoubleSide});materials.set('distant-pine',distantNeedles);
 const skinMaps=materialMaps('meal-photo',[.085,.082],textures);if(skinMaps.map)skinMaps.map.offset.set(.425,.203);
 const foodSkin=new T.MeshPhysicalMaterial({color:'#ac8855',...skinMaps,roughness:.43,clearcoat:.18,clearcoatRoughness:.36});materials.set('food-skin',foodSkin);
 const potatoMaps=materialMaps('meal-photo',[.047,.032],textures);if(potatoMaps.map)potatoMaps.map.offset.set(.656,.247);
 const potato=new T.MeshStandardMaterial({color:'#dbc08e',...potatoMaps,bumpMap:potatoMaps.map,bumpScale:.0007,roughness:.51});materials.set('potato-surface',potato);
 const brick=pbr('brick_wall_001',[3.6,1.3],'#d6c8b6'),fabric=pbr('fabric_pattern_05',[2,2],'#b1a494');
 const paperMat=new T.MeshStandardMaterial({map:plaster,color:'#f2e5c9',roughness:1});materials.set('paper',paperMat);
 const stoneMat=new T.MeshStandardMaterial({map:stone,color:'#b5b2a1',roughness:1});materials.set('stone',stoneMat);
 const woodDark=pbr('wood_table',[1,1],'#8b8171');woodDark.roughness=.76;woodDark.roughnessMap=null;woodDark.normalScale.set(.16,.16);
 function instances(g,geo,m,items){geometries.add(geo);const o=new T.InstancedMesh(geo,typeof m==='string'?mat(m):m,items.length),dummy=new T.Object3D();items.forEach((v,i)=>{dummy.position.set(...v.p);dummy.scale.set(...(v.s||[1,1,1]));dummy.rotation.set(...(v.r||[0,0,0]));dummy.updateMatrix();o.setMatrixAt(i,dummy.matrix);if(v.color)o.setColorAt(i,new T.Color(v.color));});o.castShadow=true;o.receiveShadow=true;g.add(o);return o;}
 function mesh(g,geo,m,pos=[0,0,0]){geometries.add(geo);const o=new T.Mesh(geo,typeof m==='string'?mat(m):m);o.position.set(...pos);o.castShadow=true;o.receiveShadow=true;g.add(o);return o;}
 const box=(g,s,p,c)=>mesh(g,new T.BoxGeometry(...s),c,p);
 const roundedBox=(g,s,p,c,r=.02)=>mesh(g,new RoundedBoxGeometry(...s,3,r),c,p);
 const photo=(g,asset,p,w,h)=>{const m=new T.MeshStandardMaterial({color:'#ffffff',roughness:.7,...materialMaps(asset,[1,1],textures)});materials.set('photo'+materials.size,m);return mesh(g,new T.PlaneGeometry(w,h),m,p);};
 const scan=(id,parent,pos,width)=>scannedProp(id,parent,pos,width,{materials,geometries,textures});
 const sphere=(g,s,p,c)=>{const m=mesh(g,new T.SphereGeometry(1,20,14),c,p);m.scale.set(...(Array.isArray(s)?s:[s,s,s]));return m;};
 const cyl=(g,r1,r2,h,p,c,n=24)=>mesh(g,new T.CylinderGeometry(r1,r2,h,n),c,p);
 function tube(g,points,r,c){const curve=new T.CatmullRomCurve3(points.map(p=>new T.Vector3(...p)));return mesh(g,new T.TubeGeometry(curve,Math.max(10,points.length*5),r,6,false),c);}
 function label(g,text,pos,w=2,color='#f8edcd',bg='#294b42',height=.45){const c=document.createElement('canvas');c.width=1024;c.height=Math.round(1024*height/w);const x=c.getContext('2d');x.fillStyle=bg;x.fillRect(0,0,c.width,c.height);x.strokeStyle=color;x.globalAlpha=.4;x.strokeRect(10,10,c.width-20,c.height-20);x.globalAlpha=1;x.textAlign='center';x.textBaseline='middle';x.fillStyle=color;x.font=`600 ${Math.min(c.height*.49,1024/(text.length*.62+2))}px Pretendard, sans-serif`;x.fillText(text,512,c.height/2);const tx=new T.CanvasTexture(c);tx.colorSpace=T.SRGBColorSpace;textures.add(tx);const m=new T.MeshBasicMaterial({map:tx,toneMapped:false});materials.set('label'+materials.size,m);return mesh(g,new T.PlaneGeometry(w,height),m,pos);}
 // Painted signs receive the same light and shadow as their supporting facade.
 function sign(...args){const o=label(...args),m=new T.MeshStandardMaterial({map:o.material.map,roughness:.68,metalness:.06});materials.set('painted-sign'+materials.size,m);o.material=m;return o;}
 function lamp(g,p,scale=1,color='#ffd897'){
  const a=new T.Group();g.add(a);a.position.set(...p);a.scale.setScalar(scale);
  cyl(a,.22,.22,.5,[0,0,0],mat(color,{emissive:color,emissiveIntensity:.8}));
  for(let i=0;i<7;i++)cyl(a,.227,.227,.009,[0,-.22+i*.07,0],'#8a4b31');
  cyl(a,.17,.17,.06,[0,.29,0],'#3d3023');cyl(a,.17,.17,.04,[0,-.28,0],'#3d3023');
  tube(a,[[0,.3,0],[0,.52,0]],.012,'#42352a');return a;
 }
 function roof(g,w,d,p){return curvedRoof(g,w,d,p,{mesh,tube,sphere,box,mat,woodDark});}
 function table(g,p,w=1.5,d=.9,h=.76){const a=new T.Group();a.position.set(...p);g.add(a);roundedBox(a,[w,.075,d],[0,h,0],woodMat,.025);const steel=mat('#292b29',{metalness:.65,roughness:.36});for(const x of [-w*.41,w*.41])for(const z of [-d*.35,d*.35])cyl(a,.025,.022,h-.03,[x,(h-.03)/2,z],steel,12);for(const z of [-d*.35,d*.35])box(a,[w*.84,.06,.035],[0,h-.1,z],steel);return a;}
 function chair(g,p,rot=0){const a=new T.Group();a.position.set(...p);a.rotation.y=rot;g.add(a);const black=mat('#242726',{roughness:.42}),steel=mat('#333837',{metalness:.7,roughness:.27});roundedBox(a,[.44,.075,.44],[0,.445,0],black,.03);const back=roundedBox(a,[.43,.32,.05],[0,.77,-.205],black,.025);back.rotation.x=.13;for(const side of [-1,1]){tube(a,[[side*.17,.04,-.21],[side*.18,.44,-.19],[side*.17,.85,-.23]],.017,steel);tube(a,[[side*.2,.02,.19],[side*.17,.43,.16],[side*.17,.46,-.17]],.017,steel);}return a;}
 function bowl(g,p,r=.18,color='#f0e6d5',liquid=null){const m=mesh(g,bowlGeometry(r),mat(color,{roughness:.35}),p);if(liquid)cyl(g,r*.84,r*.84,.003,[p[0],p[1]+r*.55,p[2]],mat(liquid,{roughness:.2}));return m;}

 function plant(g,p,s=1){
  const a=new T.Group();g.add(a);a.position.fromArray(p);a.scale.setScalar(s);
  const profile=[[0,0],[.14,0],[.22,.35],[.234,.36],[.234,.395],[.215,.397],[.205,.352],[.13,.033],[0,.033]].map(v=>new T.Vector2(...v));
  mesh(a,new T.LatheGeometry(profile,48),mat('#956d51',{roughness:.94}));cyl(a,.205,.205,.009,[0,.35,0],mat('#342d23',{roughness:1}));
  tube(a,[[0,.35,0],[.014,.7,-.025],[-.018,1.02,0]],.009,'#596047');
  for(let i=0;i<15;i++){
   const angle=i*2.399,base=.43+i*.033,reach=.11+(i%3)*.02,x=Math.sin(angle)*reach,z=Math.cos(angle)*reach;
   tube(a,[[0,base,0],[x*.5,base+.045,z*.5],[x,base+.055,z]],.0035,'#536747');
   const geo=new T.PlaneGeometry(1,1,10,16),v=geo.attributes.position,colors=[];
   for(let n=0;n<v.count;n++){const t=v.getY(n)+.5,u=v.getX(n)*2,edge=Math.pow(Math.sin(Math.PI*t),.8),crease=Math.abs(u)*.009;
    v.setXYZ(n,u*.065*edge,t*.30,.025*Math.sin(t*Math.PI)-crease+.018*t*t);const c=new T.Color().setHSL(.25+(i%3)*.015,.34,.21+.075*(1-Math.abs(u)));colors.push(c.r,c.g,c.b);}
   geo.setAttribute('color',new T.Float32BufferAttribute(colors,3));geo.computeVertexNormals();const leaf=mesh(a,geo,mat('#ffffff',{side:T.DoubleSide,vertexColors:true,roughness:.64}),[x,base+.055,z]);leaf.rotation.set(.65+(i%3)*.2,angle,Math.sin(i)*.2);
  }return a;
 }

 function pot(g,p,s=1){const a=new T.Group();g.add(a);a.position.set(...p);a.scale.setScalar(s);const pts=[[0,0],[.19,0],[.28,.12],[.31,.4],[.25,.55],[.21,.57]].map(v=>new T.Vector2(...v));mesh(a,new T.LatheGeometry(pts,28),mat('#544031',{roughness:.36}));a.userData.lid=cyl(a,.245,.245,.035,[0,.58,0],'#45362c');return a;}
 function steam(g,p){
  const c=document.createElement('canvas');c.width=c.height=64;const x=c.getContext('2d'),fade=x.createRadialGradient(32,32,1,32,32,31);fade.addColorStop(0,'rgba(240,242,238,.65)');fade.addColorStop(.4,'rgba(240,242,238,.24)');fade.addColorStop(1,'rgba(240,242,238,0)');x.fillStyle=fade;x.fillRect(0,0,64,64);const tx=new T.CanvasTexture(c);textures.add(tx);
  const m=new T.SpriteMaterial({map:tx,color:'#f2efe8',transparent:true,opacity:.13,depthWrite:false});materials.set('steam'+materials.size,m);const sprite=new T.Sprite(m);sprite.position.fromArray(p);sprite.scale.set(.15,.22,1);g.add(sprite);return sprite;
 }
 function flower(parent,p,s=1){
  const a=new T.Group();a.position.fromArray(p);a.scale.setScalar(s);parent.add(a);
  sphere(a,[.007,.005,.007],[0,.006,0],mat('#ad802b',{roughness:.83}));
  const petals=[];for(let row=0;row<3;row++)for(let n=0;n<20+row*4;n++){
   const angle=n*Math.PI*2/(20+row*4)+row*.27,r=.006+row*.005;
   petals.push({p:[Math.sin(angle)*r,.005-row*.001+Math.sin(n*3)*.001,Math.cos(angle)*r],s:[.0026,.001,.008+row*.003],r:[.16+row*.15,angle,Math.sin(n)*.12],color:n%4===0?'#d3ac50':'#ead183'});
  }instances(a,new T.SphereGeometry(1,12,8),mat('#ffffff',{roughness:.73}),petals);return a;
 }
 function teapot(g,p,s=1){
  const a=new T.Group();g.add(a);a.position.fromArray(p);a.scale.setScalar(s);
  const glaze=mat('#899281',{roughness:.24,metalness:.03}),rim=mat('#bdc2a8',{roughness:.34});
  const points=[[0,.015],[.16,.015],[.21,.045],[.29,.16],[.32,.32],[.27,.47],[.21,.54],[.205,.57],[.186,.57],[.19,.53],[.25,.46],[.29,.31],[.26,.15],[.17,.052],[0,.052]].map(x=>new T.Vector2(...x));
  mesh(a,new T.LatheGeometry(points,72),glaze);
  tube(a,[[.24,.28,0],[.36,.36,0],[.44,.47,0],[.51,.52,0]],.044,glaze);
  const mouth=cyl(a,.031,.031,.012,[.515,.526,0],'#3c4941',32);mouth.rotation.z=-Math.PI*.29;
  tube(a,[[-.23,.44,0],[-.43,.49,0],[-.5,.34,0],[-.42,.18,0],[-.27,.17,0]],.026,glaze);
  a.userData.spout=[.515,.526,0];a.userData.lid=new T.Group();a.add(a.userData.lid);cyl(a.userData.lid,.207,.207,.025,[0,.578,0],rim,64);sphere(a.userData.lid,[.048,.026,.048],[0,.606,0],glaze);
  for(const y of [.08,.1,.48]){const ring=mesh(a,new T.TorusGeometry(y>.4?.262:.23,.0025,6,64),rim,[0,y,0]);ring.rotation.x=Math.PI/2;}
  return a;
 }
 function mask(g,p,s=1){const a=new T.Group();g.add(a);a.position.set(...p);a.scale.setScalar(s);const face=sphere(a,[.27,.34,.115],[0,0,0],'#c79358');
  for(const side of [-1,1]){sphere(a,[.09,.032,.025],[side*.115,.07,.098],'#2c251f');tube(a,[[side*.04,.17,.075],[side*.12,.195,.087],[side*.21,.14,.07]],.02,'#3b2822');sphere(a,[.095,.06,.042],[side*.165,-.065,.086],'#b87942');}
  sphere(a,[.037,.095,.08],[0,.015,.13],'#d0a16c');tube(a,[[-.16,-.15,.075],[-.08,-.205,.11],[.07,-.21,.11],[.16,-.14,.075]],.035,'#382821');sphere(a,[.19,.075,.078],[0,-.26,.064],'#b7834b');a.userData.face=face;return a;
 }
 function hand(g,side=1){return createVisitorHand(g,side,{mesh,mat,sphere,skin,fabric});}
 const skinCanvas=document.createElement('canvas');skinCanvas.width=skinCanvas.height=256;const skinContext=skinCanvas.getContext('2d');skinContext.fillStyle='#cfa38c';skinContext.fillRect(0,0,256,256);
 let skinSeed=981;const skinRandom=()=>{skinSeed=(skinSeed*1664525+1013904223)>>>0;return skinSeed/4294967296;};
 for(let i=0;i<2300;i++){skinContext.fillStyle=i%2?'rgba(121,65,47,.055)':'rgba(235,196,173,.075)';skinContext.beginPath();skinContext.ellipse(skinRandom()*256,skinRandom()*256,.6+skinRandom()*2,.5+skinRandom()*2,0,0,Math.PI*2);skinContext.fill();}
 const skinTx=new T.CanvasTexture(skinCanvas);skinTx.colorSpace=T.SRGBColorSpace;textures.add(skinTx);const skin=new T.MeshStandardMaterial({map:skinTx,bumpMap:skinTx,bumpScale:.00018,roughness:.72});materials.set('skin',skin);
 const foodKit={mesh,mat,cyl,sphere,tube,bowl,instances,roundedBox,foodSkin,potato};
 const food=(g,kind)=>cookedMeal(g,kind,foodKit);
 const sideDishes=g=>diningSides(g,foodKit);
 const grove=(g,trees)=>pineGrove(g,trees,{instances,bark,needles:trees.length>12?distantNeedles:needles});
 function person(parent,p,options){return visitor(parent,p,options,{mesh,mat,sphere,roundedBox,cyl,tube,hand,fabric,skin});}
 return {mat,surface:pbr,sign,mesh,instances,grove,forest,sideDishes,flower,woodDark,brick,fabric,roundedBox,scan,photo,box,sphere,cyl,tube,label,lamp,roof,table,chair,bowl,plant,pot,teapot,steam,mask,hand,food,person,floor,paving,plaster:wall,wood:woodMat,paper:paperMat,stone:stoneMat,
 dispose(){for(const g of geometries)g.dispose();for(const m of materials.values())m.dispose();for(const t of textures)t.dispose();}};
}
