const dosan = {
  provider:'안동시 도산서원',checkedAt:'2026-09-29',
  hours:'2–10월 09:00–18:00 (입장 17:30까지) · 11–1월 09:00–17:00 (입장 16:30까지)',
  price:'성인 2,000원 · 청소년·어린이 1,000원. 할인·면제 조건은 공식 안내 확인',
  phone:'054-856-1073',address:'경상북도 안동시 도산면 도산서원길 154',
  source:'https://www.andong.go.kr/dosanseowon/contents.do?mId=0502000000',
  vr:{title:'도산서원 공식 실사 VR',url:'https://my.matterport.com/show/?m=1wW24pkKSh3',source:'https://www.andong.go.kr/dosanseowon/contents.do?mId=0403000000',provider:'안동시 도산서원 · Matterport'},
};
const bongjeong = {
  provider:'국가유산진흥원 방문 캠페인',checkedAt:'2026-09-29',
  hours:'5–9월 09:00–19:00 · 10–4월 09:00–18:00',price:'관람료 무료',phone:'054-853-4181',
  address:'경상북도 안동시 서후면 봉정사길 222',
  source:'https://www.kh.or.kr/visit/kor/road/4/view.do?key=2408220004',
};
export function heritageVisit(place){
  if(place?.proposed)return null;
  const region=place?.region||place?.id?.split(':')[0];
  return ({dosan,bongjeong})[region]||null;
}
