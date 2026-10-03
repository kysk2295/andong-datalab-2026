"""스케치 시트 storyboard.html 생성 (움직임 없음, 스크립트 없음, file://로 열림)

숫자·점 위치·분포는 assets/data.js(make_data.py 출력)에서 읽어 그린다. 각 칸은 1920×1080 SVG를 줄여 보인다.
실행: python3 tools/make_storyboard.py (프로젝트 폴더에서)
"""
import json, html
from pathlib import Path

P = Path(__file__).resolve().parents[1]
ED = json.loads((P / 'assets/data.js').read_text(encoding='utf-8').split('=', 1)[1].strip().rstrip(';'))
BG, INK, TXT, MUTED, LIGHT, BLUE, DEEP, BL, WASH, GRAY, TRACK = (
    '#FBFCFE', '#34383C', '#222222', '#555555', '#8A9096', '#2D6BD9', '#1A4FA8', '#A8C4F0', '#EAF1FC', '#D5D9DC', '#ECEEF0')
SECTIONS = ('문제', '해법', '시행 전 계산', '시행 후 확인')
e = html.escape


def t(x, y, s, size=32, w=500, fill=TXT, anchor='start', extra=''):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{anchor}" {extra}>{e(s)}</text>'


def head(eyebrow, l1, l2, tag=None):
    s = t(120, 128, eyebrow, 24, 700, BLUE, extra='letter-spacing="3"')
    if tag:
        s += f'<rect x="{140 + 24 * len(eyebrow) * .62}" y="100" width="96" height="38" rx="19" fill="none" stroke="{BLUE}" stroke-width="2"/>' \
             + t(188 + 24 * len(eyebrow) * .62, 127, tag, 22, 700, BLUE, 'middle')
    s += t(120, 222, l1, 72, 800, INK) + t(120, 310, l2, 72, 800, BLUE)
    return s + f'<rect x="120" y="344" width="72" height="5" fill="{BLUE}"/>'


def source(txt):
    return f'<rect x="120" y="968" width="14" height="14" fill="{BLUE}"/>' + t(146, 982, '출처: ' + txt, 20, 500, LIGHT)


def strip(cur):
    s, w = '', 1680 / 4
    for i, name in enumerate(SECTIONS):
        x = 120 + i * w
        on = i == cur
        s += f'<rect x="{x + 4}" y="1024" width="{w - 8}" height="6" rx="3" fill="{BLUE if on else TRACK}"/>'
        s += t(x + 4, 1058, name, 18, 700 if on else 500, BLUE if on else LIGHT)
    return s


def svg(body):
    return f'<svg viewBox="0 0 1920 1080" xmlns="http://www.w3.org/2000/svg" font-family="Pretendard"><rect width="1920" height="1080" fill="{BG}"/>{body}</svg>'


def swarm(x0, x1, yc, andong=None, ghosts=(), step=14):
    """위로 쌓는 점 그림: 축(yc) 위에 층(k)마다 step px. 눈금·라벨은 축 아래."""
    ex = ED['ex']; lo, hi = ex['lo'], ex['hi']
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    s = f'<line x1="{x0}" y1="{yc + 10}" x2="{x1}" y2="{yc + 10}" stroke="{GRAY}" stroke-width="2"/>'
    for v in (-40, -20, 0, 20, 40):
        s += t(X(v), yc + 44, f'{v:+d}%'.replace('+0', '0').replace('-', '−'), 20, 500, LIGHT, 'middle')
    for d in ex['dots']:
        if d['n'] == '안동시': continue
        s += f'<circle cx="{X(d["v"]):.1f}" cy="{yc - d["k"] * step:.1f}" r="7" fill="{GRAY}"/>'
    s += t(x0 - 12, yc + 7, f'← {ex["below"]}곳', 18, 600, LIGHT, 'end') + t(x1 + 12, yc + 7, f'{ex["above"]}곳 →', 18, 600, LIGHT)
    mx = X(ex['median'])
    s += f'<line x1="{mx}" y1="{yc - 190}" x2="{mx}" y2="{yc + 16}" stroke="{INK}" stroke-width="3" stroke-dasharray="8 8"/>'
    s += t(mx, yc - 204, f'전국 중앙 {ex["median"]}%'.replace('-', '−'), 24, 700, INK, 'middle')
    for g in ghosts:
        s += f'<circle cx="{X(g):.1f}" cy="{yc}" r="11" fill="{BG}" stroke="{BL}" stroke-width="3"/>'
    if andong is not None:
        s += f'<circle cx="{X(andong):.1f}" cy="{yc}" r="13" fill="{BLUE}"/>'
    return s, X


def people(x0, y0, n_on, n_soft=0, gap=46, r=15):
    s = ''
    for i in range(100):
        cx, cy = x0 + (i % 10) * gap, y0 + (i // 10) * gap
        c = BLUE if i < n_on else (BL if i < n_on + n_soft else TRACK)
        s += f'<circle cx="{cx}" cy="{cy - 8}" r="{r * .45}" fill="{c}"/><rect x="{cx - r * .75}" y="{cy}" width="{r * 1.5}" height="{r * .9}" rx="{r * .45}" fill="{c}"/>'
    return s


F = []
ex, sc, mc, pw = ED['ex'], ED['sc'], ED['mc'], ED['pw']

# F1
b = head('문제 01', '방문객은 늘었는데', '체험·문화 소비는 줄고 있다')
b += t(120, 520, f'{ex["y2024"]}원 →', 52, 700, LIGHT) + t(112, 690, f'{ex["y2026"]}원', 150, 800, BLUE)
b += t(120, 760, '방문 1회당 체험·문화 소비(외지인)', 28, 600, MUTED) + t(120, 800, '2024년 → 2026년, 각 1~8월', 24, 500, LIGHT)
sw, X = swarm(960, 1780, 700, andong=ex['change'])
b += sw + t(X(ex['change']), 800, f'안동 {ex["change"]}%'.replace('-', '−'), 30, 800, BLUE, 'middle')
b += t(X(ex['change']), 836, f'146개 시·군 중 감소폭 {ex["rank"]}번째', 22, 600, MUTED, 'middle')
b += source('한국관광 데이터랩 신용카드 관광소비(외지인), 레저용품 쇼핑 제외') + strip(0)
F.append(('f01', 'PROBLEM', '0–12s', '줄고 있다', svg(b), '<b>183.5원이 152.7원으로 내려가며 세어지고,</b> 오른쪽 146개 점이 먼저 깔린 뒤 안동 점만 파랑으로 떨어진다. 전국 중앙선이 마지막에 그어진다.', 'cut'))

# F2
b = t(120, 470, '시행하기 전에,', 96, 800, INK) + t(120, 590, '데이터로 먼저 계산했습니다', 96, 800, BLUE)
b += f'<rect x="120" y="640" width="72" height="5" fill="{BLUE}"/>' + t(120, 720, '그리고 시행하면서 확인할 방법까지 정했습니다', 40, 600, MUTED) + strip(0)
F.append(('f02', 'PROMISE', '12–18s', '먼저 계산했다', svg(b), '<b>멈추는 장면.</b> 두 줄이 한 번 올라오고 3초 이상 그대로 읽힌다. 영상의 약속을 여기서 말한다.', 'crossfade'))

# F3 / F4 공통 선
L0, L1, LY = 380, 1540, 700


def line(color, w=6, km=True):
    return (f'<line x1="{L0}" y1="{LY}" x2="{L1}" y2="{LY}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<circle cx="{L0}" cy="{LY}" r="26" fill="{INK}"/><circle cx="{L1}" cy="{LY}" r="26" fill="{INK}"/>'
            + t(L0, LY + 76, '원도심', 34, 800, INK, 'middle') + t(L1, LY + 76, '월영교', 34, 800, INK, 'middle')
            + (t((L0 + L1) / 2, LY - 24, '3.2km', 22, 600, LIGHT, 'middle') if km else ''))


b = head('문제 02', '사람이 모이는 곳엔 혜택이 없고,', '막차 앞에서 밤이 끊긴다') + line(GRAY)
b += t(L0, 520, '0곳', 110, 800, BLUE, 'middle') + t(L0, 568, '주민증 혜택 업체', 28, 700, INK, 'middle') + t(L0, 604, '외지인 방문 1위(12.5%)', 22, 500, MUTED, 'middle')
b += t(960, 870, '0회', 110, 800, BLUE, 'middle') + t(960, 918, '19시 이후 시내버스', 28, 700, INK, 'middle') + t(960, 952, '112번 원도심 출발 막차 18:45', 22, 500, MUTED, 'middle')
b += t(L1, 520, '0곳', 110, 800, BLUE, 'middle') + t(L1, 568, '1km 안 주점', 28, 700, INK, 'middle') + t(L1, 604, '21시까지 식사 가능 3곳', 22, 500, MUTED, 'middle')
b += strip(0)
F.append(('f03', 'GAPS', '18–30s', '데이터로 찾은 빈 곳', svg(b), '<b>선이 왼쪽에서 오른쪽으로 그어지고</b> 0이 원도심 → 선 가운데 → 월영교 순서로 튀어 오른다. 출처는 마지막에.', 'slide-left'))

# F4
b = head('해법', '낮의 원도심에서', '밤의 월영교까지 잇는다') + line(BLUE, km=False)
b += t(L0, 470, '1 낮', 26, 800, BLUE, 'middle') + t(L0, 530, '0곳 → 83곳', 64, 800, BLUE, 'middle') + t(L0, 574, '원도심 식당에서 식사 → 체험 10% 할인', 24, 600, INK, 'middle')
b += f'<rect x="700" y="610" width="520" height="44" rx="22" fill="{BLUE}"/>' + t(960, 642, '2 저녁 18:30 ~ 21:00 이동', 26, 800, '#FFFFFF', 'middle')
b += t(960, 866, '택시로 월영교까지, 이용이 늘면 셔틀', 26, 700, INK, 'middle') + t(960, 904, '주말 안동역 승차 18~19시 최다 · 막차 21~22시', 22, 500, MUTED, 'middle')
b += t(L1, 470, '3 밤', 26, 800, BLUE, 'middle') + t(L1, 530, '문보트 · 팝업', 56, 800, BLUE, 'middle') + t(L1, 574, '21시 이후 식사·주점 팝업', 24, 600, INK, 'middle')
b += source('코레일 안동역 시간대별 승차 · 팀 설문(2026.9.23~24)') + strip(1)
F.append(('f04', 'RELAY', '30–44s', '3단계 릴레이', svg(b), '<b>같은 선이 파랑으로 다시 칠해지며</b> 1 → 2 → 3이 차례로 켜지고, 장면 3의 0이 채워진 값으로 뒤집힌다.', 'none(연속)'))

# F5
b = head('시행 전 계산 01', '실제 기록을 넣고,', '설문은 깎아서 넣었다')
for i, s_ in enumerate(('주민증 이용 기록', '축제 방문객 소비', '체험 가격 27개', '팀 설문 103명')):
    y = 440 + i * 100
    b += f'<rect x="120" y="{y}" width="400" height="70" rx="35" fill="{WASH}" stroke="{BL}" stroke-width="2"/>' + t(320, y + 46, s_, 28, 700, INK, 'middle')
    b += f'<line x1="520" y1="{y + 35}" x2="700" y2="{590 + 20}" stroke="{BL}" stroke-width="3"/>'
b += f'<rect x="700" y="540" width="300" height="140" rx="20" fill="{BLUE}"/>' + t(850, 625, '1만 번 계산', 40, 800, '#FFFFFF', 'middle')
b += t(1180, 420, "설문에서 '하겠다' 100명", 28, 700, INK) + people(1200, 470, 33, 7)
b += t(1180, 950, '실제로 할 것으로 본 사람 33~40명(선행연구)', 28, 800, BLUE)
b += t(120, 900, '설문 의향은 체험 결제율·저녁 이동 배수에만 반영', 22, 500, LIGHT) + strip(2)
F.append(('f05', 'INPUTS', '44–58s', '무엇을 넣었나', svg(b), '<b>입력 칩 넷이 선을 타고 가운데 상자로 들어가고,</b> 오른쪽 100명 중 60명이 흐려지며 33~40명만 남는다.', 'slide-left'))

# F6
b = head('시행 전 계산 02', '한 번이 아니라', '1만 번 돌렸다', tag='예측')
b += t(1800, 250, f'{mc["n"]:,}번', 110, 800, BLUE, 'end') + t(1800, 296, '계산한 횟수', 24, 600, MUTED, 'end')
HX0, HX1, HY = 160, 1760, 880
bw = (HX1 - HX0) / len(mc['counts']); mxc = max(mc['counts'])
Xm = lambda v: HX0 + v / 6 * (HX1 - HX0)
b += f'<rect x="{Xm(mc["p5"])}" y="420" width="{Xm(mc["p95"]) - Xm(mc["p5"])}" height="{HY - 420}" fill="{WASH}"/>'
for i, c in enumerate(mc['counts']):
    h = c / mxc * 400
    b += f'<rect x="{HX0 + i * bw + 3:.1f}" y="{HY - h:.1f}" width="{bw - 6:.1f}" height="{h:.1f}" rx="4" fill="{BLUE if mc["p5"] <= mc["edges"][i] < mc["p95"] else BL}"/>'
b += f'<line x1="{HX0}" y1="{HY}" x2="{HX1}" y2="{HY}" stroke="{INK}" stroke-width="2"/>'
for v in range(7):
    b += t(Xm(v), HY + 36, f'{v}억', 20, 500, LIGHT, 'middle')
b += f'<line x1="{Xm(mc["p50"])}" y1="400" x2="{Xm(mc["p50"])}" y2="{HY}" stroke="{INK}" stroke-width="3" stroke-dasharray="8 8"/>'
b += t(Xm(mc['p50']) + 14, 440, f'가운데 값 연 {mc["p50"]}억 원', 30, 800, INK)
b += t(Xm(mc['p95']) + 14, 520, '1만 번 중 가운데 90%', 22, 700, BLUE) + t(Xm(mc['p95']) + 14, 552, f'{mc["p5"]}~{mc["p95"]}억 원', 22, 700, BLUE)
b += t(160, 956, '안동에서 늘어나는 소비(연간) · 참여 2% 기준 · 할인액·원래 썼을 돈 제외 · 2026년 1~8월 자료 연간 환산', 20, 500, LIGHT) + strip(2)
F.append(('f06', 'MONTE CARLO', '58–74s', '1만 번 계산', svg(b), '<b>카운터가 100 → 1,000 → 3,000 → 10,000으로 넘어갈 때마다</b> 실제 계산값 막대가 쌓여 모양이 잡힌다. 마지막에 가운데 선과 90% 띠가 깔린다.', 'slide-left'))

# F7
b = head('시행 전 계산 03', '몇 명이 참여해야', '전국 중앙까지 오나') + people(140, 440, 10, gap=40, r=13)
for i, (nm, lab) in enumerate((('기준', '100명 중 2명'), ('흥행', '4명'), ('목표', '10명'))):
    y = 900 + i * 0
b += t(120, 880, f'목표 10명 참여', 30, 800, BLUE) + t(120, 920, f'기준 2명 {sc["기준"]["change"]}% · 흥행 4명 {sc["흥행"]["change"]}%'.replace('-', '−'), 22, 600, MUTED)
sw, X = swarm(760, 1760, 700, andong=sc['목표']['change'], ghosts=(ex['change'], sc['기준']['change'], sc['흥행']['change']))
b += sw + t(X(sc['목표']['change']), 800, f'{sc["목표"]["change"]}% ({sc["목표"]["rank"]}번째)'.replace('-', '−'), 28, 800, BLUE, 'middle')
b += t(X(ex['change']), 800, '지금 −16.8%', 20, 600, LIGHT, 'middle')
b += t(760, 910, '10명 중 1명이 참여하면 전국 중앙 수준(−2.0%)', 34, 800, INK)
b += t(760, 948, '순위는 다른 시·군이 그대로일 때 · 1만 번 계산의 가운데 값', 20, 500, LIGHT) + strip(2)
F.append(('f07', 'THRESHOLD', '74–92s', '몇 명이 참여해야 하나', svg(b), '<b>장면 1의 점 분포가 다시 나온다.</b> 왼쪽 사람이 2 → 4 → 10명 켜질 때마다 안동 점이 오른쪽으로 옮겨 가고 지나온 자리는 빈 원으로 남는다.', 'slide-left'))

# F8
b = head('시행 후 확인', '식당 83곳을', '추첨 순서로 연다')
MX, MY, CW, CH = 330, 470, 150, 84
for m in range(pw['months']):
    b += t(MX + m * CW + CW / 2, MY - 20, f'{m + 1}개월', 22, 600, MUTED, 'middle')
for g, n in enumerate(pw['groups']):
    y = MY + g * (CH + 14)
    b += t(MX - 24, y + CH / 2 + 9, f'{g + 1}묶음 {n}곳', 24, 700, INK, 'end')
    for m in range(pw['months']):
        on = m >= g + 1
        b += f'<rect x="{MX + m * CW + 5}" y="{y}" width="{CW - 10}" height="{CH}" rx="10" fill="{BLUE if on else TRACK}"/>'
b += t(1500, 600, f'{round(pw["power50"] * 100)}%', 170, 800, BLUE, 'middle') + t(1500, 650, '5개월 만에 효과를 확인할 확률', 28, 700, INK, 'middle')
b += t(1500, 690, '체험 결제 +50% 효과 기준', 22, 500, MUTED, 'middle') + t(1500, 730, f'효과가 없는데 있다고 잘못 볼 확률 {pw["fp"] * 100:.1f}%', 22, 500, LIGHT, 'middle')
b += f'<path d="M 330 930 H 1280" stroke="{BLUE}" stroke-width="3" fill="none" stroke-dasharray="10 8"/>' + t(330, 912, '↺ 시행 첫 달 실제 기록으로 1만 번 계산을 다시 한다', 26, 800, BLUE)
b += source('순차 확대 모의실험 1,000회(과산포 반영)') + strip(3)
F.append(('f08', 'ROLLOUT', '92–108s', '시행하면서 확인', svg(b), '<b>표가 한 달씩 오른쪽으로 채워진다</b>(1개월째는 전부 회색 = 시행 전 비교 기간). 85%가 올라오고, 끝에 되돌이 화살표가 장면 6으로 돌아가는 뜻을 준다.', 'slide-left'))

# F9
mp = ED['map']; s_ = 820 / mp['h']
b = head('확산', '안동과 같은 유형 6곳,', '주민증 운영 52개 지자체로')
b += f'<g transform="translate(1180 150) scale({s_:.3f})">'
for p in mp['paths']:
    c = DEEP if p['n'] == '안동시' else (BLUE if p['n'].replace('시', '').replace('군', '') in ED['same'] and p['n'] != '안동시' else TRACK)
    b += f'<path d="{p["d"]}" fill="{c}" stroke="{BG}" stroke-width="1.5"/>'
b += '</g>'
for i, nm in enumerate(ED['same']):
    x = 120 + (i % 3) * 190; y = 450 + (i // 3) * 90
    b += f'<rect x="{x}" y="{y}" width="170" height="64" rx="32" fill="{WASH}" stroke="{BLUE}" stroke-width="2"/>' + t(x + 85, y + 43, nm, 30, 800, BLUE, 'middle')
b += t(120, 730, '체험 소비 변화 · 숙박일수 · 저녁 방문을', 26, 600, MUTED) + t(120, 768, '같은 기준으로 144곳 진단', 26, 600, MUTED)
b += t(120, 880, '안동 이어드림', 44, 800, INK) + t(120, 926, '원도심에서 도는 돈과 월영교에 모이는 사람을 밤까지 잇는다', 24, 600, MUTED)
b += t(120, 990, '효과는 시행 전 예측(1만 번 계산의 가운데 값)이며 시행 첫 달 기록으로 다시 계산', 18, 500, LIGHT) + strip(3)
F.append(('f09', 'CLOSE', '108–120s', '확산과 마무리', svg(b), '<b>지도에서 6곳이 차례로 켜지고</b> 칩이 따라 나온다. 마지막 3초는 사업명 잠금 + 예측 안내 한 줄.', 'crossfade'))

cells = ''
for i, (fid, tag, tm, name, sv, note, seam) in enumerate(F, 1):
    cells += (f'<article class="cell" id="frame-{i:02d}"><div class="art">{sv}</div>'
              f'<div class="lab"><span>{i:02d} · {e(name)}</span><span>{fid} · {tm}</span></div>'
              f'<p class="note">{note}</p><span class="chip">들어오는 방식: {e(seam)}</span></article>')
seams = ' → '.join(f'{i:02d} <i>{e(s)}</i>' for i, (_, _, _, _, _, _, s) in enumerate(F, 1))
page = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>안동 이어드림 사전검증 영상 스토리보드 v1</title>
<style>
@font-face{{font-family:Pretendard;src:url(assets/fonts/PretendardVariable.ttf) format("truetype");font-weight:100 900}}
:root{{--blue:{BLUE};--ink:{INK};--muted:{MUTED};--light:{LIGHT};--track:{TRACK}}}
body{{margin:0;background:#F3F5F8;font-family:Pretendard,system-ui,sans-serif;color:var(--ink);word-break:keep-all}}
header{{padding:40px 48px 16px}} h1{{margin:0;font-size:34px;font-weight:800}} h1 small{{color:var(--blue);font-size:18px;margin-left:10px}}
.dek{{color:var(--muted);font-size:17px;margin:8px 0 0}} .tag{{display:inline-block;margin-top:12px;border:2px solid var(--blue);color:var(--blue);border-radius:99px;padding:3px 14px;font-size:14px;font-weight:700}}
.act{{margin:22px 48px 0;font-size:14px;font-weight:800;color:var(--blue);letter-spacing:.12em}}
main{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:28px;padding:16px 48px 48px}}
@media (max-width:1100px){{main{{grid-template-columns:1fr}}}}
.cell{{background:#fff;border-radius:14px;padding:12px;box-shadow:0 1px 0 #E1E5EA}}
.art svg{{display:block;width:100%;height:auto;aspect-ratio:16/9;border-radius:8px}}
.lab{{display:flex;justify-content:space-between;font-size:14px;font-weight:800;margin:10px 2px 4px}} .lab span+span{{color:var(--light);font-weight:600}}
.note{{font-size:14px;line-height:1.55;color:var(--muted);margin:4px 2px 8px}} .note b{{color:var(--ink)}}
.chip{{display:inline-block;font-size:12px;font-weight:700;color:var(--blue);background:#EAF1FC;border-radius:99px;padding:3px 10px}}
.meta{{font-size:14px;line-height:1.7;color:var(--muted)}} .meta b{{color:var(--ink)}} .sw{{display:inline-block;width:14px;height:14px;border-radius:3px;vertical-align:-2px;margin-right:4px}}
</style></head><body>
<header><h1>안동 이어드림 · 시행 전 효과 검증 영상 <small>스토리보드 v1</small></h1>
<p class="dek">이 영상은 경진대회 심사위원에게 "시행 전에 데이터로 효과를 먼저 계산했고, 시행하면서 확인할 방법까지 정했다"를 보여 준다.</p>
<span class="tag">1920×1080 · 약 120초 · 9장면 · 내레이션 없음, 배경음</span></header>
<div class="act">문제 → 해법 (0–44초) · 시행 전 계산 → 시행 후 확인 (44–108초) · 확산 (108–120초)</div>
<main>{cells}
<article class="cell"><div class="lab"><span>장면 연결</span><span>9개</span></div><p class="meta">{seams}</p>
<p class="meta"><b>한 방향 규칙:</b> 새 장면은 오른쪽에서 들어온다. 장면 3→4는 같은 선을 이어 쓰고, 2와 9만 겹쳐 바뀐다.</p></article>
<article class="cell"><div class="lab"><span>색 · 글꼴 · 금지</span><span>frame.md</span></div>
<p class="meta"><span class="sw" style="background:{BLUE}"></span>데이터랩 파랑 {BLUE} (안동·이어드림)<br><span class="sw" style="background:{INK}"></span>차콜 {INK} (비교 대상·제목 첫 톤)<br><span class="sw" style="background:{GRAY}"></span>회색 {GRAY} (나머지) · 바탕 {BG}<br>
<b>글꼴</b> Pretendard 800(제목·숫자) / 500~700(본문)<br><b>금지</b> 증명 · 검증 완료 · 신뢰구간 · 1인당 · 사후 검증 · 엠대시 · 어두운 바탕 · 원그래프</p></article>
</main></body></html>'''
(P / 'storyboard.html').write_text(page, encoding='utf-8')
print(P / 'storyboard.html', f'{len(page) / 1024:.0f}KB')
