# -*- coding: utf-8 -*-
"""이어드림 3단계 기대효과 — 2단계: 몬테카를로 시뮬레이션 (2026-09-23, 구조 확정판)

입력 분포는 scripts/이어드림_파라미터추정.py 결과(파라미터추정.json·파라미터_부트스트랩.csv).
엑셀(scripts/이어드림_예측엑셀.py)과 같은 식을 고정 난수로 계산해 보고서 숫자와 그림을 만든다.

운영 구조 (9/23 사용자 결정)
  1단계  원도심 식당 영수증 QR 인증(주민증 앱 밖 개방형) → 낮 체험(18시 마감 시설) 결제
  2단계  인증자 중 저녁에 월영교로 가는 사람(자연 완주율 c, 철도공사 역산 × 야간 비중) × 저녁 이동 배수 lam(설문)
  3단계  월영교: 저녁 체험 = 문보트(주말 23시 운영) + 야간 팝업

1회 추출의 계산 (T개월, 기준 기간 2026년 1~8월)
  인증 N_R      = 중구동 외지인 방문(T개월) × (참여 식당 n1 ÷ 83) × p
  낮 체험 N_D    = N_R × r                     저녁 도착 M = N_R × c × lam
  문보트 N_B     = M × q_b                     팝업(릴레이) = M × q_p
  체험 추가소비   = (N_D × 체험가격 + N_B × 문보트가격) × (1 − 반사실 − 할인율)
  팝업 직접 지출  = 월영교 주말 저녁 방문기회 × 축제 방문당 소비 × 식음 0.606 × k × (n3 ÷ 24)
  지표① 방문당 체험·문화 소비 = 152.7원 + 체험 추가소비 ÷ 안동 외지인 방문(T개월)
  지표② 강남동 외지인 관광소비 증가율 = 팝업 추가소비 ÷ 강남동 관광총소비(T개월)

시나리오: 기본안(식당 20곳, p = 실측·사례) / 확대안(83곳 전부, p = 계산대 권유 가정)
          + 참여율 3단계(9/27 저녁): 기준 2% / 흥행 4%(강진 반값여행 규모) / 목표 10%(참여 식당 전원 안내), 모두 83곳

운영 기간(9/27 밤): T = 12개월(2026년 1~8월 월평균 × 12, 연간). 건수·금액은 연간, 비율 지표(방문당·격차)는 기간과 무관.

설문 보정(9/27 저녁, 사용자 결정 — 파라미터추정.json F_설문보정)
  r   = 설문 6번 의향(베타 사후) × 실현율 U(0.33, 0.40)                          [가정 베타(2, 6) 대체]
        의향 기준: 추출마다 반반 확률로 "매우 있다" 또는 "매우 + 있다"(9/27 밤, 선행연구 적용 범주 불명)
  lam = (c + (1 − c) × 새 이동) ÷ c, 새 이동 = 비이동자 셔틀 "매우 있다"(차 유무별 베타, 차 없음 10.5% 가중) × 실현율
        기존 lam = 1(연결이 저녁 이동을 늘리지 않음)은 "보수" 기준으로 함께 낸다
  할인율 10%: 새로 체험한 사람은 할인가만 내고, 원래 할 사람은 할인만큼 덜 낸다 → 순효과에서 가격 × 할인율을 뺀다
출력: 보고서/성과도출_20260922/시뮬레이션결과.json, 그림 g1~g4 (png·svg)
"""
import json, numpy as np, pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import spearmanr, beta as beta_dist
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

D = '보고서/성과도출_20260922'
P = json.load(open(f'{D}/파라미터추정.json'))
Q = json.load(open('보고서/교수브리핑_20260922/수치.json'))
S = json.load(open(f'{D}/성과도출_수치.json'))
boot = pd.read_csv(f'{D}/파라미터_부트스트랩.csv')
rng = np.random.default_rng(20260923)
N = 10000

# ── 고정값 ───────────────────────────────────────────────────────────
V26 = Q['방문']['2026_1-8']
EXP26, EXP24 = Q['체험문화']['안동_2026'], Q['체험문화']['안동_2024']
TARGET = EXP24 * (1 + Q['체험문화']['중앙_변화율'] / 100)
GAP = (TARGET - EXP26) * V26                                   # 목표까지 메워야 할 추가 소비(8개월)
JG_M = P['A_중구동_월방문']
OPP3 = S['3단계']['방문기회_주말저녁_2026_1_8']
GN_TOUR = S['3단계']['강남동_외지인관광소비_2026_1_8_원']
POP_ORIG, BOOTH_REF, FOOD, JM26 = 83, 24, 0.606, 887.5
NOCAR = 0.091 + 0.014                                         # 철도·버스 유입 비중(철도공사 SKT 추정, 2022.4~6) = 저녁 교통 없이는 못 가는 몫
WKND_DAYS = 70

# ── p 하한: 주민증 경로(음이항, α 최대우도 — 파라미터추정.py A절과 같은 모형) ──────────
bz = pd.DataFrame(P['A_업체'])
bz['l방문'] = np.log(bz['동월방문'])
glm = smf.negativebinomial('이용 ~ l방문 + C(분류, Treatment("식음료"))', data=bz,
                           offset=np.log(np.full(len(bz), P['A_가맹개월']))).fit(disp=0, maxiter=500)
glm_m = float(glm.predict(pd.DataFrame({'l방문': [np.log(JG_M)], '분류': ['식음료']}), offset=[0.0])[0])   # 월 1개월당 예측
P_LO = glm_m * POP_ORIG / JG_M                                  # 원도심 83곳이 모두 주민증 가맹일 때 방문 대비 이용률
P_MD = 6715 / (V26 / 8)                                         # 안동 반값여행 1차 신청 ÷ 월 외지인 방문
P_HI = S['3단계']['하회마을_이용률_pct'] / 100                  # 혜택이 있는 하회마을 이용률
SV = P['F_설문보정']                                            # 설문 보정 집계(9/27 저녁)
DISC = SV['할인율']

BASE = dict(이름='기본안', n1=20, n3=8, T=12.0, p=(P_LO, P_MD, P_HI), cf=(5, 5), disc=DISC,
            qb=(0.10, 0.25, 0.50), qp=(0.20, 0.40, 0.60), k=(0.10, 0.25, 0.50), boat=(7000, 9333, 12000), lam=None)
WIDE = {**BASE, '이름': '확대안', 'n1': 83, 'p': (P_MD, 0.02, 0.05)}
SCN = [BASE, WIDE]


def base(key, n):
    # 실현율을 "매우 있다"에만 적용할지 "매우 + 있다"에 적용할지 선행연구로 확인되지 않아, 추출마다 반반 확률로 둘 중 하나를 쓴다
    hi = rng.uniform(size=n) < SV['해석_섞기']
    k = np.where(hi, SV[f'{key}_긍정'][0], SV[f'{key}_매우'][0])
    return k, SV[f'{key}_매우'][1]


def draw_r(n):
    k, m = base('r', n)
    return rng.beta(k + 1, m - k + 1) * rng.uniform(*SV['실현율'], n)


def draw_new(n):
    (kc, nc), (kn, nn), w = base('lam_차', n), base('lam_차없음', n), SV['차없음_비중']
    return (w * rng.beta(kn + 1, nn - kn + 1) + (1 - w) * rng.beta(kc + 1, nc - kc + 1)) * rng.uniform(*SV['실현율'], n)


def draw(inp, n):
    tri = lambda t: np.full(n, float(t[0])) if t[0] == t[2] else rng.triangular(*t, n)   # 참여율 고정 시나리오는 상수
    pick = lambda col: boot[col].sample(n, replace=True, random_state=int(rng.integers(1e9))).values
    d = pd.DataFrame({'p': tri(inp['p']), 'r': draw_r(n), '체험가격': pick('체험가격'),
                      'c': pick('c_자연완주율'), 'q_b': tri(inp['qb']), '문보트가격': tri(inp['boat']),
                      'q_p': tri(inp['qp']), 'k': tri(inp['k']), '팝업객단가': pick('팝업객단가'),
                      '반사실': rng.beta(*inp['cf'], n)})
    d['lam'] = (d['c'] + (1 - d['c']) * draw_new(n)) / d['c']        # 저녁 이동 배수(설문)
    return d


def model(inp, d):
    s = inp['T'] / 8
    NR = JG_M * 8 * s * (inp['n1'] / POP_ORIG) * d['p']
    ND = NR * d['r']
    lam = d['lam'] if inp.get('lam') is None else inp['lam']   # 저녁 이동 배수: None = 설문 추정, 1 = 늘리지 않음(보수)
    M0 = NR * d['c']                                          # 연결이 없어도 원래 저녁에 월영교로 가는 인증자
    M = M0 * lam
    NB = M * d['q_b']
    keep = 1 - d['반사실'] - inp.get('disc', 0.0)                # 할인 체험권: 새로 한 사람은 할인가, 원래 할 사람은 할인만큼 덜 냄
    G1 = ND * d['체험가격'] + NB * d['문보트가격']
    E1 = G1 * keep
    Gp_r = M * d['q_p'] * d['팝업객단가']
    Gp_d = OPP3 * s * d['팝업객단가'] * FOOD * d['k'] * (inp['n3'] / BOOTH_REF)
    E3 = (Gp_r + Gp_d) * (1 - d['반사실'])
    days = WKND_DAYS * s
    base_buy = FOOD * d['k'] * (inp['n3'] / BOOTH_REF)          # 릴레이 없이도 월영교 저녁 방문객이 팝업에 쓰는 비율(객단가 환산)
    L_boat = NB * d['문보트가격'] * keep                        # 연결이 있어야 생기는 저녁 문보트 결제
    L_pop = M * np.maximum(d['q_p'] - base_buy, 0) * d['팝업객단가'] * (1 - d['반사실'])
    LINK = L_boat + L_pop
    return pd.DataFrame({
        '연결_문보트': L_boat, '연결_팝업': L_pop, '연결효과': LINK, '연결비중': LINK / (E1 + E3), '연결_교통몫': LINK * NOCAR,
        '구성_낮체험': ND * d['체험가격'] * keep, '구성_팝업단독': E3 - L_pop,
        '인증': NR, '인증_월': NR / (8 * s), '주민증대비_증가율': NR / (8 * s) / JM26,
        '낮체험': ND, '문보트': NB, '체험결제합': ND + NB, '하루_이동': M / days, '하루_이동_보수': M0 / days, '새이동_하루': (M - M0) / days,
        '하루_택시운행': np.ceil(M / days / 4), '팝업_하루': (M * d['q_p'] + Gp_d / d['팝업객단가']) / days,
        '체험총지출': G1, '체험추가소비': E1, '팝업총지출': Gp_r + Gp_d, '팝업추가소비': E3, '추가소비합': E1 + E3,
        '지표1_원': EXP26 + E1 / (V26 * s), '지표1_증가율': E1 / (V26 * s) / EXP26,
        '격차기여율': E1 / (GAP * s), '지표2_강남동': E3 / (GN_TOUR * s)})


qs = lambda x: {'P5': float(np.quantile(x, .05)), 'P50': float(np.quantile(x, .5)), 'P95': float(np.quantile(x, .95))}
R = {'p근거': {'하한_주민증GLM': P_LO, '최빈_반값여행': P_MD, '상한_하회': P_HI, 'GLM_원도심식음1곳_월이용': glm_m},
     '고정값': {'목표': TARGET, '격차_8개월': GAP, '중구동_월방문': JG_M, '월영교_저녁기회': OPP3, '강남동소비': GN_TOUR}}
OUT = {}
for sc in SCN:
    d = draw(sc, N)
    o = model(sc, d)
    OUT[sc['이름']] = (d, o)
    res = {k: qs(o[k]) for k in o.columns}
    res['목표도달확률'] = float((o['지표1_원'] >= TARGET).mean())
    con = {}
    for tgt in ('체험결제합', '추가소비합', '지표1_원'):
        rho = {k: spearmanr(d[k], o[tgt])[0] for k in d.columns}
        rho = {k: (0.0 if np.isnan(v) else v) for k, v in rho.items()}
        tot = sum(v ** 2 for v in rho.values())
        con[tgt] = {k: float(v ** 2 / tot) for k, v in sorted(rho.items(), key=lambda x: -abs(x[1]))}
    res['분산기여'] = con
    med = d.median()
    per_p = JG_M * 8 * (sc['n1'] / POP_ORIG) * (med['r'] * med['체험가격'] + med['c'] * med['lam'] * med['q_b'] * med['문보트가격']) * (1 - med['반사실'] - DISC)
    res['목표_필요_p'] = float(GAP / per_p)
    res['입력'] = {k: (list(v) if isinstance(v, tuple) else v) for k, v in sc.items()}
    R[sc['이름']] = res

# 연결 효과 민감도: 연결이 저녁 이동을 늘리는 배수 lam (1 = 보수, 설문 = 본 결과, 1.5·2.0 = 참고)
for sc in SCN:
    sens = {}
    for lam in (1.0, None, 1.5, 2.0):
        d = draw({**sc, 'lam': lam}, N)
        o = model({**sc, 'lam': lam}, d)
        sens['설문' if lam is None else str(lam)] = {'연결효과_P50': float(o['연결효과'].median()), '연결비중_P50': float(o['연결비중'].median()),
                          '문보트_P50': float(o['문보트'].median()), '추가소비_P50': float(o['추가소비합'].median()),
                          '하루이동_P50': float(o['하루_이동'].median()), '새이동_P50': float(o['새이동_하루'].median())}
    R[sc['이름']]['연결민감도'] = sens
    o = OUT[sc['이름']][1]
    R[sc['이름']]['구성_평균'] = {k: float(o[k].mean()) for k in ('구성_낮체험', '연결_문보트', '연결_팝업', '구성_팝업단독')}
R['NOCAR'] = NOCAR

C = P['C_월영야행']
up_day = (np.exp(C['월FE_95%'][1]) - 1) * (GN_TOUR / 8)
for nm, (d, o) in OUT.items():
    day = o['팝업추가소비'] / (WKND_DAYS * BASE['T'] / 8)
    R[nm]['검증_월영야행'] = {'행사1일_상한_원': float(up_day), '팝업하루_P50': float(day.median()), '팝업하루_P95': float(day.quantile(.95)),
                         '상한이내_비율': float((day <= up_day).mean())}

# ── 임계값(9/27): 참여율을 고정하면 격차를 얼마나 메우나 / 격차의 몇 %를 메우려면 참여율이 얼마여야 하나 ──
# 격차기여율은 참여율 p에 비례하므로, 나머지 값을 뽑은 뒤 (격차기여율 ÷ p)의 중앙값 × p = p를 고정했을 때의 중앙값이다.
# 위 결과와 난수 순서가 겹치지 않도록 맨 뒤에서 뽑는다.
P_GRID = (0.001, 0.005, 0.01, 0.02, 0.04, 0.05, 0.10)
FRAC = (0.25, 0.5, 1.0)
TH = {'참여율': list(P_GRID), '격차비율_P50': {}, '필요참여율_P50': {}}
for sc in SCN:
    d = draw(sc, N)
    g = model(sc, d)['격차기여율'] / d['p']
    TH['격차비율_P50'][sc['이름']] = [float(np.median(g) * p) for p in P_GRID]
    TH['필요참여율_P50'][sc['이름']] = {str(f): float(f / np.median(g)) for f in FRAC}
RPOOL = draw_r(200000)
LPOOL = draw(WIDE, 50000)['lam'].values
TH['r_분포'] = qs(RPOOL)
R['임계값'] = TH
R['설문보정'] = {'r': qs(RPOOL), 'r_평균': float(RPOOL.mean()), 'lam': qs(LPOOL), '할인율': DISC, '실현율': SV['실현율'],
               'r_매우': SV['r_매우'], 'lam_차_매우': SV['lam_차_매우'], 'lam_차없음_매우': SV['lam_차없음_매우'], '비이동자': SV['lam_비이동자'],
               'r_긍정': SV['r_긍정'], 'lam_차_긍정': SV['lam_차_긍정'], 'lam_차없음_긍정': SV['lam_차없음_긍정'], '해석_섞기': SV['해석_섞기'], '운영개월': BASE['T']}

# ── 입력 상관 민감도(9/27, 선행연구 대조): 위에서는 입력을 서로 독립으로 뽑았다.
# 참여율 p가 높은 곳은 체험 결제율 r도 높을 수 있으므로, 둘을 가우스 코퓰라로 묶어(순위 상관 ≈ ρ) 결과 범위가 얼마나 바뀌는지 본다.
# 위 결과와 난수 순서가 겹치지 않도록 맨 뒤에서 뽑는다.
from scipy.stats import norm, triang
COR = {}
for sc in SCN:
    COR[sc['이름']] = {}
    for rho in (0.0, 0.5, 0.8):
        d = draw(sc, N)
        u = norm.cdf(rng.multivariate_normal([0, 0], [[1, rho], [rho, 1]], N))
        a, m, b = sc['p']
        d['p'] = triang.ppf(u[:, 0], (m - a) / (b - a), loc=a, scale=b - a)
        d['r'] = np.quantile(RPOOL, u[:, 1])
        o = model(sc, d)
        COR[sc['이름']][str(rho)] = {'격차기여율': qs(o['격차기여율']), '추가소비합': qs(o['추가소비합'])}
R['상관민감도'] = COR

# ── 참여율 3단계 시나리오(9/27 저녁, 사용자 결정): 83곳, 참여율만 고정하고 나머지는 1만 회 추출 ──
# 기준 2% = 확대안 최빈 / 흥행 4% = 강진 반값여행 2025 참여 규모를 안동 방문 규모로 옮긴 수준의 약 2배 / 목표 10% = 참여 식당 전원 안내(설계 목표)
# 저녁 이동은 설문 배수(본 결과)와 배수 1(보수)을 같은 추출로 함께 낸다. 맨 뒤에서 뽑아 위 결과의 난수 순서는 그대로다.
KEYS = ('인증_월', '체험결제합', '문보트', '하루_이동', '새이동_하루', '팝업_하루', '하루_택시운행', '지표1_증가율', '격차기여율',
        '체험추가소비', '팝업추가소비', '추가소비합', '연결효과', '연결비중', '지표2_강남동')
SC3 = {}
for nm, p_ in (('기준', 0.02), ('흥행', 0.04), ('목표', 0.10)):
    sc = {**WIDE, '이름': nm, 'p': (p_, p_, p_)}
    d = draw(sc, N)
    o, o1 = model(sc, d), model({**sc, 'lam': 1.0}, d)
    SC3[nm] = {'참여율': p_, **{k: qs(o[k]) for k in KEYS}, '목표도달확률': float((o['지표1_원'] >= TARGET).mean()),
               '보수_lam1': {k: qs(o1[k]) for k in ('하루_이동', '문보트', '팝업_하루', '연결효과', '추가소비합', '지표2_강남동', '지표1_증가율')}}
R['시나리오'] = SC3
json.dump(R, open(f'{D}/시뮬레이션결과.json', 'w'), ensure_ascii=False, indent=1, default=float)

# ── 그림 (브리핑 PDF와 같은 글꼴·색) ───────────────────────────────────
plt.rcParams.update({'font.family': 'NanumGothic', 'axes.unicode_minus': False, 'svg.fonttype': 'path',
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#999999',
                     'axes.titleweight': 'bold', 'axes.titlesize': 11, 'font.size': 9.5})
RED, RED_L, GRAY, GRAY_L = '#D64541', '#F1A9A0', '#8C8C8C', '#CFCFCF'


def save(fig, name):
    for ext in ('png', 'svg'):
        fig.savefig(f'{D}/{name}.{ext}', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)


# g1 하루 동선
fig, ax = plt.subplots(figsize=(9, 3.1))
rows = [('1단계 원도심', [(11, 14, '식사 · 영수증 QR 인증', RED_L), (14, 18, '낮 체험 (탈 만들기·공예, 18시 마감)', RED)]),
        ('2단계 이동', [(18.5, 19.5, '', GRAY)]),
        ('3단계 월영교', [(19, 23, '문보트 · 야간 팝업(식사·주점)', RED)]),
        ('귀가', [(21, 22, '', GRAY)])]
NOTE = {'2단계 이동': (19.6, '원도심 → 월영교 3.2km (택시 재배치)'), '귀가': (22.1, '안동역 막차 21~22시')}
for i, (lab, segs) in enumerate(rows[::-1]):
    for a, b, t, col in segs:
        ax.barh(i, b - a, left=a, color=col, height=.55, edgecolor='white')
        ax.text((a + b) / 2, i, t, ha='center', va='center', fontsize=7.8, color='white' if col in (RED, GRAY) else '#333')
    if lab in NOTE:
        ax.text(NOTE[lab][0], i, NOTE[lab][1], va='center', fontsize=7.8, color='#333')
ax.axvspan(18.5, 21, color='#FFE599', alpha=.45, zorder=0)
ax.text(19.75, len(rows) - .35, '릴레이 저녁 창 18:30~21:00 (112번 막차 18:45 이후 대중교통 0회)', ha='center', fontsize=8.3, fontweight='bold')
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows[::-1]])
ax.set_xlim(10.5, 23.5); ax.set_ylim(-.5, len(rows) - .1)
ax.set_xticks(range(11, 24)); ax.set_xticklabels([f'{h}시' for h in range(11, 24)], fontsize=8)
ax.set_title('이어드림 하루 동선: 낮 체험은 원도심, 저녁 체험은 월영교 문보트', loc='left')
save(fig, 'g1_하루동선')

# g2 산출 지표 전후
b = R['기본안']; w = R['확대안']
items = [('원도심 참여 식당', 0, 20, 83), ('19시 이후 원도심→월영교\n하루 운행 횟수', 0, b['하루_택시운행']['P50'], w['하루_택시운행']['P50']),
         ('월영교 21시까지\n식사 가능 업소', 3, 3 + 8, 3 + 8), ('월영교 1km 주점', 0, 8, 8)]
fig, ax = plt.subplots(figsize=(9, 3.0))
x = np.arange(len(items)); wd = .26
for j, (lab, col) in enumerate((('현재', GRAY_L), ('기본안', RED_L), ('확대안', RED))):
    vals = [it[1 + j] for it in items]
    bars = ax.bar(x + (j - 1) * wd, vals, wd, color=col, label=lab)
    for bb, v in zip(bars, vals):
        ax.text(bb.get_x() + bb.get_width() / 2, v + .8, f'{v:g}', ha='center', fontsize=8)
ax.set_xticks(x); ax.set_xticklabels([it[0] for it in items], fontsize=8.5); ax.legend(frameon=False, fontsize=8.5)
ax.set_title('산출 지표: 사업을 하면 확정되는 변화 (팝업 부스 8개 기준)', loc='left'); ax.set_yticks([])
ax.spines['left'].set_visible(False)
save(fig, 'g2_산출지표')

# g3 안동 전체 지표 기여 분포
fig, axs = plt.subplots(1, 2, figsize=(9, 3.0))
for ax, nm, col in zip(axs, ('기본안', '확대안'), (RED_L, RED)):
    o = OUT[nm][1]['지표1_증가율'] * 100
    o = o[o <= np.quantile(o, .99)]
    ax.hist(o, bins=50, color=col, edgecolor='white', linewidth=.3)
    r_ = R[nm]['지표1_증가율']
    ax.axvline(r_['P50'] * 100, color='#333', lw=1.2)
    if nm == '확대안':
        tg = (TARGET / EXP26 - 1) * 100
        ax.axvline(tg, color='#333', lw=1, ls='--')
        ax.text(tg, ax.get_ylim()[1] * .9, f' 목표 +{tg:.1f}%\n 도달 확률 {R[nm]["목표도달확률"]:.0%}', fontsize=8)
    ax.set_title(f"{nm}: 중앙 +{r_['P50'] * 100:.1f}% (90% 구간 +{r_['P5'] * 100:.1f}~+{r_['P95'] * 100:.1f}%)", fontsize=9.5, loc='left')
    ax.set_xlabel('방문당 체험·문화 소비 증가율(%)', fontsize=8.5); ax.set_yticks([]); ax.spines['left'].set_visible(False)
fig.suptitle(f'안동 전체 지표에 대한 기여 (회복 목표 +{(TARGET / EXP26 - 1) * 100:.1f}%, 몬테카를로 1만 회)', x=.01, ha='left', fontweight='bold', fontsize=11)
fig.tight_layout()
save(fig, 'g3_기여분포')

# g4 분산 기여(확대안, 추가 소비)
lab = {'p': '참여(인증)율 p', 'r': '낮 체험 결제율 r', 'lam': '저녁 이동 배수', '체험가격': '체험 가격', 'c': '자연 완주율 c', 'q_b': '문보트 결제율',
       '문보트가격': '문보트 가격', 'q_p': '팝업 구매율', 'k': '팝업 강도 k', '팝업객단가': '팝업 객단가', '반사실': '반사실 몫'}
tag = {'p': '가정', 'r': '설문', 'lam': '설문', '체험가격': '실측', 'c': '추정', 'q_b': '가정', '문보트가격': '미확인', 'q_p': '가정', 'k': '가정',
       '팝업객단가': '사례', '반사실': '가정'}
con = R['확대안']['분산기여']['추가소비합']
ks = [k for k in con if con[k] >= .01][:7][::-1]
fig, ax = plt.subplots(figsize=(9, 2.9))
ax.barh(range(len(ks)), [con[k] * 100 for k in ks], color=[RED if tag[k] == '가정' else GRAY for k in ks], height=.6)
for i, k in enumerate(ks):
    ax.text(con[k] * 100 + .6, i, f'{con[k] * 100:.0f}%', va='center', fontsize=8)
ax.set_yticks(range(len(ks))); ax.set_yticklabels([f'{lab[k]} [{tag[k]}]' for k in ks], fontsize=8.5)
ax.set_xlabel('추가 소비의 불확실성 중 차지하는 비중(%) · 빨강 = 가정(현장·시행 후 측정 대상)', fontsize=8.5)
ax.set_title('결과를 가장 크게 흔드는 값 (확대안)', loc='left')
save(fig, 'g4_분산기여')

# g5 추가 소비 구성: 단계 단독 vs 연결이 있어야 생기는 몫
fig, ax = plt.subplots(figsize=(9, 2.7))
parts = [('구성_낮체험', '1단계 낮 체험(단독)', GRAY_L), ('구성_팝업단독', '3단계 팝업(단독)', GRAY),
         ('연결_문보트', '연결: 저녁 문보트', RED), ('연결_팝업', '연결: 팝업 추가 구매', RED_L)]
for i, nm in enumerate(('기본안', '확대안')):
    left = 0
    tot = sum(R[nm]['구성_평균'][k] for k, _, _ in parts)
    for k, lab_, col in parts:
        v = R[nm]['구성_평균'][k] / tot * 100
        ax.barh(i, v, left=left, color=col, height=.55, label=lab_ if i == 0 else None, edgecolor='white')
        if v >= 4:
            ax.text(left + v / 2, i, f'{v:.0f}%', ha='center', va='center', fontsize=8, color='white' if col in (RED, GRAY) else '#333')
        left += v
ax.set_yticks([0, 1]); ax.set_yticklabels(['기본안', '확대안']); ax.set_xlim(0, 100); ax.set_xlabel('안동 내 추가 소비(평균)의 구성 %', fontsize=8.5)
ax.legend(ncol=4, frameon=False, fontsize=8, loc='upper center', bbox_to_anchor=(.5, -.32))
save(fig, 'g5_연결효과')

for nm in ('기본안', '확대안'):
    r_ = R[nm]
    print(f"  연결효과 {r_['연결효과']['P50']/1e8:.3f}억, 비중 {r_['연결비중']['P50']:.1%}, 교통몫 {r_['연결_교통몫']['P50']/1e8:.4f}억, 구성 { {k: round(v/1e8,3) for k,v in r_['구성_평균'].items()} }")
    print('  연결민감도', {k: (round(v['연결효과_P50']/1e8,3), round(v['연결비중_P50'],3)) for k, v in r_['연결민감도'].items()})

for nm in ('기본안', '확대안'):
    r_ = R[nm]
    print(f"\n[{nm}] 인증 {r_['인증']['P50']:,.0f} (월 {r_['인증_월']['P50']:,.0f}, 주민증 대비 +{r_['주민증대비_증가율']['P50']:.0%})")
    print(f"  체험 결제 {r_['체험결제합']['P50']:,.0f}건 (낮 {r_['낮체험']['P50']:,.0f} + 문보트 {r_['문보트']['P50']:,.0f}), 90% {r_['체험결제합']['P5']:,.0f}~{r_['체험결제합']['P95']:,.0f}")
    print(f"  하루 이동 {r_['하루_이동']['P50']:.1f}명 · 택시 {r_['하루_택시운행']['P50']:.0f}회, 팝업 하루 {r_['팝업_하루']['P50']:.0f}명")
    print(f"  지표① +{r_['지표1_증가율']['P50']:.2%} ({r_['지표1_증가율']['P5']:.2%}~{r_['지표1_증가율']['P95']:.2%}), 격차 기여 {r_['격차기여율']['P50']:.1%}, 목표확률 {r_['목표도달확률']:.1%}, 필요 p {r_['목표_필요_p']:.1%}")
    print(f"  지표② 강남동 +{r_['지표2_강남동']['P50']:.2%}, 추가소비 {r_['추가소비합']['P50']/1e8:.2f}억 ({r_['추가소비합']['P5']/1e8:.2f}~{r_['추가소비합']['P95']/1e8:.2f})")
    print('  분산기여', {k: round(v, 2) for k, v in r_['분산기여']['추가소비합'].items() if v > .01})
    print('  검증', r_['검증_월영야행'])
    print('  임계값 격차비율', [f'{x:.1%}' for x in R['임계값']['격차비율_P50'][nm]], '필요 p', {k: f'{v:.2%}' for k, v in R['임계값']['필요참여율_P50'][nm].items()})
print('\n설문 보정', {k: v for k, v in R['설문보정'].items() if k in ('r', 'lam')})
for nm, v in R['시나리오'].items():
    print(f"[{nm} {v['참여율']:.0%}] 체험결제 월 {v['체험결제합']['P50']/BASE['T']:,.0f} · 저녁이동 하루 {v['하루_이동']['P50']:.0f}(새로 {v['새이동_하루']['P50']:.0f}, 보수 {v['보수_lam1']['하루_이동']['P50']:.0f})"
          f" · 팝업 하루 {v['팝업_하루']['P50']:.0f} · 방문당 +{v['지표1_증가율']['P50']:.1%} · 격차 {v['격차기여율']['P50']:.0%} · 추가소비 {v['추가소비합']['P50']/1e8:.2f}억 · 도달 {v['목표도달확률']:.0%}")
