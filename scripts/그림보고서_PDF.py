# -*- coding: utf-8 -*-
"""아이디어 소개형 그림 보고서: 한국관광 데이터랩 통계 화면(예: 방한 외래관광객) 틀 (2026-09-29)

레퍼런스: 사용자 영상(데이터랩 '방한 외래관광객' 화면 스크롤).
  머리(로고·검색·메뉴) → 쪽 제목 → 조회 상자 → '알아두세요!' → 탭(기본조회/상세조회) → 표
  → 2열 차트 카드(제목 + 파란 칩 + 오른쪽 '차트 그림 저장 | 데이터 출처') → 금색 '데이터 설명' 띠 + 구분/세부내용 표.
사용자 지시(9/29): 길게 하지 말고 전부 넣지 말 것. 아이디어가 흐름대로 소개되고 그 사이에 보고서 그림이 들어가게.
  → 5단계(문제 → 원인 → 해법 → 기대효과 → 검증·확산) × 핵심 그림 2~4장 = 12장.
출력(같은 데이터):
  1) 그림보고서.html  인터랙티브(단계 탭·조회·검색·그림 확대·그림별 출처 펼치기·데이터 설명 아코디언)
  2) 안동이어드림_그림보고서_20260929.pdf  A4 세로 인쇄본(출처 펼친 상태, 단계마다 한 쪽, 그림은 폭 전체)
그림은 scripts/보고서그림.py의 PNG를 그대로 쓴다. 제목·부제·출처는 scripts/그림메타_추출.py가 뽑은 그림메타.json.
단계 설명의 숫자는 그림 제목(메타)과 같은 JSON에서 읽는다.
실행: .venv_pdf/bin/python scripts/그림메타_추출.py && .venv_pdf/bin/python scripts/그림보고서_PDF.py
"""
import json, math, subprocess
from html import escape
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / '보고서/보고서그림_20260928'
OUT = ROOT / '보고서/그림보고서_20260929'
OUT.mkdir(parents=True, exist_ok=True)
J = lambda p: json.loads((ROOT / p).read_text(encoding='utf-8'))
Q = J('보고서/교수브리핑_20260922/수치.json')
S = J('보고서/성과도출_20260922/시뮬레이션결과.json')
PW = J('보고서/성과도출_20260922/순차도입_검정력.json')
META = {x['no']: x for x in J('보고서/그림보고서_20260929/그림메타.json')}
FILES = {int(f.name[:2]): f for f in FIG.glob('[0-9][0-9]_*.png')}
assert sorted(FILES) == list(range(1, 43)) == sorted(META), '보고서그림 42장과 메타가 모두 있어야 한다'
E, SC = Q['체험문화'], S['시나리오']
NAMES = ('기준', '흥행', '목표')
P = lambda n, k: SC[n][k]['P50']
now, y24 = E['안동_2026'], E['안동_2024']
nat = y24 * (1 + E['중앙_변화율'] / 100)
m = lambda x, d=1: f'{x:.{d}f}'.replace('-', '−')
H = lambda n: META[n]['title']                     # 그림 제목 문장(숫자 포함)


def ex_after(n):                                   # 보고서그림.py 34번 요약표와 같은 계산
    v = now * (1 + P(n, '지표1_증가율')); ch = (v / y24 - 1) * 100
    return v, ch, sum(1 for k, x in E['분포'].items() if k != '안동시' and x < ch) + 1


pct = {n: SC[n]['참여율'] * 100 for n in NAMES}
p83 = next(c['검정력'] for c in PW['확대안']['곡선'] if abs(c['효과'] - .5) < 1e-9) * 100
ROWS = [('방문 1회당 체험·문화 소비', '원', f'{now:.1f}', *[f'{ex_after(n)[0]:.1f}' for n in NAMES]),
        ('2024년 대비 변화', '%', m(E['안동_변화율']), *[m(ex_after(n)[1]) for n in NAMES]),
        (f"{E['시군수']}개 시·군 중 감소폭 순위", '위', str(E['안동_감소순위']), *[str(ex_after(n)[2]) for n in NAMES]),
        ('월영교로 새로 가는 저녁 이동 (주말 하루)', '명', '-', *[f"{P(n, '새이동_하루'):.0f}" for n in NAMES]),
        ('안동 추가 소비 (연간)', '억 원', '-', *[f"{P(n, '추가소비합') / 1e8:.2f}" for n in NAMES])]

# ── 이어드림 한눈에 (서식4 3)칸 운영안 · 그림 26과 같은 내용) ─────────────
IDEA = [('1단계', '원도심 식음 → 체험', '낮 · 식사 뒤', '원도심 식당 영수증 인증 → 체험 10% 할인', '원도심 주민증 혜택 업체 0곳', 9),
        ('2단계', '저녁 이동', '18:30 ~ 21:00', '원도심 → 월영교 택시·셔틀', '19시 이후 원도심 출발 112번 0회', 8),
        ('3단계', '월영교 야간 팝업', '21시 전후', '월영교 야간 팝업으로 밤까지 머물게', '월영교 1km 주점 0곳', 8)]

# ── 흐름 5단계: (이름, 영문, 한 줄 메시지, 설명 줄, 그림) ─────────────────
STEPS = [
    ('문제', 'PROBLEM', '방문은 늘었는데, 방문 1회당 체험·문화 소비는 줄고 있다',
     [f"방문 1회당 체험·문화 소비 {y24:.1f} → {now:.1f}원({m(E['안동_변화율'])}%), {E['시군수']}개 시·군 중 {E['안동_감소순위']}번째로 많이 줄었다.",
      f"같은 기간 전국 시·군 중앙값은 {m(E['중앙_변화율'])}%다. 수준은 {E['시군수']}곳 중 {E['안동_수준순위']}위로 중간이고, 줄어드는 속도가 빠른 것이 문제다."], [1, 2]),
    ('원인', 'WHY', '돈이 도는 원도심과 사람이 모이는 월영교가 저녁에 끊겨 있다',
     [f'원도심: {H(9)}. 혜택 이용의 대부분은 관람지에 몰려 있다.',
      f'시간: {H(15)}(코레일). 저녁에 움직일 수요는 있다.',
      f'이동·목적지: {H(16)}(안동시 BIS), 밤에 갈 주점은 원도심 86곳 · 월영교 0곳(상가정보).'], [8, 9]),
    ('해법', 'SOLUTION', '디지털 관광주민증 위 3단계 릴레이로 원도심의 낮을 월영교의 밤까지 잇는다',
     ['1 원도심 식당 영수증 → 체험 할인, 2 저녁 이동(18:30~21:00), 3 월영교 야간 팝업.',
      f'팀 설문: {H(21)}. 의향은 참여율이 아니어서 계산에는 실현율(0.33~0.40)로 보정한 값만 쓴다.'], [26, 21]),
    ('기대효과', 'IMPACT', f"참여 {pct['기준']:.0f}%만 되어도 체험 소비가 늘고, {pct['목표']:.0f}%면 전국 중앙 추세 수준에 가까워진다",
     [f"방문 1회당 체험·문화 소비: 지금 {now:.1f}원 → 참여 {pct['기준']:.0f}% {ex_after('기준')[0]:.1f}원 → 참여 {pct['목표']:.0f}% {ex_after('목표')[0]:.1f}원 "
      f"(전국 중앙 추세만큼만 줄었다면 {nat:.1f}원).",
      f"안동에 남는 돈 연 {P('기준', '추가소비합') / 1e8:.2f}억 ~ {P('목표', '추가소비합') / 1e8:.2f}억 원. 모두 시행 전 예측(1만 번 계산의 가운데 값)이다."], [28, 30]),
    ('검증·확산', 'VERIFY · SCALE', '시행 뒤에는 효과를 재는 방법이 있고, 같은 문제를 가진 곳에 옮길 수 있다',
     [f'원도심 식당 83곳을 4묶음으로 한 달씩 넓히면 체험 결제 +50% 효과를 {p83:.0f}% 확률로 확인한다.',
      f'전국 144개 시·군 진단: {H(38)}. 주민증을 운영하는 지자체에 같은 방식을 적용할 수 있다.'], [35, 38])]
STEP_OF = {n: i for i, s in enumerate(STEPS) for n in s[4]}
USED = [n for s in STEPS for n in s[4]]

T = {1: ('방문과 체험·문화 소비', '데이터랩'), 2: ('146개 시·군 체험 소비 변화', '데이터랩'), 8: ('두 거점: 원도심과 월영교', '복합'),
     9: ('읍면동 방문과 혜택 업체', '정보공개'),
     26: ('3단계 릴레이', '운영안'), 21: ('이용 의향 4문항', '설문'), 28: ('참여율별 체험 소비 회복', '예측'),
     30: ('참여율별 추가 소비', '예측'), 35: ('순차 확대 검정력', '모의실험'), 38: ('같은 문제 유형 지도', '진단표')}
assert sorted(T) == sorted(USED)

# ── 자료 출처: (id, 제공, 자료, 기간·코드, 쓰인 그림) — 이 보고서에 실린 그림만 ─────
SOURCES = [
    ('dl_visit', '한국관광 데이터랩', '이동통신 방문 연인원 (시·군, 읍면동)', 'BDT_01_01_006 · 2024~2026년 1~8월 월별', [1, 2, 8, 9, 26, 38]),
    ('dl_card', '한국관광 데이터랩', '신용카드 외지인 소비 (업종 중분류)', 'BDT_02_01_003 · 2024~2026년 1~8월 월별', [1, 2, 38]),
    ('dl_stay', '한국관광 데이터랩', '평균 숙박일수', 'LN_02_01_013 (전국 진단표)', [38]),
    ('gov', '안동시 정보공개청구', '디지털 관광주민증 혜택업체 목록 · 업체별 이용 건수', '목록 2026.9.18 · 이용 2024.6~2026.8', [8, 9]),
    ('bis', '안동시 버스정보시스템(BIS)', '시내버스 112번 노선 시간표', '평일 시간표', [8, 26]),
    ('sbiz', '소상공인시장진흥공단', '상가(상권)정보', '2026.6', [8, 26]),
    ('check', '안동팀 확인', '지도 앱 영업시간', '2026.9.19', [8]),
    ('survey', '안동팀 온라인 설문', '응답 103명 (안동 방문 경험 72명)', '2026.9.23~24', [21]),
    ('sim', '안동팀 모의실험', '이어드림 기대효과 모의실험 1만 번', '시행 전 예측 · 원도심 식당 83곳 운영 · 연간 환산', [28, 30]),
    ('power', '안동팀 모의실험', '순차 확대 검정력 1,000회', '식당 4묶음, 한 달씩 5개월', [35]),
    ('diag', '안동팀 전국 진단표', '144개 시·군 네 지표 진단', '2026.9.23', [38]),
    ('geo', '행정 경계', '2018 시·군 경계 (skorea-municipalities-2018)', '지도 그림 배경', [38])]
SRC_OF = {n: [s[0] for s in SOURCES if n in s[4]] for n in USED}
assert all(SRC_OF.values()), '모든 그림에 자료가 하나 이상 연결되어야 한다'

DESC = [('보고서명', ['안동 이어드림 분석 보고서 (요약)']), ('작성주체', ['2026 한국관광 데이터랩 활용 경진대회 안동팀']),
        ('작성목적', ['안동의 체험·문화 소비 감소와 원도심–월영교 저녁 공백을 데이터로 보이고, 3단계 릴레이의 기대효과와 효과 평가 방법을 제시']),
        ('작성방법', ['방문 1회당 소비 = 신용카드 외지인 소비 ÷ 이동통신 방문 연인원 (1인당 소비가 아님)',
                  '체험·문화 = 문화서비스 · 관광유원시설 · 기타레저. 안동 값은 전국 시·군 중앙값과 함께 표시',
                  '기대효과 = 설문 의향 × 실현율(0.33~0.40)로 보정한 모의실험 1만 번의 가운데 값과 90% 범위']),
        ('분석기간', ['2024~2026년 각 1~8월 (그림마다 기간이 다르면 그림 부제의 기간을 따름)']),
        ('유의사항', ['기대효과는 시행 전 예측이며 성과 실적이 아닙니다. 90% 범위는 신뢰구간이 아닙니다.',
                  '설문 의향 %는 참여율이 아닙니다. 순위 예측은 다른 시·군이 그대로일 때의 값입니다.',
                  f'이 보고서는 그림 42장 중 흐름에 필요한 {len(USED)}장만 실었습니다. 나머지는 보고서그림 폴더와 분석보고서에 있습니다.'])]
NOTICE = (f"방문 1회당 소비는 한국관광 데이터랩의 <u>신용카드 외지인 소비 ÷ 이동통신 방문 연인원</u>이며, 비교 기준은 {E['시군수']}개 시·군의 전국 중앙값입니다. "
          "시행 후 값은 <u>시행 전 예측(1만 번 계산의 가운데 값, 원도심 식당 83곳 운영)</u>이고, 순위는 다른 시·군이 그대로일 때입니다.")
LOGO = '''<span class="logo"><svg viewBox="0 0 40 40" width="30" height="30"><circle cx="20" cy="20" r="18" fill="#E6EEFB"/>
<path d="M6 24c6-9 14-11 28-8-10 0-17 4-22 12z" fill="#2D6BD9"/><path d="M10 29c7-5 13-6 22-4-7 1-12 3-16 7z" fill="#8FB0EA"/>
<circle cx="27" cy="11" r="3.2" fill="#E8710A"/></svg><b>안동 이어드림</b><i>데이터 리포트</i></span>'''
REL = '../보고서그림_20260928/'
ONE_LINE = '디지털 관광주민증 위 3단계 릴레이로, 원도심에서 도는 돈과 월영교에 모이는 사람을 밤까지 잇는다.'


def idea_table(web=False):
    link = (lambda n: f'<a class="fl" href="#fig-{n:02d}" data-fig="{n}">그림 {n:02d}</a>') if web else (lambda n: f'<span class="fl">그림 {n:02d}</span>')
    body = ''.join(f'<tr><td class="c"><span class="stp">{a}</span></td><td class="l"><b>{b}</b></td><td class="c">{c}</td><td class="l">{d}</td>'
                   f'<td class="l warn">{e}</td><td class="c">{link(n)}</td></tr>' for a, b, c, d, e, n in IDEA)
    return (f'<table class="dt idea"><thead><tr><th>단계</th><th class="l">무엇을</th><th>언제</th><th class="l">어떻게</th><th class="l">지금 (근거)</th><th>그림</th></tr></thead>'
            f'<tbody>{body}</tbody></table>')


def effect_table(hi=2):
    heads = ''.join(f'<th class="{"hi" if i == hi else ""}">{n} {pct[n]:.0f}%</th>' for i, n in enumerate(NAMES))
    body = ''.join(f'<tr><td class="l">{escape(r[0])}</td><td class="u">{r[1]}</td><td>{r[2]}</td>'
                   + ''.join(f'<td class="{"hi" if j == hi else ""}">{v}</td>' for j, v in enumerate(r[3:])) + '</tr>' for r in ROWS)
    return (f'<table class="dt eff"><thead><tr><th rowspan="2" class="l">지표</th><th rowspan="2">단위</th><th rowspan="2">지금<br><small>2026년 1~8월</small></th>'
            f'<th colspan="3">시행 후 예측 (원도심 방문객 중 참여율)</th></tr><tr>{heads}</tr></thead><tbody>{body}</tbody></table>')


def desc_table():
    return ''.join(f'<tr><th>{k}</th><td>{"".join(f"<div>▷ {escape(x)}</div>" for x in v)}</td></tr>' for k, v in DESC)


# ═════════════ 1) 인터랙티브 HTML ═════════════
def build_web():
    data = {'figs': [{'no': n, 'file': REL + FILES[n].name, 'tab': STEP_OF[n], 'short': T[n][0], 'tag': T[n][1], 'title': META[n]['title'],
                      'sub': META[n]['sub'], 'src': META[n]['src'], 'srcs': SRC_OF[n]} for n in USED],
            'tabs': [{'name': s[0], 'en': s[1], 'head': s[2], 'lead': s[3], 'nos': s[4]} for s in STEPS],
            'sources': [{'id': i, 'org': o, 'name': nm, 'period': p, 'figs': f} for i, o, nm, p, f in SOURCES],
            'rows': ROWS, 'names': list(NAMES), 'pct': [round(pct[n]) for n in NAMES]}
    menu = ''.join(f'<button class="gm" data-tab="{i}"><span>{i + 1:02d}</span>{s[0]}</button>' for i, s in enumerate(STEPS))
    rep = {'__LOGO__': LOGO, '__MENU__': menu, '__NOTICE__': NOTICE, '__DESC__': desc_table(), '__IDEA__': idea_table(True),
           '__ONE__': ONE_LINE, '__DATA__': json.dumps(data, ensure_ascii=False)}
    html = WEB
    for k, v in rep.items():
        html = html.replace(k, v)
    p = OUT / '그림보고서.html'
    p.write_text(html, encoding='utf-8')
    return p


WEB = r'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>안동 이어드림 분석 보고서</title>
<style>
:root{--blue:#2D6BD9;--blue-d:#1A4FA8;--blue-l:#8FB0EA;--blue-xl:#EAF1FC;--ink:#23272B;--sub:#6B7177;--line:#E3E8EE;--line2:#CBD5E1;--soft:#F5F7FA;--gold:#E2B65A;--fab:#D9853B;--acc:#E8710A}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:'Pretendard','Apple SD Gothic Neo',sans-serif;color:var(--ink);background:#fff;font-size:14px;line-height:1.5}
button{font:inherit;color:inherit;background:none;border:none;cursor:pointer}
a{color:inherit;text-decoration:none}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px}
.util{display:flex;justify-content:flex-end;gap:18px;font-size:12px;color:var(--sub);padding:8px 0 2px}
.util a:hover,.util button:hover{color:var(--blue)}
.htop{display:flex;align-items:center;gap:40px;padding:10px 0}
.logo{display:inline-flex;align-items:center;gap:7px}.logo b{color:var(--blue-d);font-size:19px;font-weight:800;letter-spacing:-.4px}.logo i{font-style:normal;color:var(--blue);font-size:15px;font-weight:600}
.search{flex:0 1 330px;display:flex;align-items:center;border:2px solid var(--blue);border-radius:24px;padding:0 6px 0 16px;height:40px}
.search input{flex:1;border:none;outline:none;font:inherit;font-size:13px;background:transparent;min-width:0}
.search button{color:var(--blue);font-size:18px;padding:0 8px}
.team{margin-left:auto;display:flex;gap:14px;font-size:12px;color:var(--sub)}.team b{color:var(--blue)}
nav.gnb{border-top:1px solid var(--line);border-bottom:1px solid var(--line);position:sticky;top:0;background:#fff;z-index:15}
nav.gnb .wrap{display:flex;gap:4px}
.gm{padding:13px 16px;font-size:15px;font-weight:700;position:relative;white-space:nowrap}
.gm span{color:#9AA2AA;font-size:11px;margin-right:6px;font-weight:800}
.gm:hover,.gm.on{color:var(--blue)}.gm.on span{color:var(--blue)}.gm.on::after{content:'';position:absolute;left:16px;right:16px;bottom:-1px;height:3px;background:var(--blue)}
.crumb{font-size:12px;color:var(--sub);margin:18px 0 6px}.crumb b{color:var(--ink)}
h1{font-size:30px;font-weight:800;letter-spacing:-.8px}
.one{font-size:15px;color:#4A5057;margin:6px 0 20px}.one b{color:var(--blue-d)}
.fab{position:fixed;right:28px;top:190px;width:74px;height:74px;border-radius:50%;background:var(--fab);color:#fff;font-size:12px;font-weight:700;line-height:1.25;
 display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(0,0,0,.2);z-index:20;transition:transform .15s}
.fab:hover{transform:scale(1.06)}.fab span{font-size:16px;margin-bottom:2px}
.filter{background:#EAF1FA;border-radius:8px;padding:18px 26px;display:flex;align-items:flex-end;gap:14px;flex-wrap:wrap}
.f label{display:block;font-size:12px;font-weight:700;margin-bottom:6px}
.f select{appearance:none;font:inherit;font-size:13px;min-width:130px;padding:7px 30px 7px 12px;border:1px solid var(--line2);border-radius:5px;background:#fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M1 1l4 4 4-4' fill='none' stroke='%23888' stroke-width='1.4'/%3E%3C/svg%3E") no-repeat right 11px center}
.go{background:var(--blue);color:#fff;font-weight:700;padding:8px 38px;border-radius:5px;margin-left:10px}.go:hover{background:var(--blue-d)}
.reset{font-size:12px;color:var(--sub);text-decoration:underline;padding-bottom:9px}
.notice{display:flex;gap:12px;align-items:flex-start;padding:18px 4px 16px;border-bottom:1px solid #EEF1F4}
.ck{width:18px;height:18px;border:1.5px solid var(--ink);border-radius:3px;font-size:12px;display:flex;align-items:center;justify-content:center;flex:none;margin-top:2px}
.notice b{font-size:15px;white-space:nowrap}.notice p{font-size:13px;line-height:1.7;color:#4A5057}.notice u{text-decoration:none;color:var(--blue-d);font-weight:600}
.tabs{display:flex;gap:4px;margin-top:26px;border-bottom:2px solid var(--blue)}
.tab{font-size:13px;padding:8px 22px;border:1px solid var(--line2);border-bottom:none;border-radius:5px 5px 0 0;color:#666;background:var(--soft)}
.tab.on{background:var(--blue);color:#fff;border-color:var(--blue);font-weight:700}
.tbar{display:flex;justify-content:space-between;align-items:center;gap:10px;margin:14px 0 12px;flex-wrap:wrap}
.subs{display:flex;gap:6px;flex-wrap:wrap}
.sub{font-size:13px;padding:5px 14px;border:1px solid var(--line2);border-radius:4px;color:#555;background:#fff}
.sub em{font-style:normal;color:#9AA2AA;margin-left:3px;font-size:12px}
.sub:hover{border-color:var(--blue);color:var(--blue)}
.sub.on{background:var(--blue);border-color:var(--blue);color:#fff;font-weight:700}.sub.on em{color:#CFE0FA}
.tools{display:flex;gap:6px;flex-wrap:wrap}.tools button,.tools a{font-size:12px;border:1px solid var(--line2);border-radius:4px;padding:5px 11px;color:#555;background:#fff}
.tools button:hover,.tools a:hover{border-color:var(--blue);color:var(--blue)}
.tw{overflow-x:auto}
table.dt{width:100%;border-collapse:collapse;font-size:13px;border-top:2px solid #34383C;min-width:640px}
.dt th{background:#F3F6FA;font-weight:700;padding:9px 10px;border:1px solid #DDE3EA;text-align:center}
.dt th small{font-weight:500;color:var(--sub);font-size:11px}
.dt td{padding:9px 12px;border:1px solid var(--line);text-align:right;font-variant-numeric:tabular-nums;transition:background .15s}
.dt .l{text-align:left}.dt .c{text-align:center}.dt td.u{text-align:center;color:var(--sub)}
.dt tbody tr:hover td{background:#F8FAFD}
.dt .hi{background:var(--blue-xl)!important;color:var(--blue-d);font-weight:800}.dt th.hi{background:#DCE8FB!important}
.idea td{padding:11px 12px}.idea .warn{color:var(--acc);font-weight:700}
.stp{display:inline-block;background:var(--blue);color:#fff;font-size:12px;font-weight:800;border-radius:12px;padding:2px 10px}
.tnote{font-size:12px;color:var(--sub);margin-top:8px}
.sec{margin-top:48px;scroll-margin-top:60px}
.sech{display:flex;align-items:center;gap:14px;margin-bottom:10px}
.sech .num{font-size:34px;font-weight:900;color:var(--blue);letter-spacing:-1px;line-height:1}
.sech .en{display:block;font-size:11px;color:var(--blue-d);font-weight:700;letter-spacing:.8px}
.sech h2{font-size:22px;font-weight:800;letter-spacing:-.5px;line-height:1.2}
.msg{border-left:4px solid var(--blue);background:#F6F9FE;padding:14px 18px;margin-bottom:18px;border-radius:0 6px 6px 0}
.msg strong{display:block;font-size:17px;font-weight:800;letter-spacing:-.3px;margin-bottom:6px}
.msg li{list-style:none;font-size:13.5px;color:#34383C;line-height:1.7;padding-left:14px;position:relative}
.msg li::before{content:'';position:absolute;left:2px;top:10px;width:5px;height:5px;background:var(--blue);border-radius:50%}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px 26px;align-items:start}
.card{border:1px solid var(--line);border-radius:8px;padding:14px 16px 12px;background:#fff;transition:box-shadow .18s,border-color .18s;scroll-margin-top:70px}
.card:hover{box-shadow:0 6px 18px rgba(26,79,168,.10);border-color:#CFDAEA}
.card.flash{animation:fl 1.6s}@keyframes fl{0%,40%{box-shadow:0 0 0 3px var(--blue-l)}100%{box-shadow:none}}
.ch{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.ch h4{font-size:16px;font-weight:800;margin-right:6px;letter-spacing:-.3px}
.ch .no{color:var(--blue);margin-right:6px}
.chip{font-size:11.5px;padding:2px 9px;border:1px solid var(--blue);color:var(--blue);border-radius:3px;white-space:nowrap}
.chip.on{background:var(--blue);color:#fff}
.links{margin-left:auto;font-size:12px;color:#8A939C;white-space:nowrap;display:flex;align-items:center;gap:6px}
.links a:hover,.links button:hover{color:var(--blue)}.links i{font-style:normal;color:var(--line2)}
.links button[aria-expanded=true]{color:var(--blue);font-weight:700}
.card figure{cursor:zoom-in;border-radius:4px;overflow:hidden}
.card img{width:100%;display:block}
.srcline{margin-top:8px;font-size:12px;color:var(--sub);display:flex;gap:6px;border-top:1px dashed var(--line);padding-top:8px}
.srcline::before{content:'';flex:none;width:6px;height:6px;background:var(--blue);margin-top:6px}
.srcbox{margin-top:10px;background:#F8FAFC;border:1px solid var(--line);border-radius:6px;padding:12px 14px;font-size:12.5px}
.srcbox[hidden]{display:none}
.srcbox dl{display:grid;grid-template-columns:78px 1fr;gap:6px 10px}
.srcbox dt{color:var(--sub);font-weight:600}.srcbox dd{color:#34383C}
.dsl{display:inline-block;font-size:11.5px;border:1px solid var(--line2);border-radius:3px;padding:1px 7px;margin:0 4px 4px 0;background:#fff}
.dsl:hover{border-color:var(--blue);color:var(--blue)}
.eff{margin-top:22px}
.next{display:flex;justify-content:flex-end;margin-top:14px}
.next button{font-size:13px;color:var(--blue);font-weight:700}.next button:hover{text-decoration:underline}
.empty{padding:60px 0;text-align:center;color:var(--sub)}
table.lst{width:100%;border-collapse:collapse;font-size:13px;border-top:2px solid #34383C;min-width:760px}
.lst th{background:#F3F6FA;padding:9px 8px;border-bottom:1px solid #DDE3EA;font-weight:700;white-space:nowrap}
.lst td{padding:9px 8px;border-bottom:1px solid var(--line);vertical-align:top}
.lst tbody tr{cursor:pointer}.lst tbody tr:hover td{background:#F8FAFD}
.lst .no{color:var(--blue);font-weight:800;text-align:center}.lst .t{font-weight:700}.lst .s{color:var(--sub);font-size:12px}
.acc{margin-top:56px;scroll-margin-top:60px}
.gold{width:100%;display:flex;justify-content:space-between;align-items:center;background:linear-gradient(#E8C067,var(--gold));border-radius:8px;padding:16px 26px;
 font-size:17px;font-weight:800;color:#3D2E10;box-shadow:0 2px 5px rgba(0,0,0,.12)}
.gold .car{transition:transform .2s;font-size:14px}.acc:not(.open) .gold .car{transform:rotate(180deg)}
.accb{overflow:hidden;transition:max-height .35s ease}.acc:not(.open) .accb{max-height:0!important}
.accin{padding-top:16px}
table.desc{width:100%;border-collapse:collapse;font-size:13px;border-top:1.5px solid #34383C}
.desc th{width:150px;background:#F6F7F9;font-weight:600;color:#4A5057;text-align:center;padding:10px;border-bottom:1px solid #E6E9ED}
.desc td{padding:10px 16px;border-bottom:1px solid #E6E9ED;line-height:1.65;color:#34383C}
.desc thead th,.desc thead td{font-weight:700;color:var(--ink);text-align:center;background:#F6F7F9}
h3.st{font-size:16px;font-weight:800;margin:30px 0 10px}
table.srct{width:100%;border-collapse:collapse;font-size:13px;border-top:1.5px solid #34383C}
.srct th{background:#F6F7F9;padding:9px 10px;border-bottom:1px solid #E6E9ED;font-weight:700;text-align:left}
.srct td{padding:9px 10px;border-bottom:1px solid #E6E9ED;vertical-align:top}
.srct tr{scroll-margin-top:70px}.srct tr.flash td{animation:fl2 1.8s}@keyframes fl2{0%,50%{background:var(--blue-xl)}100%{background:none}}
.srct .o{font-weight:700;white-space:nowrap}.srct .p{color:var(--sub);font-size:12px}
.fl{display:inline-block;text-align:center;font-size:11.5px;font-weight:700;color:var(--blue);border:1px solid #CFDAEA;border-radius:3px;padding:0 6px;margin:0 3px 3px 0;white-space:nowrap}
a.fl:hover{background:var(--blue);color:#fff}
.lic{display:flex;align-items:center;gap:18px;margin-top:14px;font-size:13px;color:#4A5057}
.open{display:inline-flex;align-items:center;border:1.6px solid var(--ink);border-radius:3px;font-weight:900;font-size:13px;padding-left:7px;flex:none}
.open em{font-style:normal;background:var(--ink);color:#fff;margin-left:7px;padding:2px 7px;font-size:11px;font-weight:700}
footer{margin-top:60px;border-top:1px solid var(--line);padding:20px 0 40px;font-size:12px;color:#9AA2AA;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
.lb{position:fixed;inset:0;background:rgba(18,22,28,.82);display:none;align-items:center;justify-content:center;z-index:50;padding:30px}
.lb.on{display:flex}
.lbin{background:#fff;border-radius:10px;max-width:1100px;width:100%;max-height:100%;overflow:auto;padding:18px 22px}
.lbh{display:flex;align-items:center;gap:8px;margin-bottom:10px}.lbh h4{font-size:17px;font-weight:800}.lbh .no{color:var(--blue);margin-right:6px}
.lbh .x{margin-left:auto;font-size:22px;color:var(--sub);padding:0 6px}
.lb img{width:100%;display:block}
.lbf{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:10px}
.lbf .nav{flex:none}.lbf .nav button{border:1px solid var(--line2);border-radius:4px;padding:5px 14px;font-size:13px;margin-left:6px}.lbf .nav button:hover{border-color:var(--blue);color:var(--blue)}
.lbf p{font-size:12.5px;color:var(--sub)}
@media(max-width:1400px){.fab{display:none}}
@media(max-width:900px){.grid{grid-template-columns:1fr}.htop{flex-wrap:wrap;gap:12px}.team{display:none}.fab{display:none}
 nav.gnb .wrap{overflow-x:auto}.gm{padding:12px 10px}.wrap{padding:0 16px}h1{font-size:24px}.desc th{width:84px}.search{flex-basis:100%}}
@media print{.fab,.util,.search,nav.gnb,.filter,.tools,.lb,.next{display:none!important}.card{break-inside:avoid}.acc .accb{max-height:none!important}}
</style></head><body>
<div class="wrap"><div class="util"><a href="#top">보고서 소개</a><a href="#acc" data-open>데이터 출처</a><button id="toList">그림 목록</button></div>
<div class="htop" id="top">__LOGO__<form class="search" id="sform"><input id="q" placeholder="지표나 그림 번호를 입력해 주세요 (예: 월영교, 설문, 16)"><button aria-label="검색">⌕</button></form>
<div class="team"><span><b>●</b> 안동팀</span><span>2026 한국관광 데이터랩 활용 경진대회</span></div></div></div>
<nav class="gnb"><div class="wrap"><button class="gm on" data-tab="-1">전체 흐름</button>__MENU__</div></nav>
<main class="wrap">
<div class="crumb">⌂ › 분석 리포트 › <b>안동 이어드림</b></div>
<h1>안동 이어드림 분석 보고서</h1>
<p class="one"><b>한 줄 기획</b> · __ONE__</p>
<a class="fab" href="#acc" data-open><span>ⓘ</span>데이터<br>설명</a>
<div class="filter">
 <div class="f"><label for="fTab">단계</label><select id="fTab"></select></div>
 <div class="f"><label for="fKind">자료</label><select id="fKind"></select></div>
 <div class="f"><label for="fPct">참여율 (효과 표 강조)</label><select id="fPct"></select></div>
 <button class="go" id="go">조회</button><button class="reset" id="reset">초기화</button>
</div>
<div class="notice"><span class="ck">✓</span><b>알아두세요!</b><p>__NOTICE__</p></div>
<div class="tabs"><button class="tab on" data-view="basic">기본조회</button><button class="tab" data-view="detail">상세조회</button></div>
<div class="tbar"><div class="subs" id="subs"></div>
 <div class="tools"><button id="csv">효과 표 CSV 저장</button><button id="allSrc">데이터 출처 모두 펼치기</button><a href="안동이어드림_그림보고서_20260929.pdf" target="_blank">PDF 인쇄본</a><button onclick="print()">인쇄</button></div></div>
<div id="basic">
 <div class="tw">__IDEA__</div>
 <p class="tnote">※ 이어드림 3단계 운영안(서식4 3)칸). 오른쪽 그림 번호를 누르면 근거 그림으로 이동합니다.</p>
 <div id="secs"></div>
</div>
<div id="detail" hidden><div class="tw"><table class="lst"><thead><tr><th>번호</th><th>단계</th><th>그림 제목</th><th>무엇을 그렸나</th><th>자료</th><th>출처</th></tr></thead><tbody id="lst"></tbody></table></div></div>
<section class="acc open" id="acc"><button class="gold" id="gold" aria-expanded="true"><span>데이터 설명</span><span class="car">⌃</span></button>
<div class="accb" id="accb"><div class="accin">
 <table class="desc"><thead><tr><th>구분</th><td>세부내용</td></tr></thead><tbody>__DESC__</tbody></table>
 <h3 class="st">자료 출처</h3>
 <div class="tw"><table class="srct"><thead><tr><th style="width:19%">제공 기관</th><th style="width:31%">자료</th><th style="width:30%">기간 · 코드</th><th>쓰인 그림</th></tr></thead><tbody id="srct"></tbody></table></div>
 <div class="lic"><span class="open">OPEN<em>출처</em></span><p>그림의 숫자는 팀 분석 파일(수치.json · 시뮬레이션결과.json 등)에서 자동으로 읽어 그렸습니다. 원자료 이용 조건은 각 제공 기관의 조건을 따릅니다.</p></div>
 <div class="lic"><span class="open">OPEN<em>코드</em></span><p>그림 scripts/보고서그림.py · 이 화면 scripts/그림보고서_PDF.py (공개 저장소 kysk2295/andong-datalab-2026)</p></div>
</div></div></section>
<footer><span>안동 이어드림 분석 보고서 · 요약</span><span>2026 한국관광 데이터랩 활용 경진대회 · 안동팀 · 2026.09.29</span></footer>
</main>
<div class="lb" id="lb" role="dialog" aria-modal="true"><div class="lbin"><div class="lbh"><h4 id="lbt"></h4><span class="chip on">안동</span><span class="chip" id="lbk"></span><button class="x" id="lbx" aria-label="닫기">×</button></div>
<img id="lbi" alt=""><div class="lbf"><p id="lbs"></p><div class="nav"><button id="lbp">‹ 이전</button><button id="lbn">다음 ›</button></div></div></div></div>
<script>
const D=__DATA__;
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const pad=n=>String(n).padStart(2,'0');
const SRC=Object.fromEntries(D.sources.map(s=>[s.id,s]));
const KINDS=[...new Set(D.figs.map(f=>f.tag))];
const st={tab:-1,kind:'',q:'',pct:2};
let shown=[];
$('#fTab').innerHTML='<option value="-1">전체 흐름</option>'+D.tabs.map((t,i)=>`<option value="${i}">${pad(i+1)} ${t.name}</option>`).join('');
$('#fKind').innerHTML='<option value="">전체</option>'+KINDS.map(k=>`<option>${esc(k)}</option>`).join('');
$('#fPct').innerHTML=D.names.map((n,i)=>`<option value="${i}">${n} ${D.pct[i]}%</option>`).join('');$('#fPct').value=2;
function effTable(){
  const h=D.names.map((n,i)=>`<th class="${i==st.pct?'hi':''}">${n} ${D.pct[i]}%</th>`).join('');
  return `<div class="tw"><table class="dt eff"><thead><tr><th rowspan="2" class="l">지표</th><th rowspan="2">단위</th><th rowspan="2">지금<br><small>2026년 1~8월</small></th><th colspan="3">시행 후 예측 (원도심 방문객 중 참여율)</th></tr><tr>${h}</tr></thead><tbody>`+
   D.rows.map(r=>`<tr><td class="l">${esc(r[0])}</td><td class="u">${r[1]}</td><td>${r[2]}</td>${r.slice(3).map((v,i)=>`<td class="${i==st.pct?'hi':''}">${v}</td>`).join('')}</tr>`).join('')+
   '</tbody></table></div><p class="tnote">※ 추가 소비는 연간 환산(1~8월 월평균 × 12). 예측은 실적이 아니며, 시행 첫 달 기록으로 갱신합니다.</p>';
}
function match(f,tab=st.tab){
  if(tab>=0&&f.tab!=tab)return false;
  if(st.kind&&f.tag!=st.kind)return false;
  if(st.q){const q=st.q.toLowerCase().trim();if(/^\d+$/.test(q))return f.no==+q;
    const hay=[f.short,f.title,f.sub,f.src,f.tag,D.tabs[f.tab].name,D.tabs[f.tab].head,...f.srcs.map(i=>SRC[i].org+' '+SRC[i].name)].join(' ').toLowerCase();
    return q.split(/\s+/).every(w=>hay.includes(w));}
  return true;
}
function card(f){
  const chips=f.srcs.map(i=>`<a class="dsl" href="#src-${i}" data-src="${i}">${esc(SRC[i].org)} · ${esc(SRC[i].name)}</a>`).join('');
  return `<article class="card" id="fig-${pad(f.no)}"><header class="ch"><h4><span class="no">${pad(f.no)}</span>${esc(f.short)}</h4><span class="chip on">안동</span><span class="chip">${esc(f.tag)}</span>
  <span class="links"><a href="${f.file}" download>차트 그림 저장</a><i>|</i><button class="sb" aria-expanded="false">데이터 출처 ▾</button></span></header>
  <figure data-no="${f.no}"><img loading="lazy" src="${f.file}" alt="${esc(f.title)}"></figure>
  <div class="srcline">출처: ${esc(f.src)}</div>
  <div class="srcbox" hidden><dl><dt>그림 제목</dt><dd>${esc(f.title)}</dd><dt>무엇을 그렸나</dt><dd>${esc(f.sub)}</dd><dt>출처</dt><dd>${esc(f.src)}</dd><dt>사용 자료</dt><dd>${chips}</dd></dl></div></article>`;
}
function render(){
  shown=D.figs.filter(f=>match(f));
  $('#subs').innerHTML=`<button class="sub ${st.tab<0?'on':''}" data-tab="-1">전체 흐름 <em>${D.figs.filter(f=>match(f,-1)).length}</em></button>`+
   D.tabs.map((t,i)=>`<button class="sub ${st.tab==i?'on':''}" data-tab="${i}">${pad(i+1)} ${t.name} <em>${D.figs.filter(f=>match(f,i)).length}</em></button>`).join('');
  $$('.gm').forEach(b=>b.classList.toggle('on',+b.dataset.tab==st.tab));
  let h='';
  D.tabs.forEach((t,i)=>{if(st.tab>=0&&st.tab!=i)return;const fs=shown.filter(f=>f.tab==i);if(!fs.length&&(st.kind||st.q))return;
    const nx=i<D.tabs.length-1?`<div class="next"><button data-go="${i+1}">다음 단계 · ${pad(i+2)} ${D.tabs[i+1].name} →</button></div>`:'';
    h+=`<section class="sec" id="step-${i}"><div class="sech"><span class="num">${pad(i+1)}</span><div><span class="en">${t.en}</span><h2>${t.name}</h2></div></div>
     <div class="msg"><strong>${esc(t.head)}</strong><ul>${t.lead.map(x=>`<li>${esc(x)}</li>`).join('')}</ul></div>
     <div class="grid">${fs.map(card).join('')}</div>${t.name=='기대효과'?effTable():''}${st.tab<0?'':nx}</section>`;});
  $('#secs').innerHTML=h||'<div class="empty">조건에 맞는 그림이 없습니다. 초기화를 눌러 주세요.</div>';
  $('#lst').innerHTML=shown.map(f=>`<tr data-no="${f.no}"><td class="no">${pad(f.no)}</td><td>${pad(f.tab+1)} ${D.tabs[f.tab].name}</td><td class="t">${esc(f.title)}</td><td class="s">${esc(f.sub)}</td><td><span class="chip">${esc(f.tag)}</span></td><td class="s">${esc(f.src)}</td></tr>`).join('')||'<tr><td colspan="6" class="empty">조건에 맞는 그림이 없습니다.</td></tr>';
  $('#allSrc').textContent='데이터 출처 모두 펼치기';
}
$('#srct').innerHTML=D.sources.map(s=>`<tr id="src-${s.id}"><td class="o">${esc(s.org)}</td><td>${esc(s.name)}</td><td class="p">${esc(s.period)}</td><td>${s.figs.map(n=>`<a class="fl" href="#fig-${pad(n)}" data-fig="${n}">${pad(n)}</a>`).join('')}</td></tr>`).join('');
function apply(){st.tab=+$('#fTab').value;st.kind=$('#fKind').value;st.pct=+$('#fPct').value;st.q=$('#q').value;render()}
function setTab(t,scroll){st.tab=t;$('#fTab').value=t;render();if(scroll)$(t<0?'#subs':'#step-'+t).scrollIntoView({behavior:'smooth',block:'start'})}
function view(v){$$('.tab').forEach(b=>b.classList.toggle('on',b.dataset.view==v));$('#basic').hidden=v!='basic';$('#detail').hidden=v!='detail'}
function openAcc(){$('#acc').classList.add('open');$('#gold').setAttribute('aria-expanded','true');$('#accb').style.maxHeight=$('#accb').scrollHeight+'px'}
function flash(el){el.classList.remove('flash');void el.offsetWidth;el.classList.add('flash')}
function goFig(n){const f=D.figs.find(x=>x.no==n);if(!match(f)){st.tab=-1;st.kind='';st.q='';$('#q').value='';$('#fTab').value=-1;$('#fKind').value='';render()}
  view('basic');const el=$('#fig-'+pad(n));el.scrollIntoView({behavior:'smooth',block:'start'});flash(el)}
let cur=0;
function lb(n){cur=shown.findIndex(f=>f.no==n);if(cur<0){shown=D.figs;cur=shown.findIndex(f=>f.no==n)}show()}
function show(){const f=shown[cur];$('#lbt').innerHTML=`<span class="no">${pad(f.no)}</span>${esc(f.title)}`;$('#lbk').textContent=f.tag;$('#lbi').src=f.file;$('#lbi').alt=f.title;$('#lbs').textContent='출처: '+f.src;$('#lb').classList.add('on')}
function step(d){cur=(cur+d+shown.length)%shown.length;show()}
document.addEventListener('click',e=>{
  const t=e.target.closest('[data-tab],[data-view],[data-go],.sb,figure[data-no],.dsl,.fl,[data-open],#lst tr[data-no]');if(!t)return;
  if(t.matches('.gm,.sub'))setTab(+t.dataset.tab,true);
  else if(t.matches('[data-go]'))setTab(+t.dataset.go,true);
  else if(t.matches('.tab'))view(t.dataset.view);
  else if(t.matches('.sb')){const box=t.closest('.card').querySelector('.srcbox');box.hidden=!box.hidden;t.setAttribute('aria-expanded',!box.hidden);t.textContent=box.hidden?'데이터 출처 ▾':'데이터 출처 ▴'}
  else if(t.matches('figure'))lb(+t.dataset.no);
  else if(t.matches('tr'))lb(+t.dataset.no);
  else if(t.matches('.dsl')){e.preventDefault();openAcc();const r=$('#src-'+t.dataset.src);r.scrollIntoView({behavior:'smooth',block:'center'});flash(r)}
  else if(t.matches('.fl')){e.preventDefault();goFig(+t.dataset.fig)}
  else if(t.matches('[data-open]'))openAcc();
});
$('#gold').onclick=()=>{const o=$('#acc').classList.toggle('open');$('#gold').setAttribute('aria-expanded',o);if(o)$('#accb').style.maxHeight=$('#accb').scrollHeight+'px'};
$('#go').onclick=apply;$('#sform').onsubmit=e=>{e.preventDefault();apply()};
$('#fPct').onchange=()=>{st.pct=+$('#fPct').value;render()};
$('#reset').onclick=()=>{$('#fTab').value=-1;$('#fKind').value='';$('#fPct').value=2;$('#q').value='';apply()};
$('#toList').onclick=()=>{view('detail');$('.tabs').scrollIntoView({behavior:'smooth'})};
$('#allSrc').onclick=()=>{const open=$('#allSrc').textContent.includes('펼치기');$$('.card').forEach(c=>{c.querySelector('.srcbox').hidden=!open;const b=c.querySelector('.sb');b.setAttribute('aria-expanded',open);b.textContent=open?'데이터 출처 ▴':'데이터 출처 ▾'});$('#allSrc').textContent=open?'데이터 출처 모두 접기':'데이터 출처 모두 펼치기'};
$('#csv').onclick=()=>{const head=['지표','단위','지금',...D.names.map((n,i)=>`${n} ${D.pct[i]}%`)];const rows=[head,...D.rows].map(r=>r.map(v=>`"${String(v).replace(/"/g,'""')}"`).join(',')).join('\n');
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob(['﻿'+rows],{type:'text/csv'}));a.download='안동이어드림_기대효과_요약.csv';a.click()};
$('#lbx').onclick=()=>$('#lb').classList.remove('on');$('#lb').onclick=e=>{if(e.target.id=='lb')$('#lb').classList.remove('on')};
$('#lbp').onclick=()=>step(-1);$('#lbn').onclick=()=>step(1);
document.addEventListener('keydown',e=>{if(!$('#lb').classList.contains('on'))return;if(e.key=='Escape')$('#lb').classList.remove('on');if(e.key=='ArrowLeft')step(-1);if(e.key=='ArrowRight')step(1)});
render();openAcc();
if(location.hash.startsWith('#fig-'))setTimeout(()=>goFig(+location.hash.slice(5)),200);
</script></body></html>'''


# ═════════════ 2) PDF 인쇄본 (A4 세로, 한 단계 = 한 쪽, 그림은 폭 전체로 한 줄에 한 장) ═════════════
# 9/29 사용자 "세로로". 세로 폭에 2열이면 그림 글자가 절반 크기라 1열. 기대효과 표는 표지(탭 아래 표 자리)로.
# 9/29 담백한 보고서 양식을 시도했으나 사용자 지시("디자인은 아까처럼")로 데이터랩 화면 틀로 되돌림. 문구 수정(전국 중앙 등)은 유지.
PAGE_W, PAGE_H, PAD_T, PAD_B, PAD_X = 210, 297, 9, 13, 14
TOPBAR, GAP, CHROME, LINE_H = 13, 5, 16.5, 3.4
IMG_W = PAGE_W - 2 * PAD_X - 2 * 4
AVAIL = PAGE_H - PAD_T - PAD_B - TOPBAR - 3          # 3mm 여유
MSG_W = PAGE_W - 2 * PAD_X - 10                      # 설명 상자 안 글 폭
STEP_HEAD = lambda st: 23 + 4.7 * sum(math.ceil(len(x) * 2.45 / MSG_W) for x in st[3])   # 단계 머리 + 한 줄 메시지 + 설명 줄(7.8pt 글자당 2.45mm)


def img_h(no, w=IMG_W):
    im = Image.open(FILES[no]); return w * im.height / im.width


def src_lines(no):                                   # 출처 한 줄(6.4pt) 폭 어림: 글자당 2.1mm
    return max(1, math.ceil((len(META[no]['src']) + 4) * 2.1 / IMG_W))


def paginate():
    """단계마다 쪽을 새로 연다. 그림(한 줄에 한 장)이 넘치면 그 쪽 그림을 같은 비율로 줄이고(0.72까지), 그래도 넘치면 다음 쪽."""
    def scale(p):
        fixed = p['extra'] + sum(c for _, _, c in p['rows']) + GAP * (len(p['rows']) - 1)
        return min(1.0, (AVAIL - fixed) / sum(i for _, i, _ in p['rows']))
    pages = []
    for si, stp in enumerate(STEPS):
        cur = {'step': si, 'head': True, 'extra': STEP_HEAD(stp), 'rows': []}
        for r in [[n] for n in stp[4]]:
            row = (r, max(img_h(n) for n in r), CHROME + LINE_H * max(src_lines(n) for n in r))
            cur['rows'].append(row)
            if len(cur['rows']) > 1 and scale(cur) < 0.72:
                cur['rows'].pop(); pages.append(cur); cur = {'step': si, 'head': False, 'extra': 0, 'rows': [row]}
        pages.append(cur)
    for p in pages:
        s = scale(p); p['rows'] = [(r, s) for r, _, _ in p['rows']]
    return pages


def topbar(label):
    return f'<div class="topbar">{LOGO}<div class="crumb">⌂ › 분석 리포트 › 안동 이어드림 › <b>{label}</b></div></div>'


def footer(pno, total):
    return f'<div class="foot"><span>안동 이어드림 분석 보고서 · 요약</span><span>2026 한국관광 데이터랩 활용 경진대회 · 안동팀</span><span>{pno} / {total}</span></div>'


def steps_bar(active=None):
    return ''.join(f'<span class="sub{" on" if i == active else ""}">{i + 1:02d} {s[0]}</span>' for i, s in enumerate(STEPS))


def pcard(no, s):
    title, tag = T[no]
    return f'''<div class="card" id="fig-{no:02d}"><div class="ch"><h4><span class="no">{no:02d}</span>{escape(title)}</h4>
<span class="chip on">안동</span><span class="chip">{escape(tag)}</span>
<span class="links">차트 그림 저장 <i>|</i> <a href="#desc">데이터 출처</a></span></div>
<div class="img"><img src="{REL}{FILES[no].name}" style="width:{IMG_W * s:.1f}mm"></div>
<div class="srcl"><b></b>출처: {escape(META[no]['src'])}</div></div>'''


def step_page(pg, pno, total):
    si = pg['step']; name, en, head, lead, _ = STEPS[si]
    hd = ''
    if pg['head']:
        lis = ''.join(f'<li>{escape(x)}</li>' for x in lead)
        hd = f'''<div class="sech"><span class="num">{si + 1:02d}</span><div><span class="en">{en}</span><h2>{name}</h2></div>
<div class="subs">{steps_bar(si)}</div></div><div class="msg"><strong>{escape(head)}</strong><ul>{lis}</ul></div>'''
    rows = ''.join(f'<div class="row">{"".join(pcard(n, s) for n in r)}</div>' for r, s in pg['rows'])
    return f'<section class="page">{topbar(name)}{hd}<div class="grid">{rows}</div>{footer(pno, total)}</section>'


def flow_strip(first):
    """표지 아래: 5단계 흐름 목차(단계 · 한 줄 메시지 · 쪽)"""
    cells = ''.join(f'<div class="fs"><span class="n">{i + 1:02d}</span><b>{s[0]}</b><p>{escape(s[2])}</p><em>{first[i]}쪽</em></div>'
                    + ('<span class="ar">›</span>' if i < len(STEPS) - 1 else '') for i, s in enumerate(STEPS))
    return f'<h3 class="flh">보고서 흐름</h3><div class="flow">{cells}</div>'


def cover(total, first):
    menu = ''.join(f'<span><em>{i + 1:02d}</em>{s[0]}</span>' for i, s in enumerate(STEPS))
    return f'''<section class="page cover">
<div class="util"><span>보고서 소개</span><span>데이터 출처</span><span>그림 목록</span></div>
<div class="gnb-top">{LOGO}<div class="search">지표나 그림 번호를 입력해 주세요 <span>⌕</span></div>
<div class="team"><span>● 안동팀</span><span>2026 한국관광 데이터랩 활용 경진대회</span></div></div>
<nav class="gnb"><span class="on">전체 흐름</span>{menu}</nav>
<div class="crumb2">⌂ › 분석 리포트 › 안동 이어드림</div>
<h1>안동 이어드림 분석 보고서</h1>
<p class="one"><b>한 줄 기획</b> · {ONE_LINE}</p>
<a class="fab" href="#desc">ⓘ<br>데이터<br>설명</a>
<div class="filter"><div class="f"><label>단계</label><span class="sel">전체 흐름 <small>∨</small></span></div>
<div class="f"><label>자료</label><span class="sel">전체 <small>∨</small></span></div>
<div class="f"><label>참여율 (효과 표 강조)</label><span class="sel">목표 {pct['목표']:.0f}% <small>∨</small></span></div><span class="btn">조회</span></div>
<div class="notice"><span class="ck">✓</span><b>알아두세요!</b><p>{NOTICE}</p></div>
<div class="tabs"><span class="tab on">기본조회</span><span class="tab">상세조회</span></div>
<div class="tbar"><div class="subs"><span class="sub on">전체 흐름</span>{steps_bar(None)}</div>
<div class="tools"><span>효과 표 CSV 저장</span><span>데이터 출처 모두 펼치기</span><span>인쇄</span></div></div>
{idea_table()}
<h3 class="flh">지금과 시행 후 <small>시행 전 예측 · 원도심 식당 83곳 운영 · 추가 소비는 연간 환산(1~8월 월평균 × 12)</small></h3>
{effect_table()}
{flow_strip(first)}
<p class="tnote">※ 이어드림 3단계 운영안(서식4 3)칸). 다음 쪽부터 문제 → 원인 → 해법 → 기대효과 → 검증·확산 순서로 근거 그림 {len(USED)}장을 싣습니다.</p>
{footer(1, total)}</section>'''


def desc_page(pno, total):
    rows = ''.join(f'<tr><td class="o">{escape(o)}</td><td>{escape(nm)}</td><td class="p">{escape(pr)}</td><td>{"".join(f"<a class=fl href=#fig-{n:02d}>{n:02d}</a>" for n in f)}</td></tr>'
                   for _, o, nm, pr, f in SOURCES)
    return f'''<section class="page" id="desc">{topbar('데이터 설명')}
<div class="gold"><span>데이터 설명</span><span class="car">⌃</span></div>
<div class="two"><table class="desc"><thead><tr><th>구분</th><td>세부내용</td></tr></thead><tbody>{desc_table()}</tbody></table>
<div><table class="srct"><thead><tr><th style="width:26%">제공 기관</th><th style="width:34%">자료</th><th style="width:26%">기간 · 코드</th><th>그림</th></tr></thead><tbody>{rows}</tbody></table>
<div class="lic"><span class="open">OPEN<em>출처</em></span><p>그림의 숫자는 팀 분석 파일에서 자동으로 읽어 그렸습니다. 원자료 이용 조건은 각 제공 기관의 조건을 따릅니다.</p></div>
<div class="lic"><span class="open">OPEN<em>코드</em></span><p>scripts/보고서그림.py · scripts/그림보고서_PDF.py (공개 저장소 kysk2295/andong-datalab-2026)</p></div></div></div>
{footer(pno, total)}</section>'''


PCSS = '''
@page{size:210mm 297mm;margin:0}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Pretendard',sans-serif;color:#23272B;-webkit-print-color-adjust:exact;print-color-adjust:exact}
a{color:inherit;text-decoration:none}
.page{width:210mm;height:297mm;position:relative;overflow:hidden;padding:9mm 14mm 13mm;page-break-after:always;background:#fff}
.page:last-child{page-break-after:auto}
.logo{display:inline-flex;align-items:center;gap:6px}.logo b{color:#1A4FA8;font-size:13.5pt;font-weight:800;letter-spacing:-.3px}
.logo i{font-style:normal;color:#2D6BD9;font-size:10.5pt;font-weight:600;margin-left:1px}
.topbar{display:flex;align-items:center;justify-content:space-between;height:10mm;border-bottom:1px solid #E3E8EE;margin-bottom:3mm}
.topbar .logo svg{width:22px;height:22px}.topbar .logo b{font-size:11pt}.topbar .logo i{font-size:9pt}
.crumb,.crumb2{font-size:7.5pt;color:#7A828A}.crumb b{color:#23272B}
.util{display:flex;justify-content:flex-end;gap:14px;font-size:7pt;color:#7A828A;margin-bottom:1.5mm}
.gnb-top{display:flex;align-items:center;gap:10mm}
.search{width:58mm;height:8mm;border:1.5px solid #2D6BD9;border-radius:20px;font-size:7.5pt;color:#9AA2AA;display:flex;align-items:center;justify-content:space-between;padding:0 4mm}
.search span{color:#2D6BD9;font-size:12pt}
.team{margin-left:auto;display:flex;gap:10px;font-size:7.5pt;color:#555}.team span+span{display:none}.team span:first-child{color:#2D6BD9}
.gnb{display:flex;gap:5.5mm;font-size:9.5pt;font-weight:700;padding:3mm 0 2.6mm;border-top:1px solid #E3E8EE;border-bottom:1px solid #E3E8EE;margin-top:2mm}
.gnb .on{color:#2D6BD9}.gnb em{font-style:normal;color:#9AA2AA;font-size:7pt;margin-right:1.5mm;font-weight:800}
.crumb2{margin:3.2mm 0 1.5mm}
h1{font-size:21pt;font-weight:800;letter-spacing:-.6px}
.one{font-size:8.6pt;color:#4A5057;margin:1.2mm 0 3.5mm}.one b{color:#1A4FA8}
.fab{position:absolute;right:16mm;top:36mm;width:18mm;height:18mm;border-radius:50%;background:#D9853B;color:#fff;font-size:6.8pt;font-weight:700;
 display:flex;align-items:center;justify-content:center;text-align:center;line-height:1.25;box-shadow:0 2px 6px rgba(0,0,0,.18)}
.filter{background:#EAF1FA;border-radius:6px;padding:4mm 6mm;display:flex;align-items:flex-end;gap:3mm}
.f label{display:block;font-size:7pt;font-weight:700;margin-bottom:1.2mm}
.sel{display:inline-flex;justify-content:space-between;gap:4mm;min-width:26mm;background:#fff;border:1px solid #CBD5E1;border-radius:4px;padding:1.6mm 2.5mm;font-size:7.5pt}
.sel small{color:#8A939C}
.btn{margin-left:5mm;background:#2D6BD9;color:#fff;font-size:8pt;font-weight:700;padding:1.9mm 9mm;border-radius:4px}
.notice{display:flex;gap:3mm;align-items:flex-start;padding:3.5mm 1mm 3mm;border-bottom:1px solid #EEF1F4}
.ck{width:4.2mm;height:4.2mm;border:1.4px solid #23272B;border-radius:2px;font-size:7pt;display:flex;align-items:center;justify-content:center;flex:none;margin-top:.3mm}
.notice b{font-size:9pt;white-space:nowrap}.notice p{font-size:7.4pt;line-height:1.6;color:#4A5057}.notice u{text-decoration:none;color:#1A4FA8;font-weight:600}
.tabs{display:flex;gap:1.5mm;margin-top:3.5mm;border-bottom:2px solid #2D6BD9}
.tab{font-size:7.8pt;padding:1.7mm 5mm;border:1px solid #CBD5E1;border-bottom:none;border-radius:4px 4px 0 0;color:#666;background:#F5F7FA}
.tab.on{background:#2D6BD9;color:#fff;border-color:#2D6BD9;font-weight:700}
.tbar{display:flex;justify-content:space-between;align-items:center;gap:2mm;margin:3mm 0 2.5mm}.tools span:nth-child(2){display:none}
.subs{display:flex;gap:1.5mm}
.sub{font-size:7.4pt;padding:1.2mm 3.4mm;border:1px solid #CBD5E1;border-radius:3px;color:#555;background:#fff}
.sub.on{background:#2D6BD9;border-color:#2D6BD9;color:#fff;font-weight:700}
.tools{display:flex;gap:1.5mm}.tools span{font-size:6.8pt;border:1px solid #CBD5E1;border-radius:3px;padding:1.1mm 2.6mm;color:#555}
.dt{width:100%;border-collapse:collapse;font-size:7.8pt;border-top:2px solid #34383C}
.dt th{background:#F3F6FA;font-weight:700;padding:1.6mm 2mm;border:1px solid #DDE3EA;text-align:center}
.dt th small{font-weight:500;color:#7A828A;font-size:6.5pt}
.dt td{padding:1.7mm 2mm;border:1px solid #E3E8EE;text-align:right;font-variant-numeric:tabular-nums}
.dt .l{text-align:left}.dt .c{text-align:center}.dt td.u{text-align:center;color:#7A828A}
.eff .l{width:34%}
.dt .hi{background:#EAF1FC;color:#1A4FA8;font-weight:800}.dt th.hi{background:#DCE8FB}
.idea td{padding:2.3mm 2.4mm}.idea .warn{color:#E8710A;font-weight:700}
.stp{display:inline-block;background:#2D6BD9;color:#fff;font-size:7pt;font-weight:800;border-radius:3mm;padding:.5mm 2.6mm}
.fl{display:inline-block;text-align:center;font-size:6.6pt;font-weight:700;color:#2D6BD9;border:1px solid #CFDAEA;border-radius:2px;padding:0 1.4mm;margin:0 .8mm .5mm 0;white-space:nowrap}
.tnote{font-size:6.8pt;color:#7A828A;margin-top:2mm}
.flh{font-size:9pt;font-weight:800;margin:5mm 0 2mm}.flh small{font-size:6.8pt;font-weight:500;color:#7A828A;margin-left:2mm}
.flow{display:flex;align-items:stretch;gap:1.5mm}
.fs{flex:1;border:1px solid #E3E8EE;border-top:1.2mm solid #2D6BD9;border-radius:3px;padding:2.4mm 3mm;display:flex;flex-direction:column;background:#fff}
.fs .n{font-size:13pt;font-weight:900;color:#2D6BD9;line-height:1}.fs b{font-size:9pt;margin:1mm 0 .8mm}
.fs p{font-size:7pt;color:#4A5057;line-height:1.5;flex:1}.fs em{font-style:normal;font-size:6.4pt;color:#9AA2AA;margin-top:1.2mm}
.ar{display:none}
.sech{display:flex;align-items:center;gap:3.5mm;margin-bottom:2.2mm}
.sech .num{font-size:20pt;font-weight:900;color:#2D6BD9;letter-spacing:-.5px;line-height:1}
.sech .en{display:block;font-size:6.6pt;color:#1A4FA8;font-weight:700;letter-spacing:.6px}
.sech h2{font-size:14pt;font-weight:800;letter-spacing:-.4px;line-height:1.15}
.sech .subs{margin-left:auto}
.msg{border-left:1.2mm solid #2D6BD9;background:#F6F9FE;padding:2.6mm 4mm;margin-bottom:3mm;border-radius:0 4px 4px 0}
.msg strong{display:block;font-size:10.5pt;font-weight:800;letter-spacing:-.3px;margin-bottom:1mm}
.msg li{list-style:none;font-size:7.8pt;color:#34383C;line-height:1.65;padding-left:3mm;position:relative}
.msg li::before{content:'';position:absolute;left:.4mm;top:1.9mm;width:1.2mm;height:1.2mm;background:#2D6BD9;border-radius:50%}
.grid{display:flex;flex-direction:column;gap:5mm}
.row{display:flex;gap:6mm;align-items:flex-start}
.card{flex:0 0 100%;border:1px solid #E3E8EE;border-radius:5px;padding:2.4mm 4mm 2.6mm;background:#fff}
.ch{display:flex;align-items:center;gap:1.4mm;height:6.5mm;margin-bottom:1.2mm}
.ch h4{font-size:9pt;font-weight:800;margin-right:1.5mm;letter-spacing:-.2px}
.ch .no{color:#2D6BD9;margin-right:1.6mm}
.chip{font-size:6.4pt;padding:.7mm 2mm;border:1px solid #2D6BD9;color:#2D6BD9;border-radius:2px;white-space:nowrap}
.chip.on{background:#2D6BD9;color:#fff}
.links{margin-left:auto;font-size:6.3pt;color:#8A939C;white-space:nowrap}.links i{font-style:normal;color:#CBD5E1;margin:0 1mm}
.img{text-align:center}.img img{display:inline-block}
.srcl{display:flex;gap:1.5mm;font-size:6.4pt;line-height:1.45;color:#5B6269;margin-top:1.2mm;padding-top:1.2mm;border-top:1px dashed #E3E8EE}
.srcl b{flex:none;width:1.4mm;height:1.4mm;background:#2D6BD9;margin-top:1mm}
.eff{margin-top:3.5mm}
.foot{position:absolute;left:14mm;right:14mm;bottom:5mm;display:flex;justify-content:space-between;font-size:6.5pt;color:#9AA2AA;border-top:1px solid #EEF1F4;padding-top:1.6mm}
.gold{display:flex;justify-content:space-between;align-items:center;background:linear-gradient(#E8C067,#E2B65A);border-radius:6px;padding:3mm 6mm;margin:3mm 0 3.5mm;
 font-size:10.5pt;font-weight:800;color:#3D2E10;box-shadow:0 1px 3px rgba(0,0,0,.12)}
.two{display:flex;flex-direction:column;gap:5mm}
.desc,.srct{width:100%;border-collapse:collapse;font-size:7.1pt;border-top:1.5px solid #34383C}
.desc th{width:17mm;background:#F6F7F9;font-weight:600;color:#4A5057;text-align:center;padding:1.5mm 1.5mm;border-bottom:1px solid #E6E9ED}
.desc thead th,.desc thead td{font-weight:700;color:#23272B;text-align:center;background:#F6F7F9}
.desc td{padding:1.5mm 2.5mm;border-bottom:1px solid #E6E9ED;line-height:1.55;color:#34383C}
.srct th{background:#F6F7F9;padding:1.5mm 1.8mm;border-bottom:1px solid #E6E9ED;text-align:left}
.srct td{padding:1.3mm 1.8mm;border-bottom:1px solid #E6E9ED;vertical-align:top}
.srct .o{font-weight:700}.srct .p{color:#6B7177}
.lic{display:flex;align-items:center;gap:3mm;margin-top:2.6mm;font-size:6.8pt;color:#4A5057}
.open{display:inline-flex;align-items:center;border:1.4px solid #23272B;border-radius:3px;font-weight:900;font-size:7.5pt;padding-left:1.8mm;flex:none}
.open em{font-style:normal;background:#23272B;color:#fff;margin-left:1.8mm;padding:.6mm 1.8mm;font-size:6.5pt;font-weight:700}
'''


def build_pdf():
    pages = paginate()
    total = 1 + len(pages) + 1
    first = {}
    for i, pg in enumerate(pages):
        first.setdefault(pg['step'], i + 2)
    body = [cover(total, first)] + [step_page(pg, i + 2, total) for i, pg in enumerate(pages)] + [desc_page(total, total)]
    h = OUT / '_인쇄본.html'
    h.write_text(f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>안동 이어드림 분석 보고서</title><style>{PCSS}</style></head><body>{"".join(body)}</body></html>', encoding='utf-8')
    pdf = OUT / '안동이어드림_그림보고서_20260929.pdf'
    subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                    '--allow-file-access-from-files', '--virtual-time-budget=15000', '--run-all-compositor-stages-before-draw',
                    f'--print-to-pdf={pdf}', h.as_uri()], check=True, capture_output=True)
    n = subprocess.run(['/opt/homebrew/bin/pdfinfo', str(pdf)], capture_output=True, text=True).stdout.split('Pages:')[1].split()[0]
    return pdf, n, total, [(p['step'], [r for r, _ in p['rows']], round(p['rows'][0][1], 2)) for p in pages]


web = build_web()
pdf, n, total, lay = build_pdf()
print(web.relative_to(ROOT))
print(pdf.relative_to(ROOT), n, '쪽 (예상', total, '쪽)')
for x in lay:
    print('  단계', STEPS[x[0]][0], x[1], '배율', x[2])
