# -*- coding: utf-8 -*-
from pathlib import Path
import datetime as dt
import json
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
print('imports ok')

ROOT = Path('/Users/koyunseo/한국관광데이터분석')
RAW = ROOT / 'data/external/작업목록_2-3_수집_20260921'
OUT = ROOT / '조사'
TODAY = dt.date(2026, 9, 21)
FONT = Font(name='Arial', size=10)
BOLD = Font(name='Arial', size=10, bold=True)
LINK = Font(name='Arial', size=10, color='0563C1', underline='single')
HEAD_FILL = PatternFill('solid', fgColor='D9D9D9')
WRAP = Alignment(wrap_text=True, vertical='top')
print('setup', RAW.exists(), OUT.exists())


def write_table(ws, header, rows, widths=None, link_cols=(), date_cols=(), num_cols=None):
    ws.append(header)
    for c in ws[1]:
        c.font, c.fill, c.alignment = BOLD, HEAD_FILL, Alignment(wrap_text=True, vertical='center')
    for r in rows:
        ws.append(list(r))
    idx = {h: i + 1 for i, h in enumerate(header)}
    num_cols = num_cols or {}
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for c in row:
            c.font, c.alignment = FONT, WRAP
    for name in link_cols:
        col = idx[name]
        for r in range(2, ws.max_row + 1):
            c = ws.cell(r, col)
            if isinstance(c.value, str) and c.value.startswith('http'):
                c.hyperlink, c.font = c.value, LINK
    for name in date_cols:
        for r in range(2, ws.max_row + 1):
            ws.cell(r, idx[name]).number_format = 'yyyy-mm-dd'
    for name, fmt in num_cols.items():
        for r in range(2, ws.max_row + 1):
            ws.cell(r, idx[name]).number_format = fmt
    if widths:
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = f'A1:{get_column_letter(len(header))}{ws.max_row}'
    return idx

def notes_sheet(wb, lines):
    ws = wb.create_sheet('출처·메모')
    ws.append(['구분', '내용'])
    for c in ws[1]:
        c.font, c.fill = BOLD, HEAD_FILL
    for k, v in lines:
        ws.append([k, v])
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font, c.alignment = FONT, WRAP
    ws.column_dimensions['A'].width = 22
    ws.column_dimensions['B'].width = 120
    return ws
print('helpers ok')

REGION_COLOR = {
    '강원특별자치도': '강원(파랑)', '경기도': '경인(빨강)', '인천광역시': '경인(빨강)',
    '충청남도': '충청(보라)', '충청북도': '충청(보라)', '전북특별자치도': '호남(초록)',
    '전남광주통합특별시': '호남(초록)', '전라남도': '호남(초록)', '경상북도': '영남(주황)',
    '부산광역시': '영남(주황)', '경상남도': '영남(주황)',
}
DISPLAY = {('26','26170'): '부산광역시 동구', ('26','26140'): '부산광역시 서구', ('26','26200'): '부산광역시 영도구'}
BENEFIT_MODE = '단순할인(가맹점 QR·쿠폰). 단계형 공식 표기 없음'
SRC_MAIN = 'https://korean.visitkorea.or.kr/dgtourcard/'
SRC_ANDONG = 'https://korean.visitkorea.or.kr/dgtourcard/biz/regn/regnMain.do?mtpcDoCd=47&signguCd=47170'
START_TXT = '못 찾음 — 공식 지역 페이지·서비스소개에 지자체별 개시일 칸 없음. 화면 확인: 공지 신규 참여지역 8곳 오픈(2026-06-02) 이미지에 전국 52개 지역 / 신규 참여 지역 6월 8일 OPEN만 보임. 8곳 개별 이름은 이미지 하단이라 이 조사에서 글자를 확정하지 않음'
ISSUE_TXT = '못 찾음 — 공식 사이트 비로그인 화면에 지자체별 발급 건수 없음(로그인 또는 정보공개 필요)'

def load(rel):
    return json.loads((RAW/rel).read_text(encoding='utf-8'))

def build_02():
    regs = load('02_주민증/참여지역_원자료.json')
    counts = {x['시군코드']: x for x in load('02_주민증/지자체별_혜택업체수.json')}
    merchants = load('02_주민증/안동_가맹점목록.json')
    notices = load('02_주민증/공지목록.json')
    wb = Workbook(); ws = wb.active; ws.title = '운영지자체'
    rows=[]
    for r in regs:
        code=r['signguCd']
        name=DISPLAY.get((r['mtpcDoCd'], code), r['lgovNm'])
        cnt=counts.get(code, {}).get('혜택업체수')
        sido=r['mtpcDoCdFullNm']
        url=f"https://korean.visitkorea.or.kr/dgtourcard/biz/regn/regnMain.do?mtpcDoCd={r['mtpcDoCd']}&signguCd={code}"
        note='안동 혜택업체 27곳 = 공식 API totCnt 27 = R1 회신 27곳(2026-09-17 활성). 발급 건수는 공식 화면에 없음' if r['lgovNm']=='안동시' else ''
        rows.append([name, START_TXT, BENEFIT_MODE, ISSUE_TXT, cnt, r['mtpcDoCd'], code, sido, REGION_COLOR.get(sido,''), url, '화면 확인(목록 API 2026-09-21)', TODAY, note])
    write_table(ws, ['지자체명','시작 시기','혜택 방식(단순할인/단계형)','발급 건수','혜택업체 수','시도코드','시군코드','시도','지도권역(화면)','출처 URL','게시일','조사일','비고'], rows, widths=[22,42,30,30,12,10,10,18,14,54,24,12,40], link_cols=['출처 URL'], date_cols=['조사일'], num_cols={'혜택업체 수':'#,##0'})
    n=ws.max_row
    ws.cell(n+2,1,'합계(혜택업체 수)'); ws.cell(n+2,5,f'=SUM(E2:E{n})'); ws.cell(n+2,5).number_format='#,##0'
    ws.cell(n+3,1,'지자체 수'); ws.cell(n+3,5,f'=COUNTA(A2:A{n})')
    mws=wb.create_sheet('안동_혜택업체27'); mrows=[]
    for x in merchants:
        mrows.append([x.get('mbrbNm'), x.get('mbrbBnefClCdNm'), x.get('bnefCn') or x.get('svcCn') or '명시 없음', x.get('utztCnt') if x.get('utztCnt') is not None else '명시 없음', x.get('mbrbIntroWordsCn') or '', SRC_ANDONG, '화면 확인(가맹점 API 2026-09-21)', TODAY, 'utztCnt는 공식 목록의 이용 표시값. 정의(할인건/QR건)는 문서에 없음'])
    write_table(mws, ['혜택업체명','공식분류','혜택 내용','목록 이용표시(utztCnt)','소개문구','출처 URL','게시일','조사일','비고'], mrows, widths=[28,10,50,18,40,54,28,12,40], link_cols=['출처 URL'], date_cols=['조사일'])
    mn=mws.max_row; mws.cell(mn+2,1,'행 수'); mws.cell(mn+2,2,f'=COUNTA(A2:A{mn})')
    nws=wb.create_sheet('공식공지_참여확대'); nrows=[]
    for ntc in notices:
        title=ntc['notcTtlNm']
        if not any(k in title for k in ['참여','오픈','풍성','발급','반값']): continue
        url=f"https://korean.visitkorea.or.kr/dgtourcard/biz/notc/notcDetail.do?notcId={ntc['notcId']}"
        extra=''
        if '8곳 오픈' in title: extra='화면 확인: 이미지 문구 전국 52개 지역으로 확대 / 신규 참여 지역 6월 8일 OPEN. 8곳 개별 지자체명은 이미지 하단이라 이 표에 옮기지 않음(추정 금지)'
        if title.startswith('임시'): extra='임시 발급 서비스 안내. 지자체 목록·발급 건수는 본문에 숫자로 없음'
        nrows.append([ntc['rn'], title, ntc['regDtDisp'].replace(' ',''), extra, url, ntc['regDtDisp'].replace(' ',''), TODAY])
    write_table(nws, ['공지번호','제목','게시일(화면)','화면에서 읽은 내용','출처 URL','게시일','조사일'], nrows, widths=[10,46,14,70,54,14,12], link_cols=['출처 URL'], date_cols=['조사일'])
    notes_sheet(wb, [
        ('작업 목록 열','지자체명 / 시작 시기 / 혜택 방식(단순할인/단계형) / 발급 건수 / 혜택업체 수. 지자체명과 시작 시기만 있어도 된다고 되어 있어 발급 건수는 못 찾으면 그대로 적음.'),
        ('목록 출처', SRC_MAIN + ' 공식 메인 지도 52개 라벨 + getRegnList.json(시도코드별).'),
        ('혜택업체 수','getRegnMbrbList.json totCnt. 안동 27 = R1 회신과 일치. 다른 시군 totCnt는 같은 API. 목록 첫 페이지는 8건만 내려오므로 업체 이름은 안동만 전수.'),
        ('시작 시기','공식 지역 페이지에 개시일 필드 없음. 2026-06-02 공지 이미지가 6월 8일 OPEN·52개 지역만 확정. 지자체별 연도는 못 찾음.'),
        ('발급 건수','비로그인 공식 화면에 없음. 안동 발급 건수는 정보공개청구 14번 항목. 이용 건수 19,353은 R1(혜택 이용)이지 발급이 아님.'),
        ('혜택 방식','서비스 소개는 가맹점 제시·3km 쿠폰·QR 스캔의 단순 할인. 앞 단계 혜택을 쓴 사람에게만 다음 혜택 같은 단계형은 공식 소개에 없음.'),
        ('비교군 메모','릴레이(단계형)가 없는 주민증 운영지가 비교군 후보. 공식 목록 52곳은 모두 단순할인으로 보임. 옥천 26곳·단양 64곳·안동 27곳.'),
        ('조사일','2026-09-21'),
    ])
    path = OUT / '02_디지털관광주민증_운영지자체.xlsx'
    wb.save(path)
    return path, len(rows), sum(counts[r['signguCd']]['혜택업체수'] for r in regs)
print('build_02 defined')


def build_03():
    crafts = load('03_체험/전통공예_목록.json')
    merchants = load('02_주민증/안동_가맹점목록.json')
    wb = Workbook(); ws = wb.active; ws.title = '체험프로그램'
    programs = [
        ['하회세계탈박물관 관람','하회세계탈박물관(사립)','안동시 풍천면 전서로 206','관람료 전체무료','명시 없음(관람)','09:30','18:00','설날, 추석','명시 없음','불가(18:00 종료)','https://www.tourandong.com/public/sub2/sub3.cshtml?seq=1254&page=3&searchKey=0&search=','페이지 게시일 미표기',TODAY,'공식 관광사이트 상세. 전화 054-853-2288'],
        ['하회세계탈박물관 나만의 탈 만들기(클레이 탈·탈 에코백·탈 열쇠고리·탈부채 등)','하회세계탈박물관','안동시 풍천면 전서로 206','5,000원~10,000원','30분 내외','09:30','18:00','설날, 추석(관람 휴장일과 같게 적혀 있음. 체험만의 별도 마감 시각은 없음)','명시 없음','불가(관람 종료 18:00)','https://www.tourandong.com/public/sub2/sub3.cshtml?seq=1254&page=3&searchKey=0&search=','페이지 게시일 미표기',TODAY,'작업 목록의 하회세계탈박물관 핵심 행. 저녁 식사 후 연결은 이 공식 시간으로는 안 됨'],
        ['하회별신굿탈놀이 상설공연','하회별신굿탈놀이보존회','안동하회마을 하회별신굿탈놀이 전수회관(마을입구 관리사무소 맞은편)','관람료 무료','약 70분(13:50 안내~15:10 뒤풀이)','13:50','15:10','월요일(3~12월은 화~일, 1~2월은 토·일만)','명시 없음(공연)','불가(오후 공연)','https://www.tourandong.com/public/sub2/sub2.cshtml?seq=276','페이지 게시일 미표기',TODAY,'주최 보존회, 후원 문체부·경북·안동시'],
        ['탈춤따라배우기·탈만들기 체험','하회별신굿탈놀이 전수관 안내(공식 관광사이트)','경북 안동시 풍천면 하회종가길 3-15 (하회리) 탈놀이 전수관','명시 없음','1시간 내외','명시 없음','명시 없음','명시 없음','문의전화 054-854-3664','판단 불가(시작·종료 시각 없음)','https://www.tourandong.com/public/sub2/sub3.cshtml?seq=1383&page=3&searchKey=0&search=','페이지 게시일 미표기',TODAY,'축제 기간 선유줄불놀이 관람 가능(만송정)이라고만 적혀 있음. 평소 저녁 운영이라고 단정하지 않음'],
        ['명인 안동소주 양조장체험(누룩만들기·전통주 빚기·칵테일)','명인 안동소주(박재서 명인, 전통식품 명인 6호)','안동시 풍산읍 산업단지6길 6','명시 없음','2시간 내외','명시 없음','명시 없음','명시 없음','신청시 운영','판단 불가(시작·종료 시각 없음)','https://www.tourandong.com/public/sub2/sub3.cshtml?seq=1540&page=1&searchKey=0&search=','페이지 게시일 미표기',TODAY,'전화 054-856-6903. 신청시 운영만 있어 저녁 고정 회차는 공식 페이지에 없음'],
        ['민속주 안동소주 만들기 체험','안동소주박물관','안동시 강남로 71-1','입장료 무료. 체험비 명시 없음','체험 1시간 내외 / 관람 30분~1시간','09:00','18:00','명시 없음','문의 054-858-4541','불가(18:00 종료)','https://www.tourandong.com/public/sub2/sub3.cshtml?seq=51&page=4&searchKey=0&search=','페이지 게시일 미표기',TODAY,'작업 목록의 안동소주 체험. 박물관 체험장. 명인 안동소주(풍산)와 장소가 다름'],
        ['월영교 문보트 체험','월영교 문보트(공식 관광사이트 상세, 문의 054-823-0716 / 054-853-0715)','안동시 민속촌길 26','명시 없음. 안동시민·국가유공자·장애인·다자녀 20% 할인','30분','평일 10:00 / 토 11:00 / 일 10:00','평일 22:00 / 토 23:00 / 일 23:00','명시 없음','전화 문의','가능(평일 22:00, 주말 23:00까지)','https://www.tourandong.com/public/sub2/sub4.cshtml?seq=1544','페이지 게시일 미표기',TODAY,'1단계 저녁 연결 후보. 공식 페이지에 요금 원가는 없음'],
        ['월영교 황포돛배체험','월영교 일대(같은 상세 페이지)','안동시 민속촌길 26','명시 없음. 단체 10% 할인','20분','평일 10:00 / 토 11:00 / 일 10:00','평일 22:00 / 토 23:00 / 일 23:00','명시 없음','전화 문의','가능(문보트와 같은 영업시간으로 적혀 있음)','https://www.tourandong.com/public/sub2/sub4.cshtml?seq=1544','페이지 게시일 미표기',TODAY,'영업시간이 문보트와 한 덩어리로 적혀 있어 돛배만의 막 시간은 분리되어 있지 않음'],
        ['선성현 의복체험','선성현문화단지(선성현의복체험관)','경북 안동시 도산면 선성중앙길 77 (서부리)','주민증 혜택: 복식체험 이용객 메밀꽃피면2 카페 커피 1,000원 할인. 체험 자체 가격은 공식 관광 상세에 없음','명시 없음','명시 없음','명시 없음','명시 없음','전화 054-840-3478','판단 불가','https://www.tourandong.com/public/sub2/sub3.cshtml?seq=1542&page=1&searchKey=0&search=','페이지 게시일 미표기',TODAY,'주민증 가맹 선성현의복체험관. 공식 관광 페이지는 단지 소개만 있고 운영 종료 시각 없음. 원도심이 아님'],
        ['한국문화테마파크 선비숙녀변신방·의병전투체험 등','한국문화테마파크','경북 안동시 도산면 월천길 300','입장 개인일반 5,000원 / 개인할인 4,000원. 선비숙녀변신방 10,000원, 의병전투체험 7,000원, 활쏘기 3,000원, 연무대 3,000원','명시 없음','명시 없음','명시 없음','명시 없음','전화 054-857-9921','판단 불가(종료 시각 없음)','https://www.tourandong.com/public/sub2/sub3.cshtml?seq=1553&page=1&searchKey=0&search=','페이지 게시일 미표기',TODAY,'주민증 혜택: 어른 5,000→4,000원 등. 도산 권역. 원도심 저녁 연결과 거리상 별개'],
        ['안동호반힐링타운 황토방·한방목공예·치유체험','안동호반힐링타운','안동시 도산면 동부리 36','명시 없음','1회당 약 2.5시간','09:30 / 14:00 (1일 2회)','12:00 / 16:30','명시 없음','전화 054-855-3371','불가(16:30 종료)','https://www.tourandong.com/public/sub2/sub3.cshtml?seq=1543&page=1&searchKey=0&search=','페이지 게시일 미표기',TODAY,'도산 권역'],
        ['탈춤축제 체험부스(탈춤따라 배우기 등)','2026 안동국제탈춤페스티벌','축제장(탈춤공원 일원)','공식 입장권 안내에 체험 요금 표기 없음','조사 7번 일정표 참고','축제 기간 한정(2026-09-24~10-04)','일정표 회차별. 평소 상시 아님','축제 아닌 날 없음','공식 일정표','축제 회차에 따름','https://www.maskdance.com/','2026-09-21 수집본',TODAY,'작업 목록이 7번과 나눠 둔 항목. 평소 1단계 연결용이 아니라 축제 기간 한정'],
    ]
    write_table(ws, ['체험명','운영주체','주소','가격','소요시간','운영 시작','운영 종료','휴무','예약 방법','저녁연결(18시 이후)','출처 URL','게시일','조사일','비고'], programs, widths=[36,28,36,36,18,24,24,28,22,24,54,18,12,40], link_cols=['출처 URL'], date_cols=['조사일'])
    cws=wb.create_sheet('전통공예_공식목록22'); crows=[]
    for x in crafts:
        crows.append([x['name'],'안동시 공식 관광사이트 전통공예 목록', x.get('주소') or '명시 없음','목록 페이지에 가격 없음','목록 페이지에 없음','목록 페이지에 없음','목록 페이지에 없음','목록 페이지에 없음','상세에서 확인', x['url'],'페이지 게시일 미표기', TODAY, f"seq={x['seq']} / 총 22곳 중 {x['page']}쪽"])
    write_table(cws, ['체험명','운영주체','주소','가격','소요시간','운영 시작','운영 종료','휴무','예약 방법','출처 URL','게시일','조사일','비고'], crows, widths=[28,28,36,20,16,16,16,16,16,54,18,12,24], link_cols=['출처 URL'], date_cols=['조사일'])
    ews=wb.create_sheet('주민증_체험가맹'); erows=[]
    for x in merchants:
        if x.get('mbrbBnefClCd') != 'EXPRN': continue
        erows.append([x['mbrbNm'],'디지털 관광주민증 가맹(체험)','주소는 가맹 API에 없음 — R1 회신 주소 참고', x.get('bnefCn') or '명시 없음','명시 없음','명시 없음','명시 없음','명시 없음','명시 없음', SRC_ANDONG,'화면 확인 2026-09-21', TODAY,'할인 내용만 있음. 운영 종료 시각은 가맹 목록에 없음'])
    write_table(ews, ['체험명','운영주체','주소','가격','소요시간','운영 시작','운영 종료','휴무','예약 방법','출처 URL','게시일','조사일','비고'], erows, widths=[22,28,40,40,12,12,12,12,12,54,22,12,36], link_cols=['출처 URL'], date_cols=['조사일'])
    notes_sheet(wb, [
        ('작업 목록 열','체험명 / 운영주체 / 주소 / 가격 / 소요시간 / 운영 시작 / 운영 종료 / 휴무 / 예약 방법. 운영 종료 시각이 필수.'),
        ('핵심 판정','공식 페이지에서 저녁(18시 이후) 종료가 확인된 것은 월영교 문보트·황포돛배뿐. 탈박물관·안동소주박물관은 18:00 종료. 명인 안동소주·탈만들기(전수관)는 종료 시각이 없어 1단계 저녁 연결 근거로 쓰지 않음.'),
        ('하회동탈박물관','공식 관광사이트 전통공예 22곳에 하회동탈박물관 이름은 없고 하회세계탈박물관만 있음. 별도 시설로 추정하지 않음.'),
        ('공방','전통공예 목록 22곳이 공방·체험시설 묶음. 개별 공방의 종료 시각은 목록에 없어 상세가 있는 것만 첫 시트에 옮김. 원도심 공방은 현장조사(현4) 대상.'),
        ('탈춤 체험부스','평소 상시가 아님. 7번 엑셀과 중복되지 않게 한 줄로만 적음.'),
        ('조사일','2026-09-21'),
    ])
    path = OUT / '03_체험프로그램_목록가격.xlsx'
    wb.save(path)
    evening = [p for p in programs if str(p[9]).startswith('가능')]
    return path, len(programs), len(crafts), len(evening)

p2, n2, sum2 = build_02()
p3, n3, ncraft, nev = build_03()
print(p2)
print('지자체', n2, '혜택업체합', sum2)
print(p3)
print('핵심프로그램', n3, '전통공예목록', ncraft, '저녁가능', nev)
