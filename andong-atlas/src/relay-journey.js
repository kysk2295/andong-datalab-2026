// These short links represent proposed circulation, not surveyed street geometry.
export const JOURNEYS={
 workshop:{from:2,to:3,exit:'exit',title:'식당 밖, 다음 경험으로',location:'원도심 골목 → 한옥 체험 거점',night:false,legs:[
  {key:'turn',label:'골목 이정표까지 걷기',position:[0,1.7,1],target:[4,1.6,-5]},
  {key:'gate',label:'한옥 공방의 문으로 들어가기',position:[3,1.7,-8],target:[3,1.8,-12]}]},
 pickup:{from:3,to:4,exit:'exit',title:'작품을 챙겨, 저녁을 향해',location:'공방 마당 → 승차 지점',night:true,legs:[
  {key:'stop',label:'승차 안내판까지 걷기',position:[0,1.7,0],target:[2.5,1.6,-4]},
  {key:'board',label:'차량 문 앞에서 탑승하기',position:[2.3,1.7,-4.2],target:[4,1.5,-4.2]}]},
 arrival:{from:4,to:5,exit:'alight',title:'차에서 내려 강바람 속으로',location:'하차 지점 → 월영교 산책 구간',night:true,legs:[
  {key:'walkway',label:'강변 보행로로 나가기',position:[0,1.7,1],target:[0,1.7,-8]},
  {key:'bridge',label:'월영교 산책 시작하기',position:[0,1.7,-8],target:[0,1.8,-15]}]},
 riverside:{from:5,to:6,exit:'shore',title:'다리에서 강변의 장터로',location:'월영교 산책 → 강변 팝업',night:true,legs:[
  {key:'shore',label:'강변 산책로 따라 걷기',position:[0,1.7,0],target:[3,1.6,-6]},
  {key:'market',label:'팝업 장터에 들어가기',position:[3,1.7,-8],target:[3,1.8,-12]}]}
};
export function journeyFor(from,to){if(from===0&&to===3)return 'workshop';return Object.entries(JOURNEYS).find(([,j])=>j.from===from&&j.to===to)?.[0]||null;}
// Door faces the pavement after the bus turns to face the approaching lane.
export const JOURNEY_BUSES={pickup:{x:4.5,z:-8.09},arrival:{x:6,z:4.11}};
export function journeyVehicle(id,transport='shuttle'){
 const legacy=id==='pickup'?{x:4.5,z:-3.8}:{x:6,z:8};
 return transport==='taxi'?{...legacy,w:2.5,d:4.5}:{...JOURNEY_BUSES[id],w:2.6,d:10.25};
}
export function journeyLayout(id,transport='shuttle'){
 const j=JOURNEYS[id];if(!j)throw new Error('Unknown relay journey');
 return {bounds:{x:[-2.1,5.1],z:[-9.5,9]},obstacles:id==='workshop'?[{x:-1.55,z:-5,w:1.1,d:3}]:['pickup','arrival'].includes(id)&&transport!=='walk'?[journeyVehicle(id,transport)]:[],stations:Object.fromEntries(j.legs.map(leg=>[leg.key,{name:leg.label,position:leg.position,target:leg.target}]))};
}
