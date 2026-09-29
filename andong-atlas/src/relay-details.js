import * as T from 'three';

// Reconstructed visitor spaces: proportions and circulation, never a surveyed replica.
export function enrichRelaySet(id,r,k,o){
 const g=r.group,{box,cyl,sphere,tube,label,pot,plant,table,chair,lamp,mask}=k;
 const spot=(object,action,name)=>{object.userData.action=action;object.userData.name=name;r.hotspots.push(object);return object;};
 const obstacle=(x,z,w,d)=>{(r.obstacles??=[]).push({x,z,w,d});};
 const station=(key,name,position,target)=>{(r.stations??={})[key]={name,position,target};};
 const metal=k.mat('#767e78',{metalness:.65,roughness:.36});
 const glow=k.mat('#ffd793',{emissive:'#ffd08c',emissiveIntensity:2.4});
 function poster(parent,lines,pos,w=1.2,h=1.7,bg='#ece1c7',color='#51422f'){
  const p=new T.Group();p.position.set(...pos);parent.add(p);box(p,[w+.06,h+.06,.035],[0,0,-.03],k.wood);
  box(p,[w,h,.012],[0,0,0],bg);lines.forEach((s,i)=>label(p,s,[0,h*.35-i*h*.7/Math.max(1,lines.length-1),.015],w*.84,color,bg,h*.65/lines.length));return p;
 }
 function cushion(parent,p,color='#9c5e46'){k.roundedBox(parent,[.41,.05,.4],p,k.fabric,.024);for(const x of [-.17,.17])box(parent,[.004,.007,.35],[p[0]+x,p[1]+.038,p[2]],'#d7bd91');}
 function stonePath(z0,z1){for(let z=z0;z<z1;z+=.75){box(g,[1.62,.055,.61],[Math.sin(z*2)*.05,.025,z],k.paving);}}
 function tree(x,z){k.grove(g,[{x,z,height:4.7,seed:x*7+z}]);}
 if(id==='workshop'){
  // A ceiling with visible rafters, lower timber panels and operable-looking openings.
  if(id==='workshop')for(const x of [-4.72,4.72]){
   box(g,[.08,.85,8.7],[x,.43,.05],k.wood);
   for(let z=-3.8;z<4.1;z+=.4)box(g,[.05,2.35,.026],[x,1.95,z],'#685342');
   box(g,[.1,.1,8.7],[x,.91,.05],k.wood);
  }
  if(id==='workshop')for(let x=-4.5;x<4.7;x+=.4)box(g,[.055,.07,8.7],[x,3.35,.05],k.wood);
  // Exterior is visible through the generous open entry, with a timber threshold.
  for(const x of [-3.48,3.48]){box(g,[2.6,3.4,.15],[x,1.7,4.4],k.plaster);box(g,[.2,3.4,.2],[Math.sign(x)*2.1,1.7,4.4],k.wood);}
  for(const x of [-3.48,3.48])obstacle(x,4.4,2.6,.15);
  box(g,[4.4,.25,.23],[0,3.05,4.4],k.wood);box(g,[4.3,.06,.3],[0,.01,4.4],k.wood);
  const floor=box(g,[9.5,.045,8.55],[0,.015,.1],k.floor);floor.receiveShadow=true;
  for(const z of [-4.12,4.24])box(g,[9.6,.035,.07],[0,.043,z],'#574433');
  for(const x of [-4.59,4.59])box(g,[.07,.035,8.5],[x,.043,.05],'#574433');
  if(id==='workshop')for(const x of [-2.4,2.4]){cyl(g,.12,.12,.5,[x,2.86,-1.4],glow);for(let i=0;i<10;i++)box(g,[.022,.55,.26],[x+Math.sin(i)*.1,2.86,-1.4],'#72543a');}
  r.bounds={x:[-4.4,4.4],z:[-3.5,id==='workshop'?12:5.9]};
  obstacle(0,0,id==='workshop'?2.5:1.75,id==='workshop'?1.5:1.15);
  r.camera=id==='workshop'?[0,1.7,10.8]:[0,1.7,5.4];r.target=[0,1.3,0];
  station('table',id==='workshop'?'전통 체험 작업대':'내 식탁',id==='workshop'?(o.program==='soju'?[0,1.7,2.3]:[0,1.4,1.35]):[0,1.22,.96],id==='workshop'&&o.program==='soju'?[0,1.35,0]:[0,.89,0]);
  station('door',id==='workshop'?'한옥 마당':'식당 입구',[0,1.7,id==='workshop'?9.8:5.1],[0,1.5,-1]);
  station('exit',id==='workshop'?'공방 바깥길':'식당 밖 골목',[0,1.7,id==='workshop'?11.7:5.65],[0,1.65,id==='workshop'?16:10]);
  const seat=chair(g,[0,0,id==='workshop'?1.26:.96],Math.PI);cushion(seat,[0,.52,0]);spot(seat,'station:table','의자에 앉기');
  const menu=poster(g,id==='workshop'?['이어드림 공방','탈 · 차 · 전통주','체험권은 접수대에서']:['오늘의 한 상','안동찜닭   18,000','간고등어   12,000','헛제사밥   13,000','시연 메뉴 · 예시 가격'],id==='workshop'?[-1.28,1.7,-.65]:[-1.65,1.25,-1.5],.54,.81);menu.rotation.y=.12;spot(menu,'station:table',id==='workshop'?'작업대 살펴보기':'메뉴판 보고 앉기');
  // Real service counter, separate from the dining/work table.
  const counter=new T.Group();g.add(counter);counter.position.set(3.1,0,2.45);
  box(counter,[2.45,1.06,.82],[0,.53,0],k.wood);box(counter,[2.58,.08,.93],[0,1.1,0],k.mat('#4c5149',{roughness:.3}));
  for(let x=-1.1;x<1.2;x+=.13)box(counter,[.04,.89,.02],[x,.53,.423],'#6a513b');
  label(counter,id==='workshop'?'체험 접수 · 할인권':'계산 · 영수증',[0,.74,.446],1.6,'#eee0b9','#443e31',.24);
  const terminal=new T.Group();counter.add(terminal);terminal.position.set(.55,1.14,0);box(terminal,[.29,.06,.25],[0,0,0],metal);box(terminal,[.25,.35,.035],[0,.19,-.03],'#273d36');label(terminal,'이어드림',[0,.23,-.008],.21,'#dfd4b3','#253f36',.13);label(terminal,'카드 · 현금',[0,.12,-.007],.21,'#dfd4b3','#253f36',.06);
  const paper=label(counter,o.paid?'결제 완료 · 영수증':'시연 결제 안내',[-.45,1.3,.29],.36,'#35483b','#f4efdc',.45);paper.rotation.x=-.17;
  r.refs.counter=counter;r.refs.terminal=terminal;r.refs.counterPaper=paper;
  pot(counter,[-.93,1.13,-.1],.28);spot(counter,'station:counter',id==='workshop'?'체험 접수하기':'계산대 이용하기');
  obstacle(3.1,2.45,2.5,.95);station('counter',id==='workshop'?'체험 접수대':'식당 계산대',[3,1.62,3.8],[3.1,1.15,2.4]);
  const clerk=k.person(g,[3.2,0,1.4],{coat:'#687560',apron:true});r.refs.people.push(clerk);
  poster(g,['한 끼 → 한 번의 체험','영수증 QR 인증','체험 10% 할인 제안'],[3.15,2.33,1.15],1.48,.85,'#395e4e','#e8d7ad');
  if(id==='receipt'){r.camera=[0,1.65,1.85];r.target=[3.1,1.2,2.4];}
 }
 if(id==='workshop'){
  box(g,[12,.06,9],[0,-.04,8.7],k.paving);stonePath(4.8,12.6);
  for(const x of [-5.6,5.6]){box(g,[.35,1.1,7],[x,.5,7],k.plaster);k.roof(g,.7,7.2,[x,1.02,7]);tree(x*.73,7.9);obstacle(x*.73,7.9,1,1);}
  for(const x of [-3.48,3.48]){
   box(g,[1.8,1.55,.08],[x,1.65,4.51],k.paper);
   for(let dx=-.9;dx<=.91;dx+=.225)box(g,[.028,1.6,.04],[x+dx,1.65,4.57],k.wood);
   for(let y=.85;y<=2.46;y+=.23)box(g,[1.84,.028,.04],[x,y,4.57],k.wood);
   box(g,[2.6,.18,.21],[x,.22,4.5],k.wood);
  }
  box(g,[.08,1.5,.08],[3,.75,7.8],k.wood);
  for(const x of [-4.55,-2.1,2.1,4.55]){cyl(g,.12,.15,3.25,[x,1.7,4.43],k.woodDark);cyl(g,.21,.24,.17,[x,.1,4.43],k.stone);}
  k.roof(g,10.7,9.4,[0,3.5,0]);label(g,'이 어 드 림 공 방',[0,2.84,4.63],2.3,'#ead7ad','#3b4335',.34);
  for(const x of [-2.05,2.05])lamp(g,[x,2.5,4.8],.65);
  for(let i=0;i<6;i++)pot(g,[-3.7+(i%3)*.5,0,5.4+Math.floor(i/3)*.6],.8+(i%2)*.25);
  for(const side of [-1,1]){table(g,[side*3.1,0,-1.65],1.45,1,.73);obstacle(side*3.1,-1.65,1.5,1.8);chair(g,[side*3.1,.038,-.75],Math.PI);obstacle(side*3.1,-.75,.6,.65);}
  k.scan('wooden_bowl_01',g,[2.75,.79,-1.5],.35);
  mask(g,[-3.2,.98,-1.55],.65).rotation.x=-1.1;pot(g,[3.1,.8,-1.65],.6);k.bowl(g,[3.5,.8,-1.65],.13,'#ddd3b7','#b29548');
  poster(g,['손으로 만드는 여행','01 탈에 표정 더하기','02 국화꽃 차 우리기','03 전통주 과정 체험'],[-2.2,1.83,-4.1],1.35,1.15);
  k.roundedBox(g,[1.48,.009,.87],[0,.791,.05],k.fabric,.004);
  const name={mask:'하회탈 꾸미기',tea:'국화차 우리기',soju:'전통주 과정 체험'}[o.program];box(g,[.36,.078,.025],[.45,.842,-.53],k.wood);label(g,name,[.45,.845,-.514],.32,'#4d503a','#ded0a9',.058);
  spot(label(g,'저녁 이동 · 월영교 →',[3,1.55,7.8],1.35,'#e9d7aa','#365547',.36),'station:door','마당 둘러보기');
 }
 if(id==='bridge'){
  station('pavilion','월영정까지 산책',[0,2.16,-13.8],[0,2.5,-18]);
  station('river','문보트가 보이는 난간',[1.35,1.94,1],[9,.9,-6]);
  station('shore','산책 시작점',[0,1.94,13],[0,1.8,-12]);

 }
}
