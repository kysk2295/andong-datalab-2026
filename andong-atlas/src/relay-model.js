import {RELAY_VISITS,validRelayVisit} from './relay-entry.js';
import {DINING_SEATS} from './relay-dining-layout.js';
export const CHAPTERS = [
  {id:'market',chapter:0,kicker:'01 · 원도심에서 시작하는 한 끼',title:'골목의 맛을 만나다',subtitle:'안동구시장의 골목을 둘러보고 식당으로 들어가세요.',location:'안동구시장 · 찜닭골목',minutes:0},
  {id:'meal',chapter:0,kicker:'01 · 식사',title:'따뜻한 한 상 앞에서',subtitle:'찜닭, 간고등어, 헛제사밥. 오늘의 한 끼를 고르고 맛보세요.',location:'원도심 식당 · 시연 공간',minutes:45},
  {id:'receipt',chapter:1,kicker:'02 · 영수증 인증',title:'한 끼가 다음 경험으로',subtitle:'식사 영수증을 스캔하면 전통 체험 할인권이 생깁니다.',location:'식당 계산대 · 인증 시연',minutes:5},
  {id:'workshop',chapter:2,kicker:'03 · 전통 체험',title:'손끝에 남는 안동',subtitle:'내 손으로 탈을 꾸미고, 차를 우리고, 전통주의 이야기를 만납니다.',location:'원도심 체험 거점 · 제안 공간',minutes:40},
  {id:'transit',chapter:2,kicker:'연결 · 저녁 이동',title:'도시의 저녁을 지나',subtitle:'원도심의 경험을 월영교의 밤으로 이어갑니다.',location:'원도심 → 월영교',minutes:20},
  {id:'bridge',chapter:3,kicker:'04 · 월영교 산책',title:'달빛이 머무는 다리',subtitle:'나무다리를 걸으며 강 위의 불빛과 월영정을 둘러보세요.',location:'월영교 · 야경 재구성',minutes:20},
  {id:'popup',chapter:3,kicker:'04 · 야간 팝업',title:'밤에도 이어지는 즐거움',subtitle:'로컬 푸드와 공예, 작은 놀이가 있는 강변 장터를 만나세요.',location:'월영교 권역 · 야간 팝업 제안',minutes:30},
];
export const MEALS = {
 jjimdak:{name:'안동찜닭',detail:'간장 양념 · 당면 · 닭고기',photo:'tour-2866691',examplePrice:18000},
 mackerel:{name:'안동간고등어',detail:'노릇하게 구운 생선과 밥',photo:null,examplePrice:12000},
 jesabap:{name:'헛제사밥',detail:'나물과 간장으로 비비는 한 상',photo:'tour-134770',examplePrice:13000},
};
export const PROGRAMS = {
 mask:{name:'하회탈 꾸미기',short:'탈 공예',tool:'붓',minutes:40,examplePrice:12000,steps:['바탕색 칠하기','볼에 색 입히기','눈썹과 표정 그리기'],description:'나무 빛깔의 탈에 세 가지 색을 더해 나만의 표정을 완성해요.',reality:'하회탈 문화와 공예체험을 참고한 시연입니다. 이 거점의 운영·요금·정원은 제안 단계입니다.'},
 tea:{name:'국화차 우리기',short:'국화차',tool:'다관',minutes:30,examplePrice:10000,steps:['국화꽃 담기','따뜻한 물 붓기','찻잔에 차 따르기'],description:'찻잎 대신 국화꽃을 담고, 노란빛이 우러난 차를 따라보세요.',reality:'안동 국화차 체험의 과거 행사 사례를 참고했습니다. 현재 상시 운영처·예약·정원은 확인되지 않았습니다.'},
 soju:{name:'안동소주 빚기',short:'전통주',tool:'소주고리',minutes:60,examplePrice:20000,steps:['쌀과 누룩 살펴보기','발효·증류 과정 살펴보기','완성된 술병에 표찰 달기'],description:'쌀과 누룩, 소주고리로 이어지는 전통주의 과정을 짧게 경험해요.',reality:'실제 민속주 안동소주 체험은 강남로 71-1, 1시간·20,000원, 최소 7일 전 예약 안내가 있습니다. 화면은 원도심 유치 제안이며 실제 예약이 아닙니다.'},
};
export const TRANSPORTS = {
 shuttle:{name:'이어드림 연결차량',minutes:20,note:'18:30–21:00 운영 구상 · 20분은 시연 가정. 운행 주체·배차·요금 미확정.'},
 taxi:{name:'택시',minutes:15,note:'15분은 시연 가정 · 실제 교통상황과 승하차 위치에 따라 달라집니다. 요금 실측 없음.'},
 walk:{name:'도보',minutes:60,note:'60분은 시연 가정 · 현장 보도와 횡단 가능 여부 확인 필요.'},
};
export const POPUP_ITEMS={
 tea:{name:'따뜻한 국화차',detail:'꽃잎을 띄운 국화차 한 잔',examplePrice:4000,edible:true},
 food:{name:'안동찜닭 컵',detail:'당면과 닭고기를 담은 따뜻한 컵',examplePrice:7000,edible:true},
 grill:{name:'간고등어 한 접시',detail:'노릇한 간고등어와 곁들임',examplePrice:6000,edible:true},
 apple:{name:'안동 사과 한 컵',detail:'먹기 좋게 준비한 사과',examplePrice:3000,edible:true},
 sikhye:{name:'안동 식혜',detail:'안동의 향토 음료 한 잔',examplePrice:4000,edible:true},
 craft:{name:'작은 탈 기념품',detail:'탈과 전통 공예품 부스',examplePrice:5000},
};
export const POPUP_STAMPS=['moon','bridge','mask'];

export function createRelayState(){return {version:1,stage:0,started:false,meal:'jjimdak',seat:'center',ordered:false,paid:false,payment:null,eaten:false,receipt:'none',scanError:false,coupon:'none',program:'mask',redeemedProgram:null,paintColor:'#c77a48',maskArt:null,craftSteps:0,craftProgress:{mask:0,tea:0,soju:0},completedPrograms:[],transport:'shuttle',arrived:false,bridgeWalked:false,cart:[],popupPayments:{},popupTasted:[],popupStamps:[],popupPhotos:0,gameScore:0,gameAttempts:0,performanceScore:null,finished:false};}
export function canEnter(s,index){
 const start=validRelayVisit(s.visit)?RELAY_VISITS[s.visit]:null;
 if(start!==null&&index===start)return true;
 if(start>=3&&index<start)return false;
 if(index===0||index===1)return true;
 if(index===2)return s.eaten;
 if(index===3)return s.coupon!=='none';
 if(index===4)return s.completedPrograms.length>0;
 if(index===5)return s.arrived;
 if(index===6)return s.bridgeWalked;
 return false;
}
export function relayReducer(s,a){
 switch(a.type){
 case 'RESET':return createRelayState();
 case 'START':return {...s,started:true};
 case 'GO':return Number.isInteger(a.index)&&canEnter(s,a.index)?{...s,stage:a.index,started:true}:s;
 case 'MEAL':return MEALS[a.id]&&!s.ordered?{...s,meal:a.id}:s;
 case 'SEAT':return s.stage===1&&!s.ordered&&Object.hasOwn(DINING_SEATS,a.id)?{...s,seat:a.id}:s;
 case 'ORDER':return s.stage===1&&!s.ordered?{...s,ordered:true}:s;
 case 'EAT':return s.stage===1&&s.ordered&&!s.eaten?{...s,eaten:true}:s;
 case 'PAY':return s.stage===2&&s.eaten&&!s.paid&&['card','cash'].includes(a.method)?{...s,paid:true,payment:a.method,receipt:'ready'}:s;
 case 'SCAN':return s.stage===2&&s.receipt==='ready'?a.valid===false?{...s,scanError:true}:{...s,receipt:'verified',scanError:false,coupon:'issued'}:s;
 case 'PROGRAM':return PROGRAMS[a.id]&&s.stage===3?{...s,program:a.id,craftSteps:s.craftProgress[a.id]}:s;
 case 'ART':return s.stage===3&&s.program==='mask'&&typeof a.image==='string'&&a.image.length<400000&&/^data:image\/png;base64,[A-Za-z0-9+/=]+$/.test(a.image)?{...s,maskArt:a.image}:s;
 case 'COLOR':return s.stage===3&&['#c77a48','#d9b661','#4a8274','#bd5b4b'].includes(a.color)?{...s,paintColor:a.color}:s;
 case 'REDEEM':return s.stage===3&&s.coupon==='issued'?{...s,coupon:'used',redeemedProgram:s.program}:s;
 case 'CRAFT':{
  if(s.stage!==3||(s.coupon!=='used'&&s.visit!=='workshop')||s.craftSteps>=3)return s;
  const craftSteps=s.craftSteps+1;return {...s,craftSteps,craftProgress:{...s.craftProgress,[s.program]:craftSteps},completedPrograms:craftSteps===3?[...new Set([...s.completedPrograms,s.program])]:s.completedPrograms};
 }
 case 'TRANSPORT':return TRANSPORTS[a.id]&&!s.arrived?{...s,transport:a.id}:s;
 case 'ARRIVE':return s.stage===4?{...s,arrived:true}:s;
 case 'WALK':return s.stage===5?{...s,bridgeWalked:true}:s;
 case 'BUY':return s.stage===6&&Object.hasOwn(POPUP_ITEMS,a.id)&&!s.cart.includes(a.id)?{...s,cart:[...s.cart,a.id],popupPayments:{...s.popupPayments,[a.id]:a.method==='cash'?'cash':'card'}}:s;
 case 'TASTE':return s.stage===6&&Object.hasOwn(POPUP_ITEMS,a.id)&&POPUP_ITEMS[a.id].edible&&s.cart.includes(a.id)&&!s.popupTasted.includes(a.id)?{...s,popupTasted:[...s.popupTasted,a.id]}:s;
 case 'STAMP':return s.stage===6&&POPUP_STAMPS.includes(a.id)&&!s.popupStamps.includes(a.id)?{...s,popupStamps:[...s.popupStamps,a.id]}:s;
 case 'PHOTO':return s.stage===6?{...s,popupPhotos:Math.min(99,s.popupPhotos+1)}:s;
 case 'THROW':return s.stage===6&&s.gameAttempts<3?{...s,gameAttempts:s.gameAttempts+1,gameScore:s.gameScore+(a.hit===true?1:0)}:s;
 case 'PERFORMANCE':return s.stage===6&&Number.isInteger(a.score)&&a.score>=0&&a.score<=4?{...s,performanceScore:a.score}:s;
 case 'FINISH':return s.stage===6&&(s.cart.length>0||s.gameAttempts>0||s.performanceScore!==null||s.popupStamps.length>0||s.popupPhotos>0)?{...s,finished:true}:s;
 default:return s;
 }
}
export function nextAction(s){
 switch(s.stage){
 case 0:return {label:'식당으로 들어가기',type:'GO',index:1,animation:'enter'};
 case 1:return !s.ordered?{label:'메뉴를 확인하고 주문하기',type:'ORDER'}:s.eaten?{label:'영수증 받으러 가기',type:'GO',index:2}:{label:`${MEALS[s.meal].name} 맛보기`,type:'EAT',animation:'eat'};
 case 2:return !s.paid?{label:'계산하고 영수증 받기',type:'PAY'}:s.coupon!=='none'?{label:'할인권 들고 체험장으로',type:'GO',index:3}:{label:s.scanError?'다시 스캔하기':'영수증 QR 스캔하기',type:'SCAN',valid:true,animation:'scan'};
 case 3:return s.coupon==='issued'?{label:'체험 10% 할인권 사용하기',type:'REDEEM',animation:'redeem'}:s.craftSteps<3?{label:PROGRAMS[s.program].steps[s.craftSteps],type:'CRAFT',animation:s.program}:{label:'월영교로 이동하기',type:'GO',index:4};
 case 4:return s.arrived?{label:'월영교 산책 시작하기',type:'GO',index:5}:{label:`${TRANSPORTS[s.transport].name} 이용하기`,type:'ARRIVE',animation:'travel'};
 case 5:return s.bridgeWalked?{label:'강변 팝업 구경하기',type:'GO',index:6}:{label:'월영정까지 걸어보기',type:'WALK',animation:'walk'};
 case 6:return {label:'오늘의 여정 마치기',type:'FINISH',disabled:!(s.cart.length||s.gameAttempts||s.performanceScore!==null||s.popupStamps.length||s.popupPhotos)};
 }
}
export function minutesAt(s){
 const programs=[...new Set([...s.completedPrograms,s.program])];
 const duration=programs.reduce((total,id)=>total+PROGRAMS[id].minutes,0);
 const times=[1020,1020,1065,1070,1070+duration,1070+duration+TRANSPORTS[s.transport].minutes,1090+duration+TRANSPORTS[s.transport].minutes];
 return times[s.stage];
}
export function clockLabel(minute){return `${String(Math.floor(minute/60)).padStart(2,'0')}:${String(minute%60).padStart(2,'0')}`;}
export function restoreRelayState(raw,visit=null){
 const initial=()=>validRelayVisit(visit)?{...createRelayState(),visit,started:true,stage:RELAY_VISITS[visit]}:createRelayState();
 try{
  const x=JSON.parse(raw);if(x.version!==1)return initial();
  // Rebuild by valid transitions. Stored data cannot create an impossible redeemed coupon.
  let s=initial();if(x.started)s=relayReducer(s,{type:'START'});
  if(MEALS[x.meal])s=relayReducer(s,{type:'MEAL',id:x.meal});
  if(x.seat&&Object.hasOwn(DINING_SEATS,x.seat)){s=relayReducer(s,{type:'GO',index:1});s=relayReducer(s,{type:'SEAT',id:x.seat});}
  if(x.ordered||x.eaten){s=relayReducer(s,{type:'GO',index:1});s=relayReducer(s,{type:'ORDER'});}
  if(x.eaten){s=relayReducer(s,{type:'EAT'});}
  if(x.paid||(!Object.hasOwn(x,'paid')&&x.eaten)){s=relayReducer(s,{type:'GO',index:2});s=relayReducer(s,{type:'PAY',method:x.payment==='cash'?'cash':'card'});}
  if(x.receipt==='verified'){s=relayReducer(s,{type:'GO',index:2});s=relayReducer(s,{type:'SCAN'});}
  if(x.coupon==='used'){s=relayReducer(s,{type:'GO',index:3});s=relayReducer(s,{type:'PROGRAM',id:x.redeemedProgram});s=relayReducer(s,{type:'REDEEM'});}
  if(s.coupon==='used'||s.visit==='workshop')for(const id of [...new Set((Array.isArray(x.completedPrograms)?x.completedPrograms:[]).filter(k=>PROGRAMS[k]))]){s=relayReducer(s,{type:'PROGRAM',id});for(let i=0;i<3;i++)s=relayReducer(s,{type:'CRAFT'});}
  if((s.coupon==='used'||s.visit==='workshop')&&x.craftProgress)for(const id of Object.keys(PROGRAMS)){if(s.completedPrograms.includes(id))continue;s=relayReducer(s,{type:'PROGRAM',id});for(let i=0;i<Math.min(2,Math.max(0,Number(x.craftProgress[id])||0));i++)s=relayReducer(s,{type:'CRAFT'});}
  if(PROGRAMS[x.program]&&(s.coupon!=='none'||s.visit==='workshop')){s=relayReducer(s,{type:'GO',index:3});s=relayReducer(s,{type:'PROGRAM',id:x.program});s=relayReducer(s,{type:'COLOR',color:x.paintColor});if(!x.craftProgress&&!s.completedPrograms.includes(x.program))for(let i=0;i<Math.min(2,Math.max(0,Number(x.craftSteps)||0));i++)s=relayReducer(s,{type:'CRAFT'});}
  if(x.maskArt&&(s.coupon==='used'||s.visit==='workshop')){const selected=s.program;s=relayReducer(s,{type:'PROGRAM',id:'mask'});s=relayReducer(s,{type:'ART',image:x.maskArt});s=relayReducer(s,{type:'PROGRAM',id:selected});}
  s=relayReducer(s,{type:'TRANSPORT',id:x.transport});
  if(x.arrived){s=relayReducer(s,{type:'GO',index:4});s=relayReducer(s,{type:'ARRIVE'});}
  if(x.bridgeWalked){s=relayReducer(s,{type:'GO',index:5});s=relayReducer(s,{type:'WALK'});}
  if(s.bridgeWalked){s=relayReducer(s,{type:'GO',index:6});for(const id of Array.isArray(x.cart)?x.cart:[])s=relayReducer(s,{type:'BUY',id,method:x.popupPayments?.[id]});for(let i=0;i<Math.min(3,Math.max(0,Number(x.gameAttempts)||0));i++)s=relayReducer(s,{type:'THROW',hit:i<Math.min(3,Number(x.gameScore)||0)});if(Number.isInteger(x.performanceScore))s=relayReducer(s,{type:'PERFORMANCE',score:x.performanceScore});s=restorePopupActivities(s,x);if(x.finished)s=relayReducer(s,{type:'FINISH'});}
  if(!x.started&& !x.eaten&&!validRelayVisit(visit))return initial();
  const restored=relayReducer(s,{type:'GO',index:Number.isInteger(x.stage)?x.stage:0});return x.finished?relayReducer(restored,{type:'FINISH'}):restored;
 }catch{return initial();}
}

export function restorePopupActivities(s,x){
 for(const id of Array.isArray(x.popupTasted)?x.popupTasted:[])s=relayReducer(s,{type:'TASTE',id});
 for(const id of Array.isArray(x.popupStamps)?x.popupStamps:[])s=relayReducer(s,{type:'STAMP',id});
 const photos=Number.isInteger(x.popupPhotos)?Math.max(0,Math.min(99,x.popupPhotos)):0;
 for(let i=0;i<photos;i++)s=relayReducer(s,{type:'PHOTO'});
 return s;
}
