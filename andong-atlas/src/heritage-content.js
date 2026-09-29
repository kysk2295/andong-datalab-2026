const seowon='https://contents.history.go.kr/play/view.do?levelId=tt_b75';
const dosan='https://www.andong.go.kr/dosanseowon/contents.do?mId=0104000000';
const temple='https://www.kh.or.kr/visit/kor/road/4/view.do?key=2408220004';
const descriptions={
  'dosan:농운정사':['퇴계 이황의 제자들이 머물며 학문을 닦던 공간입니다. 도산서당 옆에 놓인 건물과 마당의 구성을 살펴보세요.',dosan],
  'dosan:진도문':['도산서당과 농운정사 사이에서 위쪽 서원 영역으로 이어지는 문입니다. 아래쪽 서당과 위쪽 강학 공간의 배치를 살펴보세요.',dosan],
  'dosan:전교당':['서원의 강학 공간입니다. 앞마당과 동재·서재의 관계를 함께 살펴볼 수 있습니다.',dosan],
  'dosan:광명실':['책을 보관하는 서고입니다. 진도문 양옆에 자리하며, 습기를 피하도록 바닥을 높였습니다.',dosan],
  'dosan:동재':['유생들이 머물던 공간입니다. 마당 건너편의 서재와 마주하는 배치를 살펴보세요.',dosan],
  'dosan:옥진각':['퇴계 이황의 유물을 소개하는 전시 공간입니다. 실제 전시·개방 상태는 현장 안내를 확인하세요.',dosan],
  'byeongsan:입교당':['서원의 강학 공간입니다. 동재·서재와 마주하는 마당과 만대루를 함께 살펴보세요.',seowon],
  'byeongsan:동재':['유생들이 머물던 공간입니다. 입교당 양옆의 동재·서재 배치를 지도에서 비교할 수 있습니다.',seowon],
  'byeongsan:서재':['유생들이 머물던 공간입니다. 입교당 양옆의 동재·서재 배치를 지도에서 비교할 수 있습니다.',seowon],
  'byeongsan:존덕사':['서원의 제향 공간입니다. 강학 공간보다 뒤쪽에 놓인 배치를 살펴보세요.',seowon],
  'byeongsan:만대루':['마당과 낙동강 쪽 풍경 사이에 놓인 누각입니다. 만대루를 지나 입교당과 동재·서재가 이어집니다.',seowon],
  'dosan:도산서당':['퇴계 이황이 학문을 닦고 유생을 가르치던 곳입니다. 주변의 서원 건물과 함께 위치를 살펴보세요.',dosan],
  'bongjeong:극락전':['봉정사의 극락전과 대웅전은 각각 마당을 갖춘 영역을 이룹니다. 두 영역의 배치와 목조 건축의 외관을 비교해 보세요.',temple],
  'bongjeong:대웅전':['봉정사의 대웅전과 극락전은 각각 마당을 갖춘 영역을 이룹니다. 옆 마당으로 이어지는 공간 구성을 지도에서 살펴보세요.',temple],
};
export function heritageDescription(region,name){const value=descriptions[`${region}:${name}`];return value?{description:value[0],descriptionSource:value[1]}:{};}
