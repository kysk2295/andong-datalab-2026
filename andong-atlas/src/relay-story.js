import {MEALS,PROGRAMS} from './relay-model.js';
export const RELAY_STEPS = [
 {stage:0,label:'식사',detail:'원도심의 한 상'},
 {stage:2,label:'영수증 혜택',detail:'다음 체험 할인'},
 {stage:3,label:'전통 체험',detail:'내 손으로 만드는 안동'},
 {stage:4,label:'저녁 이동',detail:'원도심에서 월영교로'},
 {stage:5,label:'월영교·팝업',detail:'야경과 로컬 장터'},
];

export function relayStepIndex(stage){
 return Math.max(0,RELAY_STEPS.findLastIndex(step=>stage>=step.stage));
}

// A preview changes the viewed step, never the visitor's completion record.
export function relayProgress(state,viewedStage=state.stage){
 const completed=[state.eaten,state.receipt==='verified',state.completedPrograms.length>0,state.arrived,state.finished];
 return RELAY_STEPS.map((step,index)=>({...step,current:index===relayStepIndex(viewedStage),completed:completed[index]}));
}

export function relayConnection(state){
 switch(state.stage){
 case 0:case 1:return {title:'식사 → 영수증 혜택',text:state.eaten?'한 끼를 마쳤어요. 영수증을 인증해 다음 체험의 할인권을 받아보세요.':'원도심에서 먹은 한 끼가 다음 전통 체험의 혜택으로 이어집니다.'};
 case 2:return {title:'영수증 혜택 → 전통 체험',text:!state.paid?'계산을 마치고 영수증을 받아요. 이 영수증이 다음 체험의 혜택을 연결합니다.':state.coupon==='none'?'직접 QR을 맞춰보세요. 식사 영수증이 체험 10% 할인권으로 바뀝니다.':'발급받은 할인권을 체험장에서 사용하고, 내 손으로 안동의 전통을 만나세요.'};
 case 3:return state.completedPrograms.length?{title:'전통 체험 → 저녁 이동',text:'직접 만든 추억을 가지고 출발해요. 다음 목적지는 월영교의 밤입니다.'}:{title:'식사에서 받은 혜택으로 체험',text:state.coupon==='issued'?'식사 영수증으로 받은 할인권을 사용해 체험 릴레이를 이어가세요.':state.coupon==='used'?'할인권을 사용했어요. 탈·국화차·안동소주 중 원하는 체험을 직접 해보세요.':'식사 영수증을 인증하면 이곳에서 체험 할인권을 사용할 수 있어요.'};
 case 4:return {title:'저녁 이동 → 월영교·팝업',text:'원도심에서 끝날 수 있던 하루를 이동으로 연결해, 월영교의 야간 체류로 이어갑니다.'};
 case 5:return {title:'월영교 야경 → 로컬 팝업',text:'달빛 산책을 마치면 로컬 음식과 공예, 놀이가 있는 강변 장터가 이어집니다.'};
 case 6:return {title:'한 끼에서 안동의 밤까지',text:state.finished?'식사·혜택·체험·이동·팝업을 한 사람의 여행으로 모두 이었습니다.':'로컬 푸드와 공예, 투호를 즐기고 오늘의 릴레이를 완성해보세요.'};
 default:return {title:'이어드림 릴레이',text:'식사에서 체험으로, 체험에서 안동의 밤으로 이어갑니다.'};
 }
}

export function relayTasks(s){
 const tasks=[
  [['골목을 둘러보고 식당 찾기',s.ordered]],
  [['메뉴 선택·주문',s.ordered],['세 번 맛보기',s.eaten],['계산대로 이동',s.paid]],
  [['계산·영수증 수령',s.paid],['QR 정렬·인증',s.receipt==='verified'],['체험 할인권 발급',s.coupon!=='none']],
  [['할인권 사용',s.coupon==='used'],['재료·도구 직접 조작',s.craftSteps>0],['작품 완성',s.craftSteps===3]],
  [['이동 수단 선택',s.arrived],['원도심 → 월영교 이동',s.arrived]],
  [['월영정까지 산책',s.bridgeWalked],['강변 팝업으로 연결',s.finished]],
  [['음식·공예·차 부스 이용',s.cart.length>0],['투호·탈춤 장단 즐기기',s.gameAttempts>0||s.performanceScore!==null],['여행 기록 완성',s.finished]],
 ];return tasks[s.stage].map(([label,done])=>({label,done:!!done}));
}

// Read only: revisiting a scene or previewing it never creates a benefit.
export function relayCarry(s){
 const meal=MEALS[s.meal].name;
 if(s.coupon==='used'){const p=PROGRAMS[s.redeemedProgram];return {status:'used',title:`${meal} → ${p.short}`,value:`${(p.examplePrice*.1).toLocaleString('ko-KR')}원 혜택 사용`,detail:s.completedPrograms.length?'완성한 체험을 가지고 월영교의 밤으로':'식사 영수증으로 받은 10% · 체험 1회 시연'};}
 if(s.coupon==='issued')return {status:'issued',title:`${meal} 영수증에서 받은 혜택`,value:'체험 10% 할인권 1장',detail:'공방 접수대에서 원하는 체험에 사용하세요'};
 if(s.paid)return {status:'receipt',title:`${meal} 식사 영수증`,value:'인증하고 체험 혜택 받기',detail:'계산대에서 영수증 QR을 직접 맞춰보세요'};
 if(s.eaten)return {status:'meal',title:`${meal} 한 끼 완료`,value:'다음은 영수증 혜택',detail:'계산대에서 영수증을 챙기세요'};
 return null;
}
