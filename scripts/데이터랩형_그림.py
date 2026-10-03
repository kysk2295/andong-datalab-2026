# -*- coding: utf-8 -*-
"""데이터랩 화면 형식의 기대효과 그림 (2026-09-28, 사용자 요청: "실제 데이터랩처럼 자세하고 예쁘게")

수상작 서식4처럼 "1. 번호 제목 → 흰 카드(제목·ⓘ·태그·⋯, 격자, 아래 범례) → 아래 <출처> 캡션 띠" 형식.
  d1  위젯 1  안동시 월별 방문 1회당 체험·문화 소비 (외지인, 2024~2026년 1~8월)   ← 실제 데이터랩 카드·방문 자료
      위젯 2  참여율별 방문 1회당 체험·문화 소비 예측                              ← 시뮬레이션결과.json
  d2  위젯 3  참여율별 안동 추가 소비 (연간, 막대 = 가운데 값, 선 = 1만 번 계산 중 90% 범위)
      위젯 4  참여율별 월영교 주말 하루 이용 (새 저녁 이동 · 야간 팝업)
  d3  표      참여율별 기대효과 요약
숫자는 앞단 JSON과 원자료 로더(체험프레임_검증.py)에서 읽는다. 색: 참여율 = 빨강 한 색 순차, 두 계열 비교 = 파랑·주황(검증 통과).
실행: .venv_pdf/bin/python scripts/데이터랩형_그림.py
"""
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, FancyBboxPatch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from 체험프레임_검증 import visits, cards, per_visit   # 수치.json과 같은 로더

OUT = ROOT / '보고서/핵심그림_20260928'
OUT.mkdir(parents=True, exist_ok=True)
R = json.loads((ROOT / '보고서/교수브리핑_20260922/수치.json').read_text(encoding='utf-8'))
S = json.loads((ROOT / '보고서/성과도출_20260922/시뮬레이션결과.json').read_text(encoding='utf-8'))
SC = S['시나리오']
E = R['체험문화']
CARD = 'data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv'
EXP = ['문화서비스', '관광유원시설', '기타레저']

plt.rcParams.update({'font.family': 'NanumGothic', 'axes.unicode_minus': False, 'font.size': 8})
INK, SUB, MUTED, GRID, BORDER = '#222222', '#555555', '#888888', '#E6E6E6', '#C8C8C8'
TAG = '#3E7CB1'
SEQ = ['#E8918B', '#D2524C', '#A12B27']                   # 참여 2% · 4% · 10%
NOW, OLD = '#8C8C8C', '#C9C9C9'
BLUE, ORANGE = '#3B6FC4', '#E07B39'
YEAR = {2024: '#B5B5B5', 2025: '#8FB3E6', 2026: '#2A5DB0'}
NAMES = ('기준', '흥행', '목표')
P = lambda n, k, q='P50': SC[n][k][q]


def mn(x, d=1):
    return f'{x:.{d}f}'                      # 나눔고딕에 U+2212가 없어 하이픈 그대로


# ── 위젯 틀 ──────────────────────────────────────────────────────────
def widget(fig, x0, y0, w, h, num_title, title, tag):
    """번호 제목 + 흰 카드(제목 · ⓘ · 태그 · ⋯). 차트가 들어갈 축 영역(그림 좌표)을 돌려준다."""
    fig.text(x0, y0 + h + 0.018, num_title, fontsize=8.4, fontweight='bold', color=INK, va='bottom')
    fig.patches.append(FancyBboxPatch((x0, y0), w, h, boxstyle='round,pad=0,rounding_size=0.006', transform=fig.transFigure,
                                      fc='white', ec=BORDER, lw=0.8, zorder=-5))
    ty = y0 + h - 0.055
    t = fig.text(x0 + 0.014, ty, title, fontsize=8.6, fontweight='bold', color=INK, va='center')
    fig.canvas.draw()
    bb = t.get_window_extent().transformed(fig.transFigure.inverted())
    fig.text(bb.x1 + 0.016, ty, 'i', fontsize=5.8, fontweight='bold', color='white', va='center', ha='center',
             bbox=dict(boxstyle='circle,pad=0.28', fc='#BDBDBD', ec='none'))
    fig.text(bb.x1 + 0.036, ty, tag, fontsize=6.6, color='white', va='center',
             bbox=dict(boxstyle='round,pad=0.35,rounding_size=0.25', fc=TAG, ec='none'))
    fig.text(x0 + w - 0.014, ty, '···', fontsize=9, color=MUTED, va='center', ha='right')
    return x0 + 0.075, y0 + 0.17, w - 0.095, h - 0.33


def style_ax(ax, ylabel):
    ax.set_facecolor('white')
    for sp in ('top', 'right', 'left'):
        ax.spines[sp].set_visible(False)
    ax.spines['bottom'].set_color('#9E9E9E')
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(axis='both', colors=SUB, labelsize=7, length=0)
    ax.text(0, 1.03, f'({ylabel})', transform=ax.transAxes, fontsize=6.6, color=SUB, ha='right', va='bottom')   # 데이터랩처럼 단위를 축 위에


def legend(fig, x0, w, y, items):
    """카드 아래쪽 가운데 범례. items = [(이름, 색, 'line'|'bar'|'range')]"""
    hs = []
    for name, c, kind in items:
        if kind == 'dash':
            hs.append(Line2D([], [], color=c, lw=1.0, ls='--', label=name))
        elif kind == 'line':
            hs.append(Line2D([], [], color=c, lw=1.6, marker='o', ms=4, label=name))
        elif kind == 'range':
            hs.append(Line2D([], [], color=c, lw=1.2, marker='_', ms=7, label=name))
        else:
            hs.append(Rectangle((0, 0), 1, 1, fc=c, ec='none', label=name))
    fig.legend(handles=hs, loc='center', bbox_to_anchor=(x0 + w / 2, y), ncol=len(hs), frameon=False,
               fontsize=6.8, handlelength=1.6, columnspacing=1.4, labelcolor=SUB)


def frame(fig, caption, cap_h=0.1):
    fig.patches.append(Rectangle((0.004, 0.004), 0.992, 0.992, transform=fig.transFigure, fill=False, ec=BORDER, lw=0.8))
    fig.add_artist(Line2D([0.004, 0.996], [cap_h, cap_h], transform=fig.transFigure, color=BORDER, lw=0.8))
    fig.text(0.5, cap_h / 2, caption, ha='center', va='center', fontsize=8.6, color=INK)


# ── d1: 월별 추이(실제) + 참여율별 회복 예측 ─────────────────────────
mon = {y: [] for y in YEAR}
for y in YEAR:
    for m in range(1, 9):
        W, d = cards(CARD, y, [m])
        mon[y].append(float(per_visit(W, visits(y, [m]), d)[EXP].sum(axis=1)['안동시']))

fig = plt.figure(figsize=(7.4, 3.5))
CAP = 0.1
x1, y1, w1, h1 = 0.015, CAP + 0.035, 0.475, 0.77
ax = fig.add_axes(widget(fig, x1, y1, w1, h1, '1. 안동시 월별 방문 1회당 체험·문화 소비 (외지인, 1~8월)', '체험·문화 소비 추이', '외지인'))
style_ax(ax, '원')
xs = np.arange(1, 9)
for y, c in YEAR.items():
    ax.plot(xs, mon[y], color=c, lw=2.0 if y == 2026 else 1.3, marker='o', ms=3.4 if y == 2026 else 2.6, zorder=3 if y == 2026 else 2)
ax.set_xticks(xs); ax.set_xticklabels([f'{m}월' for m in xs])
ax.set_ylim(100, 300); ax.set_yticks(range(100, 301, 50))
ax.text(8.15, mon[2026][-1], f'{mon[2026][-1]:.0f}', fontsize=6.6, color=YEAR[2026], va='center', fontweight='bold')
ax.text(0.98, 0.97, f"1~8월 합계  {E['안동_2024']:.1f}원 (2024) → {E['안동_2026']:.1f}원 (2026), {mn(E['안동_변화율'])}%",
        transform=ax.transAxes, fontsize=6.8, color=INK, va='top', ha='right',
        bbox=dict(boxstyle='round,pad=0.3', fc='#F5F7FA', ec='none'))
legend(fig, x1, w1, y1 + 0.06, [(f'{y}년', c, 'line') for y, c in YEAR.items()])

x2 = 0.51
ax = fig.add_axes(widget(fig, x2, y1, w1, h1, '2. 참여율별 방문 1회당 체험·문화 소비 예측 (원도심 식당 83곳)', '체험·문화 소비 회복', '예측'))
style_ax(ax, '원')
now, y24 = E['안동_2026'], E['안동_2024']
nat = y24 * (1 + E['중앙_변화율'] / 100)
labs = ['2024년', '지금', '참여 2%', '참여 4%', '참여 10%']
vals = [y24, now] + [now * (1 + P(n, '지표1_증가율')) for n in NAMES]
cols = [OLD, NOW] + SEQ
b = ax.bar(labs, vals, width=0.56, color=cols, zorder=2)
for i, (r, v) in enumerate(zip(b, vals)):
    ax.text(r.get_x() + r.get_width() / 2, v + 3, f'{v:.1f}', ha='center', va='bottom', fontsize=6.9, color=INK, fontweight='bold' if i > 1 else 'normal')
    if i > 1:
        ax.text(r.get_x() + r.get_width() / 2, v - 8, f'+{v - now:.1f}', ha='center', va='top', fontsize=6.4, color='white', fontweight='bold')
ax.axhline(nat, color=SUB, lw=0.8, ls='--', zorder=3)
ax.set_ylim(0, 215); ax.set_yticks(range(0, 201, 50))
legend(fig, x2, w1, y1 + 0.06, [('실적', NOW, 'bar'), ('예측', SEQ[1], 'bar'), (f'전국 평균만큼 줄었다면 {nat:.1f}원', SUB, 'dash')])
frame(fig, '<한국관광 데이터랩 · 이어드림 기대효과 모의실험> 방문 1회당 체험·문화 소비 추이와 참여율별 회복 예측', CAP)
fig.savefig(OUT / 'd1_체험소비_추이와_회복.png', dpi=300, facecolor='white')
plt.close(fig)

# ── d2: 추가 소비(범위 포함) + 월영교 주말 이용 ─────────────────────
fig = plt.figure(figsize=(7.4, 3.5))
ax = fig.add_axes(widget(fig, x1, y1, w1, h1, '3. 참여율별 안동에서 늘어나는 소비 (연간, 순수 증가분)', '안동 추가 소비', '예측'))
style_ax(ax, '억 원')
labs = [f'참여 {SC[n]["참여율"] * 100:.0f}%' for n in NAMES]
mid = [P(n, '추가소비합') / 1e8 for n in NAMES]
lo = [P(n, '추가소비합', 'P5') / 1e8 for n in NAMES]
hi = [P(n, '추가소비합', 'P95') / 1e8 for n in NAMES]
b = ax.bar(labs, mid, width=0.5, color=SEQ, zorder=2)
ax.errorbar(range(3), mid, yerr=[np.subtract(mid, lo), np.subtract(hi, mid)], fmt='none', ecolor=SUB, elinewidth=0.9, capsize=3, zorder=3)
ax.set_xticks(range(3))                                      # 범위 선과 겹치지 않게 값은 막대 아래 이름 줄에 적는다
ax.set_xticklabels([f'{l}\n{v:.2f}억 원' for l, v in zip(labs, mid)])
for t in ax.get_xticklabels():
    t.set_color(INK)
ax.set_ylim(0, 18); ax.set_yticks(range(0, 19, 3))
legend(fig, x1, w1, y1 + 0.06, [('가운데 값', SEQ[1], 'bar'), ('1만 번 계산 중 90% 범위', SUB, 'range')])

ax = fig.add_axes(widget(fig, x2, y1, w1, h1, '4. 참여율별 월영교 주말 하루 이용 예측', '월영교 저녁·야간 이용', '예측'))
style_ax(ax, '명')
mv = [P(n, '새이동_하루') for n in NAMES]
pp = [P(n, '팝업_하루') for n in NAMES]
xs, bw = np.arange(3), 0.34
for off, v, c in ((-bw / 2 - 0.01, mv, BLUE), (bw / 2 + 0.01, pp, ORANGE)):
    bb = ax.bar(xs + off, v, width=bw, color=c, zorder=2)
    for r, vv in zip(bb, v):
        ax.text(r.get_x() + r.get_width() / 2, vv + 8, f'{vv:.0f}', ha='center', va='bottom', fontsize=6.9, color=INK)
ax.set_xticks(xs); ax.set_xticklabels(labs)
ax.set_ylim(0, 640); ax.set_yticks(range(0, 601, 150))
legend(fig, x2, w1, y1 + 0.06, [('월영교로 새로 가는 저녁 이동', BLUE, 'bar'), ('야간 팝업 이용', ORANGE, 'bar')])
frame(fig, '<이어드림 기대효과 모의실험> 참여율별 추가 소비와 월영교 주말 이용 (할인액·원래 썼을 돈 제외, 2026년 1~8월 월평균 × 12)', CAP)
fig.savefig(OUT / 'd2_추가소비와_월영교이용.png', dpi=300, facecolor='white')
plt.close(fig)

# ── d3: 요약 표 (데이터랩 표 형식) ───────────────────────────────────
def ex_after(n):
    v = now * (1 + P(n, '지표1_증가율')); ch = (v / y24 - 1) * 100
    return v, ch, sum(1 for k, x in E['분포'].items() if k != '안동시' and x < ch) + 1


rows = [('방문 1회당 체험·문화 소비', f'{now:.1f}원') + tuple(f'{ex_after(n)[0]:.1f}원' for n in NAMES),
        ('2024년 대비 변화', f"{mn(E['안동_변화율'])}%") + tuple(f'{mn(ex_after(n)[1])}%' for n in NAMES),
        (f"{E['시군수']}개 시·군 중 감소폭 순위", f"{E['안동_감소순위']}위") + tuple(f'{ex_after(n)[2]}위' for n in NAMES),
        ('원도심 식당 → 체험 인증 (월)', '0건') + tuple(f"{P(n, '인증_월'):,.0f}건" for n in NAMES),
        ('월영교로 새로 가는 저녁 이동 (주말 하루)', '-') + tuple(f"{P(n, '새이동_하루'):.0f}명" for n in NAMES),
        ('야간 팝업 이용 (주말 하루)', '-') + tuple(f"{P(n, '팝업_하루'):.0f}명" for n in NAMES),
        ('안동 추가 소비 (연간)', '-') + tuple(f"{P(n, '추가소비합') / 1e8:.2f}억 원" for n in NAMES)]
head = ('지표', '지금', '기준 · 참여 2%', '흥행 · 참여 4%', '목표 · 참여 10%')
fig = plt.figure(figsize=(7.4, 3.0))
fig.text(0.02, 0.95, '5. 참여율별 기대효과 요약 (원도심 식당 83곳 운영, 연간 환산)', fontsize=8.4, fontweight='bold', color=INK, va='top')
cw = [0.36, 0.13, 0.155, 0.155, 0.16]
cx = np.concatenate([[0.02], 0.02 + np.cumsum(cw)[:-1]])
top, rh = 0.855, 0.088
fig.patches.append(Rectangle((0.02, top - rh), sum(cw), rh, transform=fig.transFigure, fc='#EEF3FA', ec='none'))
fig.add_artist(Line2D([0.02, 0.02 + sum(cw)], [top, top], transform=fig.transFigure, color=TAG, lw=1.6))
for j, h in enumerate(head):
    c = INK if j < 2 else SEQ[j - 2]
    fig.text(cx[j] + (0.012 if j == 0 else cw[j] / 2), top - rh / 2, h, fontsize=7.6, fontweight='bold', color=INK,
             ha='left' if j == 0 else 'center', va='center')
    if j >= 2:
        fig.patches.append(Rectangle((cx[j] + 0.01, top - 0.006), cw[j] - 0.02, 0.006, transform=fig.transFigure, fc=c, ec='none'))
for i, r in enumerate(rows):
    yt = top - rh * (i + 1)
    if i % 2:
        fig.patches.append(Rectangle((0.02, yt - rh), sum(cw), rh, transform=fig.transFigure, fc='#FAFAFA', ec='none'))
    fig.add_artist(Line2D([0.02, 0.02 + sum(cw)], [yt - rh, yt - rh], transform=fig.transFigure, color=GRID, lw=0.7))
    for j, v in enumerate(r):
        fig.text(cx[j] + (0.012 if j == 0 else cw[j] / 2), yt - rh / 2, v, fontsize=7.4,
                 color=INK if j != 1 else SUB, fontweight='bold' if j == 4 else 'normal',
                 ha='left' if j == 0 else 'center', va='center')
fig.add_artist(Line2D([0.02, 0.02 + sum(cw)], [top - rh * (len(rows) + 1)] * 2, transform=fig.transFigure, color='#9E9E9E', lw=0.9))
frame(fig, '<한국관광 데이터랩 · 이어드림 기대효과 모의실험> 시행 전 예측, 1만 번 계산의 가운데 값. 순위는 다른 시·군이 그대로일 때', 0.1)
fig.savefig(OUT / 'd3_기대효과_요약표.png', dpi=300, facecolor='white')
plt.close(fig)
print('저장:', OUT, [f'{y}: {[round(v) for v in mon[y]]}' for y in mon])
