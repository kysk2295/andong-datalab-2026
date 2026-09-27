# -*- coding: utf-8 -*-
"""핵심 그림 5장 (2026-09-28): 문제 → 근거 → 해법 → 효과를 그림 한 장씩으로.

서식4·발표에 넣을 후보. 숫자는 전부 앞단 JSON에서 읽는다(교수브리핑 수치.json, 시뮬레이션결과.json).
  k1 문제 1  안동 vs 전국 중앙: 방문당 체험·문화 소비 증감률
  k2 문제 2  월영교: 방문 점유율 vs 소비 건수 점유율 (철도공사 8대 도시, 데이터랩과 섞지 않음)
  k3 근거    방문 상위 읍면동의 주민증 혜택업체 수
  k4 해법    이어드림 하루 동선 (기존 g1_하루동선.png 그대로 사용)
  k5 효과    참여율 3단계별 방문당 체험·문화 소비(원): 지금 → 시행 후 (9/28 격차 % 대신 원으로)
  k6 효과    참여율 3단계별 추가 소비와 월영교 새 저녁 이동
  k7 서식4   4)칸 표 대신 넣을 두 패널 그림(수상작 형식: 번호 제목 + 테두리 + 아래 캡션 띠)
실행: .venv_pdf/bin/python scripts/핵심그림.py
"""
import json, shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / '보고서/핵심그림_20260928'
OUT.mkdir(parents=True, exist_ok=True)
R = json.loads((ROOT / '보고서/교수브리핑_20260922/수치.json').read_text(encoding='utf-8'))
S = json.loads((ROOT / '보고서/성과도출_20260922/시뮬레이션결과.json').read_text(encoding='utf-8'))
G1 = ROOT / '보고서/성과도출_20260922/g1_하루동선.png'

plt.rcParams.update({'font.family': 'NanumGothic', 'axes.unicode_minus': False,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#999999',
                     'axes.titleweight': 'bold', 'axes.titlesize': 13, 'font.size': 11})
RED, GRAY_L, INK = '#D64541', '#CFCFCF', '#333333'


def save(fig, name):
    fig.savefig(OUT / name, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)


# ── k1 문제 1: 안동 vs 전국 중앙 ──
E = R['체험문화']
fig, ax = plt.subplots(figsize=(6.4, 2.6))
lab, val = ['전국 중앙값', '안동'], [E['중앙_변화율'], E['안동_변화율']]
ax.barh(lab, val, height=0.55, color=[GRAY_L, RED])
for i, v in enumerate(val):
    ax.text(v - 0.4, i, f'{v:+.1f}%', va='center', ha='right', fontsize=13, fontweight='bold', color=RED if i else INK)
ax.axvline(0, color='#555555', lw=0.8)
ax.set_xlim(-22, 1)
ax.set_xticks([])
ax.spines['bottom'].set_visible(False)
ax.get_yticklabels()[1].set_color(RED)
ax.get_yticklabels()[1].set_fontweight('bold')
ax.set_title('방문 1회당 체험·문화 소비, 안동은 전국보다 크게 줄고 있다', loc='left')
ax.text(0, -0.28, f"2024 → 2026년 1~8월. 안동 {E['안동_2024']:.1f}원 → {E['안동_2026']:.1f}원, "
        f"{E['시군수']}개 시·군 중 감소폭 {E['안동_감소순위']}번째 (한국관광 데이터랩, 외지인)",
        transform=ax.transAxes, fontsize=9, color='#666666')
save(fig, 'k1_문제1_체험소비.png')

# ── k2 문제 2: 월영교 방문 vs 소비 ──
WG = next(r for r in R['철도공사'] if r['관광지명'] == '월영교')
OPEN = [w for w in R['월영교조사'] if w['상태'] == '영업']
MEAL_21 = [w for w in OPEN if w['상권업종중분류명'].strip() in ('한식', '서양식') and w['영업종료'] >= '21:00']
BAR = [w for w in OPEN if w['상권업종중분류명'].strip() == '주점']
fig, ax = plt.subplots(figsize=(6.4, 3.2))
lab, val = ['방문 점유율', '소비 건수 점유율'], [WG['방문점유율_pct'], WG['방문객소비건수점유율_pct']]
b = ax.bar(lab, val, width=0.5, color=[GRAY_L, RED])
for r, v in zip(b, val):
    ax.text(r.get_x() + r.get_width() / 2, v + 0.3, f'{v:.2f}%', ha='center', va='bottom', fontsize=14, fontweight='bold')
ax.set_ylim(0, 19)
ax.set_yticks([])
ax.spines['left'].set_visible(False)
ax.set_title(f"월영교: 사람은 오는데 쓸 곳이 없다 (소비 ÷ 방문 = {WG['소비방문배율']:.2f})", loc='left')
ax.text(0, -0.2, f"반경 1km 영업 음식점 {len(OPEN)}곳 중 21시까지 식사 {len(MEAL_21)}곳, 주점 {len(BAR)}곳\n"
        '한국철도공사 8대 도시(안동) 가명결합 분석, 2022.4~6 (데이터랩 수치와 별개 체계)',
        transform=ax.transAxes, fontsize=9, color='#666666', va='top')
save(fig, 'k2_문제2_월영교.png')

# ── k3 근거: 방문 상위 읍면동의 혜택업체 ──
BP = R['혜택배치']
rows = BP[:7] + [x for x in BP if x['행정동'] == '도산면']
rows = rows[::-1]
fig, ax = plt.subplots(figsize=(6.4, 3.6))
hl = ('중구동', '도산면')
ax.barh([x['행정동'] for x in rows], [x['방문점유율'] for x in rows], height=0.6,
        color=[RED if x['행정동'] in hl else GRAY_L for x in rows])
for i, x in enumerate(rows):
    strong = x['행정동'] in hl
    ax.text(x['방문점유율'] + 0.2, i, f"혜택 {x['혜택업체']}곳", va='center', fontsize=10.5,
            color=RED if strong else '#444444', fontweight='bold' if strong else 'normal')
for t in ax.get_yticklabels():
    if t.get_text() in hl:
        t.set_color(RED)
        t.set_fontweight('bold')
ax.set_xlim(0, 15.5)
ax.set_xlabel('외지인 방문 점유율(%)')
ax.set_title('사람이 가장 많이 오는 원도심(중구동)에 혜택이 없다', loc='left')
ax.text(0, -0.24, '방문 상위 7곳 + 혜택이 가장 많은 도산면. 2026년 1~8월, 주민증 혜택업체 27곳(안동시 정보공개)',
        transform=ax.transAxes, fontsize=9, color='#666666')
save(fig, 'k3_근거_혜택배치.png')

# ── k4 해법: 하루 동선 (기존 그림) ──
shutil.copy(G1, OUT / 'k4_해법_하루동선.png')

# ── k5 효과: 참여율별 방문당 체험·문화 소비 (9/28 팀 요청: 기존 수치 대비 얼마나 늘어나는지, 격차 % 대신 원) ──
SC = S['시나리오']
E = R['체험문화']
now, y24, nat = E['안동_2026'], E['안동_2024'], E['안동_2024'] * (1 + E['중앙_변화율'] / 100)
rows = [('2024년', y24, GRAY_L), ('지금 (2026년)', now, '#8C8C8C')] + \
       [(f"{n} · 참여 {SC[n]['참여율'] * 100:.0f}%", now * (1 + SC[n]['지표1_증가율']['P50']), c)
        for n, c in (('기준', '#F0B3B0'), ('흥행', '#E88A85'), ('목표', RED))]
fig, ax = plt.subplots(figsize=(6.8, 3.4))
ys = list(range(len(rows)))[::-1]
ax.axvline(nat, color='#555555', lw=0.9, ls='--')
ax.text(nat - 0.6, len(rows) - 0.45, f'전국처럼 줄었다면 {nat:.1f}원', ha='right', va='center', fontsize=9, color='#555555')
for y, (lab, v, c) in zip(ys, rows):
    if lab.startswith(('기준', '흥행', '목표')):
        ax.annotate('', xy=(v, y), xytext=(now, y), arrowprops=dict(arrowstyle='-|>', color=c, lw=2.2))
        ax.text(v + 0.8, y, f'{v:.1f}원  +{v - now:.1f}원', va='center', fontsize=11, fontweight='bold', color=INK)
    else:
        ax.text(v + 0.8, y, f'{v:.1f}원', va='center', fontsize=11, color=INK)
    ax.scatter([v], [y], s=90, color=c, zorder=3, edgecolor='white')
ax.set_yticks(ys)
ax.set_yticklabels([r[0] for r in rows])
ax.set_xlim(145, 198)
ax.set_ylim(-0.6, len(rows) - 0.1)
ax.set_xticks([])
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.tick_params(axis='y', length=0)
ax.set_title('참여가 늘면 방문 1회당 체험·문화 소비가 얼마나 돌아오나', loc='left')
ax.text(0, -0.12, '원도심 식당 83곳 운영, 참여율 = 원도심 방문객 중 영수증 인증 비율. 시행 전 예측(1만 번 계산의 가운데 값)',
        transform=ax.transAxes, fontsize=8.5, color='#666666')
save(fig, 'k5_효과_참여율.png')

# ── k6 효과: 참여율별 추가 소비와 월영교 저녁 이동 ──
lab = [f"{n}\n참여 {SC[n]['참여율'] * 100:.0f}%" for n in ('기준', '흥행', '목표')]
col = ['#F0B3B0', '#E88A85', RED]
money = [SC[n]['추가소비합']['P50'] / 1e8 for n in ('기준', '흥행', '목표')]
move = [SC[n]['새이동_하루']['P50'] for n in ('기준', '흥행', '목표')]
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0))
for ax, vals, t, fmt in ((axs[0], money, '안동에서 늘어나는 소비 (연간)', '{:.2f}억 원'),
                         (axs[1], move, '월영교에 새로 가는 저녁 이동 (주말 하루)', '{:.0f}명')):
    b = ax.bar(lab, vals, width=0.6, color=col)
    for r, v in zip(b, vals):
        ax.text(r.get_x() + r.get_width() / 2, v * 1.02, fmt.format(v), ha='center', va='bottom', fontsize=11, fontweight='bold')
    ax.set_ylim(0, max(vals) * 1.18)
    ax.set_yticks([])
    ax.spines['left'].set_visible(False)
    ax.set_title(t, loc='left', fontsize=11)
fig.text(0.01, -0.04, '할인액과 원래 썼을 돈을 뺀 순수 증가분. 시행 전 예측(1만 번 계산의 가운데 값, 2026년 1~8월 월평균 × 12)',
         fontsize=8.5, color='#666666')
fig.tight_layout()
save(fig, 'k6_효과_소비이동.png')

# ── k7 서식4 4)칸용 (9/28 사용자 요청: 표 대신 수상작처럼 "번호 제목 + 테두리 패널 두 개 + 아래 출처 캡션 띠") ──
# 색: 참여율 3단계 = 빨강 한 색상 순차(밝음 → 어두움, 밝기 단조), 지금·2024 = 회색. 모든 점·막대에 값과 이름을 직접 적어 색만으로 구분하지 않는다.
SEQ = ['#E8918B', '#D2524C', '#A12B27']
BOX, HEAD = '#BFBFBF', '#222222'
fig = plt.figure(figsize=(7.2, 3.35))
cap_h = 0.13                                               # 아래 캡션 띠 높이(그림 비율)
panels = [(0.015, '1. 참여율별 방문 1회당 체험·문화 소비 (외지인, 연간 환산)', '방문 1회당 체험·문화 소비'),
          (0.515, '2. 참여율별 안동에서 늘어나는 소비 (연간, 순수 증가분)', '안동 추가 소비')]
for x0, head, inner in panels:
    fig.text(x0, 0.955, head, fontsize=8.6, fontweight='bold', color=HEAD, va='top')
    fig.patches.append(plt.Rectangle((x0, cap_h + 0.04), 0.47, 0.72, transform=fig.transFigure, fill=False, ec=BOX, lw=0.8))
    fig.text(x0 + 0.012, cap_h + 0.735, inner, fontsize=8.4, fontweight='bold', color=INK, va='top')
fig.patches.append(plt.Rectangle((0.003, 0.003), 0.994, 0.994, transform=fig.transFigure, fill=False, ec=BOX, lw=0.8))
fig.add_artist(plt.Line2D([0.003, 0.997], [cap_h, cap_h], transform=fig.transFigure, color=BOX, lw=0.8))
fig.text(0.5, cap_h / 2, '<한국관광 데이터랩 + 이어드림 기대효과 모의실험> 참여율별 체험 소비 회복과 추가 소비',
         ha='center', va='center', fontsize=9, color=INK)

# 패널 1: 지금 → 참여율별 도착점(원). 막대 대신 점·화살표로 0 기준선 없이 차이를 보여 준다.
ax = fig.add_axes([0.13, cap_h + 0.07, 0.34, 0.56])
rows = [('2024년', y24, GRAY_L), ('지금', now, '#8C8C8C')] + \
       [(f"참여 {SC[n]['참여율'] * 100:.0f}%", now * (1 + SC[n]['지표1_증가율']['P50']), c) for n, c in zip(('기준', '흥행', '목표'), SEQ)]
ys = list(range(len(rows)))[::-1]
for y_a, y_b in ((-0.6, 0.62), (1.38, len(rows) - 0.2)):          # 참여 4% 값 글자와 겹치는 구간은 선을 끊는다
    ax.plot([nat, nat], [y_a, y_b], color='#777777', lw=0.8, ls='--', zorder=1)
ax.text(nat - 0.8, len(rows) - 0.55, f'전국 평균만큼 줄었다면 {nat:.1f}원', ha='right', va='center', fontsize=6.8, color='#555555')
for y, (lab, v, c) in zip(ys, rows):
    if lab.startswith('참여'):
        ax.annotate('', xy=(v - 0.6, y), xytext=(now, y), arrowprops=dict(arrowstyle='-|>', color=c, lw=1.8, mutation_scale=9))
        ax.text(v + 1.2, y, f'{v:.1f}원 (+{v - now:.1f})', va='center', fontsize=7.6, fontweight='bold', color=INK, zorder=4,
                bbox=dict(fc='white', ec='none', pad=0.6))
    else:
        ax.text(v + 1.2, y, f'{v:.1f}원', va='center', fontsize=7.6, color=INK, zorder=4, bbox=dict(fc='white', ec='none', pad=0.6))
    ax.scatter([v], [y], s=34, color=c, zorder=3, edgecolor='white', lw=1)
ax.set_yticks(ys); ax.set_yticklabels([r[0] for r in rows], fontsize=7.8)
ax.set_xlim(147, 200); ax.set_ylim(-0.6, len(rows) - 0.2)
ax.set_xticks([]); ax.tick_params(axis='y', length=0)
for sp in ('bottom', 'left'):
    ax.spines[sp].set_visible(False)

# 패널 2: 참여율별 추가 소비(억 원) 막대, 0 기준.
ax = fig.add_axes([0.56, cap_h + 0.16, 0.40, 0.48])
labs = [f"참여 {SC[n]['참여율'] * 100:.0f}%\n{n}" for n in ('기준', '흥행', '목표')]
vals = [SC[n]['추가소비합']['P50'] / 1e8 for n in ('기준', '흥행', '목표')]
b = ax.bar(labs, vals, width=0.52, color=SEQ)
for r, v in zip(b, vals):
    ax.text(r.get_x() + r.get_width() / 2, v + max(vals) * 0.03, f'{v:.2f}억 원', ha='center', va='bottom', fontsize=7.8, fontweight='bold', color=INK)
ax.set_ylim(0, max(vals) * 1.2); ax.set_yticks([])
ax.spines['left'].set_visible(False)
ax.tick_params(axis='x', labelsize=7.6, length=0)
fig.savefig(OUT / 'k7_서식4_기대효과.png', dpi=300, facecolor='white')
plt.close(fig)

# ── 한 장 모아 보기 (문제 → 근거 → 해법 → 효과 순서) ──
fig = plt.figure(figsize=(15, 13))
gs = fig.add_gridspec(3, 4, height_ratios=[1, 1.05, 1.05], hspace=0.1, wspace=0.05)
for f, cell in [('k1_문제1_체험소비.png', gs[0, :2]), ('k2_문제2_월영교.png', gs[0, 2:]),
                ('k3_근거_혜택배치.png', gs[1, :2]), ('k4_해법_하루동선.png', gs[1, 2:]), ('k5_효과_참여율.png', gs[2, 1:3])]:
    a = fig.add_subplot(cell)
    a.imshow(mpimg.imread(OUT / f))
    a.axis('off')
fig.savefig(OUT / '핵심그림_모아보기.png', dpi=110, bbox_inches='tight', facecolor='white')
print('저장:', OUT)
