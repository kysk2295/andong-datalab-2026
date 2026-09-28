# -*- coding: utf-8 -*-
"""보고서·서식4·발표용 인포그래픽 26장 (2026-09-28 2차: 사용자 요청 "레퍼런스처럼 디자인")

레퍼런스: Pinterest 「Creative Charts」(흰 바탕 · 민트 한 색 + 차콜 · 두 톤 제목 · 도넛 링 · 회색 트랙 막대 · 번호 원 · 셰브론).
기준 문서: docs/디자인.md. 흐름: 문제 → 근거 → 설문 → 해법 → 효과 → 검증·확산. 한 장에 그림 하나.
숫자는 앞단 JSON·원자료에서만 읽는다. 설문은 실제 응답(103명, 방문 경험 72명) 그대로.
색: 데이터랩 파랑 = 안동·이어드림(주인공), 차콜 = 비교 대상, 연회색 = 나머지·트랙 (파랑-차콜, 파랑-회색 모두 색각 검사 통과).
지도: data/external/경계/skorea-municipalities-2018-geo.json (시·군 이름으로 매칭, 진단표 144곳 전부 일치).
출력: 보고서/보고서그림_20260928/NN_흐름_내용.png (6.7인치 = 서식4 본문 폭, 300dpi)
실행: .venv_pdf/bin/python scripts/보고서그림.py
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.collections, matplotlib.text
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, FancyBboxPatch, Polygon, Circle, Wedge, Ellipse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from 체험프레임_검증 import visits, cards, per_visit   # 수치.json과 같은 로더

for f in Path.home().joinpath('Library/Fonts').glob('Pretendard-*.otf'):
    font_manager.fontManager.addfont(str(f))
plt.rcParams.update({'font.family': 'Pretendard', 'axes.unicode_minus': True, 'font.size': 8})

OUT = ROOT / '보고서/보고서그림_20260928'
OUT.mkdir(parents=True, exist_ok=True)
J = lambda p: json.loads((ROOT / p).read_text(encoding='utf-8'))
Q = J('보고서/교수브리핑_20260922/수치.json')
S = J('보고서/성과도출_20260922/시뮬레이션결과.json')
PW = J('보고서/성과도출_20260922/순차도입_검정력.json')
VV = J('보고서/성과도출_20260922/사후검증_결과.json')
PA = J('보고서/성과도출_20260922/파라미터추정.json')
SV = J('data/설문/설문_집계.json')
SVC = pd.read_csv(ROOT / 'data/설문/설문_문항별_집계.csv')
DG = pd.read_csv(ROOT / '보고서/전국진단_20260923/전국진단표.csv')
DGJ = J('보고서/전국진단_20260923/전국진단.json')
SU = pd.read_csv(ROOT / '보고서/교수님_대시보드/data/시군_업종.csv')
SC, E = S['시나리오'], Q['체험문화']
CARD = 'data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv'
EXP = ['문화서비스', '관광유원시설', '기타레저']

# ── 색 (9/28 사용자: 데이터랩 파랑 한 색 + 차콜 + 회색) ───────────────
BG = '#FFFFFF'
BLUE, BLUE_D, BLUE_L, BLUE_XL = '#2D6BD9', '#1A4FA8', '#A8C4F0', '#EAF1FC'          # 한국관광 데이터랩 파랑
RED, RED_D, RED_L, RED_XL = '#D93A3F', '#A8262B', '#F2B3B5', '#FDECEC'              # 9/28: 문제·경고 숫자만 빨강 (파랑·차콜과 색각 검사 통과)
RED_TITLE = {'방문과체험소비', '146개시군_체험소비변화', '전국지도_체험소비변화', '월별체험소비추이', '5개도시_방문과방문당소비', '두거점_원도심과월영교',
             '읍면동_방문vs혜택업체', '주민증_월평균이용추이', '검색비중_2018_2025', '112번_원도심월영교_시간표', '월영교1km_영업종료',
             '원도심식당_영업종료_표본', '업종구성_월영교vs원도심', '관광지_방문vs소비_철도공사', '버스불편_식사후월영교', '이동불편_포기한곳',
             '안동_네지표_문제백분위', '전국지도_진단점수'}
CHAR, CHAR_L = '#34383C', '#6B7177'
GRAY, GRAY_L, TRACK = '#A7ADB2', '#D5D9DC', '#ECEEF0'
INK, SUB = '#23272B', '#6B7177'
SEQ = [BLUE_L, BLUE, BLUE_D]                              # 참여 2% · 4% · 10% (밝음 → 진함)
NAMES = ('기준', '흥행', '목표')
P = lambda n, k, q='P50': SC[n][k][q]
now, y24 = E['안동_2026'], E['안동_2024']
nat = y24 * (1 + E['중앙_변화율'] / 100)
W_IN = 6.7
DONE = []
SEC = {'문제': 'PROBLEM', '근거': 'EVIDENCE', '설문': 'SURVEY', '해법': 'SOLUTION', '효과': 'IMPACT', '검증': 'VERIFY', '확산': 'SCALE'}


def m(x, d=1):
    return f'{x:.{d}f}'.replace('-', '−')


# ── 틀: 가운데 두 톤 제목 + 부제 + 민트 짧은 선, 아래 출처 한 줄 ──────────
CNT = [0]


def base(name, no, sec, t_dark, t_mint, sub, src, h_in=3.9):
    CNT[0] += 1; no = CNT[0]                              # 번호는 코드 순서대로 자동(흐름 = 코드 순서)
    fig = plt.figure(figsize=(W_IN, h_in), facecolor=BG)
    fig._nm = f'{no:02d}_{sec}_{name}'
    ty = 1 - 0.42 / h_in
    fig.text(0.5, 1 - 0.17 / h_in, f'{SEC[sec]}  {no:02d}', ha='center', va='center', fontsize=6.4, color=BLUE_D, fontweight='semibold')
    r = fig.canvas.get_renderer()
    a = fig.text(0, ty, t_dark + ' ', fontsize=13.5, fontweight='extra bold', color=CHAR, va='center')
    b = fig.text(0, ty, t_mint, fontsize=13.5, fontweight='extra bold', color=RED if name in RED_TITLE else BLUE, va='center')
    wa = a.get_window_extent(r).width / fig.bbox.width
    wb = b.get_window_extent(r).width / fig.bbox.width
    gap = 0.1 / W_IN                                       # 두 톤 사이 공백(끝 공백은 폭 계산에서 빠짐)
    a.set_x(0.5 - (wa + wb + gap) / 2); b.set_x(0.5 - (wa + wb + gap) / 2 + wa + gap)
    fig.text(0.5, ty - 0.24 / h_in, sub, ha='center', va='center', fontsize=7.6, color=SUB)
    fig.add_artist(Line2D([0.47, 0.53], [ty - 0.39 / h_in] * 2, color=BLUE, lw=1.6, transform=fig.transFigure))
    fig.patches.append(Rectangle((0.03, 0.2 / h_in - 0.035 / h_in), 0.007, 0.07 / h_in, transform=fig.transFigure, fc=BLUE, ec='none'))
    fig.text(0.043, 0.2 / h_in, src, fontsize=6.4, color=SUB, va='center')
    fig._top = ty - 0.52 / h_in
    fig._bot = 0.36 / h_in
    fig._h = h_in
    return fig


def axes(fig, l=0.1, r=0.04, legend=False):
    b = fig._bot + (0.55 / fig._h if legend else 0.3 / fig._h)
    ax = fig.add_axes([l, b, 1 - l - r, fig._top - b - 0.12 / fig._h])
    ax.set_facecolor('none')
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(colors=SUB, labelsize=7.2, length=0)
    return ax


def base_line(ax, axis='x'):
    if axis == 'x':
        ax.axhline(ax.get_ylim()[0], color=GRAY_L, lw=1)
    ax.grid(axis='y' if axis == 'x' else 'x', color=TRACK, lw=0.8)
    ax.set_axisbelow(True)


def legend(fig, items, y=None):
    hs = []
    for nm, c, kind in items:
        if kind == 'dash':
            hs.append(Line2D([], [], color=c, lw=1.1, ls='--', label=nm))
        elif kind == 'line':
            hs.append(Line2D([], [], color=c, lw=1.8, marker='o', ms=4, mfc='white', mew=1.4, label=nm))
        elif kind == 'dot':
            hs.append(Line2D([], [], color=c, lw=0, marker='o', ms=5.5, label=nm))
        else:
            hs.append(Rectangle((0, 0), 1, 1, fc=c, ec='none', label=nm))
    fig.legend(handles=hs, loc='center', bbox_to_anchor=(0.5, y if y is not None else fig._bot + 0.12 / fig._h), ncol=len(hs),
               frameon=False, fontsize=6.9, handlelength=1.5, columnspacing=1.6, labelcolor=SUB)


def unit(ax, u, x=0.0):
    ax.text(x, 1.02, u, transform=ax.transAxes, fontsize=6.5, color=SUB, ha='left', va='bottom')


OVERLAP = {}


def _texts(fig):
    """그림 안 모든 글자(그림 글자, 축 글자, 눈금, 범례)를 모은다."""
    ts = list(fig.texts)
    for ax_ in fig.axes:
        if ax_.axison:
            (x0_, x1_), (y0_, y1_) = sorted(ax_.get_xlim()), sorted(ax_.get_ylim())
            ts += [t for t, v in zip(ax_.get_xticklabels(), ax_.get_xticks()) if x0_ - 1e-9 <= v <= x1_ + 1e-9]
            ts += [t for t, v in zip(ax_.get_yticklabels(), ax_.get_yticks()) if y0_ - 1e-9 <= v <= y1_ + 1e-9]
        ts += list(ax_.texts)
        ts += [c for c in ax_.get_children() if isinstance(c, matplotlib.text.Annotation)]
    for lg in fig.legends:
        ts += list(lg.get_texts())
    seen, out = set(), []
    for t in ts:
        if t.get_visible() and t.get_text().strip() and id(t) not in seen:
            seen.add(id(t)); out.append(t)
    return out


def check_overlap(fig, pad=1.0):
    """글자끼리 겹침 + 그림 밖으로 나간 글자를 찾는다(9/28 사용자: 라벨 겹침 전수 점검)."""
    fig.canvas.draw(); r = fig.canvas.get_renderer()
    ts = _texts(fig); bbs = [matplotlib.text.Text.get_window_extent(t, r).padded(-pad) for t in ts]   # 주석은 화살표를 빼고 글자만
    W_, H_ = fig.bbox.width, fig.bbox.height
    bad = []
    for i in range(len(ts)):
        b_ = bbs[i]
        if b_.x0 < -1 or b_.y0 < -1 or b_.x1 > W_ + 1 or b_.y1 > H_ + 1:
            bad.append(f"밖: {ts[i].get_text()[:18]!r}")
        for j in range(i + 1, len(ts)):
            if b_.overlaps(bbs[j]) and ts[i].get_text() != ts[j].get_text():
                bad.append(f"겹침: {ts[i].get_text()[:14]!r} × {ts[j].get_text()[:14]!r}")
    # 글자가 점(산점도·선 표시) 위를 덮는지: 점 중심이 글자 상자 안에 있으면 표시
    pts = []
    for ax_ in fig.axes:
        for c in ax_.collections:
            if isinstance(c, matplotlib.collections.PathCollection) and len(c.get_offsets()):
                pts += list(ax_.transData.transform(c.get_offsets()))
        for ln in ax_.lines:
            if ln.get_marker() not in (None, 'None', '', ' ') and len(ln.get_xydata()):
                pts += list(ax_.transData.transform(ln.get_xydata()))
    for t, b_ in zip(ts, bbs):
        hit = [p_ for p_ in pts if b_.x0 < p_[0] < b_.x1 and b_.y0 < p_[1] < b_.y1]
        if hit:
            bad.append(f"점 가림: {t.get_text()[:18]!r} ({len(hit)}개)")
    if bad:
        OVERLAP[fig._nm] = bad


def save(fig):
    check_overlap(fig)
    fig.savefig(OUT / f'{fig._nm}.png', dpi=300, facecolor=BG)
    plt.close(fig)
    DONE.append(fig._nm)


def ring(fig, cx, cy, r_in, frac, color, width=0.16, track=TRACK, text=None, tsize=15, tcolor=None):
    """도넛 링. cx, cy, r은 인치."""
    ax = fig.add_axes([(cx - r_in) / W_IN, (cy - r_in) / fig._h, 2 * r_in / W_IN, 2 * r_in / fig._h])
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(Wedge((0, 0), 1, 0, 360, width=width * 2, color=track))
    ax.add_patch(Wedge((0, 0), 1, 90 - 360 * frac, 90, width=width * 2, color=color))
    if text:
        ax.text(0, 0, text, ha='center', va='center', fontsize=tsize, fontweight='extra bold', color=tcolor or CHAR)
    return ax


def badge(fig, x, y, txt, fc=BLUE, r=0.028, fs=8, tc='white', ec=None):
    fig.patches.append(Ellipse((x, y), 2 * r, 2 * r * W_IN / fig._h, transform=fig.transFigure, fc=fc, ec=ec or fc, lw=1.2, zorder=3))
    fig.text(x, y, txt, ha='center', va='center', fontsize=fs, fontweight='bold', color=tc, zorder=4)


def hbar_track(ax, labels, vals, vmax, colors, fmt, lw=9, lab_color=None):
    """레퍼런스의 가로 트랙 막대: 연회색 전체 트랙 + 채운 막대 + 끝에 값."""
    ys = np.arange(len(vals))[::-1]
    for y, v, c in zip(ys, vals, colors):
        ax.plot([0, vmax], [y, y], color=TRACK, lw=lw, solid_capstyle='round', zorder=1)
        ax.plot([0, max(v, vmax * 0.012)], [y, y], color=c, lw=lw, solid_capstyle='round', zorder=2)
        ax.text(vmax * 1.04, y, fmt(v), va='center', ha='left', fontsize=7.6, fontweight='bold', color=INK)
    ax.set_yticks(ys); ax.set_yticklabels(labels, fontsize=7.4, color=lab_color or INK)
    ax.set_xlim(0, vmax * 1.3); ax.set_xticks([]); ax.set_ylim(-0.7, len(vals) - 0.3)


def side_axes(fig, l, w):
    ax = fig.add_axes([l, fig._bot + 0.08, w, fig._top - fig._bot - 0.14]); ax.set_facecolor('none')
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    return ax




# ── 전국 시·군 지도 (경계 GeoJSON, geopandas 없이 PolyCollection) ────────────
from matplotlib.collections import PolyCollection
GEO = J('data/external/경계/skorea-municipalities-2018-geo.json')
ALIAS = {'세종특별자치시': '세종시'}


def _rings(f):
    g = f['geometry']
    cs = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    return [np.array(c[0]) for c in cs]


GP = [(f['properties']['name'], _rings(f)) for f in GEO['features']]
CEN = {}
for nm_, rs in GP:
    big = max(rs, key=len)
    CEN.setdefault(nm_, (big[:, 0].mean(), big[:, 1].mean()))


def kmap(ax, colors, default='#F1F3F5', hl=(), hl_col=None):
    colors = {ALIAS.get(k, k): v for k, v in colors.items()}
    verts, fcs = [], []
    for nm_, rs in GP:
        for r_ in rs:
            verts.append(r_); fcs.append(colors.get(nm_, default))
    ax.add_collection(PolyCollection(verts, facecolors=fcs, edgecolors='white', linewidths=0.25))
    for nm_, rs in GP:
        if nm_ in hl:
            ax.add_collection(PolyCollection(rs, facecolors='none', edgecolors=hl_col or CHAR, linewidths=1.3, zorder=3))
    ax.set_xlim(124.6, 131.0); ax.set_ylim(33.1, 38.65); ax.set_aspect(1 / np.cos(np.radians(36))); ax.axis('off')


def map_label(ax, nm_, txt, dx=0.35, dy=0.0, color=None, fs=7.2, bold=True):
    x, y = CEN[nm_]
    ax.annotate(txt, (x, y), xytext=(x + dx, y + dy), fontsize=fs, fontweight='extra bold' if bold else 'semibold', color=color or CHAR,
                va='center', arrowprops=dict(arrowstyle='-', color=color or CHAR, lw=0.7), zorder=5)


# ═════════════ 1. 문제 ═════════════
# 01 방문 vs 체험 소비: 2024 = 100 지수 + 숫자 카드 (9/28 2차: "너무 대충" → 연도 흐름과 격차를 보이게)
M8 = list(range(1, 9)); VY, PY = {}, {}
for y in (2024, 2025, 2026):
    VY[y] = visits(y, M8); W_, d_ = cards(CARD, y, M8); PY[y] = per_visit(W_, VY[y], d_)
ix3 = sorted(set(PY[2024].index) & set(PY[2025].index) & set(PY[2026].index))
ex3 = {y: PY[y].loc[ix3, EXP].sum(axis=1) for y in PY}
yrs = [2024, 2025, 2026]
i_vis = [VY[y]['안동시'] / VY[2024]['안동시'] * 100 for y in yrs]
i_exp = [ex3[y]['안동시'] / ex3[2024]['안동시'] * 100 for y in yrs]
i_med = [100 + ((ex3[y] / ex3[2024] - 1) * 100).median() for y in yrs]
v_med = ((VY[2026].loc[ix3] / VY[2024].loc[ix3] - 1) * 100).median()
fig = base('방문과체험소비', 1, '문제', '방문은 늘고', '체험 소비는 줄었다',
           '외지인 방문 연인원과 방문 1회당 체험·문화 소비 (각 연도 1~8월, 2024년 = 100)',
           '출처: 한국관광 데이터랩(이동통신 방문 연인원, 신용카드 외지인 소비). 체험·문화 = 문화서비스·관광유원시설·기타레저', h_in=4.1)
# 왼쪽 숫자 카드 두 장
cards_ = [(f"+{i_vis[-1] - 100:.1f}%", '외지인 방문 연인원', f"전국 시·군 중앙 +{v_med:.1f}%", CHAR, '#F4F6F7'),
          (f"{m(i_exp[-1] - 100)}%", '방문 1회당 체험·문화 소비', f"{ex3[2024]['안동시']:.1f}원 → {ex3[2026]['안동시']:.1f}원 · 전국 중앙 {m(i_med[-1] - 100)}%", RED, RED_XL)]
ch_ = (fig._top - fig._bot - 0.06) / 2
for k, (big, lab, sub_, col, bg) in enumerate(cards_):
    y0 = fig._top - (k + 1) * ch_ - k * 0.03
    fig.patches.append(FancyBboxPatch((0.035, y0), 0.3, ch_, boxstyle='round,pad=0,rounding_size=0.02', transform=fig.transFigure, fc=bg, ec='none'))
    fig.patches.append(Rectangle((0.035, y0 + 0.02), 0.006, ch_ - 0.04, transform=fig.transFigure, fc=col, ec='none'))
    fig.text(0.06, y0 + ch_ - 0.055, lab, fontsize=7.8, fontweight='bold', color=INK, va='center')
    fig.text(0.06, y0 + ch_ * 0.45, big, fontsize=22, fontweight='black', color=col, va='center')
    fig.text(0.06, y0 + 0.045, sub_, fontsize=6.6, color=SUB, va='center')
    fig.text(0.315, y0 + ch_ * 0.45, '▲' if k == 0 else '▼', fontsize=13, color=col, va='center', ha='right')
# 오른쪽 지수 선
ax = fig.add_axes([0.42, fig._bot + 0.17, 0.44, fig._top - fig._bot - 0.2]); ax.set_facecolor('none')
for sp in ax.spines.values():
    sp.set_visible(False)
ax.tick_params(colors=SUB, labelsize=7.2, length=0)
xy_ = np.arange(3)
ax.fill_between(xy_, i_exp, i_vis, color=RED_XL, zorder=0)
ax.plot(xy_, i_med, color=GRAY, lw=1.4, ls=(0, (4, 2)), marker='o', ms=4, mfc='white', mew=1.2, zorder=2)
ax.plot(xy_, i_vis, color=CHAR, lw=2, marker='o', ms=5, mfc='white', mew=1.5, zorder=3)
ax.plot(xy_, i_exp, color=RED, lw=2.8, marker='o', ms=6, mfc='white', mew=1.8, zorder=4)
for vals_, lab_, col_, dy_ in ((i_vis, '방문', CHAR, 0), (i_med, '전국 중앙 체험', GRAY, 0), (i_exp, '안동 체험', RED, 0)):
    ax.text(2.12, vals_[-1] + dy_, f'{vals_[-1]:.1f}  {lab_}', va='center', fontsize=7.4, fontweight='extra bold' if col_ == RED else 'semibold', color=col_)
gap_ = i_vis[-1] - i_exp[-1]
ax.annotate('', xy=(1.93, i_exp[-1] + 0.4), xytext=(1.93, i_vis[-1] - 0.4), arrowprops=dict(arrowstyle='<->', color=RED, lw=1))
ax.text(1.86, i_exp[-1] + (i_med[-1] - i_exp[-1]) * 0.45, f'{gap_:.1f}p\n벌어짐', ha='right', va='center', fontsize=7.6, fontweight='extra bold', color=RED, linespacing=1.2)
ax.axhline(100, color=GRAY_L, lw=1, zorder=1)
ax.set_xticks(xy_); ax.set_xticklabels([f'{y}' for y in yrs], fontsize=7.6, fontweight='bold')
ax.set_xlim(-0.15, 2.1); ax.set_ylim(78, 110); ax.set_yticks([80, 90, 100, 110]); ax.grid(axis='y', color=TRACK, lw=0.8); ax.set_axisbelow(True)
ax.text(0, 1.03, '지수 (2024년 1~8월 = 100)', transform=ax.transAxes, fontsize=6.5, color=SUB)
save(fig)

# 02 146개 시·군 벌떼
dist = pd.Series(E['분포'])
fig = base('146개시군_체험소비변화', 2, '문제', f"{E['시군수']}개 시·군 중", f"{E['안동_감소순위']}번째로 많이 줄었다",
           '시·군별 방문 1회당 체험·문화 소비 변화율 (2024 → 2026년 1~8월). 점 하나 = 시·군 하나',
           '출처: 한국관광 데이터랩. +80%를 넘는 4곳은 오른쪽 끝에 모아 표시')
ax = axes(fig, 0.05, 0.05, legend=True)
xs = dist.clip(upper=82).values
order = np.argsort(xs); ys = np.zeros(len(xs)); placed = []
for i in order:
    x = xs[i]
    for k in range(80):
        yy = ((k + 1) // 2) * 0.12 * (1 if k % 2 else -1)
        if all((x - px) ** 2 / 2.5 ** 2 + (yy - py) ** 2 / 0.11 ** 2 >= 1 for px, py in placed if abs(px - x) < 3):
            break
    ys[i] = yy; placed.append((x, yy))
isA = dist.index == '안동시'
ax.axvspan(-60, E['중앙_변화율'], color=RED_XL, zorder=0, lw=0)
ax.scatter(xs[~isA], ys[~isA], s=17, color=GRAY_L, edgecolor='white', lw=0.5, zorder=2)
ax.scatter(xs[isA], ys[isA], s=90, color=RED, edgecolor='white', lw=1.2, zorder=4)
ax.axvline(E['중앙_변화율'], color=CHAR, lw=1, ls=(0, (3, 2)), zorder=3)
ax.annotate('', xy=(xs[isA][0], ys[isA][0] + 0.08), xytext=(-40, 1.05),
            arrowprops=dict(arrowstyle='-', color=RED, lw=1, connectionstyle='angle,angleA=0,angleB=90'))
ax.text(-40.5, 1.05, f"안동시 {m(E['안동_변화율'])}%", ha='right', va='center', fontsize=10, fontweight='extra bold', color=RED)
ax.text(E['중앙_변화율'] + 1, 1.22, f"전국 중앙값 {m(E['중앙_변화율'])}%", fontsize=7, fontweight='semibold', color=CHAR)
ax.text(-58, -1.15, '← 줄어든 곳', fontsize=6.8, color=SUB); ax.text(80, -1.15, '늘어난 곳 →', fontsize=6.8, color=SUB, ha='right')
ax.set_xlim(-60, 85); ax.set_ylim(-1.3, 1.45); ax.set_yticks([])
ax.set_xticks(range(-60, 81, 20)); ax.set_xticklabels([f'{m(v, 0)}%' if v else '0' for v in range(-60, 81, 20)])
ax.axhline(-1.3, color=GRAY_L, lw=1)
legend(fig, [('안동시', RED, 'dot'), ('다른 시·군', GRAY_L, 'dot'), ('전국 중앙값', CHAR, 'dash')])
save(fig)

# 전국 지도: 방문 1회당 체험·문화 소비 변화율
bins = [(-1e9, -30, '#8E1F24', '-30% 이하'), (-30, -15, RED, '-30 ~ -15%'), (-15, E['중앙_변화율'], '#EE8C8E', f"-15 ~ {m(E['중앙_변화율'])}%"),
        (E['중앙_변화율'], 0, '#FAD9DA', f"{m(E['중앙_변화율'])} ~ 0%"), (0, 1e9, GRAY_L, '늘어남')]
col_of = lambda v: next(c for lo_, hi_, c, _ in bins if lo_ < v <= hi_)
fig = base('전국지도_체험소비변화', 0, '문제', '지도로 보면', '진한 빨강일수록 많이 줄었다',
           f"시·군별 방문 1회당 체험·문화 소비 변화율 (2024 → 2026년 1~8월, {E['시군수']}곳)",
           '출처: 한국관광 데이터랩(신용카드 외지인 ÷ 이동통신 방문). 흰 칸 = 비교 대상 아님(광역시 구, 구가 있는 시 등). 경계: 2018 시·군', h_in=5.2)
ax = fig.add_axes([0.02, fig._bot + 0.02, 0.56, fig._top - fig._bot - 0.03])
kmap(ax, {k: col_of(v) for k, v in dist.items()}, hl=('안동시',), hl_col=CHAR)
map_label(ax, '안동시', f"안동시 {m(E['안동_변화율'])}%", dx=0.9, dy=0.35, color=RED, fs=9)
yb = fig._top - 0.06
fig.text(0.6, yb, '변화율 구간', fontsize=8, fontweight='extra bold', color=INK)
cnt = pd.cut(dist, [b[0] for b in bins] + [1e9], labels=[b[3] for b in bins]).value_counts()
for i, (lo_, hi_, c, lab) in enumerate(bins):
    y_ = yb - 0.07 - i * 0.062
    fig.patches.append(FancyBboxPatch((0.6, y_ - 0.018), 0.035, 0.036, boxstyle='round,pad=0,rounding_size=0.006', transform=fig.transFigure, fc=c, ec='none'))
    fig.text(0.645, y_, lab, fontsize=7.4, color=INK, va='center')
    fig.text(0.86, y_, f'{cnt[lab]}곳', fontsize=7.6, fontweight='bold', color=INK, va='center', ha='right')
y2 = yb - 0.07 - 5 * 0.062 - 0.04
fig.add_artist(Line2D([0.6, 0.95], [y2 + 0.02] * 2, color=TRACK, lw=1, transform=fig.transFigure))
fig.text(0.6, y2 - 0.03, f"안동 {m(E['안동_변화율'])}%", fontsize=15, fontweight='black', color=RED, va='center')
fig.text(0.6, y2 - 0.1, f"전국 중앙값 {m(E['중앙_변화율'])}%, {E['시군수']}곳 중 {E['안동_감소순위']}번째", fontsize=7.4, color=SUB, va='center')
fig.text(0.6, y2 - 0.15, f"{y24:.1f}원 → {now:.1f}원 (방문 1회당)", fontsize=7.4, color=SUB, va='center')
save(fig)

# 03 월별 추이
YC = {2024: GRAY_L, 2025: GRAY, 2026: RED}
mon = {y: [] for y in YC}
for y in YC:
    for mth in range(1, 9):
        W_, d_ = cards(CARD, y, [mth])
        mon[y].append(float(per_visit(W_, visits(y, [mth]), d_)[EXP].sum(axis=1)['안동시']))
fig = base('월별체험소비추이', 3, '문제', '2026년이', '거의 모든 달에서 가장 낮다',
           '안동시 월별 방문 1회당 체험·문화 소비 (외지인, 1~8월)', '출처: 한국관광 데이터랩. 신용카드 외지인 소비 ÷ 이동통신 방문 연인원, 월별')
ax = axes(fig, 0.08, 0.1, legend=True)
xm = np.arange(1, 9)
ax.fill_between(xm, mon[2026], 100, color=RED_XL, zorder=1)
for y, c in YC.items():
    lw = 2.4 if y == 2026 else 1.4
    ax.plot(xm, mon[y], color=c, lw=lw, marker='o', ms=5 if y == 2026 else 3.6, mfc='white', mew=1.6 if y == 2026 else 1.1, zorder=3 if y == 2026 else 2)
    ax.text(8.2, mon[y][-1] + (4 if y == 2024 else (-8 if y == 2025 else 7)), f'{y}', fontsize=7, color=RED if y == 2026 else SUB,
            fontweight='bold' if y == 2026 else 'normal', va='center')
ax.set_xticks(xm); ax.set_xticklabels([f'{i}월' for i in xm]); ax.set_xlim(0.7, 8.7)
ax.set_ylim(100, 290); ax.set_yticks(range(100, 291, 50)); base_line(ax); unit(ax, '원')
fig.patches.append(FancyBboxPatch((0.64, fig._top - 0.2), 0.27, 0.13, boxstyle='round,pad=0,rounding_size=0.015', transform=fig.transFigure,
                                  fc=CHAR, ec='none', zorder=5))
fig.text(0.775, fig._top - 0.1, '1~8월 합계', ha='center', va='center', fontsize=6.6, color='#C9CDD1', zorder=6)
fig.text(0.775, fig._top - 0.155, f"{y24:.1f} → {now:.1f}원", ha='center', va='center', fontsize=9.5, fontweight='extra bold', color='white', zorder=6)
legend(fig, [(f'{y}년', c, 'line') for y, c in YC.items()])
save(fig)

# 04 업종별: 전국 추세 대비 차이
g = SU.dropna(); g = g[g['2024'] > 0]
med = (g['2026'] / g['2024'] - 1).groupby(g['업종']).median()
an = SU[SU['시군'] == '안동시'].set_index('업종')
diff = (an['2026'] - an['2024'] * (1 + med.reindex(an.index))).sort_values()
diff = diff[diff.abs() >= 1]
fig = base('업종별_전국추세대비', 4, '문제', '업종별로 보면', '외식·숙박은 전국보다 낫다',
           '업종별 방문 1회당 소비: 전국 중앙 추세만큼 변했을 때와 실제의 차이 (안동, 원)',
           '출처: 한국관광 데이터랩. 2024년 값 × (1 + 업종별 전국 중앙 변화율)과 2026년 실제 값의 차이, 1~8월', h_in=4.4)
ax = axes(fig, 0.17, 0.08, legend=True)
yy = np.arange(len(diff))
for y, (k, v) in zip(yy, diff.items()):
    c = BLUE if v > 0 else (RED if k in EXP else GRAY_L)
    ax.barh(y, v, color=c, height=0.62, zorder=2)
    ax.text(v + (10 if v >= 0 else -10), y, m(v, 0) if v < 0 else f'+{v:,.0f}', va='center', ha='left' if v >= 0 else 'right', fontsize=6.8,
            color=INK, fontweight='bold' if k in EXP or v > 0 else 'normal')
ax.set_yticks(yy); ax.set_yticklabels(diff.index, fontsize=7.2)
for t in ax.get_yticklabels():
    if t.get_text() in EXP:
        t.set_fontweight('bold'); t.set_color(RED)
ax.axvline(0, color=CHAR, lw=1)
ax.set_xlim(diff.min() * 1.25, diff.max() * 2.4); ax.set_xticks([])
legend(fig, [('전국보다 나은 업종', BLUE, 'bar'), ('체험·문화 업종', RED, 'bar'), ('다른 업종', GRAY_L, 'bar')])
save(fig)

# 당일 방문 비중
mb = Q['무박_연간']
fig = base('당일방문비중_그대로', 0, '문제', '당일 방문 비중은', '7년째 그대로',
           '안동 외지인 방문 중 당일(무박) 방문 비중', '출처: 한국관광 데이터랩 이동통신 숙박일수별 관광객(연간). "당일치기가 급증했다"는 설명은 맞지 않음', h_in=3.2)
cy_in = (fig._top + fig._bot) / 2 * fig._h + 0.08
for j, (yr, v) in enumerate(mb.items()):
    cx_in = W_IN * (0.2 + 0.3 * j)
    ring(fig, cx_in, cy_in, 0.62, v / 100, BLUE if j == 2 else BLUE_L, width=0.15, text=f'{v:.1f}%', tsize=14)
    fig.text(cx_in / W_IN, fig._bot + 0.03, f'{yr}년', ha='center', fontsize=9, fontweight='extra bold', color=BLUE_D if j == 2 else SUB)
for j in range(2):
    fig.text((W_IN * (0.35 + 0.3 * j)) / W_IN, cy_in / fig._h, '→', ha='center', va='center', fontsize=14, color=GRAY)
save(fig)

# 비슷한 관광 도시 비교
c5 = Q['5개도시']
order5 = sorted(c5, key=lambda k: c5[k]['방문당소비'])
fig = base('5개도시_방문과방문당소비', 0, '문제', '방문은 늘었는데', f"방문당 소비는 {m(c5['안동']['방문당소비'])}%",
           '관광 도시 5곳의 외지인 방문 변화와 방문 1회당 전체 소비 변화 (2024 → 2026년 1~8월)', '출처: 한국관광 데이터랩(이동통신 방문, 신용카드 외지인 소비 전체 업종)', h_in=3.8)
ax = axes(fig, 0.1, 0.12, legend=True)
yy = np.arange(len(order5))
for y_, c_ in zip(yy, order5):
    if c_ == '안동':
        ax.axhspan(y_ - 0.45, y_ + 0.45, color=RED_XL, lw=0, zorder=0)
    ax.barh(y_ + 0.17, c5[c_]['방문'], height=0.3, color=GRAY_L, zorder=2)
    ax.barh(y_ - 0.17, c5[c_]['방문당소비'], height=0.3, color=RED if c_ == '안동' else CHAR, zorder=2)
    ax.text(c5[c_]['방문'] + 0.2, y_ + 0.17, f"+{c5[c_]['방문']:.1f}%", va='center', fontsize=6.8, color=SUB)
    v_ = c5[c_]['방문당소비']
    ax.text(v_ + (0.2 if v_ >= 0 else -0.2), y_ - 0.17, f'{m(v_) if v_ < 0 else "+" + f"{v_:.1f}"}%', va='center', ha='left' if v_ >= 0 else 'right',
            fontsize=7.4, fontweight='extra bold', color=RED if c_ == '안동' else INK)
ax.set_yticks(yy); ax.set_yticklabels(order5, fontsize=8)
for t in ax.get_yticklabels():
    if t.get_text() == '안동':
        t.set_fontweight('extra bold'); t.set_color(RED)
ax.axvline(0, color=CHAR, lw=1); ax.set_xlim(-5, 12); ax.set_xticks([])
legend(fig, [('방문 변화', GRAY_L, 'bar'), ('방문당 소비 변화', CHAR, 'bar'), ('안동 방문당 소비', RED, 'bar')])
save(fig)

# ═════════════ 2. 근거 ═════════════
_wy = pd.DataFrame(Q['월영교조사']); _wy = _wy[_wy['상태'] == '영업']
n_meal21 = int(((_wy['상권업종중분류명'].str.strip() != '비알코올') & (_wy['영업종료'] >= '21:00')).sum())

# 원도심과 월영교 두 거점
hbm = {r['행정동']: r for r in Q['혜택배치']}
fig = base('두거점_원도심과월영교', 0, '근거', '돈이 도는 원도심, 사람이 모이는 월영교', '3.2km 사이가 끊겼다',
           '두 거점의 방문·가게·교통 한눈에 보기 (원도심 = 중구동, 월영교 = 강남동)', '출처: 한국관광 데이터랩(읍면동 방문 2026년 1~8월), 상가정보 2026.6, 안동시 BIS, 주민증 혜택업체, 팀 확인', h_in=4.3)
hh_ = fig._h                                              # 세로 위치는 인치 기준(그림 높이가 바뀌어도 간격 유지)
cy = fig._top - 0.62 / hh_
for x, lab, col in ((0.22, '원도심', CHAR), (0.78, '월영교', BLUE)):
    fig.patches.append(Ellipse((x, cy), 0.16, 0.16 * W_IN / fig._h, transform=fig.transFigure, fc=col, ec='none', zorder=3))
    fig.text(x, cy, lab, ha='center', va='center', fontsize=12, fontweight='black', color='white', zorder=4)
fig.add_artist(Line2D([0.31, 0.69], [cy, cy], color=GRAY_L, lw=3, ls=(0, (2, 1.5)), transform=fig.transFigure))
fig.text(0.5, cy + 0.2 / hh_, f"{Q['원도심_월영교_km']:.1f}km", ha='center', fontsize=11, fontweight='extra bold', color=CHAR)
fig.text(0.5, cy - 0.15 / hh_, '시내버스 112번 하나\n19시 이후 원도심 출발 0회', ha='center', va='top', fontsize=7.2, color=RED, fontweight='bold', linespacing=1.4)
facts = [('외지인 방문 점유율', f"{hbm['중구동']['방문점유율']:.1f}%", f"{hbm['강남동']['방문점유율']:.1f}%"),
         ('반경 1km 음식점', f"{sum(Q['반경1km업종']['원도심'].values())}곳", f"{sum(Q['반경1km업종']['월영교'].values())}곳"),
         ('그중 주점', f"{Q['반경1km업종']['원도심'].get('주점', 0)}곳", '0곳'),
         ('주민증 혜택 업체', f"{hbm['중구동']['혜택업체']}곳", '1곳 (카페)'),
         ('21시 이후 식사 가능', '0곳 (표본 8곳)', f'{n_meal21}곳')]
y0_ = cy - 0.9 / hh_
for i, (lab, a_, b_) in enumerate(facts):
    y_ = y0_ - i * 0.3 / hh_
    fig.text(0.5, y_, lab, ha='center', va='center', fontsize=7.2, color=SUB)
    fig.text(0.22, y_, a_, ha='center', va='center', fontsize=9.5, fontweight='extra bold', color=RED if a_.startswith('0곳') else CHAR)
    fig.text(0.78, y_, b_, ha='center', va='center', fontsize=9.5, fontweight='extra bold', color=RED if b_.startswith('0곳') else BLUE_D)
    fig.add_artist(Line2D([0.08, 0.92], [y_ - 0.15 / hh_] * 2, color=TRACK, lw=0.8, transform=fig.transFigure))
save(fig)
hb = pd.DataFrame(Q['혜택배치']).head(10)
tot_b = Q['주민증']['혜택업체']
hb['혜택점유율'] = hb['혜택업체'] / tot_b * 100
fig = base('읍면동_방문vs혜택업체', 5, '근거', '사람이 가장 많은 원도심에', '혜택은 0곳',
           '읍면동별 외지인 방문 점유율과 주민증 혜택업체 점유율 (방문 상위 10곳, 2026년 1~8월)',
           f'출처: 한국관광 데이터랩(읍면동 방문), 안동시 정보공개(혜택업체 {tot_b}곳 주소). 중구동 = 원도심', h_in=4.4)
ax = axes(fig, 0.13, 0.1, legend=True)
yy = np.arange(len(hb))[::-1]
for y_, (_, r) in zip(yy, hb.iterrows()):
    if r['행정동'] == '중구동':
        ax.axhspan(y_ - 0.45, y_ + 0.45, color=RED_XL, zorder=0, lw=0)
    ax.plot([r['방문점유율'], r['혜택점유율']], [y_, y_], color=GRAY_L, lw=3, solid_capstyle='round', zorder=1)
    ax.text(max(r['방문점유율'], r['혜택점유율']) + 0.55, y_, f"혜택 {int(r['혜택업체'])}곳", va='center', fontsize=6.9,
            color=RED if r['혜택업체'] == 0 else SUB, fontweight='bold' if r['혜택업체'] == 0 else 'normal')
ax.scatter(hb['방문점유율'], yy, s=48, color=BLUE, zorder=3, edgecolor='white', lw=1)
ax.scatter(hb['혜택점유율'], yy, s=48, color=CHAR, zorder=3, edgecolor='white', lw=1)
ax.set_yticks(yy); ax.set_yticklabels(hb['행정동'], fontsize=7.4)
for t in ax.get_yticklabels():
    if t.get_text() == '중구동':
        t.set_fontweight('extra bold'); t.set_color(RED)
ax.set_xlim(-0.6, 16.5); ax.set_xticks(range(0, 17, 4)); ax.set_xticklabels([f'{v}%' for v in range(0, 17, 4)])
ax.grid(axis='x', color=TRACK, lw=0.8); ax.set_axisbelow(True)
legend(fig, [('외지인 방문 점유율', BLUE, 'dot'), ('혜택업체 점유율', CHAR, 'dot')])
save(fig)

# 혜택업체 27곳 분류
bc = pd.Series(Q['주민증']['분류']).sort_values(ascending=False)
fig = base('혜택업체27곳_분류', 0, '근거', '혜택 업체 27곳 중', f"식음료는 {bc['식음료']}곳",
           '안동 디지털 관광주민증 혜택 업체의 분류', '출처: 안동시 정보공개청구(혜택업체 목록, 2026.9.18)', h_in=3.4)
cy_in = (fig._top + fig._bot) / 2 * fig._h
axd = fig.add_axes([(1.9 - 1.0) / W_IN, (cy_in - 1.0) / fig._h, 2.0 / W_IN, 2.0 / fig._h]); axd.set_aspect('equal'); axd.axis('off')
pal = [CHAR, BLUE, '#5B8EDC', BLUE_L, GRAY, GRAY_L, TRACK]
axd.pie(bc.values, colors=pal[:len(bc)], startangle=90, counterclock=False, wedgeprops=dict(width=0.32, edgecolor='white', linewidth=1.6))
axd.text(0, 0.08, f"{bc.sum()}곳", ha='center', va='center', fontsize=15, fontweight='extra bold', color=CHAR)
axd.text(0, -0.22, '혜택 업체', ha='center', va='center', fontsize=7, color=SUB)
for i, (k, v) in enumerate(bc.items()):
    y_ = fig._top - 0.06 - i * 0.075
    fig.patches.append(FancyBboxPatch((0.52, y_ - 0.02), 0.03, 0.04, boxstyle='round,pad=0,rounding_size=0.006', transform=fig.transFigure, fc=pal[i], ec='none'))
    fig.text(0.565, y_, k, fontsize=8, color=INK, va='center', fontweight='bold' if k == '식음료' else 'regular')
    fig.text(0.8, y_, f'{v}곳', fontsize=8.6, fontweight='extra bold', color=BLUE_D if k == '식음료' else INK, va='center', ha='right')
    fig.text(0.9, y_, f'{v / bc.sum() * 100:.0f}%', fontsize=7.2, color=SUB, va='center', ha='right')
save(fig)

# 06 주민증 이용 분류 (도넛 + 트랙)
use = pd.Series({k: 0.0 for k in ('관람', '식음료', '숙박', '체험')})
for r in PA['A_업체']:
    use[r['분류']] += r['이용']
share = use / use.sum() * 100
fig = base('주민증이용_분류별', 6, '근거', '주민증 혜택 이용의', f"{share['관람']:.0f}%는 관람지",
           f"디지털 관광주민증 혜택 이용 건수의 분류별 비중 (이용 표시 {use.sum():,.0f}건)",
           '출처: 안동시 정보공개청구, 혜택업체별 이용 건수(2024.6~2026.8). 관람 = 하회마을·도산서원·유교랜드 등', h_in=3.4)
cy_in = (fig._top + fig._bot) / 2 * fig._h
ax_r = ring(fig, 1.9, cy_in, 1.0, share['관람'] / 100, BLUE, width=0.2, text=f"{share['관람']:.1f}%", tsize=17, tcolor=BLUE_D)
ax_r.text(0, -0.34, '관람지', ha='center', fontsize=8, color=SUB)
for i, (k, c) in enumerate([('식음료', CHAR), ('숙박', GRAY), ('체험', GRAY_L)]):
    yb = fig._top - 0.12 - i * 0.19
    fig.text(0.46, yb, k, fontsize=8.4, fontweight='semibold', color=INK, va='center')
    axb = fig.add_axes([0.56, yb - 0.025, 0.26, 0.05]); axb.axis('off'); axb.set_xlim(-0.1, 5.1)
    axb.plot([0, 5], [0, 0], color=TRACK, lw=7, solid_capstyle='round'); axb.plot([0, share[k]], [0, 0], color=c, lw=7, solid_capstyle='round')
    fig.text(0.84, yb, f'{share[k]:.1f}%', fontsize=9.5, fontweight='extra bold', color=INK, va='center')
    fig.text(0.93, yb, f'{use[k]:,.0f}건', fontsize=6.9, color=SUB, va='center')
fig.text(0.46, fig._bot + 0.04, '관람지를 뺀 세 분류를 합쳐도 5% 남짓 (막대 끝 = 5%)', fontsize=6.6, color=SUB, va='center')
save(fig)

# 주민증 월평균 이용 추이
jm = Q['주민증']['월평균']
rate = jm[-1]['월평균'] / (Q['방문']['2026_1-8'] / 8) * 100
fig = base('주민증_월평균이용추이', 0, '근거', '주민증 이용은 늘고 있지만', f'월 외지인 방문의 {rate:.2f}%',
           '안동 디지털 관광주민증 혜택 월평균 이용 건수', '출처: 안동시 정보공개청구(이용 건수), 한국관광 데이터랩(외지인 방문 연인원 2026년 1~8월 월평균)', h_in=3.4)
ax = axes(fig, 0.08, 0.36, legend=False)
xs3 = np.arange(len(jm)); v3 = [r['월평균'] for r in jm]
ax.bar(xs3, [1000] * 3, width=0.5, color=TRACK, zorder=1)
ax.bar(xs3, v3, width=0.5, color=[BLUE_L, '#5B8EDC', BLUE], zorder=2)
for i, v in enumerate(v3):
    ax.text(i, v + 25, f'{v:,.0f}건', ha='center', fontsize=8.6, fontweight='extra bold', color=BLUE_D if i == 2 else INK)
    if i:
        ax.text(i - 0.5, (v3[i - 1] + v) / 2 + 120, f'+{(v / v3[i - 1] - 1) * 100:.0f}%', ha='center', fontsize=7, color=SUB)
ax.set_xticks(xs3); ax.set_xticklabels([r['기간'] for r in jm], fontsize=7.4); ax.set_ylim(0, 1000); ax.set_yticks([])
ring(fig, W_IN * 0.82, (fig._top + fig._bot) / 2 * fig._h + 0.1, 0.62, rate / 100 * 50, RED, width=0.15, text=f'{rate:.2f}%', tsize=12, tcolor=RED)
fig.text(0.82, fig._bot + 0.05, '월 외지인 방문 대비 이용\n(링 한 바퀴 = 2%)', ha='center', fontsize=6.8, color=SUB, linespacing=1.3)
save(fig)

# 관심 관광지 검색 비중 변화 (슬로프)
sr = pd.DataFrame(Q['검색비중'])


def spread(vals, gap):
    """가까운 값의 라벨 위치를 gap 이상 떨어뜨린다(순서 유지)."""
    o = np.argsort(vals); pos = np.array(vals, float)[o]
    for k in range(1, len(pos)):
        pos[k] = max(pos[k], pos[k - 1] + gap)
    out = np.empty(len(vals)); out[o] = pos - (pos.mean() - np.array(vals)[o].mean()) * 0
    return out


yl_ = spread(list(sr['2018']), 0.5); yr_ = spread(list(sr['2025']), 0.5)
fig = base('검색비중_2018_2025', 0, '근거', '하회마을 검색 비중', f"{m(sr.iloc[0]['변화율'], 0)}%, 가장 크게 줄었다",
           '시·군 전체 내비게이션 목적지 검색 중 관광지별 비중 (2018 → 2025)', '출처: 한국관광 데이터랩 내비게이션 목적지 검색. 월영교·도산서원 감소는 경주·영주와 비슷한 수준', h_in=4.2)
ax = axes(fig, 0.2, 0.25, legend=True)
for (ri, r) in sr.reset_index(drop=True).iterrows():
    hl = r['관광지'] == '안동하회마을'; an_ = r['시군'] == '안동시'
    c = RED if hl else (CHAR if an_ else GRAY_L)
    ax.plot([0, 1], [r['2018'], r['2025']], color=c, lw=2.6 if hl else 1.4, marker='o', ms=6 if hl else 4.5, mfc='white', mew=1.6, zorder=3 if hl else 2)
    ax.text(-0.04, yl_[ri], f"{r['관광지'].replace('안동', '')} {r['2018']:.1f}%", ha='right', va='center', fontsize=6.9, color=c if c != GRAY_L else SUB,
            fontweight='bold' if an_ else 'regular')
    ax.text(1.04, yr_[ri], f"{r['2025']:.1f}%  ({m(r['변화율'], 0)}%)", ha='left', va='center', fontsize=6.9, color=c if c != GRAY_L else SUB,
            fontweight='extra bold' if hl else 'regular')
ax.set_xlim(-0.05, 1.05); ax.set_xticks([0, 1]); ax.set_xticklabels(['2018', '2025'], fontsize=8, fontweight='bold'); ax.set_yticks([])
legend(fig, [('안동하회마을', RED, 'line'), ('안동 다른 관광지', CHAR, 'line'), ('경주·영주', GRAY_L, 'line')])
save(fig)

# 역사유적지 검색 비중
hs_ = Q['역사유적지검색']
fig = base('역사유적지_검색비중', 0, '근거', '볼거리를 찾는 수요는 있다', f"역사유적지 검색 {hs_['2026_1-8|안동시']:.1f}%",
           '관심 관광지 검색 중 역사유적지 비중: 안동 vs 경주 (1~8월)', '출처: 한국관광 데이터랩 관심관광지 검색(중분류 역사유적지 비중). 기간과 지표를 함께 표기', h_in=3.3)
for j, yr in enumerate(('2025', '2026')):
    for k, (city, col) in enumerate((('안동시', BLUE), ('경주시', CHAR))):
        v = hs_[f'{yr}_1-8|{city}']
        cx_in = W_IN * (0.15 + 0.23 * (j * 2 + k))
        ring(fig, cx_in, (fig._top + fig._bot) / 2 * fig._h + 0.12, 0.55, v / 100, col if yr == '2026' else (BLUE_L if k == 0 else GRAY), width=0.15,
             text=f'{v:.1f}%', tsize=12, tcolor=BLUE_D if (k == 0 and yr == '2026') else INK)
        fig.text(cx_in / W_IN, fig._bot + 0.05, f"{city.replace('시', '')} {yr}", ha='center', fontsize=8.4, fontweight='extra bold' if yr == '2026' else 'semibold',
                 color=BLUE_D if k == 0 else CHAR)
fig.add_artist(Line2D([0.5, 0.5], [fig._bot + 0.02, fig._top - 0.02], color=TRACK, lw=1, transform=fig.transFigure))
save(fig)

# 07 안동역 주말 시간대별 승차
st = pd.Series(Q['안동역_주말승차']); st = st[st > 0]
hrs = [int(k[:2]) for k in st.index]
fig = base('안동역_주말시간대별승차', 7, '근거', '주말 안동역 승차는', '18시대에 다시 몰린다',
           '안동역 주말 시간대별 승차 인원 (2024.1~2026.8 합계). 음영 = 이어드림 저녁 운영 18:30~21:00',
           '출처: 코레일 안동역 시간대별 승하차. 막차는 21~22시')
ax = axes(fig, 0.09, 0.04, legend=True)
ax.axvspan(18.5 - 0.5, 21 - 0.5, color=BLUE_XL, zorder=0, lw=0)
ax.bar(hrs, st.values, color=[BLUE if h == 18 else GRAY_L for h in hrs], width=0.66, zorder=2)
ax.text(18, st['18-19'] + 400, f"{st['18-19']:,}명", ha='center', fontsize=7.4, fontweight='extra bold', color=BLUE_D)
ax.text(19.75, st.max() * 1.03, '운영 18:30~21:00', ha='center', fontsize=7, fontweight='bold', color=BLUE_D)
ax.set_xticks(hrs); ax.set_xticklabels([f'{h}' for h in hrs], fontsize=6.8)
ax.set_ylim(0, st.max() * 1.1); ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{v / 1000:.0f}천' if v else '0'))
base_line(ax); unit(ax, '명')
ax.text(1, -0.1, '시', transform=ax.transAxes, fontsize=6.5, color=SUB, ha='right')
legend(fig, [('승차 인원', GRAY_L, 'bar'), ('18시대', BLUE, 'bar'), ('저녁 운영 시간', BLUE_XL, 'bar')])
save(fig)

# 08 112번 시간표
bus = Q['버스']
fig = base('112번_원도심월영교_시간표', 8, '근거', '19시 이후 원도심에서', '월영교 가는 버스 0회',
           '원도심과 월영교를 잇는 유일한 시내버스 112번의 출발 시각 (평일)', '출처: 안동시 버스정보시스템(BIS) 노선 시간표', h_in=3.2)
ax = axes(fig, 0.17, 0.25, legend=False)
rows = [('월영교 → 원도심', bus['월영교→원도심']['시각']), ('원도심 → 월영교', bus['원도심→월영교']['시각'])]
ax.axvspan(19, 23, color=RED_XL, zorder=0, lw=0)
for i, (lab, ts) in enumerate(rows):
    tv = [int(t[:2]) + int(t[3:]) / 60 for t in ts]
    ax.plot([6, 23], [i, i], color=GRAY_L, lw=2.2, solid_capstyle='round', zorder=1)
    ax.scatter(tv, [i] * len(tv), s=70, color='white', edgecolor=BLUE if i else CHAR, lw=1.8, zorder=3)
    prev = -9
    for t, v in zip(ts, tv):
        below = v - prev < 0.9
        ax.text(v, i - 0.3 if below else i + 0.22, t, ha='center', fontsize=6.6, color=INK, va='center')
        prev = v
ax.text(21, 0.5, '19시 이후', ha='center', va='center', fontsize=7, color=RED, fontweight='bold')
ax.set_yticks([0, 1]); ax.set_yticklabels([r[0] for r in rows], fontsize=7.6); ax.set_ylim(-0.7, 1.6)
ax.set_xlim(6, 23); ax.set_xticks(range(6, 24, 2)); ax.set_xticklabels([f'{h}시' for h in range(6, 24, 2)])
cyb = (fig._top + fig._bot) / 2
badge(fig, 0.87, cyb + 0.05, '0회', fc=RED, r=0.055, fs=13)
fig.text(0.87, cyb - 0.12, '19시 이후\n원도심 출발', ha='center', va='center', fontsize=7.2, fontweight='bold', color=RED, linespacing=1.3)
save(fig)

# 09 월영교 1km 음식점 종료 시각
wy = pd.DataFrame(Q['월영교조사']); wy = wy[wy['상태'] == '영업'].copy()
wy['업종'] = wy['상권업종중분류명'].str.strip().map(lambda s: '카페' if s == '비알코올' else '식당')
wy['종료'] = wy['영업종료'].map(lambda t: int(t[:2]) + int(t[3:]) / 60)
wy = wy.sort_values(['종료', '업종'])
n_meal21 = int(((wy['업종'] == '식당') & (wy['종료'] >= 21)).sum())
fig = base('월영교1km_영업종료', 9, '근거', '21시에 월영교에서 식사할 곳', f'{n_meal21}곳, 주점 0곳',
           f'월영교 반경 1km 영업 음식점 {len(wy)}곳의 영업 종료 시각', '출처: 소상공인 상가(상권)정보, 팀 확인(2026.9.19)', h_in=4.8)
ax = axes(fig, 0.25, 0.06, legend=True)
yy = np.arange(len(wy))
ax.axvspan(21, 24.3, color=RED_XL, zorder=0, lw=0)
for y_, (_, r) in zip(yy, wy.iterrows()):
    c = BLUE if r['업종'] == '식당' else CHAR
    ax.plot([17, r['종료']], [y_, y_], color=TRACK, lw=5, solid_capstyle='round', zorder=1)
    ax.scatter(r['종료'], y_, s=34, color=c, zorder=3, edgecolor='white', lw=0.8)
ax.axvline(21, color=RED, lw=1, ls=(0, (3, 2)))
ax.text(21.1, len(wy) - 0.2, '21시 이후 식사 가능 식당', fontsize=7, fontweight='bold', color=RED)
ax.set_yticks(yy); ax.set_yticklabels(wy['상호명'], fontsize=6.6)
ax.set_xlim(17, 24.3); ax.set_xticks(range(17, 25)); ax.set_xticklabels([f'{h}시' for h in range(17, 25)])
ax.set_ylim(-0.7, len(wy) + 0.2)
legend(fig, [('식당', BLUE, 'dot'), ('카페', CHAR, 'dot')])
save(fig)

# 원도심 식당 영업 종료 확인 표본
sm = Q['원도심영업표본']
tv8 = sorted(int(t[:2]) + int(t[3:]) / 60 for t in sm['종료'])
fig = base('원도심식당_영업종료_표본', 0, '근거', '원도심 식당도', f"21시를 넘기는 곳 {sm['21시넘김']}곳",
           f"원도심 식당 표본 {sm['표본']}곳 중 영업 종료 시각을 확인한 {sm['확인']}곳", '출처: 팀 확인(지도 앱 영업시간). 표본이 작아 참고용', h_in=2.9)
ax = axes(fig, 0.06, 0.06, legend=False)
ax.axvspan(21, 23, color=RED_XL, lw=0, zorder=0)
ax.plot([17, 23], [0, 0], color=GRAY_L, lw=2.4, solid_capstyle='round', zorder=1)
from collections import Counter
for t, c_ in Counter(tv8).items():
    for k in range(c_):
        ax.scatter(t, 0.28 * k, s=120, color=CHAR, edgecolor='white', lw=1.4, zorder=3)
    ax.text(t, -0.35, f'{int(t)}:{int(round((t % 1) * 60)):02d}', ha='center', fontsize=7.2, color=INK)
ax.text(22, 0.55, '21시 이후\n0곳', ha='center', va='center', fontsize=10, fontweight='extra bold', color=RED, linespacing=1.2)
ax.set_xlim(17.2, 23); ax.set_ylim(-0.6, 1.3); ax.set_xticks([]); ax.set_yticks([])
save(fig)

# 10 업종 구성 (9/28 4차: 점 그림도 안 와닿음 → 위 큰 숫자 카드 둘(주점 86곳 vs 0곳) + 아래 업종 비중 대칭 막대)
bk = Q['반경1km업종']
grp = lambda d: {'주점': d.get('주점', 0), '한식': d.get('한식', 0), '카페': d.get('비알코올', 0),
                 '기타 식당': sum(v for k, v in d.items() if k not in ('한식', '비알코올', '주점'))}
g_o, g_w = grp(bk['원도심']), grp(bk['월영교'])
n_o, n_w = sum(g_o.values()), sum(g_w.values())
fig = base('업종구성_월영교vs원도심', 10, '근거', '밤에 갈 주점, 원도심 86곳', '월영교 0곳',
           '반경 1km 안의 음식점 업종', '출처: 소상공인 상가(상권)정보 2026.6. 월영교는 폐업 확인 가게 포함 17곳', h_in=4.3)
ty_, th_ = fig._top - 1.25 / fig._h, 1.13 / fig._h                    # 카드 위치·높이
for x0_, nm_, n_, k_, col, bg in ((0.06, '원도심 반경 1km', n_o, g_o['주점'], CHAR, '#F4F6F7'),
                                  (0.53, '월영교 반경 1km', n_w, g_w['주점'], RED, RED_XL)):
    fig.patches.append(FancyBboxPatch((x0_, ty_), 0.41, th_, boxstyle='round,pad=0,rounding_size=0.02', transform=fig.transFigure, fc=bg, ec='none'))
    fig.text(x0_ + 0.03, ty_ + th_ - 0.2 / fig._h, nm_, fontsize=7.8, fontweight='bold', color=INK, va='center')
    fig.text(x0_ + 0.03, ty_ + th_ * 0.42, '주점', fontsize=9, fontweight='bold', color=col, va='center')
    fig.text(x0_ + 0.105, ty_ + th_ * 0.42, f'{k_}곳', fontsize=24, fontweight='black', color=col, va='center')
    fig.text(x0_ + 0.38, ty_ + th_ * 0.42, f'음식점 {n_}곳 중\n{k_ / n_ * 100:.0f}%', fontsize=7, color=SUB, va='center', ha='right', linespacing=1.4)
fig.text(0.5, ty_ + th_ / 2, 'vs', fontsize=8, fontweight='bold', color=GRAY, ha='center', va='center')
ax = fig.add_axes([0.06, fig._bot + 0.12 / fig._h, 0.88, ty_ - fig._bot - 0.42 / fig._h]); ax.axis('off')
cats = list(g_o); ys = np.arange(len(cats))[::-1]; G0 = 13; SC_ = 0.62            # 가운데 이름 칸 폭, 막대 배율(% → 축)
for y_, k in zip(ys, cats):
    so, sw = g_o[k] / n_o * 100, g_w[k] / n_w * 100
    if k == '주점':
        ax.add_patch(FancyBboxPatch((-G0 - 60 * SC_ - 9, y_ - 0.42), 2 * (G0 + 60 * SC_ + 9), 0.84, boxstyle='round,pad=0,rounding_size=0.3',
                                    fc=RED_XL, ec='none', zorder=0, mutation_aspect=0.05))
    ax.plot([-G0, -G0 - 60 * SC_], [y_, y_], color=TRACK, lw=9, solid_capstyle='round', zorder=1)
    ax.plot([G0, G0 + 60 * SC_], [y_, y_], color=TRACK, lw=9, solid_capstyle='round', zorder=1)
    ax.plot([-G0, -G0 - max(so, 0.8) * SC_], [y_, y_], color=CHAR, lw=9, solid_capstyle='round', zorder=2)
    if sw > 0:
        ax.plot([G0, G0 + sw * SC_], [y_, y_], color=BLUE, lw=9, solid_capstyle='round', zorder=2)
    ax.text(-G0 - so * SC_ - 2.2, y_, f'{so:.0f}%', ha='right', va='center', fontsize=7.6, fontweight='bold', color=INK)
    hot = k == '주점'
    ax.text(G0 + sw * SC_ + (2.2 if sw else 0.5), y_, f'{sw:.0f}%', ha='left', va='center', fontsize=10 if hot else 7.6,
            fontweight='black' if hot else 'bold', color=RED if hot else INK)
    ax.text(0, y_, k, ha='center', va='center', fontsize=8, fontweight='extra bold' if hot else 'semibold', color=RED if hot else INK)
ax.text(-G0, len(cats) - 0.35, '원도심', ha='right', va='center', fontsize=7.4, fontweight='bold', color=CHAR)
ax.text(G0, len(cats) - 0.35, '월영교', ha='left', va='center', fontsize=7.4, fontweight='bold', color=BLUE_D)
ax.set_xlim(-G0 - 60 * SC_ - 10, G0 + 60 * SC_ + 10); ax.set_ylim(-0.6, len(cats) - 0.05)
save(fig)

# 11 관광지별 방문 vs 소비 (철도공사)
rc = pd.DataFrame(Q['철도공사']).sort_values('방문점유율_pct', ascending=False).head(8).iloc[::-1]
fig = base('관광지_방문vs소비_철도공사', 11, '근거', '월영교는 방문 15%,', '소비 건수는 6%',
           '관광지별 방문 점유율과 방문객 소비 건수 점유율 (안동, 2022년 4~6월). × = 소비 ÷ 방문',
           '출처: 한국철도공사 8대 도시 가명결합 분석. 데이터랩과 다른 자료라 따로 표시', h_in=4.3)
ax = axes(fig, 0.19, 0.12, legend=True)
yy = np.arange(len(rc))
for y_, (_, r) in zip(yy, rc.iterrows()):
    hl = r['관광지명'] == '월영교'
    if hl:
        ax.axhspan(y_ - 0.45, y_ + 0.45, color=RED_XL, zorder=0, lw=0)
    ax.plot([r['방문객소비건수점유율_pct'], r['방문점유율_pct']], [y_, y_], color=GRAY_L, lw=3, solid_capstyle='round', zorder=1)
    ax.text(max(r['방문점유율_pct'], r['방문객소비건수점유율_pct']) + 0.7, y_, f"× {r['소비방문배율']:.2f}", va='center', fontsize=7,
            color=RED if hl else SUB, fontweight='extra bold' if hl else 'normal')
ax.scatter(rc['방문점유율_pct'], yy, s=48, color=BLUE, zorder=3, edgecolor='white', lw=1)
ax.scatter(rc['방문객소비건수점유율_pct'], yy, s=48, color=CHAR, zorder=3, edgecolor='white', lw=1)
ax.set_yticks(yy); ax.set_yticklabels(rc['관광지명'], fontsize=7.4)
for t in ax.get_yticklabels():
    if t.get_text() == '월영교':
        t.set_fontweight('extra bold'); t.set_color(RED)
xm_ = max(rc['방문점유율_pct'].max(), rc['방문객소비건수점유율_pct'].max())
ax.set_xlim(-0.6, xm_ + 5); ax.set_xticks(range(0, int(xm_) + 1, 10)); ax.set_xticklabels([f'{v}%' for v in range(0, int(xm_) + 1, 10)])
ax.grid(axis='x', color=TRACK, lw=0.8); ax.set_axisbelow(True)
legend(fig, [('방문 점유율', BLUE, 'dot'), ('소비 건수 점유율', CHAR, 'dot')])
save(fig)

# ═════════════ 3. 설문 (실제 응답 그대로) ═════════════
n_all, n_vis = SV['표본']['응답'], SV['표본']['3년내_방문_예']


def likert(qn):
    s = SVC[(SVC['문항'] == qn) & (SVC['기준'] == '방문자')].set_index('응답')['명']
    s.index = s.index.str.replace(' ', '')
    get = lambda p: int(sum(v for i, v in s.items() if i.startswith(p)))
    return {'매우': get('매우있다'), '있다': get('있다'), '보통': get('보통'), '별로': get('별로없다'), '전혀': get('전혀없다')}


items = [('식사 후 체험\n할인 쿠폰', 'Q6_영수증_체험쿠폰_의향'), ('저녁 셔틀·택시로\n월영교 이동', 'Q8_야간택시셔틀_의향'),
         ('월영교\n야간 팝업', 'Q10_야간팝업포차_의향'), ('영수증으로\n축제 혜택', 'Q12_영수증_축제혜택_의향')]
fig = base('이용의향_4문항', 12, '설문', '방문객 10명 중 8명이', '이용하겠다고 답했다',
           f'이어드림 요소별 이용 의향: "매우 있다" + "있다" (안동 방문 경험 {n_vis}명)',
           f'출처: 팀 온라인 설문(2026.9.23~24, 응답 {n_all}명 중 방문 경험 {n_vis}명). 의향은 참여율이 아니며 계산에는 33~40%만 반영', h_in=3.7)
cy_in = (fig._top + fig._bot) / 2 * fig._h + 0.12
for j, (lab, qn) in enumerate(items):
    c = likert(qn); n_i = sum(c.values()); top2 = c['매우'] + c['있다']
    cx_in = W_IN * (0.125 + 0.25 * j)
    ax_r = ring(fig, cx_in, cy_in, 0.6, top2 / n_i, BLUE, width=0.17)
    ax_r.add_patch(Wedge((0, 0), 1, 90 - 360 * c['매우'] / n_i, 90, width=0.34, color=BLUE_D))
    ax_r.text(0, 0.1, f'{top2 / n_i * 100:.0f}%', ha='center', va='center', fontsize=14, fontweight='extra bold', color=CHAR)
    ax_r.text(0, -0.3, f'{top2}/{n_i}명', ha='center', va='center', fontsize=6.6, color=SUB)
    fig.text(cx_in / W_IN, (cy_in - 0.84) / fig._h, lab, ha='center', va='center', fontsize=7.6, fontweight='semibold', color=INK, linespacing=1.3)
    fig.text(cx_in / W_IN, (cy_in - 1.17) / fig._h, f"매우 {c['매우']} · 있다 {c['있다']}", ha='center', va='center', fontsize=6.6, color=SUB)
legend(fig, [('매우 있다', BLUE_D, 'bar'), ('있다', BLUE, 'bar'), ('보통·없다', TRACK, 'bar')], y=fig._top - 0.005)
save(fig)

# 버스 불편 · 식사 후 월영교
b3 = SV['Q3_버스불편_버스이용방문자']; q5 = SV['Q5_식사후_월영교_방문자']
fig = base('버스불편_식사후월영교', 0, '설문', '버스 탄 방문객 4명 중 3명이', '불편했다',
           '버스를 이용한 방문객의 불편 경험, 식사 후 월영교 등 야경을 보러 이동한 방문객', '출처: 팀 온라인 설문(2026.9.23~24, 안동 방문 경험자)', h_in=3.3)
for j, (v, lab, sub_) in enumerate(((b3, '버스 이용이 불편했다', f"버스 이용 방문객 {b3['n']}명 중 {b3['k']}명"),
                                    (q5, '식사 후 월영교 등 야경을 보러 갔다', f"방문 경험 {q5['n']}명 중 {q5['k']}명"))):
    cx_in = W_IN * (0.27 + 0.46 * j)
    ring(fig, cx_in, (fig._top + fig._bot) / 2 * fig._h + 0.15, 0.68, v['k'] / v['n'], RED if j == 0 else CHAR, width=0.16,
         text=f"{v['pct']:.0f}%", tsize=17, tcolor=RED if j == 0 else CHAR)
    fig.text(cx_in / W_IN, fig._bot + 0.1, lab, ha='center', fontsize=8.4, fontweight='extra bold', color=INK)
    fig.text(cx_in / W_IN, fig._bot + 0.03, sub_, ha='center', fontsize=6.9, color=SUB)
save(fig)

# 13 망설임 이유
s11 = SVC[(SVC['문항'] == 'Q11_유료체험_망설임') & (SVC['기준'] == '전체') & (SVC['응답'] != '(빈칸)')].set_index('응답')['명']
main = {'체험 정보가 부족해서': '정보가 부족해서', '줄을 오래 서거나 예약하기 불편해서': '줄·예약이 불편해서',
        '다음 장소로 이동할 시간이 부족해서': '이동 시간이 부족해서', '가격이 부담스러워서': '가격이 부담스러워서'}
r11 = pd.Series({v: int(s11.get(k, 0)) for k, v in main.items()}); r11['기타'] = int(s11.sum() - r11.sum())
n11 = int(s11.sum()); nonp = int(r11[['정보가 부족해서', '줄·예약이 불편해서', '이동 시간이 부족해서']].sum())
fig = base('유료체험_망설임이유', 13, '설문', '체험을 망설이는 이유는', '가격보다 정보·예약·이동',
           f'유료 공연·체험이 망설여지는 가장 큰 이유 (응답 {n11}명, 하나 선택)', '출처: 팀 온라인 설문(2026.9.23~24)', h_in=3.5)
ring(fig, 1.15, (fig._top + fig._bot) / 2 * fig._h + 0.08, 0.75, nonp / n11, BLUE, width=0.18, text=f'{nonp / n11 * 100:.0f}%', tsize=16, tcolor=BLUE_D)
fig.text(1.15 / W_IN, fig._bot + 0.04, '가격이 아닌 이유', ha='center', fontsize=7.4, fontweight='semibold', color=INK)
ax = side_axes(fig, 0.47, 0.37)
hbar_track(ax, list(r11.index), list(r11.values), r11.max(), [BLUE if k in list(main.values())[:3] else GRAY_L for k in r11.index],
           lambda v: f'{v}명  {v / n11 * 100:.0f}%', lw=8)
save(fig)

# 14 이동이 불편해 포기한 곳
q4 = SV['Q4_포기한곳_방문자']
lab4 = {'야간 명소(월영교)': '월영교 같은 야간 명소', '외곽 관광지(하회·도산)': '하회·도산 외곽 관광지', '원도심 밤 가게·식당': '원도심 밤 가게·식당', '없음': '포기한 곳 없음'}
r4 = pd.Series({lab4[k]: v['k'] for k, v in q4.items()}); r4 = pd.concat([r4.drop('포기한 곳 없음').sort_values(ascending=False), r4[['포기한 곳 없음']]]); n4 = list(q4.values())[0]['n']
any4 = SV['Q4_포기한곳_있음_방문자']
fig = base('이동불편_포기한곳', 14, '설문', '방문객 4명 중 3명이', '이동 때문에 포기한 곳이 있다',
           f'이동이 불편해 가고 싶었지만 포기한 곳 (방문 경험 {n4}명, 중복 선택)', '출처: 팀 온라인 설문(2026.9.23~24)', h_in=3.5)
ring(fig, 1.15, (fig._top + fig._bot) / 2 * fig._h + 0.08, 0.75, any4['k'] / any4['n'], RED, width=0.18, text=f"{any4['pct']:.0f}%", tsize=16, tcolor=RED)
fig.text(1.15 / W_IN, fig._bot + 0.04, f"한 곳 이상 포기 {any4['k']}명", ha='center', fontsize=7.4, fontweight='semibold', color=INK)
ax = side_axes(fig, 0.5, 0.34)
hbar_track(ax, list(r4.index), list(r4.values), n4, [BLUE if '월영교' in k else (GRAY_L if '없음' in k else BLUE_L) for k in r4.index],
           lambda v: f'{v}명  {v / n4 * 100:.0f}%', lw=8)
save(fig)

# 15 귀가 시간대
s13 = SVC[(SVC['문항'] == 'Q13_귀가_교통_시간대') & (SVC['기준'] == '방문자')].set_index('응답')['명']
r13 = pd.Series({'18시 이전': s13.get('18시 이전', 0), '18~20시': s13.get('18시 ~ 20시', 0), '20~22시': s13.get('20시 ~ 22시 (막차 시간대)', 0)})
stay = int(s13.get('당일 귀가 안 함 (안동에서 숙박)', 0)); day = int(r13.sum())
fig = base('당일귀가시각', 15, '설문', '당일 귀가자의', f'{r13["20~22시"] / day * 100:.0f}%가 20~22시에 떠난다',
           f'안동에서 집으로 돌아가는 시간대 (방문 경험 {day + stay}명 중 당일 귀가 {day}명)',
           '출처: 팀 온라인 설문(2026.9.23~24). 18:30~21:00 운영 시간을 정한 근거', h_in=3.0)
ax = axes(fig, 0.06, 0.06, legend=False)
left = 0
for k, c in zip(r13.index, [GRAY_L, GRAY, BLUE]):
    v = r13[k]
    ax.barh(0, v, left=left, color=c, height=0.5, edgecolor='white', lw=2)
    ax.text(left + v / 2, 0, f'{k}\n{int(v)}명', ha='center', va='center', fontsize=7.8 if v > 6 else 6.4,
            fontweight='bold', color='white' if c != GRAY_L else INK, linespacing=1.3)
    left += v
ax.set_xlim(0, day); ax.set_ylim(-0.6, 0.9); ax.set_xticks([]); ax.set_yticks([])
ax.text(day, 0.5, f'숙박 {stay}명은 제외', ha='right', fontsize=6.6, color=SUB)
save(fig)

# ═════════════ 4. 해법 ═════════════
# 9/28 4차: 시간 띠도 안 와닿음 → 노선도 두 줄. 지금 = 끊긴 회색 점선 + 역마다 빨간 공백, 이어드림 = 이어진 파란 선 + 해법
fig = base('3단계릴레이', 16, '해법', '끊긴 하루를 한 줄로 잇는', '3단계 릴레이',
           '낮에 원도심에서, 저녁에 월영교로, 밤까지 머물게', '출처: 서식4 3)칸 운영안, 한국관광 데이터랩·BIS·상가정보', h_in=3.6)
ax = fig.add_axes([0.03, fig._bot + 0.05 / fig._h, 0.94, fig._top - fig._bot - 0.1 / fig._h]); ax.axis('off')
ax.set_xlim(0, 10); ax.set_ylim(0, 10)
ASP = (0.94 * W_IN) / ((fig._top - fig._bot - 0.1 / fig._h) * fig._h)     # 가로 1칸 대비 세로 1칸 길이 비 → 원이 찌그러지지 않게
st_ = [(2.3, '1', '원도심', '낮 · 식사 → 체험', '혜택 0곳', '식당 83곳 체험 할인'),
       (5.5, '2', '저녁 이동', '18:30 ~ 21:00', '버스 0회', '택시·셔틀'),
       (8.7, '3', '월영교', '밤 · 21시 이후', '주점 0곳', '야간 팝업')]
YN, YE = 6.3, 2.4                                                       # 지금 줄, 이어드림 줄
ax.text(0.15, YN, '지금', fontsize=9, fontweight='extra bold', color=RED, va='center')
ax.text(0.15, YE, '안동 이어드림', fontsize=9, fontweight='extra bold', color=BLUE_D, va='center')
ax.plot([2.3, 8.7], [YN, YN], color=GRAY_L, lw=2.2, ls=(0, (2.5, 2.5)), zorder=1)
for xm_ in (3.9, 7.1):                                                 # 역 사이가 끊겼다는 표시
    ax.add_patch(Ellipse((xm_, YN), 0.5, 0.5 * ASP, fc='white', ec='none', zorder=3))
    for sx_ in (1, -1):
        ax.plot([xm_ - 0.13, xm_ + 0.13], [YN - 0.13 * ASP * sx_, YN + 0.13 * ASP * sx_], color=RED, lw=2.4, solid_capstyle='round', zorder=4)
ax.plot([2.3, 8.7], [YE, YE], color=BLUE, lw=6, solid_capstyle='round', zorder=1)
for x_, no_, nm_, tm_, bad_, fix_ in st_:
    ax.text(x_, 9.6, nm_, ha='center', va='center', fontsize=10, fontweight='black', color=CHAR)
    ax.text(x_, 8.75, tm_, ha='center', va='center', fontsize=7, color=SUB)
    ax.add_patch(Ellipse((x_, YN), 0.42, 0.42 * ASP, fc='white', ec=GRAY, lw=1.6, zorder=3))
    ax.text(x_, YN - 1.1, bad_, ha='center', va='center', fontsize=12, fontweight='black', color=RED)
    ax.add_patch(Ellipse((x_, YE), 0.6, 0.6 * ASP, fc=BLUE_D, ec='white', lw=2, zorder=3))
    ax.text(x_, YE, no_, ha='center', va='center', fontsize=8, fontweight='bold', color='white', zorder=4)
    ax.text(x_, YE - 1.15, fix_, ha='center', va='center', fontsize=9.5, fontweight='extra bold', color=BLUE_D, linespacing=1.25)
ax.plot([0.15, 9.85], [4.2, 4.2], color=TRACK, lw=0.8, zorder=0)
save(fig)

# ═════════════ 5. 효과 (시행 전 예측) ═════════════
SRC_P = '출처: 이어드림 기대효과 모의실험. 시행 전 예측, 1만 번 계산의 가운데 값, 원도심 식당 83곳 운영'
fig = base('지금과시행후', 17, '효과', '지금과', '시행 후 (참여 2%)', '원도심 방문객 100명 중 2명만 참여해도 달라지는 세 가지', SRC_P, h_in=3.4)
tiles = [('원도심 혜택 업체', '0곳', '83곳', f"식당 → 체험 인증 월 {P('기준', '인증_월'):,.0f}건"),
         ('월영교 저녁 이동', '19시 이후 버스 0회', f"{P('기준', '새이동_하루'):.0f}명", '주말 하루 새로 가는 인원'),
         ('방문 1회당 체험 소비', f'{now:.1f}원', f"{now * (1 + P('기준', '지표1_증가율')):.1f}원", f"+{now * P('기준', '지표1_증가율'):.1f}원 (+{P('기준', '지표1_증가율') * 100:.1f}%)")]
cy = (fig._top + fig._bot) / 2 - 0.01
for i, (lab, a, b, sub) in enumerate(tiles):
    x = 1 / 6 + i / 3
    fig.patches.append(FancyBboxPatch((x - 0.145, cy - 0.3), 0.29, 0.58, boxstyle='round,pad=0,rounding_size=0.025', transform=fig.transFigure,
                                      fc='#F4F6F7', ec='none'))
    badge(fig, x, cy + 0.28, f'0{i + 1}', fc=BLUE, r=0.03, fs=7.6)
    fig.text(x, cy + 0.17, lab, ha='center', va='center', fontsize=7.8, fontweight='semibold', color=SUB)
    fig.text(x, cy + 0.07, a, ha='center', va='center', fontsize=9, color=RED, fontweight='extra bold')
    fig.text(x, cy - 0.01, '▼', ha='center', va='center', fontsize=7, color=BLUE)
    fig.text(x, cy - 0.12, b, ha='center', va='center', fontsize=19, fontweight='black', color=BLUE_D)
    fig.text(x, cy - 0.23, sub, ha='center', va='center', fontsize=6.4, color=SUB)
save(fig)

# 18 참여율별 방문당 회복
fig = base('참여율별_체험소비회복', 18, '효과', '참여 10%면', '전국 평균 수준까지 돌아온다',
           '참여율별 방문 1회당 체험·문화 소비 (참여율 = 원도심 방문객 중 영수증 인증 비율)', SRC_P)
ax = axes(fig, 0.06, 0.1, legend=True)
labs = ['2024년', '지금', '참여 2%', '참여 4%', '참여 10%']
vals = [y24, now] + [now * (1 + P(n, '지표1_증가율')) for n in NAMES]
ax.bar(range(5), [215] * 5, width=0.5, color=TRACK, zorder=1)
ax.bar(range(5), vals, width=0.5, color=[GRAY_L, RED] + SEQ, zorder=2)
for i, v in enumerate(vals):
    ax.text(i, v + 5, f'{v:.1f}', ha='center', va='bottom', fontsize=8.4, fontweight='extra bold' if i > 1 else 'semibold',
            color=BLUE_D if i > 1 else (RED if i == 1 else INK), zorder=5, bbox=dict(boxstyle='round,pad=0.2', fc=TRACK, ec='none'))
    if i > 1:
        ax.text(i, v / 2, f'+{v - now:.1f}', ha='center', va='center', fontsize=7.6, fontweight='bold', color='white' if i > 2 else CHAR, zorder=3)
ax.axhline(nat, color=CHAR, lw=1, ls=(0, (3, 2)), zorder=3)
ax.text(4.32, nat, f'전국 평균만큼\n줄었다면 {nat:.1f}', fontsize=6.4, color=CHAR, va='center', ha='left')
ax.set_xticks(range(5)); ax.set_xticklabels(labs, fontsize=7.4); ax.set_xlim(-0.5, 4.5)
ax.set_ylim(0, 215); ax.set_yticks([]); unit(ax, '원')
legend(fig, [('2024년', GRAY_L, 'bar'), ('지금', RED, 'bar'), ('참여 2%', SEQ[0], 'bar'), ('4%', SEQ[1], 'bar'), ('10%', SEQ[2], 'bar')])
save(fig)

# 19 참여율을 사람 100명으로
fig = base('참여율_100명', 19, '효과', '원도심 방문객 100명 중', '2명 · 4명 · 10명',
           '기준 2% = 반값여행 신청률과 강진 사이 · 흥행 4% = 강진 반값여행 규모 · 목표 10% = 전원 안내',
           '근거: 안동 반값여행 1차 신청 = 월 방문의 0.46%. 강진 반값여행 2025 = 방문의 0.65%, 안동 규모로 옮기면 원도심 방문의 약 3.5%', h_in=3.7)
pw_ = 0.28
for j, n in enumerate(NAMES):
    k = int(round(SC[n]['참여율'] * 100))
    axp = fig.add_axes([0.05 + j * (pw_ + 0.04), fig._bot + 0.15, pw_, fig._top - fig._bot - 0.18])
    axp.set_axis_off(); axp.set_xlim(-0.6, 9.6); axp.set_ylim(-0.7, 9.7); axp.set_aspect('equal')
    for idx in range(100):
        cx_, cy_ = idx % 10, 9 - idx // 10
        c = (BLUE_D if j == 2 else BLUE) if idx < k else GRAY_L
        axp.add_patch(Circle((cx_, cy_ + 0.24), 0.19, color=c, lw=0))
        axp.add_patch(FancyBboxPatch((cx_ - 0.25, cy_ - 0.4), 0.5, 0.44, boxstyle='round,pad=0,rounding_size=0.18', color=c, lw=0))
    fig.text(0.05 + j * (pw_ + 0.04) + pw_ / 2, fig._bot + 0.06, f'{n}  {k}명', ha='center', fontsize=10, fontweight='extra bold',
             color=BLUE_D if j else CHAR)
save(fig)

# 20 참여율별 추가 소비 + 범위
lb = [f'참여 {SC[n]["참여율"] * 100:.0f}%' for n in NAMES]
mid = [P(n, '추가소비합') / 1e8 for n in NAMES]
lo = [P(n, '추가소비합', 'P5') / 1e8 for n in NAMES]
hi = [P(n, '추가소비합', 'P95') / 1e8 for n in NAMES]
fig = base('참여율별_추가소비', 20, '효과', '안동에 남는 돈', f'연 {mid[0]:.2f}억 ~ {mid[2]:.2f}억 원',
           '참여율별 안동 추가 소비 (연간, 할인액·원래 썼을 돈을 뺀 순수 증가분)', SRC_P.replace('가운데 값', '가운데 값과 90% 범위'))
ax = axes(fig, 0.08, 0.04, legend=True)
for i in range(3):
    ax.plot([i, i], [lo[i], hi[i]], color=BLUE_L, lw=14, solid_capstyle='round', zorder=1, alpha=0.6)
    ax.scatter(i, mid[i], s=150, color=SEQ[i] if i else BLUE, edgecolor='white', lw=1.8, zorder=3)
    ax.text(i + 0.14, mid[i], f'{mid[i]:.2f}억', va='center', fontsize=10, fontweight='extra bold', color=BLUE_D, zorder=4)
    ax.text(i - 0.12, hi[i], f'높게 {hi[i]:.1f}억', va='center', ha='right', fontsize=6.4, color=SUB)   # 범위 글자는 왼쪽, 가운데 값은 오른쪽
    ax.text(i - 0.12, lo[i], f'낮게 {lo[i]:.1f}억', va='center', ha='right', fontsize=6.4, color=SUB)
ax.set_xticks(range(3)); ax.set_xticklabels(lb, fontsize=7.6); ax.set_xlim(-0.6, 2.8)
ax.set_ylim(0, 18); ax.set_yticks(range(0, 19, 3)); base_line(ax); unit(ax, '억 원')
legend(fig, [('가운데 값', BLUE, 'dot'), ('1만 번 계산 중 90% 범위', BLUE_L, 'bar')])
save(fig)

# 21 월영교 주말 이용
mv, pp = [P(n, '새이동_하루') for n in NAMES], [P(n, '팝업_하루') for n in NAMES]
fig = base('참여율별_월영교이용', 21, '효과', '밤의 월영교에', f'주말 하루 {mv[0]:.0f}~{mv[2]:.0f}명이 새로 온다',
           '참여율별 월영교 주말 하루 이용: 원도심에서 새로 가는 저녁 이동과 야간 팝업 이용', SRC_P)
ax = axes(fig, 0.06, 0.04, legend=True)
xs_, bw = np.arange(3), 0.3
for off, v, c in ((-bw / 2 - 0.02, mv, BLUE), (bw / 2 + 0.02, pp, CHAR)):
    ax.bar(xs_ + off, [640] * 3, width=bw, color=TRACK, zorder=1)
    ax.bar(xs_ + off, v, width=bw, color=c, zorder=2)
    for x_, vv in zip(xs_ + off, v):
        ax.text(x_, vv + 12, f'{vv:.0f}', ha='center', va='bottom', fontsize=8.4, fontweight='extra bold', color=BLUE_D if c == BLUE else CHAR, zorder=3)
ax.set_xticks(xs_); ax.set_xticklabels(lb, fontsize=7.6); ax.set_ylim(0, 640); ax.set_yticks([]); unit(ax, '명 / 주말 하루')
legend(fig, [('월영교로 새로 가는 저녁 이동', BLUE, 'bar'), ('야간 팝업 이용', CHAR, 'bar')])
save(fig)

# 22 참여율 효과 곡선
pts = [0.0] + [SC[n]['참여율'] for n in NAMES]
qq = {k: [0.0] + [P(n, '지표1_증가율', k) * 100 for n in NAMES] for k in ('P5', 'P50', 'P95')}
target = (nat / now - 1) * 100
half_p = S['임계값']['필요참여율_P50']['확대안']['0.5'] * 100
fig = base('참여율_효과곡선', 22, '효과', '절반을 되찾으려면', f'참여 {half_p:.1f}%',
           '참여율에 따른 방문 1회당 체험·문화 소비 증가율. 띠 = 1만 번 계산 중 90% 범위',
           '출처: 이어드림 기대효과 모의실험. 계산한 참여율(0·2·4·10%) 사이는 직선으로 이음')
ax = axes(fig, 0.08, 0.05, legend=True)
xp = np.array(pts) * 100
ax.fill_between(xp, qq['P5'], qq['P95'], color=BLUE_XL, lw=0, zorder=1)
ax.plot(xp, qq['P50'], color=BLUE, lw=2.4, zorder=3)
ax.scatter(xp[1:], qq['P50'][1:], s=46, color='white', edgecolor=BLUE_D, lw=1.8, zorder=4)
ax.axhline(target, color=CHAR, lw=1, ls=(0, (3, 2)))
ax.text(0.2, target + 1.2, f'전국 평균만큼 줄었을 때 수준 +{target:.1f}%', fontsize=6.6, color=CHAR)
ax.plot([half_p, half_p], [0, target / 2], color=BLUE_D, lw=1, ls=(0, (2, 2)))
ax.plot([0, half_p], [target / 2, target / 2], color=BLUE_D, lw=1, ls=(0, (2, 2)))
ax.scatter([half_p], [target / 2], s=60, color=BLUE_D, zorder=5)
ax.text(half_p + 0.25, target / 2 - 2.8, f'절반 = 참여 {half_p:.1f}%', fontsize=7.4, fontweight='extra bold', color=BLUE_D)
for x_, y_ in zip(xp[1:], qq['P50'][1:]):                   # 2·4%는 점 오른쪽 아래(점선 피함), 10%는 왼쪽 위
    if x_ < 9:
        ax.text(x_ + 0.2, y_ - 0.8, f'+{y_:.1f}%', fontsize=7.4, fontweight='bold', color=INK, ha='left', va='top')
    else:
        ax.text(x_ - 0.2, y_ + 1.6, f'+{y_:.1f}%', fontsize=7.4, fontweight='bold', color=INK, ha='right')
ax.set_xlim(0, 10.6); ax.set_xticks(range(0, 11, 2)); ax.set_xticklabels([f'{x}%' for x in range(0, 11, 2)])
ax.set_ylim(0, max(qq['P95']) * 1.04); ax.set_yticks(range(10, int(max(qq['P95'])) + 1, 10)); base_line(ax); unit(ax, '방문당 증가율 %')
ax.text(1, -0.11, '참여율', transform=ax.transAxes, fontsize=6.5, color=SUB, ha='right')
legend(fig, [('가운데 값', BLUE, 'line'), ('90% 범위', BLUE_XL, 'bar'), ('전국 평균 수준', CHAR, 'dash')])
save(fig)

# 23 결과를 흔드는 값
vc = pd.Series(S['확대안']['분산기여']['추가소비합']).sort_values(ascending=False).head(6)
nm = {'p': '참여율', 'r': '낮 체험 결제율', 'lam': '저녁 이동 배수', '체험가격': '체험 가격', 'c': '원래 저녁에 가는 비율', 'q_b': '문보트 결제율',
      'q_p': '팝업 구매율', 'k': '팝업 이용 강도', '팝업객단가': '팝업 1인 지출', '반사실': '원래 썼을 돈의 몫', '문보트가격': '문보트 가격'}
top3 = vc.head(3).sum() * 100
fig = base('결과를흔드는값', 23, '효과', '시행 첫 달에', '이 세 값부터 잰다',
           '추가 소비 예측의 흔들림을 입력값별로 나눈 비중',
           f'출처: 이어드림 기대효과 모의실험(참여율을 0.46~5%로 뽑은 계산). 위 세 값이 흔들림의 {top3:.0f}%', h_in=3.5)
ax = axes(fig, 0.22, 0.1, legend=False)
hbar_track(ax, [nm.get(k, k) for k in vc.index], list(vc.values * 100), 40, [BLUE_D, BLUE, BLUE] + [GRAY_L] * 3, lambda v: f'{v:.1f}%', lw=9)
save(fig)

# 26 요약 표
def ex_after(n):
    v = now * (1 + P(n, '지표1_증가율')); ch = (v / y24 - 1) * 100
    return v, ch, sum(1 for k, x in E['분포'].items() if k != '안동시' and x < ch) + 1


rows = [('방문 1회당 체험·문화 소비', f'{now:.1f}원') + tuple(f'{ex_after(n)[0]:.1f}원' for n in NAMES),
        ('2024년 대비 변화', f"{m(E['안동_변화율'])}%") + tuple(f'{m(ex_after(n)[1])}%' for n in NAMES),
        (f"{E['시군수']}개 시·군 중 감소폭 순위", f"{E['안동_감소순위']}위") + tuple(f'{ex_after(n)[2]}위' for n in NAMES),
        ('원도심 식당 → 체험 인증 (월)', '0건') + tuple(f"{P(n, '인증_월'):,.0f}건" for n in NAMES),
        ('월영교로 새로 가는 저녁 이동 (주말 하루)', '-') + tuple(f"{P(n, '새이동_하루'):.0f}명" for n in NAMES),
        ('야간 팝업 이용 (주말 하루)', '-') + tuple(f"{P(n, '팝업_하루'):.0f}명" for n in NAMES),
        ('안동 추가 소비 (연간)', '-') + tuple(f"{P(n, '추가소비합') / 1e8:.2f}억 원" for n in NAMES)]
fig = base('요약표', 26, '효과', '참여율별', '기대효과 한눈에', '원도심 식당 83곳 운영, 연간 환산. 순위는 다른 시·군이 그대로일 때', SRC_P, h_in=3.9)
cw = np.array([0.34, 0.13, 0.16, 0.16, 0.16]); x0 = 0.025
cx = np.concatenate([[x0], x0 + np.cumsum(cw)[:-1]])
top_, rh = fig._top - 0.01, (fig._top - fig._bot - 0.05) / (len(rows) + 1)
heads = [('지표', None), ('지금', CHAR), ('기준 2%', SEQ[0]), ('흥행 4%', SEQ[1]), ('목표 10%', SEQ[2])]
fig.patches.append(Rectangle((cx[4] + 0.006, fig._bot + 0.035), cw[4] - 0.012, top_ - rh - fig._bot - 0.035, transform=fig.transFigure,
                             fc=BLUE_XL, ec='none', zorder=-2))
for j, (h, c) in enumerate(heads):
    if c:
        fig.patches.append(FancyBboxPatch((cx[j] + 0.012, top_ - rh * 0.88), cw[j] - 0.024, rh * 0.76, boxstyle='round,pad=0,rounding_size=0.018',
                                          transform=fig.transFigure, fc=c, ec='none'))
    fig.text(cx[j] + (0.012 if j == 0 else cw[j] / 2), top_ - rh / 2, h, fontsize=8, fontweight='extra bold',
             color=SUB if j == 0 else ('white' if j != 2 else CHAR), ha='left' if j == 0 else 'center', va='center')
for i, r in enumerate(rows):
    yt = top_ - rh * (i + 1)
    fig.add_artist(Line2D([x0, x0 + cw.sum()], [yt - rh, yt - rh], transform=fig.transFigure, color=TRACK, lw=0.8))
    for j, v in enumerate(r):
        fig.text(cx[j] + (0.012 if j == 0 else cw[j] / 2), yt - rh / 2, v, fontsize=7.4 if j == 0 else 7.8,
                 color=SUB if j == 1 else (BLUE_D if j == 4 else INK), fontweight='extra bold' if j == 4 else ('medium' if j else 'regular'),
                 ha='left' if j == 0 else 'center', va='center')
save(fig)


# ═════════════ 6. 검증 · 확산 ═════════════
p83 = next(c['검정력'] for c in PW['확대안']['곡선'] if abs(c['효과'] - .5) < 1e-9) * 100
p20 = next(c['검정력'] for c in PW['기본안']['곡선'] if abs(c['효과'] - .5) < 1e-9) * 100
fig = base('순차확대_검정력', 24, '검증', '식당 83곳이면', f'효과를 {p83:.0f}% 확률로 확인',
           '식당을 4묶음 추첨 순서로 한 달씩 넓힐 때(5개월), 가로축 = 참여 식당 손님의 체험 결제 증가',
           '출처: 순차 확대 모의실험 1,000회. 효과 = 참여 식당 손님의 체험 결제 증가')
ax = axes(fig, 0.08, 0.05, legend=True)
ax.axhspan(80, 105, color=BLUE_XL, lw=0, zorder=0)
for key, col, lw in (('기본안', GRAY, 1.6), ('확대안', BLUE, 2.6)):
    cv = PW[key]['곡선']
    ax.plot([c['효과'] * 100 for c in cv], [c['검정력'] * 100 for c in cv], color=col, lw=lw, marker='o', ms=5, mfc='white', mew=1.6)
ax.scatter([50], [p83], s=70, color=BLUE_D, zorder=5); ax.scatter([50], [p20], s=50, color=GRAY, zorder=5)
ax.text(46, p83 + 5, f'83곳 {p83:.0f}%', fontsize=9, fontweight='extra bold', color=BLUE_D, ha='right')
ax.text(54, p20 - 3, f'20곳 {p20:.0f}%', fontsize=8, fontweight='bold', color=CHAR_L, va='top')
ax.text(99, 82, '80% 이상 = 확인 가능', fontsize=6.6, color=BLUE_D, ha='right')
ax.set_xticks([10, 20, 30, 50, 75, 100]); ax.set_xticklabels(['+10%', '+20%', '+30%', '+50%', '+75%', '+100%'])
ax.set_ylim(0, 105); ax.set_yticks(range(0, 101, 20)); ax.set_yticklabels([f'{v}%' for v in range(0, 101, 20)]); base_line(ax)
legend(fig, [('식당 83곳', BLUE, 'line'), ('식당 20곳', GRAY, 'line')])
save(fig)

# 합성통제 시계열 (판정 보조)
ts_ = VV['시계열']; nq = len(ts_['분기']); npre = ts_['사전분기수']
fig = base('합성통제_기준선', 0, '검증', '시행 뒤 효과를 잴', '비교 기준선',
           '분기별 방문 1회당 체험·문화 소비 지수: 안동 vs 비슷한 시·군을 섞어 만든 비교 조합 (2022~2023 평균 = 100)',
           '출처: 한국관광 데이터랩, 합성통제. 음영 = 시행 전 가짜 시행 구간. 판정 보조 자료이며 통계적 확정이 아님')
ax = axes(fig, 0.08, 0.05, legend=True)
xq = np.arange(nq)
ax.axvspan(npre - 0.5, nq - 0.5, color=BLUE_XL, lw=0, zorder=0)
ax.plot(xq, ts_['합성'], color=GRAY, lw=1.8, ls=(0, (4, 2)), marker='o', ms=3.5, mfc='white', mew=1.2)
ax.plot(xq, ts_['안동'], color=BLUE, lw=2.4, marker='o', ms=4.5, mfc='white', mew=1.6)
ax.text(npre + (nq - npre) / 2 - 0.5, max(ts_['안동'] + ts_['합성']) * 1.02, '가짜 시행 구간', ha='center', fontsize=7, fontweight='bold', color=BLUE_D)
ax.set_xticks(xq); ax.set_xticklabels([f"{q[2:4]}.{q[4]}Q" for q in ts_['분기']], fontsize=6.4, rotation=0)
ax.set_ylim(40, max(ts_['안동'] + ts_['합성']) * 1.1); base_line(ax); unit(ax, '지수')
legend(fig, [('안동', BLUE, 'line'), ('비교 조합(합성)', GRAY, 'dash')])
save(fig)

# 전국 지도: 진단점수
same = [s_ for s_ in DGJ['안동과_같은_유형'] if s_ != '안동시']
q5b = DG['진단점수'].quantile([0.2, 0.4, 0.6, 0.8]).values
ramp = ['#FDECEC', '#F6C3C4', '#EE8C8E', RED, '#8E1F24']
sc_col = lambda v: ramp[int(np.searchsorted(q5b, v))]
aA = DGJ['안동']
fig = base('전국지도_진단점수', 0, '확산', f"전국 {DGJ['대상수']}개 시·군 진단", f"안동은 {int(aA['순위'])}위",
           '네 지표(체험 소비 변화 · 숙박일수 · 저녁 전환 · 야간 방문)로 매긴 문제 점수. 진할수록 문제가 큼',
           '출처: 한국관광 데이터랩, 팀 전국 진단표(2026.9.23). 흰 칸 = 대상 아님. 순위는 가중치에 따라 18~100위(10~90% 범위)', h_in=5.2)
ax = fig.add_axes([0.02, fig._bot + 0.02, 0.56, fig._top - fig._bot - 0.03])
kmap(ax, {r['시군']: sc_col(r['진단점수']) for _, r in DG.iterrows()}, hl=('안동시',), hl_col=CHAR)
map_label(ax, '안동시', f"안동 {int(aA['순위'])}위", dx=0.9, dy=0.35, color=RED_D, fs=9)
top10 = DG.sort_values('순위').head(10)
fig.text(0.6, fig._top - 0.05, '문제 점수 상위 10곳', fontsize=8.4, fontweight='extra bold', color=INK)
for i, (_, r) in enumerate(top10.iterrows()):
    y_ = fig._top - 0.11 - i * 0.052
    fig.text(0.6, y_, f"{int(r['순위']):>2}", fontsize=7.6, fontweight='extra bold', color=RED, va='center')
    fig.text(0.64, y_, r['시군'], fontsize=7.6, color=INK, va='center')
    axb = fig.add_axes([0.76, y_ - 0.012, 0.15, 0.024]); axb.axis('off'); axb.set_xlim(0, 100)
    axb.plot([0, 100], [0, 0], color=TRACK, lw=5, solid_capstyle='round'); axb.plot([0, r['진단점수']], [0, 0], color=sc_col(r['진단점수']), lw=5, solid_capstyle='round')
    fig.text(0.925, y_, f"{r['진단점수']:.0f}", fontsize=7, color=SUB, va='center')
yl = fig._top - 0.11 - 10 * 0.052 - 0.02
for i, c in enumerate(ramp):
    fig.patches.append(Rectangle((0.6 + i * 0.06, yl - 0.012), 0.06, 0.024, transform=fig.transFigure, fc=c, ec='white', lw=1))
fig.text(0.6, yl - 0.045, '문제 작음', fontsize=6.4, color=SUB); fig.text(0.9, yl - 0.045, '문제 큼', fontsize=6.4, color=SUB, ha='right')
save(fig)

# 전국 지도: 안동과 같은 유형
fig = base('전국지도_같은유형6곳', 0, '확산', '안동과 같은 문제를 가진', f'전국 {len(same)}곳',
           '체험·문화 소비가 전국보다 많이 줄고, 평균 숙박일수가 전국보다 짧은 유형', '출처: 한국관광 데이터랩, 팀 전국 진단표. 두 지표 모두 문제 백분위 75 이상', h_in=5.2)
ax = fig.add_axes([0.02, fig._bot + 0.02, 0.56, fig._top - fig._bot - 0.03])
kmap(ax, {**{s_: BLUE for s_ in same}, '안동시': RED}, default='#EEF1F4', hl=tuple(same) + ('안동시',), hl_col=CHAR)
offs = {'안동시': (-1.6, -0.3), '영덕군': (0.8, -0.25), '울진군': (0.75, 0.3), '양양군': (0.7, 0.2), '강릉시': (0.8, -0.1), '남해군': (0.5, -0.45), '광명시': (-1.3, 0.3)}
for s_ in same + ['안동시']:
    dx_, dy_ = offs.get(s_, (0.7, 0.2))
    map_label(ax, s_, s_, dx=dx_, dy=dy_, color=RED if s_ == '안동시' else CHAR, fs=8 if s_ == '안동시' else 7)
dd = DG[DG['시군'].isin(same + ['안동시'])].sort_values('①체험문화_변화율')
fig.text(0.6, fig._top - 0.05, '같은 유형 7곳', fontsize=8.4, fontweight='extra bold', color=INK)
fig.text(0.78, fig._top - 0.05, '체험 변화', fontsize=6.6, color=SUB, ha='center'); fig.text(0.9, fig._top - 0.05, '숙박일수', fontsize=6.6, color=SUB, ha='center')
for i, (_, r) in enumerate(dd.iterrows()):
    y_ = fig._top - 0.12 - i * 0.07
    a_ = r['시군'] == '안동시'
    if a_:
        fig.patches.append(FancyBboxPatch((0.59, y_ - 0.03), 0.37, 0.06, boxstyle='round,pad=0,rounding_size=0.01', transform=fig.transFigure, fc=RED_XL, ec='none'))
    fig.text(0.6, y_, r['시군'], fontsize=8, fontweight='extra bold' if a_ else 'semibold', color=RED if a_ else INK, va='center')
    fig.text(0.78, y_, f"{m(r['①체험문화_변화율'] * 100)}%", fontsize=8, fontweight='bold', color=INK, va='center', ha='center')
    fig.text(0.9, y_, f"{r['②평균숙박일수']:.2f}일", fontsize=8, color=INK, va='center', ha='center')
fig.text(0.6, fig._top - 0.12 - 7 * 0.07, f"전국 중앙값: 체험 변화 {m(DGJ['중앙값']['①체험문화_변화율'] * 100)}%, 숙박 {DGJ['중앙값']['②평균숙박일수']:.2f}일", fontsize=6.8, color=SUB, va='center')
save(fig)

same = [s for s in DGJ['안동과_같은_유형'] if s != '안동시']
fig = base('전국진단_유형', 25, '확산', '안동과 같은 문제를 가진 곳', f'전국 {len(same)}곳',
           f"전국 {DGJ['대상수']}개 시·군: 방문 1회당 체험·문화 소비 변화 × 평균 숙박일수. 점선 = 전국 중앙값",
           '출처: 한국관광 데이터랩. 왼쪽 아래 = 체험 소비가 줄고 숙박이 짧은 유형. ±60% 밖은 가장자리에 표시', h_in=4.4)
ax = axes(fig, 0.08, 0.05, legend=True)
dx = (DG['①체험문화_변화율'] * 100).clip(-60, 60); dy = DG['②평균숙박일수']
mx, my = DGJ['중앙값']['①체험문화_변화율'] * 100, DGJ['중앙값']['②평균숙박일수']
ax.add_patch(Rectangle((-62, dy.min() - 0.12), mx + 62, my - dy.min() + 0.12, color=RED_XL, lw=0, zorder=0))
ax.axvline(mx, color=CHAR, lw=0.9, ls=(0, (3, 2))); ax.axhline(my, color=CHAR, lw=0.9, ls=(0, (3, 2)))
kind = DG['시군'].map(lambda s: 'A' if s == '안동시' else ('S' if s in same else 'O'))
ax.scatter(dx[kind == 'O'], dy[kind == 'O'], s=14, color=GRAY_L, zorder=2)
ax.scatter(dx[kind == 'S'], dy[kind == 'S'], s=40, color=CHAR, zorder=3, edgecolor='white', lw=0.8)
ax.scatter(dx[kind == 'A'], dy[kind == 'A'], s=90, color=RED, zorder=4, edgecolor='white', lw=1.2)
for _, r in DG[kind != 'O'].iterrows():
    a_ = r['시군'] == '안동시'
    if a_:                                                  # 안동 점은 기장군과 거의 겹쳐 빈 자리로 끌어내 이름을 단다
        ax.annotate('안동시', (r['①체험문화_변화율'] * 100, r['②평균숙박일수']), xytext=(-44, 3.32), fontsize=8.4, fontweight='extra bold', color=RED,
                    va='center', ha='center', arrowprops=dict(arrowstyle='-', color=RED, lw=0.9, shrinkB=5))
        continue
    ax.text(r['①체험문화_변화율'] * 100 + 1.5, r['②평균숙박일수'] + 0.035, r['시군'], fontsize=6.8, color=INK, fontweight='semibold')
ax.text(-59, dy.min() - 0.07, '같은 유형 영역', fontsize=7, fontweight='bold', color=RED)
ax.set_xlim(-62, 62); ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: m(v, 0) + '%' if v else '0'))
ax.set_ylim(dy.min() - 0.12, dy.max() + 0.1); base_line(ax); ax.grid(axis='x', color=TRACK, lw=0.8); unit(ax, '평균 숙박일수(일)')
ax.text(1, -0.1, '방문 1회당 체험·문화 소비 변화율', transform=ax.transAxes, fontsize=6.5, color=SUB, ha='right')
legend(fig, [('안동시', RED, 'dot'), ('같은 유형', CHAR, 'dot'), ('다른 시·군', GRAY_L, 'dot')])
save(fig)


# 안동 네 지표 문제 백분위
ind = [('체험·문화 소비 변화', '①체험문화_변화율_문제백분위'), ('평균 숙박일수', '②평균숙박일수_문제백분위'),
       ('저녁 전환율', '③저녁전환율_문제백분위'), ('야간 방문 비중', '④야간방문비중_문제백분위')]
fig = base('안동_네지표_문제백분위', 0, '확산', '안동의 문제는', '체험 소비와 숙박일수',
           f"전국 {DGJ['대상수']}개 시·군 중 안동의 문제 백분위 (100에 가까울수록 문제가 큼, 75 이상 = 하위 25%)", '출처: 한국관광 데이터랩, 팀 전국 진단표. 저녁·야간은 전국 중간보다 나음', h_in=3.4)
ax = axes(fig, 0.22, 0.12, legend=False)
vals_ = [aA[k] for _, k in ind]
hbar_track(ax, [l for l, _ in ind], vals_, 100, [RED if v >= 75 else GRAY_L for v in vals_], lambda v: f'{v:.0f}', lw=10)
ax.axvline(75, color=CHAR, lw=1, ls=(0, (3, 2)))
ax.text(75, len(ind) - 0.35, '75', ha='center', fontsize=6.8, color=CHAR)
save(fig)

# 144곳 유형 분포
tp = pd.Series(DGJ['유형분포']).drop('-', errors='ignore').sort_values(ascending=False)
tp.index = [i.replace('체험문화', '체험').replace('평균숙박일수', '숙박').replace('저녁전환율', '저녁').replace('야간방문비중', '야간') for i in tp.index]
mine = '체험 · 숙박'
fig = base('전국진단_유형분포', 0, '확산', f"전국 {DGJ['대상수']}곳의 문제 유형,", f"안동 유형은 {int(tp[mine])}곳",
           f"두 개 이상 지표에서 하위 25%인 조합별 시·군 수 (문제 없음 {DGJ['유형분포'].get('-', 0)}곳 제외)", '출처: 한국관광 데이터랩, 팀 전국 진단표. 체험 = 체험·문화 소비 변화, 숙박 = 평균 숙박일수', h_in=4.2)
ax = axes(fig, 0.3, 0.12, legend=False)
hbar_track(ax, list(tp.index), list(tp.values), tp.max(), [RED if k == mine else GRAY_L for k in tp.index], lambda v: f'{int(v)}곳', lw=8)
for t in ax.get_yticklabels():
    if t.get_text() == mine:
        t.set_fontweight('extra bold'); t.set_color(RED)
save(fig)

# 주민증 운영 지자체와 발급 규모 (9/28 2차: 트랙 막대가 겹쳐 보여 → 52개 점 격자 + 발급 규모 원 크기)
iss = Q['주민증규모']['발급']
num = lambda t: float(t.replace('명', '').replace(',', '').replace('6만 1천여', '61000').replace('5만', '50000').strip())
n_op = Q['주민증']['운영지역수']
fig = base('주민증_운영지자체_발급', 0, '확산', f'주민증을 운영하는 {n_op}개 지자체에', '같은 방식을 적용할 수 있다',
           f"디지털 관광주민증 운영 지자체 수와 주요 지자체 발급 규모 (전국 누적 {Q['주민증규모']['전국누적발급'].split('(')[0].strip()})",
           '출처: 문화체육관광부 보도(2025.3.26), 각 지자체 발표. 발급 규모는 발표 시점이 서로 다름(원 아래 표기), 원 넓이 = 발급 인원', h_in=3.9)
# 왼쪽: 큰 숫자 + 52개 점
top_in, bot_in = fig._top * fig._h, fig._bot * fig._h
axl = fig.add_axes([0.04, fig._bot + 0.03, 0.36, fig._top - fig._bot - 0.05]); axl.axis('off')
wl, hl_ = 0.36 * W_IN, (fig._top - fig._bot - 0.05) * fig._h
axl.set_xlim(0, wl); axl.set_ylim(0, hl_); axl.set_aspect('equal')
axl.text(0.05, hl_ - 0.35, f'{n_op}', fontsize=34, fontweight='black', color=BLUE, va='center')
axl.text(0.82, hl_ - 0.28, '개 지자체', fontsize=10, fontweight='extra bold', color=CHAR, va='center')
axl.text(0.82, hl_ - 0.5, '디지털 관광주민증 운영', fontsize=7.2, color=SUB, va='center')
cols_, gap_ = 13, 0.17
for k in range(n_op):
    cx_, cy_ = 0.12 + (k % cols_) * gap_, hl_ - 1.05 - (k // cols_) * gap_
    axl.add_patch(Circle((cx_, cy_), 0.055, color=BLUE if k == 0 else GRAY_L, lw=0))
ly_ = hl_ - 1.05 - 4 * gap_ - 0.08
for lx_, lc_, lt_ in ((0.12, BLUE, '안동'), (0.7, GRAY_L, '다른 운영 지자체')):
    axl.add_patch(Circle((lx_, ly_), 0.045, color=lc_, lw=0))
    axl.text(lx_ + 0.09, ly_, lt_, fontsize=6.8, color=SUB, va='center')
fig.add_artist(Line2D([0.43, 0.43], [fig._bot + 0.05, fig._top - 0.03], color=TRACK, lw=1, transform=fig.transFigure))
# 오른쪽: 발급 규모 원 (넓이 비례, 바닥 정렬)
axr = fig.add_axes([0.46, fig._bot + 0.03, 0.52, fig._top - fig._bot - 0.05]); axr.axis('off')
wr, hr = 0.52 * W_IN, (fig._top - fig._bot - 0.05) * fig._h
axr.set_xlim(0, wr); axr.set_ylim(0, hr); axr.set_aspect('equal')
iss_s = sorted(iss, key=lambda r: -num(r[1]))
rmax = 0.37; vmax = num(iss_s[0][1]); base_y = 0.95
for k, (nm_, cnt_, when_) in enumerate(iss_s):
    v = num(cnt_); r_ = rmax * np.sqrt(v / vmax)
    cx_ = 0.55 + k * (wr - 1.1) / (len(iss_s) - 1)
    a_ = nm_ == '안동시'
    axr.add_patch(Circle((cx_, base_y + r_), r_, color=BLUE if a_ else ('#C9D3DE' if k else GRAY_L), lw=0))
    axr.text(cx_, base_y + r_, f'{v / 10000:.1f}만', ha='center', va='center', fontsize=11 if a_ else 9, fontweight='black',
             color='white' if a_ else CHAR)
    axr.text(cx_, base_y - 0.18, nm_, ha='center', va='center', fontsize=8.4, fontweight='extra bold', color=BLUE_D if a_ else INK)
    axr.text(cx_, base_y - 0.38, when_ + ' 발표', ha='center', va='center', fontsize=6.6, color=SUB)
axr.plot([0.1, wr - 0.1], [base_y, base_y], color=GRAY_L, lw=1)
axr.text(0.1, hr - 0.12, '발급 인원 (명)', fontsize=6.8, color=SUB, va='center')
save(fig)

print(f'저장 {len(DONE)}장:', OUT)
for k_, v_ in OVERLAP.items():
    print('[겹침]', k_, *v_[:8], sep='\n   ')
print('겹침 있는 그림', len(OVERLAP), '장')
