# -*- coding: utf-8 -*-
"""교수님 브리핑 PDF(2026-09-22)에 들어가는 모든 수치를 원자료에서 다시 계산해 JSON으로 저장한다.

출력: 보고서/교수브리핑_20260922/수치.json  → scripts/교수브리핑_PDF생성.py 가 읽는다.
데이터 규칙: 카드 = 외지인 touDiv1, 방문 연인원 = D1(BDT_01_01_006), 비교는 1~8월 동기간.
"""
import sys, os, json, pandas as pd, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 체험프레임_검증 import visits, cards, per_visit   # 같은 로더를 써야 기존 수치와 맞는다

OUT = '보고서/교수브리핑_20260922/수치.json'
M = list(range(1, 9))
CARD = 'data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv'
EXP = ['문화서비스', '관광유원시설', '기타레저']      # 골프장·스키장·여행업·레저용품쇼핑 제외
R = {}

# ── 1. 방문 연인원과 방문당 체험·문화 소비 ─────────────────────────────
V, P = {}, {}
for y in (2024, 2025, 2026):
    V[y] = visits(y, M)
    W, d = cards(CARD, y, M)
    P[y] = per_visit(W, V[y], d)

R['방문'] = {'2024_1-8': float(V[2024]['안동시']), '2026_1-8': float(V[2026]['안동시']),
             '변화율': float(V[2026]['안동시'] / V[2024]['안동시'] * 100 - 100)}

idx = sorted(set(P[2024].index) & set(P[2026].index))
a, b = P[2024].loc[idx, EXP].sum(axis=1), P[2026].loc[idx, EXP].sum(axis=1)
chg = (b / a - 1) * 100
R['체험문화'] = {
    '시군수': len(idx),
    '안동_2024': float(a['안동시']), '안동_2026': float(b['안동시']),
    '안동_변화율': float(chg['안동시']),
    '중앙_변화율': float(chg.median()),
    '안동_감소순위': int(chg.rank(method='min')['안동시']),
    '경주_2026': float(b['경주시']), '안동_경주비': float(b['안동시'] / b['경주시'] * 100),
    '중앙_2026': float(b.median()),
    '안동_수준순위': int(b.rank(ascending=False, method='min')['안동시']),
    '분포': {k: round(float(v), 2) for k, v in chg.sort_values().items()},
}

# ── 2. 관광유원시설 칸의 결함 (피드백 2번의 근거) ──────────────────────
am = P[2026].loc[idx, '관광유원시설']
R['관광유원시설'] = {
    '시군수': len(am),
    '0원': int((am == 0).sum()),
    '1원미만': int((am < 1).sum()),
    '10원미만': int((am < 10).sum()),
    '중앙': float(am.median()),
    '0원_지역': sorted(am[am == 0].index.tolist()),
    '안동': {str(y): round(float(P[y].loc['안동시', '관광유원시설']), 2) for y in (2024, 2025, 2026)},
    '안동_순위_낮은순': int(am.rank(method='min')['안동시']),
    '구간': {'0원': int((am == 0).sum()), '0~1원': int(((am > 0) & (am < 1)).sum()),
             '1~10원': int(((am >= 1) & (am < 10)).sum()), '10~100원': int(((am >= 10) & (am < 100)).sum()),
             '100원 이상': int((am >= 100).sum())},
}
EXP2 = ['문화서비스', '기타레저']                     # 관광유원시설을 빼고 다시 계산
a2, b2 = P[2024].loc[idx, EXP2].sum(axis=1), P[2026].loc[idx, EXP2].sum(axis=1)
c2 = (b2 / a2 - 1) * 100
R['관광유원시설']['제외재계산'] = {'안동_2024': float(a2['안동시']), '안동_2026': float(b2['안동시']),
                           '안동_변화율': float(c2['안동시']), '중앙_변화율': float(c2.median()),
                           '안동_감소순위': int(c2.rank(method='min')['안동시'])}

# 원문의 313원·551원 정의(레저용품쇼핑 포함) 확인
b3 = P[2026].loc[idx, EXP + ['레저용품쇼핑']].sum(axis=1)
R['원문정의'] = {'안동_2026': float(b3['안동시']), '경주_2026': float(b3['경주시']),
               '전주시_패널존재': bool('전주시' in P[2026].index)}

# ── 3. 무박 비중 (당일치기 가설 기각) ─────────────────────────────────
mob = pd.concat([pd.read_csv('data/bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1.csv'),
                 pd.read_csv('data/bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1_202608추가.csv')]
                ).drop_duplicates()
mob = mob[(mob['R:기초단체'] == '안동시') & (mob['C:방문자유형별'] == '외지인(b)')
          & ((mob['R:기준연월'] % 100).isin(M))]
R['무박'] = {}
for y in (2024, 2025, 2026):
    s = mob[mob['R:기준연월'] // 100 == y]
    tot = s['V:관광객수'].sum()
    R['무박'][str(y)] = float(s[s['C:숙박일수'] == '무박']['V:관광객수'].sum() / tot * 100) if tot else None
# 연간(1~12월): KTX-이음 운행 전 2019 vs 중앙선 전 구간 개통(2024.12) 후 2025
mob_all = pd.concat([pd.read_csv('data/bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1.csv'),
                     pd.read_csv('data/bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1_202608추가.csv')]
                    ).drop_duplicates()
mob_all = mob_all[(mob_all['R:기초단체'] == '안동시') & (mob_all['C:방문자유형별'] == '외지인(b)')]
R['무박_연간'] = {}
for y in (2019, 2024, 2025):
    s = mob_all[mob_all['R:기준연월'] // 100 == y]
    R['무박_연간'][str(y)] = float(s[s['C:숙박일수'] == '무박']['V:관광객수'].sum() / s['V:관광객수'].sum() * 100)

# 원도심(안동구시장)–월영교 직선거리: scripts/월영교_반경_음식점.py 의 기준점 좌표
def _hav(lon1, lat1, lon2, lat2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a_ = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return float(2 * 6371.0088 * np.arcsin(np.sqrt(a_)))
R['원도심_월영교_km'] = _hav(128.7280, 36.5655, 128.7609, 36.5765)

# ── 4. 관광지 방문↔소비건수 (철도공사 2022.4~6) ────────────────────────
g = pd.read_csv('data/external/철도공사_8대도시/안동_관광지_방문소비갭.csv')
R['철도공사'] = g[['관광지명', '방문점유율_pct', '방문객소비건수점유율_pct', '소비방문배율']].to_dict('records')

# ── 5. 목적지 검색 비중 (POI ÷ 시군 전체, 2018→2025) ──────────────────
f = pd.read_csv('data/api_region/관광지검색Top100_기간별_LN_03_01_037.csv')
den = pd.read_csv('data/bdt/내비게이션/시군구별_검색건수_연도별_BDT_03_01_003_1.csv'
                  ).groupby(['SGG_NM', '_YEAR']).SRCH_CNT.sum()
POI = [('경상북도 안동시', '안동시', '안동하회마을'), ('경상북도 안동시', '안동시', '월영교'),
       ('경상북도 안동시', '안동시', '도산서원'), ('경상북도 경주시', '경주시', '불국사'),
       ('경상북도 경주시', '경주시', '동궁과월지'), ('경상북도 경주시', '경주시', '경주월드'),
       ('경상북도 영주시', '영주시', '부석사')]
R['검색비중'] = []
for reg, sgg, nm in POI:
    s18 = f[(f.PERIOD == '2018') & (f.Q_SGG_NM == reg) & (f.ITS_BRO_NM == nm)].SRCH_CNT.sum() / den[(sgg, 2018)] * 100
    s25 = f[(f.PERIOD == '2025') & (f.Q_SGG_NM == reg) & (f.ITS_BRO_NM == nm)].SRCH_CNT.sum() / den[(sgg, 2025)] * 100
    R['검색비중'].append({'시군': sgg, '관광지': nm, '2018': float(s18), '2025': float(s25),
                       '변화율': float(s25 / s18 * 100 - 100)})
R['안동전체검색'] = {'2018': int(den[('안동시', 2018)]), '2025': int(den[('안동시', 2025)])}
hist = {}
for per in ('2025_1-8', '2026_1-8'):
    for reg in ('경상북도 안동시', '경상북도 경주시'):
        s = f[(f.PERIOD == per) & (f.Q_SGG_NM == reg)]
        hist[f'{per}|{reg[5:]}'] = float(s[s.KTO_CATE_NAME_B == '역사유적지'].SRCH_CNT.sum() / s.SRCH_CNT.sum() * 100)
R['역사유적지검색'] = hist

# ── 6. 안동역 주말 시간대별 승차 (전 열차, 2026 1~8월) ─────────────────
st = pd.read_csv('data/external/팀원취합_정제/안동역_승하차_월별_열차종류별_long.csv')
st = st[(st['승하차'] == '승차') & (st['연월'] >= '2026-01') & (st['연월'] <= '2026-08')]
wk = st[st['구분'] == '주말'].groupby('시간대')['인원'].sum()
R['안동역_주말승차'] = {k: int(v) for k, v in wk.items() if '06' <= k[:2] <= '23'}
R['안동역_주말합계'] = int(wk.sum())

# ── 7. 월영교 1km 영업 종료 (팀 현장조사 9/19) ───────────────────────
w = pd.read_csv('조사/16_월영교_1km_음식점.csv')
R['월영교조사'] = w[['상호명', '상권업종중분류명', '상태', '영업종료', '월영교거리m', '확인일', '출처']
                   ].fillna('').to_dict('records')

# ── 8. 시내버스 112번 (원도심↔월영교, 평일 기점 출발) ──────────────────
bus = pd.read_excel('조사/01_시내버스_노선시간표.xlsx', sheet_name='출발시각_전체')
R['버스'] = {}
for col in ('원도심→월영교', '월영교→원도심', '안동역→원도심', '원도심→안동역'):
    t = sorted(str(x)[:5] for x in bus[bus[col] == 'Y']['출발시각'])
    R['버스'][col] = {'회수': len(t), '첫차': t[0], '막차': t[-1],
                     '19시이후': sum(x >= '19:00' for x in t), '시각': t if len(t) < 10 else None}

# ── 9. 경북 야간 검색 상위 칸 점유 ────────────────────────────────────
ng = pd.read_csv('보고서/야간문제_경북검색칸점유_20260918.csv')
R['야간검색칸'] = {'합계': int(ng['합계'].sum()),
                  '상위': ng.sort_values('합계', ascending=False).head(6)[['SGG_NM', '합계']].to_dict('records'),
                  '안동': int(ng[ng.SGG_NM == '안동시']['합계'].sum())}

# ── 10. 주민증 R1 ─────────────────────────────────────────────────────
r1 = pd.read_csv('data/정보공개청구/R1_혜택업체_20260918.csv')
u1 = pd.read_csv('data/정보공개청구/R1_이용건수_20260918.csv')
R['주민증'] = {'혜택업체': len(r1), '이용합계': int(u1['이용건수'].sum()),
             '월평균': u1[['기간', '월평균']].to_dict('records'),
             '월영교1km_혜택업체': sorted(set(r1['혜택가맹점명']) & set(w['상호명']))}

def _grp(c):
    for k in ('숙박', '식음료', '체험', '전시·박물관', '관광지', '여행상품', '미상'):
        if c.startswith(k):
            return k
    return c
R['주민증']['분류'] = r1['분류_추정'].map(_grp).value_counts().to_dict()
R['주민증']['고택한옥'] = int(r1['분류_추정'].str.contains('고택').sum())
R['주민증']['카페'] = int(r1['분류_추정'].str.contains('카페').sum())
hx = pd.read_excel('조사/02_디지털관광주민증_운영지자체.xlsx', sheet_name='운영지자체')
R['주민증']['운영지역수'] = int(hx['시작 시기'].notna().sum())

# ── 11. 5개 도시 방문·방문당 관광소비 (1~8월 2024→2026, 포항·전주는 구 합계) ──
m1 = pd.read_csv('보고서/M1_방문소비_매트릭스_초벌.csv', index_col=0)
R['5개도시'] = {}
for city, parts in [('안동', ['안동시']), ('경주', ['경주시']), ('군산', ['군산시']),
                    ('포항', ['포항시 남구', '포항시 북구']), ('전주', ['전주시 덕진구', '전주시 완산구'])]:
    s = m1.loc[parts, ['v24', 'v26', 's24', 's26']].sum()
    R['5개도시'][city] = {'방문': float(s.v26 / s.v24 * 100 - 100),
                        '방문당소비': float((s.s26 / s.v26) / (s.s24 / s.v24) * 100 - 100),
                        '방문당소비_24': float(s.s24 / s.v24 * 1000), '방문당소비_26': float(s.s26 / s.v26 * 1000)}

# ── 12. 혜택 배치 진단 (결과물 ①): 읍면동 외지인 방문 2026 1~8월 × 혜택업체 행정동 ──
import re
emd = pd.read_csv('data/api_region/안동_읍면동별_외지인_월별_BDT_01_01_005_1.csv')
ev = emd[(emd.BASE_YM >= 202601) & (emd.BASE_YM <= 202608)].groupby('AREA_NM').TOU_NUM.sum()
share = ev / ev.sum() * 100
shop = pd.read_csv('data/external/팀원취합_정제/안동_상권_음식점_20260630.csv')


def _dong(addr):
    """읍·면 주소는 그대로, 도로명만 있으면 상가정보에서 같은 주소(없으면 같은 도로명 최빈) 행정동."""
    m = re.search(r'(\S+[읍면])\s', addr)
    if m:
        return m.group(1)
    road, num = re.search(r'안동시\s+(\S+)\s+(\S+)', addr).groups()
    exact = shop[shop['도로명주소'] == f'경상북도 안동시 {road} {num}']
    if len(exact):
        return exact['행정동명'].mode()[0]
    return shop[shop['도로명주소'].astype(str).str.startswith(f'경상북도 안동시 {road} ')]['행정동명'].mode()[0]


r1['행정동'] = r1['주소'].map(_dong)
cnt = r1['행정동'].value_counts()
R['혜택배치'] = [{'행정동': k, '방문점유율': float(v), '혜택업체': int(cnt.get(k, 0))}
              for k, v in share.sort_values(ascending=False).items()]
R['혜택배치_대조'] = r1[['혜택가맹점명', '주소', '행정동']].to_dict('records')

# ── 13. 원도심·월영교 반경 1km 음식점 업종 구성 (scripts/월영교_반경_음식점.py 와 같은 기준점) ──
_lat, _lon = np.radians(shop['위도'].astype(float)), np.radians(shop['경도'].astype(float))
R['반경1km업종'] = {}
for nm, (lon0, lat0) in {'원도심': (128.7280, 36.5655), '월영교': (128.7609, 36.5765)}.items():
    la0, lo0 = np.radians(lat0), np.radians(lon0)
    dist = 2 * 6371.0088 * np.arcsin(np.sqrt(np.sin((_lat - la0) / 2) ** 2 + np.cos(la0) * np.cos(_lat) * np.sin((_lon - lo0) / 2) ** 2))
    R['반경1km업종'][nm] = shop[dist <= 1.0]['상권업종중분류명'].str.strip().value_counts().to_dict()

# ── 14. 원도심 식당 영업시간 표본 (TourAPI 등록분, 조사/12) ──
s60 = pd.read_csv('조사/12_원도심_식당영업시간_표본60.csv')
done = s60[s60['점포별_영업종료'].notna()]
R['원도심영업표본'] = {'표본': len(s60), '확인': len(done), '종료': sorted(done['점포별_영업종료'].astype(str).tolist()),
                    '21시넘김': int((done['점포별_영업종료'].astype(str) > '21:00').sum())}

# ── 15. 주민증 성공 사례·규모 (조사/02 보도 수치, 수상작 인터뷰) ──
R['주민증규모'] = {'전국누적발급': '411만 건(2024년 12월 말, 문화체육관광부 2025.3.26 보도)',
                '발급': [('옥천군', '47,861명', '2023.10'), ('단양군', '25,000명', '2023.10'),
                         ('제천시', '5만 명', '2024.6'), ('안동시', '6만 1천여 명', '2024.9')]}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(R, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ── 요약 출력 ───────────────────────────────────────────────────────
e, am = R['체험문화'], R['관광유원시설']
print(f"방문 {R['방문']['2024_1-8']:,.0f} → {R['방문']['2026_1-8']:,.0f} ({R['방문']['변화율']:+.1f}%)")
print(f"무박 비중 {R['무박']}")
print(f"체험·문화 {e['안동_2024']:.1f} → {e['안동_2026']:.1f}원 ({e['안동_변화율']:+.1f}%), 중앙 {e['중앙_변화율']:+.1f}%, "
      f"감소 {e['안동_감소순위']}/{e['시군수']}위, 경주 {e['경주_2026']:.1f}원({e['안동_경주비']:.1f}%), 중앙 수준 {e['중앙_2026']:.1f}원, 수준 {e['안동_수준순위']}위")
print(f"관광유원시설: 0원 {am['0원']} · 1원 미만 {am['1원미만']} · 10원 미만 {am['10원미만']} / {am['시군수']} · 중앙 {am['중앙']:.2f}원 · 안동 {am['안동']}")
print(f"  0원 지역: {', '.join(am['0원_지역'])}")
print(f"  관광유원시설 빼고 재계산: {am['제외재계산']}")
print(f"원문 정의(레저용품쇼핑 포함) 안동 {R['원문정의']['안동_2026']:.1f} · 경주 {R['원문정의']['경주_2026']:.1f} · 전주시 패널 {R['원문정의']['전주시_패널존재']}")
print(f"역사유적지 검색: {R['역사유적지검색']}")
print(f"안동역 주말 18-19 {R['안동역_주말승차']['18-19']:,} · 21-22 {R['안동역_주말승차']['21-22']:,} · 22-23 {R['안동역_주말승차']['22-23']}")
print(f"버스: { {k: (v['회수'], v['막차'], v['19시이후']) for k, v in R['버스'].items()} }")
print(f"야간검색 칸: 안동 {R['야간검색칸']['안동']}/{R['야간검색칸']['합계']}")
print(f"주민증: {R['주민증']['혜택업체']}곳 · {R['주민증']['이용합계']:,}건 · 월영교 1km 안 혜택업체 {R['주민증']['월영교1km_혜택업체']}")
print(f"→ {OUT}")
