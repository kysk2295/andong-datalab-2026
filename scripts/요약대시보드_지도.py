# -*- coding: utf-8 -*-
"""요약 대시보드 「버스」 화면의 안동 시내 지도 PNG (2026-09-29)

옛 정류장 점 그림(위도·경도 산점도)을 실제 지도로 바꾼다. 요약대시보드.py가 make_map()을 불러 PNG를 만든 뒤 시트에 넣는다.
지도 자료는 안동 3D 지도(andong-atlas/public/data)에 이미 받아 둔 것을 쓴다(새로 받지 않음).
  - 물길·도로: OpenFreeMap / OpenMapTiles / © OpenStreetMap contributors (ODbL 1.0), 2026-09-13 스냅샷 (map.json)
  - 읍면동 경계: 통계청 SGIS 행정동 경계, 가공 vuski/admdongkor ver20260701 (boundaries.json)
  - 112번 노선 선형·정류장: 안동시 버스정보시스템 2026-09-29 수집 (transport.json)
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Polygon as MPoly
from matplotlib.collections import LineCollection, PatchCollection
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
ATLAS = ROOT / 'andong-atlas/public/data'
for f in Path.home().joinpath('Library/Fonts').glob('Pretendard-*.otf'):
    font_manager.fontManager.addfont(str(f))
plt.rcParams.update({'font.family': 'Pretendard', 'axes.unicode_minus': True})

BLUE, DEEP, RED, INK, MUTE = '#2D6BD9', '#1A4FA8', '#E03C31', '#34383C', '#6B7075'
WATER, ROAD, EDGE, LAND = '#CFE2F6', '#DDE1E5', '#B9C0C7', '#FAFBFC'
X0, X1, Y0, Y1 = 128.664, 128.792, 36.538, 36.598            # 안동역 ~ 문화관광단지
KX = np.cos(np.radians(36.57))                               # 경도 1도를 위도 1도 길이에 맞춤


def rings(geom):
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    return [np.array(p[0]) for p in polys if len(p) and len(p[0]) > 2]


def inside(a):
    return (a[:, 0].max() > X0) and (a[:, 0].min() < X1) and (a[:, 1].max() > Y0) and (a[:, 1].min() < Y1)


def make_map(out: Path, km=3.2, last_bus='18:45', after19=0):
    m = json.loads((ATLAS / 'map.json').read_text(encoding='utf-8'))
    bnd = json.loads((ATLAS / 'boundaries.json').read_text(encoding='utf-8'))
    tr = json.loads((ATLAS / 'transport.json').read_text(encoding='utf-8'))
    W = 11.0
    fig = plt.figure(figsize=(W, W * (Y1 - Y0) / ((X1 - X0) * KX)), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1); ax.set_aspect(1 / KX); ax.axis('off')
    fig.patch.set_facecolor(LAND)
    # 물길(낙동강·반변천·안동호)
    wp = [MPoly(a, closed=True) for f in m['water'] for a in rings(f['geometry']) if inside(a)]
    ax.add_collection(PatchCollection(wp, facecolor=WATER, edgecolor='none', zorder=1))
    # 도로
    segs = []
    for f in m['transportation']:
        g = f['geometry']
        lines = g['coordinates'] if g['type'] == 'MultiLineString' else ([g['coordinates']] if g['type'] == 'LineString' else [])
        for ln in lines:
            a = np.array(ln)
            if len(a) > 1 and inside(a): segs.append(a)
    ax.add_collection(LineCollection(segs, colors=ROAD, linewidths=0.6, zorder=2))
    # 112번 정류장·핵심 장소 먼저 구한다(동 이름이 장소 표시와 겹치지 않게)
    stops = {}
    for r in tr['routes']:
        if r['number'] == '112':
            for s in r['stops']: stops[s['name']] = s['coordinates']
    P = {'안동역': stops['안동역(안동터미널)'], '원도심': stops['교보생명'], '월영교': stops['월영교']}
    near = lambda x, y: any(abs(x - px) < 0.009 and abs(y - py) < 0.006 for px, py in P.values())
    # 읍면동 경계 + 이름(시내 동만)
    for f in bnd['features']:
        name = f['properties']['adm_nm'].split()[-1]
        for a in rings(f['geometry']):
            if inside(a):
                ax.plot(a[:, 0], a[:, 1], color=EDGE, lw=0.7, ls=(0, (4, 3)), zorder=3)
        big = max(rings(f['geometry']), key=len)
        cx, cy = big[:, 0].mean(), big[:, 1].mean()
        if name.endswith('동') and not near(cx, cy) and X0 + 0.004 < cx < X1 - 0.004 and Y0 + 0.003 < cy < Y1 - 0.003:
            ax.text(cx, cy, name, fontsize=7.5, color='#A3AAB1', ha='center', va='center', zorder=4)
    # 112번 노선(모든 방향) + 정류장
    for r in tr['routes']:
        if r['number'] != '112': continue
        a = np.array(r['coordinates'])
        ax.plot(a[:, 0], a[:, 1], color='white', lw=5.2, solid_capstyle='round', zorder=5)
        ax.plot(a[:, 0], a[:, 1], color=RED, lw=2.6, solid_capstyle='round', zorder=6)
    xy = np.array(list(stops.values()))
    ax.scatter(xy[:, 0], xy[:, 1], s=9, color='white', edgecolor=RED, linewidth=0.9, zorder=7)
    # 핵심 장소
    lab = {'안동역': ('안동역 · 터미널', (0, 16), 'center'), '원도심': ('원도심\n(찜닭골목·문화의거리)', (0, -30), 'center'), '월영교': ('월영교', (0, 17), 'center')}
    for k, (x, y) in P.items():
        ax.scatter([x], [y], s=150, color=DEEP, edgecolor='white', linewidth=2, zorder=9)
        t, off, ha = lab[k]
        ax.annotate(t, (x, y), xytext=off, textcoords='offset points', ha=ha, va='center', fontsize=10.5, fontweight='bold', color=INK, zorder=10,
                    bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='none', alpha=0.9))
    # 원도심 → 월영교 구간 설명
    (xa, ya), (xb, yb) = P['원도심'], P['월영교']
    ax.annotate('', xy=(xb - 0.0012, yb - 0.0006), xytext=(xa + 0.0012, ya + 0.0006),
                arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.2, ls=(0, (3, 2)), shrinkA=6, shrinkB=6), zorder=8)
    ax.text((xa + xb) / 2 - 0.002, (ya + yb) / 2 + 0.0045, f'원도심 → 월영교 {km:.1f}km\n112번 한 노선 · 원도심 출발 막차 {last_bus}\n19시 이후 {after19}회',
            fontsize=9.5, color=RED, fontweight='bold', ha='center', va='bottom', zorder=10, linespacing=1.4,
            bbox=dict(boxstyle='round,pad=0.45', fc='white', ec=RED, lw=0.8))
    # 축척·방위
    sx, sy = X1 - 0.022, Y0 + 0.004; one_km = 1 / (111.32 * KX)
    ax.plot([sx, sx + one_km], [sy, sy], color=INK, lw=2, zorder=10)
    ax.text(sx + one_km / 2, sy + 0.0012, '1km', fontsize=8, color=INK, ha='center', va='bottom', zorder=10)
    ax.annotate('N', (X1 - 0.005, Y1 - 0.004), xytext=(X1 - 0.005, Y1 - 0.011), ha='center', fontsize=9, color=INK, fontweight='bold',
                arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.2), zorder=10)
    ax.text(X0 + 0.002, Y0 + 0.0015, '지도: © OpenStreetMap contributors (ODbL), OpenFreeMap · 행정동 경계: 통계청 SGIS(vuski/admdongkor) · 노선: 안동시 버스정보시스템(2026.9)',
            fontsize=6.5, color=MUTE, ha='left', va='bottom', zorder=10)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, facecolor=LAND)
    plt.close(fig)
    return out


if __name__ == '__main__':
    print(make_map(ROOT / '보고서/요약대시보드/그림/버스_112번_지도.png'))
