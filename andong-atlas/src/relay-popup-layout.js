// A proposed festival plan, in metres. Rendering, walking and the site map share it.
export const POPUP_BOOTHS=[
 {id:'food',name:'찜닭 키친',x:-11,z:5,action:'buy-food',kind:'kitchen',color:'#8b5040'},
 {id:'grill',name:'간고등어 그릴',x:-17,z:5,action:'buy-grill',kind:'kitchen',color:'#425963'},
 {id:'apple',name:'안동 사과상회',x:-23,z:5,action:'buy-apple',kind:'market',color:'#a47843'},
 {id:'craft',name:'탈과 공예',x:-19,z:-9,action:'buy-craft',kind:'tent',color:'#c0ae91'},
 {id:'print',name:'달빛 엽서 공방',x:-25,z:-9,action:'stamp',kind:'tent',color:'#7c8d78'},
 {id:'tea',name:'월영차회',x:14,z:-9,action:'buy-tea',kind:'tent',color:'#819080'},
 {id:'sikhye',name:'안동 식혜당',x:21,z:-9,action:'buy-sikhye',kind:'market',color:'#ad9479'},
 {id:'game',name:'투호 놀이터',x:18,z:5,action:'game',kind:'tent',color:'#737c94'},
 {id:'guide',name:'밤마당 안내소',x:9,z:17,action:'popup-map',kind:'tent',color:'#a89776'},
];
export const POPUP_STAGE={x:0,z:-13,w:10,d:5.6};
export const POPUP_TABLES=[[-10,11],[-16,11],[-22,11],[-10,16],[-16,16],[-22,16],[13,-2],[21,-2]];
export const POPUP_BENCHES=[[-6,-4],[0,-4],[6,-4],[-6,-7],[0,-7],[6,-7],[-17,-19],[-9,-19],[16,-19],[24,-19]];
export const POPUP_ZONES=[
 {id:'food',name:'먹거리 마당',subtitle:'찜닭 · 간고등어 · 사과',x:-17,z:11,color:'#c38a58'},
 {id:'craft',name:'공예 골목',subtitle:'탈 공예 · 엽서 도장',x:-22,z:-5,color:'#aaa273'},
 {id:'performance',name:'달빛 무대',subtitle:'탈춤 장단 · 야외 관람',x:0,z:-5,color:'#b49bc1'},
 {id:'tea',name:'강변 찻자리',subtitle:'국화차 · 안동 식혜',x:18,z:-3,color:'#7ea594'},
 {id:'game',name:'놀이 마당',subtitle:'직접 조준하는 투호',x:18,z:10,color:'#829ebb'},
 {id:'photo',name:'수변 전망대',subtitle:'월영교 야경 · 사진',x:26,z:-20,color:'#87b7bc'},
];
export const POPUP_TUHO={x:18,z:7.6};
export function popupLayout(){return {
 bounds:{x:[-31,31],z:[-22,22]},
 obstacles:[
  ...POPUP_BOOTHS.map(b=>({x:b.x,z:b.z,w:4.5,d:3.3})),
  ...POPUP_TABLES.map(([x,z])=>({x,z,w:2.6,d:2.4})),
  ...POPUP_BENCHES.map(([x,z])=>({x,z,w:2.5,d:.55})),
  {...POPUP_STAGE}, {x:POPUP_TUHO.x,z:POPUP_TUHO.z,w:.65,d:.65},
  {x:-27,z:-16,w:5,d:.7},{x:27,z:-16,w:3,d:1},
  ...[-5,5].map(x=>({x,z:21,w:.45,d:.45})),
 ],
 stations:{
  ...Object.fromEntries(POPUP_BOOTHS.map(b=>[b.id,{name:b.name,position:[b.x,1.7,b.id==='game'?10.2:b.z+3],target:[b.x,b.id==='game'?.62:.85,b.id==='game'?POPUP_TUHO.z:b.z+1.55]}])),
  performance:{name:'달빛 무대 앞',position:[0,1.7,-8.4],target:[0,1.8,-13]},
  gallery:{name:'하회탈 야외 전시',position:[-27,1.7,-13.7],target:[-27,1.5,-16]},
  photo:{name:'월영교 야경 전망대',position:[26,1.7,-21],target:[8,2,-37]},
  picnic:{name:'먹거리 마당 쉼터',position:[-13,1.7,13.8],target:[-17,1.2,5]},
  river:{name:'강변 산책',position:[10,1.7,-20.5],target:[0,2,-36]},
  entrance:{name:'밤마당 입구',position:[-5.8,1.7,18.7],target:[-16,1.75,5]},
 }
};}
export function popupMapPoint(x,z){return {x:(x+31)/62*100,y:(z+22)/44*100};}

export function popupZoneAt(x,z){
 if(z < -17)return '수변 전망대';
 if(z>17&&x>-7&&x<11)return '밤마당 입구';
 const near=POPUP_ZONES.reduce((a,b)=>Math.hypot(x-a.x,z-a.z)<Math.hypot(x-b.x,z-b.z)?a:b);
 return near.name;
}
