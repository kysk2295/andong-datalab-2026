import * as T from 'three';

// Adult proportions, shaped clothing and articulated hands instead of block bodies.
export function visitor(parent,p,{coat='#54766a',rotation=0,apron=false,seated=false,cooking=false}={},k){
 const a=new T.Group();parent.add(a);a.position.set(...p);a.rotation.y=rotation;
 const skin=k.skin||k.mat('#c69980',{roughness:.72}),cloth=k.mat(coat,{roughness:.95}),trousers=k.mat('#303a38',{roughness:.98}),hair=k.mat('#252724',{roughness:.92});
 const limb=(points,radii,material,parent=a)=>{
  const curve=new T.CatmullRomCurve3(points.map(p=>new T.Vector3(...p))),geo=new T.TubeGeometry(curve,24,1,20,false),pos=geo.attributes.position;
  for(let row=0;row<=24;row++){const t=row/24,center=curve.getPointAt(t),half=t<.5?0:1,u=t<.5?t*2:t*2-1,r=T.MathUtils.lerp(radii[half],radii[half+1],u);
   const fold=1+.028*Math.sin(t*70)*Math.exp(-(((t-.55)/.18)**2));
   for(let col=0;col<=20;col++){const i=row*21+col,p=new T.Vector3().fromBufferAttribute(pos,i).sub(center).multiplyScalar(r*fold).add(center);pos.setXYZ(i,p.x,p.y,p.z);}}
  geo.computeVertexNormals();return k.mesh(parent,geo,material);
 };
 const seatedDrop=seated?-.36:0;
 a.userData.arms=[];a.userData.cooking=cooking;
 for(const side of [-1,1]){
  const hip=[side*.09,.86+seatedDrop,0],knee=seated?[side*.11,.46,.36]:[side*.105,.46,.015],ankle=seated?[side*.11,.1,.4]:[side*.11,.105,.01];
  limb([hip,knee,ankle],[.083,.064,.049],trousers);
  k.roundedBox(a,[.13,.066,.25],[ankle[0],.055,ankle[2]+.046],k.mat('#252a29',{roughness:.48}),.03);
  k.roundedBox(a,[.136,.015,.26],[ankle[0],.027,ankle[2]+.046],'#171e1d',.008);
  const arm=new T.Group();arm.position.set(side*.205,1.37+seatedDrop,0);a.add(arm);a.userData.arms.push(arm);
  const elbow=cooking?[side*.055,-.22,.12]:[side*.055,-.25,.025],wrist=cooking?[side*.075,-.31,.43]:[side*.075,-.47,.065];
  limb([[0,0,0],elbow,wrist],[.069,.054,.041],cloth,arm);
  const hand=k.hand(arm,side);hand.userData.sleeve.visible=false;hand.scale.setScalar(.75);hand.position.fromArray(wrist);hand.rotation.z=Math.PI;hand.rotation.x=cooking?-1.1:.15;
  if(cooking&&side===1){k.tube(arm,[[wrist[0],wrist[1]-.04,wrist[2]],[wrist[0],wrist[1]-.3,wrist[2]+.19]],.008,k.mat('#92978e',{metalness:.8,roughness:.3}));k.sphere(arm,[.044,.012,.052],[wrist[0],wrist[1]-.3,wrist[2]+.19],'#686e65');}
  k.tube(a,[[side*.08,.78+seatedDrop,.055],[side*.12,seated?.46:.55,seated?.37:.07],[side*.11,.3,seated?.39:.056]],.003,k.mat('#69716a',{roughness:1}));
 }
 const profile=[[.12,.8],[.17,.85],[.165,1],[.17,1.17],[.205,1.32],[.195,1.39],[.08,1.44]].map(([r,y])=>new T.Vector2(r,y+seatedDrop));
 const torso=k.mesh(a,new T.LatheGeometry(profile,48),cloth);torso.scale.z=.61;a.userData.torso=torso;
 k.cyl(a,.052,.06,.11,[0,1.465+seatedDrop,0],skin,32);
 const head=new T.Group();a.add(head);head.position.set(0,1.615+seatedDrop,.007);a.userData.head=head;
 const geo=new T.SphereGeometry(1,40,28),v=geo.attributes.position;
 for(let i=0;i<v.count;i++){const x=v.getX(i),y=v.getY(i),z=v.getZ(i),jaw=y<-.25?.9+(y+.25)*.11:1;v.setXYZ(i,x*.099*jaw,y*.133,z*.09+(z>0?.011*Math.exp(-(((y+.04)*3)**2)):0));}geo.computeVertexNormals();k.mesh(head,geo,skin);
 const cap=k.mesh(head,new T.SphereGeometry(1,32,20,0,Math.PI*2,0,Math.PI*.47),hair,[0,.044,-.008]);cap.scale.set(.102,.098,.092);cap.rotation.x=-.18;
 for(const side of [-1,1]){
  k.sphere(head,[.012,.025,.014],[side*.099,-.005,-.003],skin);
  k.sphere(head,[.024,.017,.012],[side*.051,.003,.079],skin);
  k.sphere(head,[.014,.005,.008],[side*.035,.023,.088],'#ddd4c2');k.sphere(head,[.0045,.0045,.003],[side*.035,.023,.096],'#322d24');
  k.tube(head,[[side*.021,.041,.087],[side*.04,.044,.087],[side*.054,.039,.081]],.0038,hair);
  k.sphere(head,[.008,.019,.02],[side*.009,-.013,.09],skin);
  for(let i=0;i<5;i++)k.tube(head,[[side*.095,.029-i*.009,-.025],[side*.098,.015-i*.009,0],[side*.087,-.006-i*.007,.025]],.004,hair);
 }
 k.sphere(head,[.012,.022,.022],[0,-.009,.098],skin);
 k.tube(head,[[-.021,-.05,.081],[0,-.052,.088],[.021,-.05,.081]],.0027,'#805348');
 k.sphere(head,[.033,.022,.01],[0,-.078,.072],skin);
 // Collar, seams, buttons and an apron that follows the torso.
 for(const side of [-1,1]){const collar=k.roundedBox(a,[.072,.087,.018],[side*.045,1.409+seatedDrop,.063],cloth,.008);collar.rotation.z=side*-.35;}
 for(let i=0;i<5;i++)k.sphere(a,.005,[0,1.33+seatedDrop-i*.085,.108],'#c2c0ac');
 if(apron&&!seated){const pts=[[-.135,.85],[-.15,1.16],[-.09,1.33],[.09,1.33],[.15,1.16],[.135,.85]].map(p=>new T.Vector2(...p)),shape=new T.Shape(pts),panel=k.mesh(a,new T.ShapeGeometry(shape,16),k.fabric,[0,0,.129]);panel.material.side=T.DoubleSide;
  k.roundedBox(a,[.17,.1,.012],[0,1.02,.143],k.fabric,.01);for(const side of [-1,1])k.tube(a,[[side*.078,1.3,.137],[side*.09,1.42,.085],[side*.07,1.45,-.03]],.008,'#ab9579');
 }
 return a;
}
