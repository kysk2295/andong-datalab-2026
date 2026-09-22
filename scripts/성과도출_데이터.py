# -*- coding: utf-8 -*-
"""이어드림 릴레이 1~3단계의 성과 도출 데이터 (2026-09-22, 교수님 요청)

단계마다 네 칸: A 기준선(보유 데이터) · B 목표·예상 효과(%) · C 행동 관측(현장) · D 시행 후 검증.
이 스크립트는 A·B의 숫자를 원자료에서 계산해 JSON으로 남긴다. C·D는 엑셀 생성 스크립트에서 문장으로 채운다.

출력: 보고서/성과도출_20260922/성과도출_수치.json
데이터 규칙: 카드 = 외지인 touDiv1, 방문 연인원 = D1(BDT_01_01_006), 비교는 1~8월 동기간.
"""
import sys, os, json, pandas as pd, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 체험프레임_검증 import cards

OUT_DIR = '보고서/성과도출_20260922'
os.makedirs(OUT_DIR, exist_ok=True)
Q = json.load(open('보고서/교수브리핑_20260922/수치.json'))   # 브리핑에서 이미 검증한 값은 다시 계산하지 않는다
M = list(range(1, 9))
CARD = 'data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv'
R = {}

V26 = Q['방문']['2026_1-8']                 # 안동 외지인 방문 연인원 2026 1~8월
EX = Q['체험문화']

# ═════════ 1단계 · 원도심 식음 → 체험 ═════════════════════════════════
gap_full = V26 * (EX['안동_2024'] - EX['안동_2026'])                    # 2024 수준까지
tgt_med = EX['안동_2024'] * (1 + EX['중앙_변화율'] / 100)              # 전국 중앙만큼만 줄었을 때
gap_med = V26 * (tgt_med - EX['안동_2026'])

# 주민증 업체별 이용 표시값(utztCnt, 공식 목록, 2026-09-21 조회. R1에 없던 업체별 실적의 대용)
bz = pd.read_excel('조사/02_디지털관광주민증_운영지자체.xlsx', sheet_name='안동_혜택업체27')
bz = bz[bz['공식분류'].notna() & (bz['혜택업체명'] != '행 수')].copy()
bz['이용'] = pd.to_numeric(bz['목록 이용표시(utztCnt)'], errors='coerce')
tot_u = bz['이용'].sum()
by_cls = bz.groupby('공식분류')['이용'].agg(['count', 'sum']).sort_values('sum', ascending=False)
top = bz.sort_values('이용', ascending=False)[['혜택업체명', '공식분류', '이용']].head(6)

month_avg = Q['주민증']['월평균'][-1]['월평균']                         # 2026.1~8 월평균 887.5
base_rate = month_avg / (V26 / 8) * 100                                  # 외지인 방문 대비 이용률(%)

R['1단계'] = {
    '체험문화_2024': EX['안동_2024'], '체험문화_2026': EX['안동_2026'],
    '감소율': EX['안동_변화율'], '전국중앙_변화율': EX['중앙_변화율'],
    '목표_2024수준_pct': (EX['안동_2024'] / EX['안동_2026'] - 1) * 100,
    '목표_중앙수준_원': tgt_med,
    '목표_중앙수준_pct': (tgt_med / EX['안동_2026'] - 1) * 100,
    '격차금액_2024수준_원': gap_full, '격차금액_중앙수준_원': gap_med,
    '필요건수': {f'{p:,}원 체험': {'2024수준': gap_full / p, '중앙수준': gap_med / p,
                               '2024수준_월': gap_full / p / 8, '중앙수준_월': gap_med / p / 8}
              for p in (10000, 20000)},
    '주민증_월평균이용_2026': month_avg,
    '주민증_이용률_기준선_pct': base_rate,
    '업체별이용_합계': float(tot_u),
    '업체별이용_분류': {k: {'업체수': int(r['count']), '이용': float(r['sum']),
                       '비중': float(r['sum'] / tot_u * 100)} for k, r in by_cls.iterrows()},
    '업체별이용_상위': top.to_dict('records'),
    '혜택배치_중구동': Q['혜택배치'][0],
}

# ═════════ 2단계 · 야간 이동 ════════════════════════════════════════
# D1 교차표에서 안동 외지인 요일×시간대 (2026 1~8월) + 전국 시군 18~21시 비중
f = 'data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_2026.csv'
parts = []
for ch in pd.read_csv(f, chunksize=2_000_000,
                      usecols=['R:기초단체', 'R:기준연월', 'C:방문자유형별', 'C:요일', 'C:시간대', 'V:방문자 수']):
    ch = ch[(ch['C:방문자유형별'] == '외지인(b)') & ch['C:시간대'].notna() & ((ch['R:기준연월'] % 100) <= 8)]
    parts.append(ch.groupby(['R:기초단체', 'C:요일', 'C:시간대'])['V:방문자 수'].sum())
d1 = pd.concat(parts).groupby(level=[0, 1, 2]).sum()
ad = d1.loc['안동시'].unstack()                                          # 요일 × 시간대
WKND = ['토요일', '일요일']
wk_tot = ad.loc[WKND].sum().sum()
all_tot = ad.sum().sum()
wk_eve = ad.loc[WKND, '18~21시'].sum()
wd_eve = ad.drop(WKND)['18~21시'].sum()
sgg = d1.groupby(level=[0, 2]).sum().unstack()
sh = sgg['18~21시'] / sgg.sum(axis=1) * 100
sh = sh[sgg.sum(axis=1) >= 1_000_000]                                     # 야간문제_수치화와 같은 하한(100만)

R['2단계'] = {
    '버스': Q['버스'],
    '안동역_주말승차_18_22': {k: Q['안동역_주말승차'][k] for k in ('18-19', '19-20', '20-21', '21-22', '22-23')},
    '안동역_19_20과_21_22_동일값': '우연(월·열차별 값이 전부 다름, 9/22 확인)',
    '저녁비중_안동_전체': float(ad['18~21시'].sum() / all_tot * 100),
    '저녁비중_전국중앙': float(sh.median()),
    '저녁비중_시군수': int(len(sh)),
    '저녁비중_안동_주말': float(wk_eve / wk_tot * 100),
    '저녁비중_안동_평일': float(wd_eve / (all_tot - wk_tot) * 100),
    '주말방문비중': float(wk_tot / all_tot * 100),
    '주말저녁_방문_연인원': float(wk_eve),
    '운영창_분': 150, '운영창_원도심출발_버스회수': 0,
}
R['2단계']['목표_중앙까지_pp'] = R['2단계']['저녁비중_전국중앙'] - R['2단계']['저녁비중_안동_전체']
R['2단계']['목표_중앙까지_pct'] = R['2단계']['목표_중앙까지_pp'] / R['2단계']['저녁비중_안동_전체'] * 100

# ═════════ 3단계 · 월영교 야간 팝업 ══════════════════════════════════
emd = pd.read_csv('data/api_region/안동_읍면동별_외지인_월별_BDT_01_01_005_1.csv')
emd = emd[(emd.BASE_YM % 100) <= 8]
gn = emd[emd.AREA_NM == '강남동'].groupby(emd.BASE_YM // 100)['TOU_NUM'].sum()

pt = pd.read_excel('조사/05_주요관광지점_입장객.xlsx', sheet_name='지점별_월별(2023-2026.6)')
wy = pt[pt['지점명'] == '월영교']
wy23_18 = wy[wy['연월'].between('2023-01', '2023-08')]['합계'].sum()
hh = pt[pt['지점명'] == '하회마을']
hh_2406_2606 = hh[hh['연월'].between('2024-06', '2026-06')]['합계'].sum()
ds = pt[pt['지점명'] == '도산서원']
ds_2406_2606 = ds[ds['연월'].between('2024-06', '2026-06')]['합계'].sum()
u = bz.set_index('혜택업체명')['이용']
rate_hh = u['하회마을'] / hh_2406_2606 * 100          # 이용 표시값은 2026-09까지 누적 → 상한 쪽
rate_ds = u['도산서원'] / ds_2406_2606 * 100

# 방문기회: 강남동(월영교 소재) 외지인 방문 × 안동 주말 비중 × 주말 저녁 비중  — 시 단위 분포를 강남동에 적용한 가정
wk_share = R['2단계']['주말방문비중'] / 100
eve_share = R['2단계']['저녁비중_안동_주말'] / 100
opp = float(gn[2026]) * wk_share * eve_share

# 객단가: 문화관광축제 외지인 방문당 소비 (2025, FE_01_01_007 외지인 ÷ FE_01_01_005 TOT_OUT)
fc = pd.read_csv('data/축제_전체/관광소비_FE_01_01_007.csv')
fc = fc[(fc.FSTV_YEAR == 2025) & (fc.LRFRN_DIV_CD == 1)].groupby('FSTV_ID')['SUM_CNSM_AMT'].sum()
fv = pd.read_csv('data/축제_전체/연도별방문자_FE_01_01_005_01.csv')
fv = fv[fv.BASE_YEAR == 2025].groupby('FSTV_ID')['TOT_OUT'].sum()
pv = (fc / fv).dropna()
pv = pv[np.isfinite(pv) & (pv > 0)]
unit = {'P10': float(pv.quantile(.1)), '중앙': float(pv.median()), 'P90': float(pv.quantile(.9))}

W26, _ = cards(CARD, 2026, M)
tour26 = float(W26.loc['안동시', '관광총소비'])
food26 = float(W26.loc['안동시'].filter(like='음식').sum()) if any('음식' in c for c in W26.columns) else None

# 강남동 외지인 관광총소비 2026 1~8월(데이터랩 화면 전사, 9/19): 109.51039억원, 식음료 50.9%
GN_TOUR = 109.51039e8
GN_FOOD = GN_TOUR * 0.509
CF = 0.5                                                   # 반사실 몫 가정: 팝업이 없었어도 안동 안에서 썼을 비율

def 계산(r, p):
    gross = opp * r / 100 * p
    net = gross * (1 - CF)
    return {'참여자수': opp * r / 100, '참여자총지출_원': gross, '추가소비_원': net,
            '강남동관광소비대비_pct': net / GN_TOUR * 100, '강남동식음료대비_pct': net / GN_FOOD * 100,
            '안동관광총소비대비_pct': net / tour26 * 100}

# (가) 릴레이 참여 = 주민증 조건형 혜택 이용자. 참여율 근거는 안동 실측 두 개뿐
grid = []
for rn, r in {'안동 주민증 평균 이용률': base_rate, '하회마을 혜택 이용률': rate_hh}.items():
    for un in ('P10', '중앙'):
        grid.append({'참여율': rn, '참여율_pct': r, '객단가': un, '객단가_원': unit[un], **계산(r, unit[un])})
# (나) 팝업 자체 이용(주민증 무관) — 참여율 근거 없음 → 민감도 표
sens = []
for r in (1, 5, 10, 20):
    for un in ('P10', '중앙'):
        sens.append({'참여율_pct': r, '객단가': un, '객단가_원': unit[un], **계산(r, unit[un])})
# 역산: 강남동 외지인 관광소비 +1%를 만들려면 필요한 참여율
need_1pct = {un: GN_TOUR * 0.01 / (1 - CF) / unit[un] / opp * 100 for un in ('P10', '중앙')}

R['3단계'] = {
    '철도공사_월영교': Q['철도공사'][0],
    '월영교1km': {'영업중': 16, '주점': 0, '20시30분까지마감_식당': 7, '21시까지_식당': 3},
    '야간검색_2026_1_8': 10914, '야간검색_변화': -34.0,
    '월영교입장객_2023': 682541, '월영교입장객_2023_1_8': float(wy23_18),
    '강남동_외지인방문_1_8': {int(k): float(v) for k, v in gn.items() if k >= 2023},
    '월영교_대_강남동_2023_1_8': float(wy23_18 / gn[2023]),
    '방문기회_주말저녁_2026_1_8': opp,
    '방문기회_산식': '강남동 외지인 방문(2026 1~8월) × 안동 주말 방문 비중 × 안동 주말 18~21시 비중',
    '하회마을_이용률_pct': rate_hh, '도산서원_이용률_pct': rate_ds,
    '하회마을_이용표시': float(u['하회마을']), '하회마을_입장객_2406_2606': float(hh_2406_2606),
    '축제객단가': unit, '축제수': int(len(pv)),
    '안동탈춤_객단가': float(pv['KCTF0041']),
    '안동_외지인관광총소비_2026_1_8_원': tour26,
    '반사실몫_가정': CF,
    '강남동_외지인관광소비_2026_1_8_원': GN_TOUR, '강남동_식음료_원': GN_FOOD,
    '시나리오_릴레이': grid, '민감도_팝업': sens, '강남동소비_1pct에_필요한_참여율': need_1pct,
}

# ── 1단계 시나리오: 체험 결제가 월 X건 늘면 방문당 체험·문화 소비가 몇 % 오르나 ──
# 이용 표시값은 가맹 시작(2024-06-01)부터 조회일(2026-09-21)까지 누적으로 본다 → 27.7개월
MON = (pd.Timestamp('2026-09-21') - pd.Timestamp('2024-06-01')).days / 30.44
X = {'지금 주민증 체험 7곳 합계': float(by_cls.loc['체험', 'sum']) / MON,
     '식음 1위(황소곳간식당) 수준': float(u['황소곳간식당']) / MON,
     '하회마을 수준': float(u['하회마을']) / MON,
     '안동 주민증 이용 전체(월평균)': month_avg}
sc1 = []
for xn, x in X.items():
    for p in (10000, 20000):
        add_won = x * 8 * p                                # 1~8월 8개월
        for cf, lab in ((0, '총지출'), (CF, '추가소비(반사실50%)')):
            per = add_won * (1 - cf) / V26
            sc1.append({'월 체험 결제': xn, '월건수': x, '체험가격': p, '구분': lab,
                       '방문당_증가_원': per, '방문당_증가_pct': per / EX['안동_2026'] * 100,
                       '격차_메움_pct(중앙수준)': add_won * (1 - cf) / gap_med * 100})
R["1단계"]["시나리오"] = sc1
R['1단계']['이용표시_누적개월'] = MON

json.dump(R, open(f'{OUT_DIR}/성과도출_수치.json', 'w'), ensure_ascii=False, indent=1, default=float)

# ── 확인용 출력 ──
s1, s2, s3 = R['1단계'], R['2단계'], R['3단계']
print(f"[1] 목표 +{s1['목표_2024수준_pct']:.1f}% / +{s1['목표_중앙수준_pct']:.1f}%  격차 {s1['격차금액_2024수준_원']/1e8:.2f}억 / {s1['격차금액_중앙수준_원']/1e8:.2f}억")
print(f"    주민증 이용률 기준선 {s1['주민증_이용률_기준선_pct']:.3f}%  업체별 합계 {s1['업체별이용_합계']:,.0f}")
for k, v in s1['업체별이용_분류'].items(): print(f"    {k} {v['업체수']}곳 {v['이용']:,.0f} ({v['비중']:.1f}%)")
print(f"    필요건수 {json.dumps(s1['필요건수'], ensure_ascii=False)}")
print(f"[2] 저녁비중 안동 {s2['저녁비중_안동_전체']:.2f} 중앙 {s2['저녁비중_전국중앙']:.2f} ({s2['저녁비중_시군수']}곳) → +{s2['목표_중앙까지_pp']:.2f}%p (+{s2['목표_중앙까지_pct']:.1f}%)")
print(f"    주말 저녁 {s2['저녁비중_안동_주말']:.2f} 평일 {s2['저녁비중_안동_평일']:.2f} 주말방문비중 {s2['주말방문비중']:.1f}  주말저녁 연인원 {s2['주말저녁_방문_연인원']:,.0f}")
print(f"[3] 강남동 {s3['강남동_외지인방문_1_8']}  월영교/강남동 2023 {s3['월영교_대_강남동_2023_1_8']:.2f}  방문기회 {opp:,.0f}")
print(f"    하회 이용률 {rate_hh:.2f}%  도산 {rate_ds:.2f}%  객단가 {unit}  축제 {len(pv)}  탈춤 {R['3단계']['안동탈춤_객단가']}")
print(f"    관광총소비 {tour26/1e8:.1f}억")
for g in grid + [dict(x, 참여율=f"{x['참여율_pct']}%") for x in sens]:
    print(f"    {g['참여율']:<16} {g['객단가']:<3} 참여 {g['참여자수']:>8,.0f}명 총지출 {g['참여자총지출_원']/1e8:6.2f}억 추가 {g['추가소비_원']/1e8:6.2f}억 강남동 {g['강남동관광소비대비_pct']:.2f}% 식음 {g['강남동식음료대비_pct']:.2f}%")
print('    강남동 +1% 필요 참여율', need_1pct)
for g in sc1:
    print(f"    [1단계] {g['월 체험 결제']:<22} 월{g['월건수']:>6.0f}건 {g['체험가격']:>6,}원 {g['구분']:<14} +{g['방문당_증가_원']:.2f}원 (+{g['방문당_증가_pct']:.2f}%) 격차 {g['격차_메움_pct(중앙수준)']:.1f}%")
