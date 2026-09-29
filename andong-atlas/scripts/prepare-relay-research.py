"""Build the immersive proposal's source register without altering report values."""
from pathlib import Path
import json,math
root=Path(__file__).resolve().parents[1]
def src(id,title,url,facts,date='2026-09-29',status='공식 안내 확인'):
 return dict(id=id,title=title,url=url,checkedAt=date,status=status,facts=facts)
sources=[
src('market','안동관광 · 찜닭골목','https://new.tourandong.com/public/sub1/sub7.cshtml',['안동구시장에 찜닭골목이 모여 있습니다.','골목·외관은 공간 연출의 참고입니다. 개별 업소 실내 도면은 확보하지 못했습니다.']),
src('restaurant','한국관광공사 · 중앙찜닭','https://chinese.visitkorea.or.kr/svc/whereToGo/locIntrdn/rgnContentsView.do?vcontsId=215200',['번영1길 51 · 09:00–20:30 · 연중무휴 안내','054-855-7272 · 현재 메뉴판 가격·평균 대기·주차 요금은 미확인','시연 식당과 실제 업소의 이어드림 참여는 별개입니다.']),
src('craft','안동관광 · 안동공예문화전시관','https://www.tourandong.com/map/resource.cshtml?seq=372',['석주로 245 · 09:00–18:00 · 054-843-5531','도자기·섬유·목공·금속·한지 공예를 전시·판매하고 체험하는 공간입니다.','월요일·1월 1일·설과 추석 전후 휴관 안내. 단체는 10인 이상, 일주일 전 연락 안내가 있습니다.', '공식 게시 예시: 우드아트 6,000–15,000원, 한지공예 5,000원부터. 화면의 하회탈 제안 체험 가격과는 다릅니다.', '주차: 전시관 앞 대형버스 약 8대·자가용 약 80대 안내. 현재 자리·주차요금·회차 정원은 미확인.']),
src('mask','안동관광 · 하회세계탈박물관','https://www.tourandong.com/map/resource.cshtml?seq=1254',['하회마을 입구의 탈 전문 박물관으로 한국과 세계의 탈을 소개합니다.','원도심 하회탈 꾸미기는 이 전통을 참고한 제안 프로그램입니다. 실제 박물관 체험 요금·정원·운영일로 사용하지 않습니다.']),
src('soju','찾아가는 양조장 · 민속주 안동소주','https://thesooltourism.com/brewery/list/detail.do?seq=B0000142',['전통방식 제조 체험 및 시설 견학: 1시간, 20,000원 안내','누룩·밑술·소주고리 증류 과정을 체험합니다.','강남로 71-1 · 사전예약, 최소 7일 전 예약 안내 · 회차 정원 미확인','원도심 유치·10% 할인은 이어드림 제안이며 현재 양조장의 확정 혜택이 아닙니다.']),
src('museum','안동관광 · 안동소주박물관','https://www.tourandong.com/map/resource.cshtml?seq=51',['강남로 71-1 · 09:00–18:00 · 박물관 입장 무료','체험 요금과 박물관 입장료는 다릅니다. 전통음식·양조 도구·제조과정 전시를 참고했습니다.']),
src('tea','정책브리핑 · 2016 가을여행주간','https://www.korea.kr/news/policyNewsView.do?newsId=148823004',['안동 국화차·다식 체험과 전통문화 프로그램의 과거 행사 사례를 확인했습니다.','현재 상시 운영처·요금·회차 정원·예약 시스템은 확인되지 않았습니다.'],status='과거 행사 사례 · 현재 운영 아님'),
src('specialty','안동시 · 특산물 소개','https://www.andong.go.kr/portal/contents.do?mId=0306010000',['안동소주·하회탈·안동포 등 지역 특산물 소개를 연출에 참고했습니다.']),
src('bridge','안동관광 · 월영교','https://new.tourandong.com/public/',['월영교는 이응태 부부의 이야기를 기리는 목교입니다.','정자·수면·목재 난간을 재구성했습니다. 현장 실측 모형은 아닙니다.','최신 분수 가동시각과 야간 점등 종료시각은 확정하지 않았습니다. 화면의 분수는 연출입니다.']),
src('boats','안동관광 · 개목나루 체험 안내','https://www.tourandong.com/map/resource.cshtml?seq=1544',['민속촌길 26 · 문의 054-823-0716 · 안동민속박물관 주차장 이용 안내', '공식 게시 체험 시간: 황포돛배 20분, 문보트 30분', '게시 영업시간: 평일 10:00–22:00, 토요일 11:00–23:00, 일요일 10:00–23:00', '당일 기상·계절별 운항 중단, 마지막 탑승, 최신 요금은 운영처 확인이 필요합니다. 영업시간이 당일 운항을 보장하지 않습니다.']),
src('festival','안동국제탈춤페스티벌 · 축제발자취','https://maskdance.com/2024/sub1/sub4.asp',['2026 개최기간: 9월 24일–10월 4일, 11일간','축제의 탈·공연·체험 분위기를 참고합니다. 월영교 팝업의 확정 운영 일정이나 부스 배치가 아닙니다.']),
src('night','안동관광 · 2019 월영야행 안내','https://webzine.tourandong.com/webzine_2016/2019-07/%EC%9B%94%EC%98%81%EC%95%BC%ED%96%89.pdf',['과거 다례·공예·공연·월영마켓 구성은 야간 팝업 기획의 참고 사례입니다.','현재 팝업 부지·부스 수·판매가·결제 수단·주민증 중복할인은 미확정입니다.'],status='2019 행사 사례 · 제안 연출 참고'),
src('transport','안동시 버스정보시스템 · 시간표','https://bus.andong.go.kr/timetable',['112번 교보생명 기점 출발표: 17:55, 18:45 (수집 자료)','반대 방향 리첼호텔건너 기점 출발표: 18:25, 19:00 (수집 자료)','기점 출발시각은 월영교 정류장 승차시각이 아닙니다. 실시간 도착·운행일 적용은 공식 BIS에서 확인하세요.']),
src('parking','안동관광 · 교통 안내','https://www.tourandong.com/public/sub5/sub1_2.cshtml',['원도심·월영교 이동은 대중교통·택시·도보를 구분합니다.','이 화면의 연결차량은 18:30–21:00 운영 제안입니다. 배차·요금·차량 수는 미확정입니다.','식당 대기시간·구간별 택시비·주차요금의 현장 실측 자료는 없습니다.']),
]
solution=json.loads((root/'public/data/solution.json').read_text());route=solution['route']
def dist(a,b):
 r=math.pi/180;dy=(b[1]-a[1])*r;dx=(b[0]-a[0])*r;v=math.sin(dy/2)**2+math.cos(a[1]*r)*math.cos(b[1]*r)*math.sin(dx/2)**2;return 6371000*2*math.atan2(math.sqrt(v),math.sqrt(1-v))
distance=sum(dist(a,b) for a,b in zip(route,route[1:]))
content=dict(version=1,checkedAt='2026-09-29',sources=sources,route=dict(coordinates=route,distanceMeters=round(distance),source=solution.get('routeNote','공개 도로망 기반 설명 경로'),kind='제안 거점 간 설명 경로 · 실제 버스 노선 아님'),chapters={
'market':['market','restaurant'],'meal':['restaurant','specialty'],'receipt':['restaurant'],'workshop':['craft','mask','soju','museum','tea'],'transit':['transport','parking'],'bridge':['bridge','boats'],'popup':['festival','night','specialty']},unknowns=['실제 식당 실내 도면·좌석 배치','메뉴 최신 가격·평균 대기·피크타임','체험 거점의 참여 업체·시간·회차 정원','국화차 상시 운영처·예약·휴무','영수증 제휴 규격·할인 중복·유효기간','현재 월영교 분수·점등 시간','문보트·황포돛배 최신 운항·요금','택시비·주차장 요금 현장 실측','팝업 부지·운영 주체·상품 가격·결제 수단'])
(root/'public/data/relay-research.json').write_text(json.dumps(content,ensure_ascii=False,indent=2)+'\n')
print(len(sources),'sources; route',round(distance),'m')
