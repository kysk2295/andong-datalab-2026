"""영상용 숫자·도형 데이터를 정본 파일에서 만든다 → assets/data.js (window.ED)

숫자를 손으로 쓰지 않기 위한 스크립트. 정본:
  보고서/교수브리핑_20260922/수치.json          146개 시·군 방문당 체험·문화 소비 변화율, 안동 2024·2026
  보고서/성과도출_20260922/시뮬레이션결과.json    참여율 3단계 시나리오
  보고서/성과도출_20260922/시나리오_기준_1만회.csv 기준 시나리오 1만 회 추출값(분포 그림)
  보고서/성과도출_20260922/순차도입_검정력.json   순차 확대 검정력
  보고서/**/전국진단.json                        같은 유형 시·군
  data/external/경계/skorea-municipalities-2018-geo.json  시·군 경계(지도)
실행: .venv_pdf/bin/python 보고서/영상_20260928/eodream-verify/tools/make_data.py (저장소 루트에서)
"""
import glob, json
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1] / 'assets' / 'data.js'
Q = json.loads((ROOT / '보고서/교수브리핑_20260922/수치.json').read_text(encoding='utf-8'))
S = json.loads((ROOT / '보고서/성과도출_20260922/시뮬레이션결과.json').read_text(encoding='utf-8'))
PW = json.loads((ROOT / '보고서/성과도출_20260922/순차도입_검정력.json').read_text(encoding='utf-8'))
DG = json.loads(Path(glob.glob(str(ROOT / '보고서/**/전국진단.json'), recursive=True)[0]).read_text(encoding='utf-8'))
DRAWS = pd.read_csv(ROOT / '보고서/성과도출_20260922/시나리오_기준_1만회.csv')

# ── 1. 146개 시·군 변화율 벌떼 배치 (x = 변화율 %, −40~+40 밖은 가장자리에 모아 개수만 표시) ──
DIST = Q['체험문화']['분포']
LO, HI, R = -40.0, 40.0, 0.7        # 축 범위(%), 점 반지름(축 단위 %) — 화면에서 점 지름 ≈ 14px
vals = sorted(DIST.items(), key=lambda kv: (kv[0] != '안동시', kv[1]))   # 안동을 맨 먼저 놓아 축 위(0층)에 둔다
placed, dots = [], []
for name, v in vals:
    if v < LO or v > HI:
        continue
    k = 0
    while any(abs(px - v) < 2 * R and pk == k for px, pk in placed):     # 겹치면 한 층 위로 (위로만 쌓는 점 그림)
        k += 1
    placed.append((v, k)); dots.append({'n': name, 'v': round(v, 2), 'k': k})
median = float(np.median(list(DIST.values())))
EX24, EX26 = Q['체험문화']['안동_2024'], Q['체험문화']['안동_2026']


def after(nm):                                   # 서식4_작성본.py ex_after와 같은 식
    ch = (EX26 * (1 + S['시나리오'][nm]['지표1_증가율']['P50']) / EX24 - 1) * 100
    return round(ch, 1), sum(1 for k, x in DIST.items() if k != '안동시' and x < ch) + 1


# ── 2. 추가 소비 1만 회 분포 (억 원, 0.2억 간격, 0~6억 밖은 양끝 칸에 더함) ──
x = DRAWS['추가소비합'].to_numpy() / 1e8
edges = np.arange(0, 6.0001, 0.2)
counts = np.histogram(np.clip(x, 0, 5.9999), bins=edges)[0]
order = np.random.default_rng(20260928).permutation(len(x))      # 쌓이는 순서(보기용, 고정 난수)
cum = [np.histogram(np.clip(x[order[:n]], 0, 5.9999), bins=edges)[0].tolist() for n in (100, 1000, 3000, 10000)]
q = {k: round(float(np.quantile(x, p)), 2) for k, p in (('p5', .05), ('p50', .5), ('p95', .95))}

# ── 3. 전국 시·군 지도 (단순화한 SVG 경로, 1000×1200 좌표) ──
G = json.loads((ROOT / 'data/external/경계/skorea-municipalities-2018-geo.json').read_text(encoding='utf-8'))
X0, X1, Y0, Y1 = 124.5, 130.0, 33.0, 38.7                       # 제주 포함, 울릉·독도 제외 범위
W, H = 1000, 1000 * (Y1 - Y0) / (X1 - X0) / np.cos(np.radians(36))
def proj(lon, lat): return ((lon - X0) / (X1 - X0) * W, (Y1 - lat) / (Y1 - Y0) * H)


def rdp(pts, eps):
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]; ab = b - a; n = np.hypot(*ab) or 1e-9
    d = np.abs(ab[0] * (pts[:, 1] - a[1]) - ab[1] * (pts[:, 0] - a[0])) / n
    i = int(np.argmax(d))
    if d[i] > eps: return np.vstack([rdp(pts[:i + 1], eps)[:-1], rdp(pts[i:], eps)])
    return np.vstack([a, b])


same = [s for s in DG['안동과_같은_유형'] if s != '안동시']
paths, cent = [], {}
for f in G['features']:
    nm = f['properties']['name']; polys = f['geometry']['coordinates']
    if f['geometry']['type'] == 'Polygon': polys = [polys]
    d, big = [], (0, None)
    for poly in polys:
        ring = np.array([proj(*p) for p in poly[0]])
        if ring[:, 0].min() > W or ring[:, 1].min() > H: continue
        area = 0.5 * abs(np.dot(ring[:, 0], np.roll(ring[:, 1], 1)) - np.dot(ring[:, 1], np.roll(ring[:, 0], 1)))
        if area < 0.6: continue
        m = len(ring) // 2                                   # 닫힌 고리는 반으로 나눠 단순화
        s = np.vstack([rdp(ring[:m + 1], 1.2)[:-1], rdp(ring[m:], 1.2)])
        if len(s) < 4: continue
        d.append('M' + 'L'.join(f'{px:.0f},{py:.0f}' for px, py in s) + 'Z')
        if area > big[0]: big = (area, ring.mean(0))
    if d:
        paths.append({'n': nm, 'd': ''.join(d)})
        if nm in same + ['안동시']: cent[nm] = [round(float(big[1][0])), round(float(big[1][1]))]

ED = {
    'ex': {'y2024': round(EX24, 1), 'y2026': round(EX26, 1), 'change': round(DIST['안동시'], 1),
           'rank': Q['체험문화']['안동_감소순위'], 'n': len(DIST), 'median': round(median, 1),
           'lo': LO, 'hi': HI, 'below': sum(v < LO for v in DIST.values()), 'above': sum(v > HI for v in DIST.values()),
           'dots': dots},
    'sc': {nm: {'p': S['시나리오'][nm]['참여율'], 'change': after(nm)[0], 'rank': after(nm)[1],
                'add': round(S['시나리오'][nm]['추가소비합']['P50'] / 1e8, 2)} for nm in ('기준', '흥행', '목표')},
    'mc': {'n': len(x), 'edges': [round(e, 1) for e in edges.tolist()], 'counts': counts.tolist(), 'cum': cum, 'steps': [100, 1000, 3000, 10000], **q},
    'pw': {'groups': [21, 21, 21, 20], 'months': 5,
           'power50': next(c['검정력'] for c in PW['확대안']['곡선'] if abs(c['효과'] - .5) < 1e-9),
           'fp': PW['확대안']['효과0_거짓양성']},
    'same': [s.replace('시', '').replace('군', '') for s in same],
    'map': {'w': W, 'h': round(H), 'paths': paths, 'cent': cent},
}
OUT.write_text('window.ED = ' + json.dumps(ED, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
print(OUT, f'{OUT.stat().st_size / 1024:.0f}KB', '| 안동', ED['ex']['change'], ED['ex']['rank'], '중앙', ED['ex']['median'],
      '| 시나리오', ED['sc'], '| 1만회', q, '| 검정력', ED['pw']['power50'], ED['pw']['fp'], '| 같은유형', ED['same'], '| 점', len(dots))
