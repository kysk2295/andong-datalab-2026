# -*- coding: utf-8 -*-
"""서식4 활용사례 작성본 (2026-09-23) — 워드(.docx) + 미리보기 PDF

양식: 공모요강 서식4(hwp 원본 구조) · 개조식 · 2~3장 · 함초롬바탕 11pt · 줄간격 160
숫자: 시뮬레이션결과.json(⑤), 설문_집계.json(팀 온라인 설문), 사후검증_결과.json·순차도입_검정력.json(⑥), 전국진단.json(⑦), 교수브리핑 수치.json
점검 근거: 보고서/서식4_점검_20260923.md
출력: 보고서/서식4_20260923/안동이어드림_서식4_활용사례_20260923.docx · .pdf
"""
import json, subprocess
from pathlib import Path
from html import escape
from docx import Document
from docx.shared import Pt, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = Path(__file__).resolve().parent.parent
O = ROOT / '보고서/서식4_20260923'
O.mkdir(parents=True, exist_ok=True)
S = json.loads((ROOT / '보고서/성과도출_20260922/시뮬레이션결과.json').read_text(encoding='utf-8'))
PW = json.loads((ROOT / '보고서/성과도출_20260922/순차도입_검정력.json').read_text(encoding='utf-8'))
DG = json.loads((ROOT / '보고서/전국진단_20260923/전국진단.json').read_text(encoding='utf-8'))
SV = json.loads((ROOT / 'data/설문/설문_집계.json').read_text(encoding='utf-8'))
B, W = S['기본안'], S['확대안']
SC = S['시나리오']                                     # 참여율 3단계(9/27 저녁): 기준 2% / 흥행 4% / 목표 10%
SB = S['설문보정']
FONT = '함초롬바탕'


def n0(x): return f'{x:,.0f}'
def pc(x, d=1): return f'{x * 100:.{d}f}%'


sv_n, sv_v = SV['표본']['응답'], SV['표본']['3년내_방문_예']
sv_bus = SV['Q3_버스불편_버스이용방문자']          # 버스 이용 방문자 중 불편
sv_night = SV['Q9_월영교밤_부족_방문자']            # 20시 이후 월영교 식당·편의 부족
sv_last = SV['Q13_당일귀가자중_20~22시']            # 당일 귀가자 중 20~22시 귀가
sv_price = SV['Q11_가격_이유']                      # 유료 체험 망설임 이유 = 가격
sv_nonprice = SV['Q11_비가격_이유']


def sv(x): return f"{x['pct']:.0f}%({x['k']}/{x['n']})"


same = [s for s in DG['안동과_같은_유형'] if s != '안동시']
pw50 = next(c['검정력'] for c in PW['확대안']['곡선'] if abs(c['효과'] - .5) < 1e-9)
TH = S['임계값']                                    # 참여율 고정 시 격차 메운 비율 / 격차를 메우는 데 필요한 참여율(중앙값)
th_half = TH['필요참여율_P50']['확대안']['0.5']
th_obs_gap = TH['격차비율_P50']['확대안'][TH['참여율'].index(0.01)]

# ───────────────────────── 내용 ─────────────────────────
HEAD = [
    ('응모작 제목', '사람이 모이는 곳엔 혜택이 없고, 막차 앞에서 밤이 끊긴다: 데이터로 다시 잇는 안동 이어드림 [팀 결정]'),
    ('한국관광 데이터랩\n(필수)', '지역별 관광 현황(외지인 방문자·요일·시간대, 읍면동 방문자), 신용카드 관광소비(업종별), 숙박 현황(평균 숙박일수), '
     '중심-연관 관광지, 내비게이션 목적지 검색, 야간관광 현황, 축제 현황(방문자·관광소비)'),
    ('타분야 데이터\n(선택)', '코레일 안동역 시간대별 승하차(2024.1~2026.8), 한국철도공사 8대 도시(안동) 가명결합 분석(2022.4~6), '
     '소상공인 상가(상권)정보(2026.6), 안동시 디지털관광주민증 혜택업체·이용 건수(정보공개청구), 주민증 가맹점별 이용 실적, '
     '관광지식정보시스템 주요관광지점 입장객, 안동시 버스정보시스템 시간표, '
     f'팀 온라인 설문({sv_n}명, 2026.9.23~24), 팀 현장 확인(월영교 1km 음식점 영업 종료)'),
    ('성과분야\n(1개 선택)', '관광지 안전문제 해결 □   마케팅 및 홍보 활성화 □   매출·수익 등 경제적 성과 □\n'
     '전략수립 및 기획 ■   상품 및 서비스 개발·개선 □   앱·웹 등 서비스 개발 □'),
    ('핵심성과\n(1-2줄 요약)', f"데이터랩 방문·시간대·카드소비와 철도·상가·주민증·설문 데이터를 융합해 원도심 → 체험 → 월영교로 잇는 3단계 야간 릴레이를 설계, "
     f"체험 결제 연 {SC['기준']['체험결제합']['P50'] / 1e4:.1f}만 건·방문 1회당 체험·문화 소비 +{SC['기준']['지표1_증가율']['P50'] * 100:.1f}% 예상(참여 2% 기준)"),
    ('계량성과', f'온라인 설문 {sv_n}명(안동 방문 경험 {sv_v}명) 수행'),
]

# 9/27 밤(사용자 요청): 공모요강 서식4 작성 예시 형식을 따름 — 칸마다 "○ 1) … 2) …" 번호 한 줄 항목, 4)칸은 숫자로 끝나는 결과 문장.
# 비전공자용 쉬운 말, 항목마다 [짧은 제목]을 붙여 한눈에 보이게 한다.
G = lambda n, k: SC[n][k]['P50']
S1 = [   # 9/27 밤: 사용자가 정리한 문제 1·2(팀 문서) 문장을 개조식 하위 항목으로 옮김. 기존 [원도심 혜택 공백] 유지, 설문 불편은 3번 근거로 합침
    ('체험·문화 소비', '방문객 증가 대비 체험 소비 급감(<b>−16.8%</b>, 전국 중앙값 −2.0%)과 유료 콘텐츠 전환 부족', [
        '방문객과 숙박 소비는 늘었으나, 레저용품 쇼핑을 제외한 체험·문화 소비는 방문당 183.5원(2024년 1~8월) → 152.7원(2026년 같은 기간)으로 −16.8%, '
        '146개 시·군 중 감소폭 22번째. 수준도 경주(302.3원)의 절반(50.5%)',
        '관심관광지 검색 중 역사유적지 비중은 26.4%로 경주(18.4%)보다 높아(2026년 1~8월) 볼거리를 찾는 수요는 있음',
        '그러나 하회마을은 방문객 점유율 6.29% 대비 소비 건수 점유율 0.40%로 <b>소비 전환 배율 0.06</b>(소비 건수 점유율 ÷ 방문 점유율, 원도심 1.73, 철도공사 2022.4~6), '
        '목적지 검색 비중도 11.4% → 5.2%(2018→2025년)로 경주 불국사·동궁과월지 등(−30%대)과 뚜렷이 구분되는 하락 → 보러 온 방문객이 지역 안에서 유료로 결제하는 데까지 이어지지 않음']),
    ('원도심 혜택 공백', '외지인이 가장 많이 찾는 원도심(방문의 12.5%)에 디지털 관광주민증 혜택 업체 <b>0곳</b>, 혜택 이용의 95%는 관람지에서만 발생', []),
    ('동선 집결 및 야간 식음 인프라 부재', '월영교 방문객 유입(외곽 관광객 54.8% 집결) 대비 야간 식사 가능 업소 18.8%(16곳 중 3곳)로 소비 전환 한계', [
        '외곽 주요 관광지 방문객의 절반 이상이 월영교를 함께 찾음(만휴정 54.8%, 도산서원 54.2%)',
        '월영교 반경 1km 영업 음식점 16곳 중 21시까지 식사 가능 3곳(18.8%), 7곳(43.8%)이 20:00~20:30 영업 종료, <b>주점 0곳</b>'
        f"(팀 설문 방문객 {sv_v}명 중 {sv_night['pct']:.0f}%가 20시 이후 월영교 주변 식당·편의시설 부족)",
        '방문 점유율 15.24% 대비 소비 건수 점유율 6.05%(<b>소비 전환 배율 0.40</b>), 소비 건수 중 편의점 25.8%·숙박 0.3%(철도공사 2022.4~6)',
        '실질 소비 상권인 원도심(음식점 764곳, 배율 1.73)과 3.2km 떨어져 있으나 잇는 시내버스는 112번 한 노선, 원도심 출발 막차 18:45(평일) → '
        f"<b>19시 이후 대중교통 연결 없음</b>(설문 시내버스 이용자 {sv_bus['pct']:.0f}% 불편)"]),
]
S2 = [
    ('혜택 위치 진단', '[데이터랩] 읍면동별 외지인 방문 + [안동시] 주민증 혜택 업체 27곳 주소 → 방문 1위 원도심에 혜택 0곳(그림 1)'),
    ('운영 시간 결정', f"[코레일] 안동역 시간대별 승차 + [팀 설문] 귀가 시각 → 주말 안동역 승차는 18~19시에 가장 많고 막차는 21~22시, 당일 귀가자 {sv_last['pct']:.0f}%가 20~22시 귀가 → 18:30~21:00 운영"),
    ('밤의 빈 곳 확인', '[상가정보] 음식점 3,254곳 + 영업 종료 현장 확인 + [버스정보시스템] 46개 노선 시간표 → 월영교 1km 주점 0곳, 19시 이후 버스 0회'),
    ('효과 미리 계산', '주민증 이용 기록·축제 방문객 소비·체험 가격 27개·팀 설문을 넣어 <b>1만 번 반복 계산</b>(몬테카를로 모의실험). 설문의 "하겠다"는 선행연구대로 33~40%만 실제로 한다고 반영'),
    ('전국 비교', '[데이터랩] 전국 144개 시·군을 같은 기준(체험 소비 변화·숙박일수·저녁 방문)으로 진단 → 안동과 비슷한 곳 찾기'),
]
S3_INTRO = '데이터로 정한 3단계 릴레이 「안동 이어드림」: 낮에 원도심에서 식사한 방문객을 체험으로, 저녁에는 월영교로 잇는다(그림 2)'
S3_TABLE = [
    ('1단계 낮: 식사 → 체험', '원도심 관광 식당 83곳(찜닭골목·문화의거리)에서 식사 후 영수증 QR 인증 → 체험 10% 할인',
     f"방문 1위인데 혜택 0곳. 체험을 망설인 이유의 {sv_nonprice['pct']:.0f}%가 가격이 아닌 정보·예약·이동"),
    ('2단계 저녁: 월영교로 이동', '18:30~21:00 원도심 → 월영교 택시(관광택시 저녁 배치), 이용이 많아지면 셔틀', '19시 이후 버스 0회, 안동역 막차 21~22시'),
    ('3단계 밤: 월영교에서', '저녁 문보트(10% 할인) + 21시 이후 식사·주점 팝업(월영야행 부지 활용)', '21시 식사 3곳·주점 0곳'),
    ('넓히는 방법', '식당을 4묶음으로 나눠 추첨 순서대로 참여', '운영하면서 효과를 바로 확인'),
]
S3_NOTE = '아직 정하지 않은 것: 팝업 부스 수·차량 대수(이용량·견적 확인 후), 주민증 조건형 혜택 가능 여부(안 되면 영수증 QR 방식)'
S4 = [
    ('원도심 체험 회복', f"원도심 방문객 100명 중 2명 참여 시 체험 결제 <b>연 {G('기준', '체험결제합') / 1e4:.1f}만 건</b>, "
     f"방문 1회당 체험·문화 소비 <b>+{pc(G('기준', '지표1_증가율'))}</b>(전국보다 더 줄어든 폭의 {pc(G('기준', '격차기여율'), 0)} 회복), 안동 소비 연 {G('기준', '추가소비합') / 1e8:.1f}억 원 증가"),
    ('흥행 조건과 효과', f"100명 중 4명(여행비 절반을 돌려준 강진 반값여행 수준)이면 +{pc(G('흥행', '지표1_증가율'))}, "
     f"식당이 모든 손님에게 안내해 10명 중 1명이 참여하면 <b>+{pc(G('목표', '지표1_증가율'))}</b>(전국보다 더 줄어든 폭의 {pc(G('목표', '격차기여율'), 0)} 회복). "
     f"절반을 되찾으려면 100명 중 약 {th_half * 100:.0f}명 참여가 필요하고, 이 참여율은 계산대에서 얼마나 안내하느냐에 달림"),
    ('밤까지 이어지는 동선', f"셔틀·택시로 월영교에 새로 가는 저녁 이동 <b>주말 하루 {G('기준', '새이동_하루'):.0f}명</b>, 월영교 팝업 이용 주말 하루 {G('기준', '팝업_하루'):.0f}명, "
     f"늘어난 소비 중 {pc(G('기준', '연결비중'), 0)}는 세 단계를 이어야만 생김"),
    ('수요 확인', f"방문객 설문 체험 할인 쿠폰 이용 의향 {SV['Q6_영수증→체험쿠폰']['방문자_top2']['pct']:.0f}%, 야간 셔틀 {SV['Q8_야간택시셔틀']['방문자_top2']['pct']:.0f}%, "
     f"야간 팝업 {SV['Q10_야간팝업포차']['방문자_top2']['pct']:.0f}%(이 중 33~40%만 실제 행동으로 계산에 반영)"),
    ('검증과 확산', f"추첨 순서로 식당을 열어 83곳·5개월이면 체험 결제 +50% 효과를 {pc(pw50, 0)} 확률로 확인, 전국에서 안동과 같은 유형 {len(same)}곳"
     f"({'·'.join(s.replace('시', '').replace('군', '') for s in same)}) 도출, 주민증 운영 52개 지자체(안동 포함)에 적용 가능"),
]
S4_TABLE = [
    ('체험 결제(연간)',) + tuple(f"{n0(G(n, '체험결제합'))}건" for n in ('기준', '흥행', '목표')),
    ('방문 1회당 체험·문화 소비',) + tuple(f"+{pc(G(n, '지표1_증가율'))}" for n in ('기준', '흥행', '목표')),
    ('전국보다 더 줄어든 폭 중 되찾는 비율',) + tuple(pc(G(n, '격차기여율'), 0) for n in ('기준', '흥행', '목표')),
    ('월영교로 새로 가는 저녁 이동',) + tuple(f"주말 하루 {G(n, '새이동_하루'):.0f}명" for n in ('기준', '흥행', '목표')),
    ('안동에서 늘어나는 소비(연간)',) + tuple(f"{G(n, '추가소비합') / 1e8:.2f}억 원" for n in ('기준', '흥행', '목표')),
]
S4_HEAD = ('원도심 식당 83곳 운영 시', '기준(100명 중 2명)', '흥행(4명)', '목표(10명)')
S4_NOTE = ('효과는 시행 전 예측(2026년 1~8월 자료의 연간 환산, 1만 번 계산의 가운데 값, 할인액·원래 썼을 돈 제외)이며 시행 첫 달 실제 기록으로 다시 계산. '
           '참고자료 zip: 분석보고서(PDF)·데이터 대시보드(엑셀)·전국 진단표·분석 스크립트')
FIG1 = ROOT / '보고서/교수브리핑_20260922/fig4_혜택배치.png'
FIG2 = ROOT / '보고서/성과도출_20260922/g1_하루동선.png'

# ───────────────────────── 워드 ─────────────────────────
doc = Document()
sec = doc.sections[0]
sec.page_height, sec.page_width = Mm(297), Mm(210)
sec.top_margin, sec.bottom_margin, sec.left_margin, sec.right_margin = Mm(20), Mm(15), Mm(20), Mm(20)
st = doc.styles['Normal']
st.font.name = FONT; st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
st.paragraph_format.line_spacing = 1.6
st.paragraph_format.space_after = Pt(0)


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), hexcolor)
    tcPr.append(sh)


def run(p, text, bold=False, size=11):
    import re
    parts = re.split(r'(<b>.*?</b>)', text)
    for part in parts:
        if not part:
            continue
        b = part.startswith('<b>')
        r = p.add_run(part[3:-4] if b else part)
        r.bold = bold or b; r.font.size = Pt(size); r.font.name = FONT
        r._element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    return p


def para(text, bold=False, size=11, indent=0, bullet='○ ', align=None):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Mm(indent + 4) if bullet else Mm(indent)
    p.paragraph_format.first_line_indent = Mm(-4) if bullet else None
    if align: p.alignment = align
    run(p, (bullet or '') + text, bold, size)
    return p


def table(rows, widths, header=None, size=9.5):
    t = doc.add_table(rows=0, cols=len(widths)); t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    if header:
        cells = t.add_row().cells
        for c, h in zip(cells, header):
            c.text = ''; run(c.paragraphs[0], h, True, size); shade(c, 'E7E6E6')
    for r in rows:
        cells = t.add_row().cells
        for c, v in zip(cells, r):
            c.text = ''; run(c.paragraphs[0], v, False, size)
    for row in t.rows:
        for c, w in zip(row.cells, widths):
            c.width = Mm(w)
            for p in c.paragraphs:
                p.paragraph_format.line_spacing = 1.25
    return t


p = doc.add_paragraph(); run(p, '[서식 4]', size=10)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; run(p, '『2026 한국관광 데이터랩 활용 경진대회』 작성양식', True, 14)
t = table([('신청자(대표)\n인적사항', '소속기관명: [팀 작성]   부서명: [팀 작성]\n성명: [팀 작성]   직명/직위: [팀 작성]   담당업무: [팀 작성]')] + HEAD, [34, 136], size=10)
for row in t.rows:
    shade(row.cells[0], 'F2F2F2')
    for par in row.cells[0].paragraphs:
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r_ in par.runs: r_.bold = True


def section(title, sub=None):
    t = doc.add_table(rows=1, cols=1); t.style = 'Table Grid'
    c = t.rows[0].cells[0]; c.text = ''; shade(c, 'F2F2F2'); run(c.paragraphs[0], title, True, 11)
    if sub:
        pp = c.add_paragraph(); run(pp, sub, False, 9)
    doc.add_paragraph().paragraph_format.line_spacing = 0.6


def items(xs):
    for i, it in enumerate(xs, 1):
        t_, x_, subs = (it + ([],))[:3] if len(it) == 2 else it
        para(f"{i}) <b>[{t_}]</b> {x_}")
        for sb in subs:
            para(sb, indent=4, bullet='- ', size=10.5)


section('1) 문제점 또는 현안사항')
items(S1)
section('2) 현안사항 해결을 위한 데이터 활용 방안', '* 한국관광 데이터랩 데이터와 타 기관·분야 데이터를 융복합해 활용')
items(S2)
fp = doc.add_paragraph(); fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
fp.add_run().add_picture(str(FIG1), width=Mm(110))
cp = doc.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER; run(cp, '< 그림 1 읍면동별 외지인 방문 점유율과 주민증 혜택업체 수(2026년 1~8월) >', size=9)
section('3) 데이터 활용을 통한 사업 개선 및 적용 사례', '* 구체적으로 기입')
para(S3_INTRO)
table(S3_TABLE, [34, 78, 58], header=('단계', '무엇을 하나', '왜(데이터 근거)'))
para(S3_NOTE, size=10)
fp = doc.add_paragraph(); fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
fp.add_run().add_picture(str(FIG2), width=Mm(125))
cp = doc.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER; run(cp, '< 그림 2 이어드림 하루 동선: 낮 체험은 원도심, 저녁 체험은 월영교 문보트 >', size=9)
section('4) 추진성과 및 기대효과', '* 시행 전이므로 예상 효과(정량)와 확인 방법을 기재')
items(S4)
table(S4_TABLE, [52, 40, 38, 40], header=S4_HEAD)
para(S4_NOTE, bullet='* ', size=9.5)

docx_out = O / '안동이어드림_서식4_활용사례_20260923.docx'
doc.save(docx_out)

# ───────────────────────── 미리보기 HTML → PDF ─────────────────────────
def li(items, small=False):
    cls = ' class="sm"' if small else ''
    return ''.join(f'<p class="o"{cls}>○ {s_}</p>' for s_ in items)


def hn(xs):
    out = ''
    for i, it in enumerate(xs, 1):
        t_, x_, subs = it if len(it) == 3 else (it[0], it[1], [])
        out += f'<p class="o">○ {i}) <b>[{t_}]</b> {x_}</p>' + ''.join(f'<p class="o3">- {sb}</p>' for sb in subs)
    return out


def htab(rows, header, widths):
    th = ''.join(f'<th style="width:{w}%">{h}</th>' for h, w in zip(header, widths))
    tr = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows)
    return f'<table class="t"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'


head_rows = ''.join(f'<tr><th>{escape(k).replace(chr(10), "<br>")}</th><td>{escape(v).replace(chr(10), "<br>")}</td></tr>'
                    for k, v in [('신청자(대표)\n인적사항', '소속기관명: [팀 작성]   부서명: [팀 작성]\n성명: [팀 작성]   직명/직위: [팀 작성]   담당업무: [팀 작성]')] + HEAD)
CSS = f"""@page{{size:A4;margin:20mm 20mm 15mm 20mm}}
body{{font-family:"{FONT}","HCR Batang","AppleMyungjo","Nanum Myeongjo",serif;font-size:11pt;line-height:1.6;color:#000;margin:0;word-break:keep-all}}
.f{{font-size:10pt}} h1{{font-size:14pt;text-align:center;margin:1mm 0 2mm}}
table{{border-collapse:collapse;width:100%}} .hd th,.hd td{{border:1px solid #000;padding:2px 6px;vertical-align:middle;line-height:1.45;font-size:10pt}}
.hd th{{background:#F2F2F2;width:20%;text-align:center}}
.sec{{border:1px solid #000;background:#F2F2F2;font-weight:bold;padding:1px 6px;margin:3mm 0 1mm}} .sec small{{font-weight:normal;font-size:9pt}}
p{{margin:0}} .o{{padding-left:4mm;text-indent:-4mm}} .sm{{font-size:10pt}} .h{{font-weight:bold;margin-top:1.2mm;padding-left:4mm;text-indent:-4mm}} .o2{{padding-left:9mm;text-indent:-4mm}} .o3{{padding-left:10mm;text-indent:-3mm;font-size:10.5pt}}
.t th,.t td{{border:1px solid #000;padding:1px 5px;font-size:9.5pt;line-height:1.3;text-align:left}} .t th{{background:#E7E6E6}}
.fig{{text-align:center;margin:1mm 0 0}} .fig img{{width:108mm}} .cap{{text-align:center;font-size:9pt}}"""
body = f'''<p class="f">[서식 4]</p><h1>『2026 한국관광 데이터랩 활용 경진대회』 작성양식</h1>
<table class="hd">{head_rows}</table>
<div class="sec">1) 문제점 또는 현안사항</div>{hn(S1)}
<div class="sec">2) 현안사항 해결을 위한 데이터 활용 방안 <small>* 한국관광 데이터랩 데이터와 타 기관·분야 데이터를 융복합해 활용</small></div>{hn(S2)}
<div class="fig"><img src="{FIG1.as_uri()}"></div><p class="cap">&lt; 그림 1 읍면동별 외지인 방문 점유율과 주민증 혜택업체 수(2026년 1~8월) &gt;</p>
<div class="sec">3) 데이터 활용을 통한 사업 개선 및 적용 사례 <small>* 구체적으로 기입</small></div>{li([S3_INTRO])}
{htab(S3_TABLE, ('단계', '무엇을 하나', '왜(데이터 근거)'), (20, 46, 34))}{li([S3_NOTE], True)}
<div class="fig"><img src="{FIG2.as_uri()}"></div><p class="cap">&lt; 그림 2 이어드림 하루 동선: 낮 체험은 원도심, 저녁 체험은 월영교 문보트 &gt;</p>
<div class="sec">4) 추진성과 및 기대효과 <small>* 시행 전이므로 예상 효과(정량)와 확인 방법을 기재</small></div>{hn(S4)}
{htab(S4_TABLE, S4_HEAD, (31, 24, 22, 23))}
<p class="sm">* {S4_NOTE}</p>'''
html = f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>서식4 활용사례</title><style>{CSS}</style></head><body>{body}</body></html>'
assert '—' not in html and '–' not in html
h = O / '서식4_미리보기.html'; h.write_text(html, encoding='utf-8')
pdf = O / '안동이어드림_서식4_활용사례_20260923.pdf'
subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                '--allow-file-access-from-files', '--virtual-time-budget=10000', '--run-all-compositor-stages-before-draw', f'--print-to-pdf={pdf}', h.as_uri()],
               check=True, capture_output=True)
pages = subprocess.run(['/opt/homebrew/bin/pdfinfo', str(pdf)], capture_output=True, text=True).stdout
print(docx_out.relative_to(ROOT)); print(pdf.relative_to(ROOT), [l for l in pages.splitlines() if l.startswith('Pages')])
