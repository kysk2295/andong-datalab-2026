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

# ───────────────────────── 내용 ─────────────────────────
HEAD = [
    ('응모작 제목', '사람이 모이는 곳엔 혜택이 없고, 막차 앞에서 밤이 끊긴다: 데이터로 다시 잇는 안동 이어드림 [팀 결정]'),
    ('한국관광 데이터랩\n(필수)', '지역별 관광 현황(외지인 방문자·요일·시간대, 읍면동 방문자), 신용카드 관광소비(업종별), 숙박 현황(평균 숙박일수), '
     '중심-연관 관광지, 내비게이션 목적지 검색, 야간관광 현황, 축제 현황(방문자·관광소비)'),
    ('타분야 데이터\n(선택)', '코레일 안동역 시간대별 승하차(2024.1~2026.8), 한국철도공사 8대 도시(안동) 가명결합 분석(2022.4~6), '
     '소상공인 상가(상권)정보(2026.6), 안동시 디지털관광주민증 혜택업체·이용 건수(정보공개청구), 주민증 가맹점별 이용 실적, '
     '관광지식정보시스템 주요관광지점 입장객, 안동시 버스정보시스템 시간표, '
     f'팀 온라인 설문({sv_n}명, 2026.9.23~24), 팀 현장조사'),
    ('성과분야\n(1개 선택)', '관광지 안전문제 해결 □   마케팅 및 홍보 활성화 □   매출·수익 등 경제적 성과 □\n'
     '전략수립 및 기획 ■   상품 및 서비스 개발·개선 □   앱·웹 등 서비스 개발 □'),
    ('핵심성과\n(1-2줄 요약)', '데이터랩 방문·소비·시간대 데이터와 철도·상가·주민증 데이터를 결합해 "방문 1위 원도심에 혜택 0곳", '
     '"19시 이후 대중교통 0회·주점 0곳"의 공백을 찾고, 원도심과 월영교를 잇는 3단계 야간 릴레이의 운영안·효과 추정·사후 검증계획을 설계'),
    ('계량성과', f'온라인 설문 {sv_n}명(안동 방문 경험 {sv_v}명) 수행 · [9/26 현장조사 후 입력] 원도심 식당 섭외 동의 ○곳/○곳 · 안내카드 ○장 배포 중 QR 접속 ○건 · '
     '저녁 원도심→월영교 택시 대기 ○분, 요금 ○원 · 반사실 설문 ○명 중 "혜택 없어도 체험" ○%'),
]

S1 = [
    '흔한 두 설명은 데이터로 기각: 관광객은 줄지 않았고(외지인 방문 +5.6%, 2024→2026년 1~8월), 당일치기도 늘지 않음(무박 비중 86.3% → 86.4%, 2019→2025년)',
    '[체험·문화 소비 감소] 외지인 방문당 체험·문화 소비 183.5원 → 152.7원(<b>−16.8%</b>, 2024→2026년 1~8월), 전국 146개 시·군 중앙 −2.0%, 감소폭 22번째. '
    '과거 추세가 비슷한 시·군 10곳의 조합과 비교해도 2025년 이후 안동만 낮아짐(합성통제)',
    '[사람이 모이는 곳에 체험 연결 없음] 외지인 방문 1위 중구동(원도심, 12.5%)에 디지털관광주민증 혜택업체 <b>0곳</b>, 12위 도산면(2.4%)에 6곳. '
    '주민증 이용의 95%가 관람지에서 발생하고 체험은 0.9%(월 약 7건). 하회마을은 방문 6.29% 대비 소비건수 0.40%(소비 전환 배율 0.06, 2022.4~6)',
    '[밤에 끊기는 동선] 만휴정·도산서원 방문자의 54%가 월영교도 찾지만 월영교는 방문 15.2% 대비 소비건수 6.1%(배율 0.40). '
    '반경 1km 영업 음식점 16곳 중 21시까지 식사 가능 3곳, 주점 <b>0곳</b>. 원도심→월영교(3.2km) 19시 이후 대중교통 <b>0회</b>(112번 막차 18:45), '
    '18시 이후 운영하는 체험은 월영교 문보트·황포돛배뿐',
    f'[방문객 응답] 팀 설문(방문 경험 {sv_v}명): 시내버스 이용자 {sv(sv_bus)}가 불편, 20시 이후 월영교 주변 식당·편의시설 부족 {sv(sv_night)}',
]

S2 = [
    '① 혜택 배치 진단: [데이터랩] 읍면동 외지인 방문 × [정보공개청구] 주민증 혜택업체 27곳 주소 × [상가정보] 행정동 대조 → 방문 1위 중구동 0곳(그림 1)',
    '② 운영 시간 창: [코레일] 안동역 주말 시간대별 승차(전 열차, 2026년 1~8월) → 18~19시 13,454명 최대, 막차 21~22시, 22시 이후 0명 → 릴레이 18:30~21:00. '
    f'[팀 설문] 당일 귀가자의 {sv(sv_last)}가 20~22시 막차 시간대에 귀가',
    '③ 저녁 동선: [철도공사] 연관규칙 역산(원도심 방문자 중 월영교 동시 방문 37~39%) × [데이터랩] 월영교 야간 검색 비중(40~43%) → 저녁 자연 이동 15~17%. '
    '[버스정보시스템] 46개 노선 시간표 → 원도심 출발 19시 이후 0회',
    '④ 야간 공백: [상가정보] 음식점 3,254곳 좌표 × [현장조사] 영업 종료 시각 → 월영교 1km 주점 0곳·21시 식사 3곳(원도심 1km는 764곳 중 주점 86곳)',
    '⑤ 효과 추정: [주민증] 가맹 26곳 이용 실적 회귀(음이항) + [데이터랩] 문화관광축제 56개 방문당 소비 + 체험 가격 27개로 파라미터를 추정하고 '
    '몬테카를로 1만 회·민감도 분석으로 효과 범위 계산',
    '⑥ 검증·확산: [데이터랩] 239개 시·군 월별 패널로 합성통제 사전 점검(과적합 발견·수정, 최소 검출 효과 +24%), 144개 시·군 4개 지표 전국 진단표',
]

S3_INTRO = '디지털관광주민증·영수증 QR 위 3단계 릴레이 「안동 이어드림」: 낮의 원도심 식음 소비를 체험으로, 저녁의 원도심 방문객을 월영교로 잇는다(그림 2)'
S3_TABLE = [
    ('1단계 식음 → 체험', '원도심 관광 식당(찜닭골목·문화의거리 83곳)에서 영수증 QR 인증 → 체험권(낮: 원도심 인근 체험)', f'방문 1위 동에 혜택 0곳. 주민증 앱만으로는 이용률 0.06%. 설문: 유료 체험을 망설이는 이유 중 가격은 {sv_price["pct"]:.0f}%, 정보·예약·이동이 {sv_nonprice["pct"]:.0f}%'),
    ('2단계 야간 이동', '18:30~21:00 원도심 → 월영교. 관광택시 저녁 재배치(비수기 3~4대), 확대 시 셔틀', '안동역 막차 21~22시, 19시 이후 버스 0회'),
    ('3단계 월영교', '저녁 체험 = 문보트(완주 혜택으로 두는 안), 21시 이후 식사·주점 팝업(월영야행 부지·입찰 구조 활용)', '21시 식사 3곳·주점 0곳, 저녁 체험은 문보트뿐'),
    ('확대 방식', '참여 식당을 골목별 4묶음으로 나눠 추첨 순서로 순차 개방', '운영과 효과 검증을 동시에'),
]
S3_NOTE = '정하지 않은 값: 부스 개수·차량 대수(처리량·견적 확보 후). 확인 중: 주민증 조건형 혜택 가능 여부(불가 시 영수증 QR 개방형으로 운영)'

S4_PRE = [
    '[분석 성과] 운영 시간 창(18:30~21:00), 혜택 배치·야간 공백 진단, 사전 검증계획서, 전국 시·군 자가 진단표(엑셀)',
    '[현장 관측] 9/26 현장조사 결과 입력(섭외 동의, 안내카드 QR 반응, 택시 대기·요금)',
    '[조건부 예상 효과] 추정 파라미터로 1만 회 모의실험(운영 8개월, 중앙값, 반사실 차감)',
]
S4_TABLE = [
    ('릴레이 인증(월)', '주민증 이용 888건', f"{n0(B['인증_월']['P50'])}건", f"{n0(W['인증_월']['P50'])}건"),
    ('체험 결제(낮 + 저녁)', '주민증 체험 월 약 7건', f"{n0(B['체험결제합']['P50'])}건", f"{n0(W['체험결제합']['P50'])}건"),
    ('저녁 체험(문보트, 연결로만 발생)', '0건', f"{n0(B['문보트']['P50'])}건", f"{n0(W['문보트']['P50'])}건"),
    ('19시 이후 원도심→월영교 운행', '0회', f"하루 {B['하루_택시운행']['P50']:.0f}회", f"하루 {W['하루_택시운행']['P50']:.0f}회(셔틀)"),
    ('월영교 21시 식사 가능 / 주점', '3곳 / 0곳', '11곳 / 8곳', '11곳 / 8곳'),
    ('방문당 체험·문화 소비', '152.7원', f"+{pc(B['지표1_증가율']['P50'])}", f"+{pc(W['지표1_증가율']['P50'])}(격차의 {pc(W['격차기여율']['P50'], 0)})"),
    ('안동 내 추가 소비', '-', f"{B['추가소비합']['P50'] / 1e8:.2f}억 원", f"{W['추가소비합']['P50'] / 1e8:.2f}억 원"),
    ('그중 단계를 이어야만 생기는 몫', '-', pc(B['연결비중']['P50'], 0), pc(W['연결비중']['P50'], 0)),
]
S4_POST = [
    f"[사후 검증] 효과는 원인이 생기는 곳에서 재고 증상으로 환산: 참여 식당을 추첨 순서로 열어 체험 전환 효과를 확인(83곳이면 5개월 안에 +50% 효과를 {pc(pw50, 0)} 확률로 판정)하고, "
    f"그 효과로 체험·문화 소비 격차(−16.8%) 중 메운 비율을 계산하며, 도시 추세는 비슷한 시·군과 비교해 함께 봄",
    f"[파급력] 전국 144개 시·군 진단표로 안동과 같은 유형(체험 소비 하락 + 짧은 숙박) {len(same)}곳({'·'.join(s.replace('시', '').replace('군', '') for s in same)}) 도출 → 확산 후보. "
    '주민증을 운영하는 52개 지자체에 같은 구조(혜택 배치 진단 + 시간 창 + 연결 혜택)로 적용 가능',
]
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


section('1) 문제점 또는 현안사항')
for s_ in S1: para(s_)
section('2) 현안사항 해결을 위한 데이터 활용 방안', '* 한국관광 데이터랩 데이터와 타 기관·분야 데이터를 융복합해 활용')
for s_ in S2: para(s_)
fp = doc.add_paragraph(); fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
fp.add_run().add_picture(str(FIG1), width=Mm(120))
cp = doc.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER; run(cp, '< 그림 1 읍면동별 외지인 방문 점유율과 주민증 혜택업체 수(2026년 1~8월) >', size=9)
section('3) 데이터 활용을 통한 사업 개선 및 적용 사례', '* 구체적으로 기입')
para(S3_INTRO)
table(S3_TABLE, [30, 82, 58], header=('단계', '운영안(정한 값)', '데이터 근거'))
para(S3_NOTE, size=10)
fp = doc.add_paragraph(); fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
fp.add_run().add_picture(str(FIG2), width=Mm(135))
cp = doc.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER; run(cp, '< 그림 2 이어드림 하루 동선: 낮 체험은 원도심, 저녁 체험은 월영교 문보트 >', size=9)
section('4) 추진성과 및 기대효과', '* 시행 전이므로 분석 성과·현장 관측·조건부 예상 효과·사후 검증을 나눠 기재')
for s_ in S4_PRE: para(s_)
table(S4_TABLE, [58, 34, 36, 42], header=('지표', '현재', '기본안(식당 20곳)', '확대안(83곳)'))
para('예상 효과는 시행 전 조건부 값(구간·가정은 참고자료). 결과를 가장 흔드는 참여율·체험 결제율·반사실은 현장조사와 시행 초기에 실측해 갱신', size=10)
for s_ in S4_POST: para(s_)
para('관련 자료(참고자료 zip): 기대효과 예측 도구(엑셀)·예측 보고서, 사후 효과 검증계획서, 전국 진단표(엑셀), 교수 브리핑, 분석 스크립트', bullet='* ', size=9.5)

docx_out = O / '안동이어드림_서식4_활용사례_20260923.docx'
doc.save(docx_out)

# ───────────────────────── 미리보기 HTML → PDF ─────────────────────────
def li(items, small=False):
    cls = ' class="sm"' if small else ''
    return ''.join(f'<p class="o"{cls}>○ {s_}</p>' for s_ in items)


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
p{{margin:0}} .o{{padding-left:4mm;text-indent:-4mm}} .sm{{font-size:10pt}}
.t th,.t td{{border:1px solid #000;padding:1px 5px;font-size:9.5pt;line-height:1.3;text-align:left}} .t th{{background:#E7E6E6}}
.fig{{text-align:center;margin:1mm 0 0}} .fig img{{width:125mm}} .cap{{text-align:center;font-size:9pt}}"""
body = f'''<p class="f">[서식 4]</p><h1>『2026 한국관광 데이터랩 활용 경진대회』 작성양식</h1>
<table class="hd">{head_rows}</table>
<div class="sec">1) 문제점 또는 현안사항</div>{li(S1)}
<div class="sec">2) 현안사항 해결을 위한 데이터 활용 방안 <small>* 한국관광 데이터랩 데이터와 타 기관·분야 데이터를 융복합해 활용</small></div>{li(S2)}
<div class="fig"><img src="{FIG1.as_uri()}"></div><p class="cap">&lt; 그림 1 읍면동별 외지인 방문 점유율과 주민증 혜택업체 수(2026년 1~8월) &gt;</p>
<div class="sec">3) 데이터 활용을 통한 사업 개선 및 적용 사례 <small>* 구체적으로 기입</small></div>{li([S3_INTRO])}
{htab(S3_TABLE, ('단계', '운영안(정한 값)', '데이터 근거'), (18, 48, 34))}{li([S3_NOTE], True)}
<div class="fig"><img src="{FIG2.as_uri()}"></div><p class="cap">&lt; 그림 2 이어드림 하루 동선: 낮 체험은 원도심, 저녁 체험은 월영교 문보트 &gt;</p>
<div class="sec">4) 추진성과 및 기대효과 <small>* 시행 전이므로 분석 성과·현장 관측·조건부 예상 효과·사후 검증을 나눠 기재</small></div>{li(S4_PRE)}
{htab(S4_TABLE, ('지표', '현재', '기본안(식당 20곳)', '확대안(83곳)'), (34, 20, 21, 25))}
{li(['예상 효과는 시행 전 조건부 값(구간·가정은 참고자료). 결과를 가장 흔드는 참여율·체험 결제율·반사실은 현장조사와 시행 초기에 실측해 갱신'], True)}{li(S4_POST)}
<p class="sm">* 관련 자료(참고자료 zip): 기대효과 예측 도구(엑셀)·예측 보고서, 사후 효과 검증계획서, 전국 진단표(엑셀), 교수 브리핑, 분석 스크립트</p>'''
html = f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>서식4 활용사례</title><style>{CSS}</style></head><body>{body}</body></html>'
assert '—' not in html and '–' not in html
h = O / '서식4_미리보기.html'; h.write_text(html, encoding='utf-8')
pdf = O / '안동이어드림_서식4_활용사례_20260923.pdf'
subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                '--allow-file-access-from-files', '--virtual-time-budget=10000', '--run-all-compositor-stages-before-draw', f'--print-to-pdf={pdf}', h.as_uri()],
               check=True, capture_output=True)
pages = subprocess.run(['/opt/homebrew/bin/pdfinfo', str(pdf)], capture_output=True, text=True).stdout
print(docx_out.relative_to(ROOT)); print(pdf.relative_to(ROOT), [l for l in pages.splitlines() if l.startswith('Pages')])
