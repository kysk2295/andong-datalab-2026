# -*- coding: utf-8 -*-
"""요약 대시보드 엑셀 (2026-09-28) — 문제 → 해법 → 기대효과 → 우리 시·군 진단

기존 교수님_통합대시보드(12화면)는 쓰지 않는다(사용자 결정 9/28). 이 파일 하나로 끝나게 만든다.
화면: 한눈에 · 1 문제 · 2 해법 · 3 기대효과 · 4 시·군 진단 · 출처. 계산·차트 원자료 시트(d_…)는 숨김.
조작 칸은 둘뿐: 3 기대효과의 참여율(▼), 4 시·군 진단의 시·군(▼). 매크로 없음(목록 + 수식 + 조건부 서식 + 차트).
숫자 입력: 교수브리핑 수치.json · 시뮬레이션결과.json · 순차도입_검정력.json · 전국진단표.csv/json · 설문_집계.json ·
          성과도출_수치.json · 철도공사 방문소비갭.csv · 교수님_대시보드/data/시군_방문소비.csv · 시·군 경계 GeoJSON
디자인 기준: 도안 https://claude.ai/artifact/VdFf5s9xzTcEYVx5G6jQJr , docs/디자인.md 0장(데이터랩 파랑 + 차콜 + 회색)
출력: 보고서/요약대시보드/안동이어드림_요약대시보드.xlsx
"""
import json, math
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, Protection
from openpyxl.comments import Comment
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.hyperlink import Hyperlink
from openpyxl.formatting.rule import FormulaRule
from openpyxl.utils import get_column_letter as CL
from openpyxl.chart import BarChart, ScatterChart, Reference, Series
from openpyxl.chart.label import DataLabelList, DataLabel
from openpyxl.chart.marker import DataPoint
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.chart.series import SeriesLabel, StrRef
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.chart.text import RichText
from openpyxl.drawing.line import LineProperties
from openpyxl.drawing.spreadsheet_drawing import TwoCellAnchor, AnchorMarker
from openpyxl.drawing.text import Paragraph, ParagraphProperties, CharacterProperties, RichTextProperties, Font as DFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / '보고서/요약대시보드'
OUT.mkdir(parents=True, exist_ok=True)
J = lambda p: json.loads((ROOT / p).read_text(encoding='utf-8'))
Q = J('보고서/교수브리핑_20260922/수치.json')
SIM = J('보고서/성과도출_20260922/시뮬레이션결과.json')
PW = J('보고서/성과도출_20260922/순차도입_검정력.json')
S3 = J('보고서/성과도출_20260922/성과도출_수치.json')
PA = J('보고서/성과도출_20260922/파라미터추정.json')
DGJ = J('보고서/전국진단_20260923/전국진단.json')
SV = J('data/설문/설문_집계.json')
GEO = J('data/external/경계/skorea-municipalities-2018-geo.json')
SG = pd.read_csv(ROOT / '보고서/교수님_대시보드/data/시군_방문소비.csv')
DG = pd.read_csv(ROOT / '보고서/전국진단_20260923/전국진단표.csv')
RAIL = pd.read_csv(ROOT / 'data/external/철도공사_8대도시/안동_관광지_방문소비갭.csv')

# ═════════════ 숫자 (모두 앞단 결과에서 읽는다) ═════════════
E = Q['체험문화']
EX24, EX26 = E['안동_2024'], E['안동_2026']
MED = E['중앙_변화율'] / 100 if abs(E['중앙_변화율']) > 1 else E['중앙_변화율']          # 전국 중앙 변화율(비율)
EX_D = E['분포']                                                                       # 146곳 변화율(%)
NOW_RANK = E['안동_감소순위']
TARGET = EX24 * (1 + MED)                                                             # 전국 중앙만큼만 줄었을 때
GAP = TARGET - EX26
VIS = Q['방문']['변화율'] / 100
MB = Q['무박_연간']
BUS = Q['버스']['원도심→월영교']
JM = Q['주민증']
R1 = Q['반경1km업종']
OLD_FOOD, OLD_PUB = sum(R1['원도심'].values()), R1['원도심'].get('주점', 0)
WY_PUB = R1['월영교'].get('주점', 0)
st = Q['안동역_주말승차']; PEAK = max((k for k in st if int(k[:2]) >= 17), key=st.get)     # 저녁(17시 이후) 중 최다 = '18-19'. 하루 최다는 15-16시
PEAK_N = st[PEAK]
rail = RAIL.set_index('관광지명')
WY = rail.loc['월영교']; OLD_RATIO = rail.loc['안동문화의거리', '소비방문배율']


def find_list(o):
    """성과도출_수치.json 안에서 주민증 혜택업체별 이용 목록(공식분류·이용)을 찾는다."""
    if isinstance(o, list) and o and isinstance(o[0], dict) and '공식분류' in o[0] and '이용' in o[0]:
        return o
    if isinstance(o, dict):
        for v in o.values():
            r = find_list(v)
            if r: return r
    if isinstance(o, list):
        for v in o:
            r = find_list(v)
            if r: return r
    return None


def find_key(o, key):
    if isinstance(o, dict):
        if key in o: return o[key]
        for v in o.values():
            r = find_key(v, key)
            if r is not None: return r
    if isinstance(o, list):
        for v in o:
            r = find_key(v, key)
            if r is not None: return r
    return None


VIEW_SHARE = sum(u['이용'] for u in PA['A_업체'] if u['분류'] == '관람') / sum(u['이용'] for u in PA['A_업체'])   # 보고서그림.py 06과 같은 계산
JUNGGU = find_key(S3, '혜택배치_중구동')['방문점유율'] / 100

SC = SIM['시나리오']
NAMES = ('기준', '흥행', '목표')
P50 = lambda n, k: SC[n][k]['P50']


def ex_after(n):
    v = EX26 * (1 + P50(n, '지표1_증가율')); ch = (v / EX24 - 1) * 100
    return v, ch / 100, sum(1 for k, x in EX_D.items() if k != '안동시' and x < ch) + 1


NEED = SIM['임계값']['필요참여율_P50']['확대안']                                            # 격차 1/4·1/2·전부
PW50 = next(c['검정력'] for c in PW['확대안']['곡선'] if abs(c['효과'] - .5) < 1e-9)
sv = lambda k: SV[k]
SV_N, SV_V = SV['표본']['응답'], SV['표본']['3년내_방문_예']
DMED = DGJ['중앙값']
SAME = [s for s in DGJ['안동과_같은_유형'] if s != '안동시']

# 고정값(앞단 JSON에 없는 것): 출처를 메모로 단다
WY_OPEN, WY_21, WY_EARLY = 16, 3, 7          # 조사/16: 월영교 1km 영업 음식점 16곳, 21시까지 식사 3곳, 20:00~20:30 종료 7곳
BIS_ROUTES = 46                               # 안동시 버스정보시스템 노선 수(조사/01)
MANHYU, DOSAN = 54.8, 54.2                    # 철도공사 8대 도시 정독노트: 만휴정·도산서원 방문자의 월영교 동시 방문 비율
EXP_OPEN_EVENING = '문보트·황포돛배'           # 조사/03 체험 12곳 중 저녁까지 운영 확인
OLD_REST = 83                                 # 원도심 관광 식당 수(찜닭골목·문화의거리), 파라미터추정

# ═════════════ 스타일 ═════════════
FN = '맑은 고딕'
BLUE, DEEP, LIGHT, PALE = '2D6BD9', '1A4FA8', 'A8C4F0', 'EAF1FC'
INK, MUTE, LINE, TRACK, CARD, SOFT = '34383C', '6B7075', 'D5D9DC', 'ECEEF0', 'F6F7F8', '7FA6EC'
F = lambda sz=10.5, b=False, c=INK, i=False, u=None: Font(name=FN, size=sz, bold=b, color=c, italic=i, underline=u)
IF = lambda sz=10.5, b=False, c=INK: InlineFont(rFont=FN, sz=sz, b=b, color=c)
FILL = lambda c: PatternFill('solid', fgColor=c)
AL = lambda h='left', v='center', w=True, ind=0: Alignment(horizontal=h, vertical=v, wrap_text=w, indent=ind)
S_ = lambda c, s='thin': Side(style=s, color=c)
MINUS = lambda s: s.replace('-', '−')


def grid(ws, n, w):
    ws.column_dimensions['A'].width = 2.5
    for c in range(2, 2 + n):
        ws.column_dimensions[CL(c)].width = w
    ws.sheet_view.showGridLines = False
    ws.sheet_view.showRowColHeaders = False
    ws.sheet_view.zoomScale = 100


def H(ws, r, pt):
    ws.row_dimensions[r].height = pt


def M(ws, r, c1, c2=None, v=None, font=None, al=None, fill=None, fmt=None, r2=None, border=None):
    """(r, c1)~(r2, c2) 칸에 값을 쓰고 합친다. 스타일은 합치기 전에 첫 칸에 준다."""
    c2 = c2 or c1; r2 = r2 or r
    cell = ws.cell(r, c1)
    if v is not None: cell.value = v
    cell.font = font or F()
    cell.alignment = al or AL()
    if fill: cell.fill = FILL(fill)
    if fmt: cell.number_format = fmt
    if border: cell.border = border
    if c2 > c1 or r2 > r:
        ws.merge_cells(start_row=r, start_column=c1, end_row=r2, end_column=c2)
    return cell


def rich(*parts):
    return CellRichText(*[TextBlock(IF(*p[1:]), p[0]) for p in parts])


def memo(cell, text, w=280, h=110):
    c = Comment(text, '안동 이어드림'); c.width, c.height = w, h
    cell.comment = c


def hline(ws, r, c1, c2, color=LINE, style='thin', top=False):
    for c in range(c1, c2 + 1):
        b = ws.cell(r, c).border
        ws.cell(r, c).border = Border(left=b.left, right=b.right, top=S_(color, style) if top else b.top, bottom=b.bottom if top else S_(color, style))


def vline(ws, r1, r2, c, color=LINE, style='thin'):
    for r in range(r1, r2 + 1):
        b = ws.cell(r, c).border
        ws.cell(r, c).border = Border(left=S_(color, style), right=b.right, top=b.top, bottom=b.bottom)


def link(ws, r, c1, c2, text, sheet, h='right'):
    cell = M(ws, r, c1, c2, text, F(10.5, True, DEEP), AL(h, 'center', False))
    cell.hyperlink = Hyperlink(ref=cell.coordinate, location=f"'{sheet}'!A1", display=text)
    return cell


def circle(ws, r, c, n, fill=BLUE, fg='FFFFFF'):
    M(ws, r, c, c, n, F(11, True, fg), AL('center', 'center', False), fill)


def header(ws, label, title, sub, subw=37, right_note=None):
    H(ws, 1, 12)
    M(ws, 2, 2, 24, label, F(10, True, DEEP), AL('left', 'bottom', False)); H(ws, 2, 20)
    M(ws, 3, 2, 28, title, F(22, True, INK), AL('left', 'center', False)); H(ws, 3, 38)
    M(ws, 4, 2, subw, sub, F(10.5, False, MUTE), AL('left', 'center', False)); H(ws, 4, 20)
    H(ws, 5, 4)
    for c in (2, 3): ws.cell(5, c).fill = FILL(BLUE)
    if right_note:
        M(ws, 4, subw + 1, 37, right_note, F(9.5, False, MUTE), AL('right', 'center', False))


def note_mark(ws, r, c1, c2, text):
    """빨간 삼각형 안내(엑셀 메모 표시와 같은 색)."""
    M(ws, r, c1, c2, rich(('◥ ', 9, False, 'D64541'), (text, 9.5, False, MUTE)), al=AL('right', 'center', False))


def tile(ws, r, c1, c2, label, value, fmt, sub, color=INK, memo_text=None, divider=True, vsz=26):
    ind = 1 if divider else 0
    M(ws, r, c1, c2, label, F(10.5, False, MUTE), AL('left', 'bottom', False, ind))
    v = M(ws, r + 1, c1, c2, value, F(vsz, True, color), AL('left', 'center', False, ind), fmt=fmt)
    M(ws, r + 2, c1, c2, sub, F(9.5, False, MUTE), AL('left', 'top', True, ind))
    if divider: vline(ws, r, r + 2, c1)
    if memo_text: memo(v, memo_text)
    return v


def protect(ws, unlocked=()):
    for ref in unlocked:
        ws[ref].protection = Protection(locked=False)
    ws.protection.sheet = True
    ws.protection.formatColumns = True
    ws.protection.formatRows = True


def printing(ws, last_col, last_row):
    ws.print_area = f'A1:{CL(last_col)}{last_row}'
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 1
    ws.page_margins.left = ws.page_margins.right = 0.3
    ws.page_margins.top = ws.page_margins.bottom = 0.3


# ── 차트 공통 ──
def txp(sz=900, color=MUTE, b=False):
    cp = CharacterProperties(sz=sz, b=b, solidFill=color, latin=DFont(typeface=FN), ea=DFont(typeface=FN))
    return RichText(bodyPr=RichTextProperties(), p=[Paragraph(pPr=ParagraphProperties(defRPr=cp), endParaRPr=cp)])


def gp(fill=None, line=None, w=None, dash=None, nofill=False, noline=False):
    g = GraphicalProperties()
    if nofill: g.noFill = True
    elif fill: g.solidFill = fill
    ln = LineProperties()
    if noline: ln.noFill = True
    elif line:
        ln.solidFill = line
        if w: ln.w = int(w * 12700)
        if dash: ln.prstDash = dash
    g.ln = ln
    return g


def bare(ch, w_cm, h_cm):
    ch.legend = None
    ch.width, ch.height = w_cm, h_cm
    ch.graphical_properties = gp(nofill=True, noline=True)
    ch.plot_area.graphicalProperties = gp(nofill=True, noline=True)
    ch.roundedCorners = False
    return ch


def full_plot(ch, x=0.0, y=0.0, w=1.0, h=1.0):
    ch.plot_area.layout = Layout(manualLayout=ManualLayout(x=x, y=y, w=w, h=h, xMode='edge', yMode='edge'))


def labels(ser_name=False, val=False, cat=False, pos=None, sz=900, color=INK, b=True, fmt=None):
    d = DataLabelList(showSerName=ser_name, showVal=val, showCatName=cat, showLegendKey=False, showPercent=False)
    d.txPr = txp(sz, color, b)
    if pos: d.position = pos
    if fmt: d.numFmt = fmt
    return d


def hide_axis(ax):
    ax.delete = True
    ax.majorGridlines = None


def show_axis(ax, sz=900, line=LINE):
    ax.delete = False
    ax.majorGridlines = None
    ax.txPr = txp(sz, MUTE)
    ax.graphicalProperties = gp(line=line, w=0.75)


def place(ws, ch, c1, r1, c2, r2):
    """차트를 칸 범위(c1~c2열, r1~r2행)에 묶는다. 맥·윈도 엑셀의 열 너비 차이에도 칸 안에 머문다."""
    ch.anchor = TwoCellAnchor(editAs='twoCell', _from=AnchorMarker(col=c1 - 1, row=r1 - 1), to=AnchorMarker(col=c2, row=r2))
    ws.add_chart(ch)


def ref_title(sheet, cell):
    return SeriesLabel(strRef=StrRef(f"'{sheet}'!{cell}"))


wb = Workbook()
S_HOME, S_P, S_S, S_E, S_D, S_SRC = '한눈에', '1 문제', '2 해법', '3 기대효과', '4 시·군 진단', '출처'
wsH = wb.active; wsH.title = S_HOME
wsP = wb.create_sheet(S_P); wsS = wb.create_sheet(S_S); wsE = wb.create_sheet(S_E); wsD = wb.create_sheet(S_D); wsR = wb.create_sheet(S_SRC)


def data_sheet(name):
    ws = wb.create_sheet(name); ws.sheet_state = 'hidden'
    return ws


# ═════════════ 숨긴 데이터 시트 ═════════════
# d_시군: 146곳 방문·체험·문화 (문제 화면)
dS = data_sheet('d_시군')
sg = SG.sort_values('체험문화_변화율').reset_index(drop=True)
dS.append(['시군', '방문_변화율', '체험문화_2024', '체험문화_2026', '체험문화_변화율', '감소순위'])
for i, r in sg.iterrows():
    dS.append([r['시군'], r['방문_변화율'], r['체험문화_2024'], r['체험문화_2026'], r['체험문화_변화율'], i + 1])
nS = len(sg) + 1
AND_S = lambda col: f"INDEX('d_시군'!${col}$2:${col}${nS},MATCH(\"안동시\",'d_시군'!$A$2:$A${nS},0))"
assert int(sg.index[sg['시군'] == '안동시'][0]) + 1 == NOW_RANK

# d_문제: 막대(안동 vs 전국 중앙)
dPb = data_sheet('d_문제')
dPb.append(['구분', '변화율'])
dPb.append(['안동시', f"={AND_S('E')}"])
dPb.append(['전국 중앙', f"=MEDIAN('d_시군'!$E$2:$E${nS})"])
for rr in (2, 3): dPb.cell(rr, 2).number_format = '+0.0%;−0.0%'

# d_시나리오: 참여율 3단계 (서식4와 같은 값)
dC = data_sheet('d_시나리오')
dC.append(['목록', '참여율', '100명중', '새이동_하루', '체험소비_후', '변화율_후', '순위_후', '추가소비_억', '인증_월'])
OPTS = [f'{n}(100명 중 {SC[n]["참여율"] * 100:.0f}명)' for n in NAMES]
for n, o in zip(NAMES, OPTS):
    v, ch, rk = ex_after(n)
    dC.append([o, SC[n]['참여율'], SC[n]['참여율'] * 100, P50(n, '새이동_하루'), v, ch, rk, P50(n, '추가소비합') / 1e8, P50(n, '인증_월')])
# 6행~: 지금 고른 값 (3 기대효과!AC3 = 목록 칸)
SEL_C = f"'{S_E}'!$AC$3"
dC['A6'] = '고른 순서'; dC['B6'] = f"=MATCH({SEL_C},$A$2:$A$4,0)"
for i, (lab, col) in enumerate([('100명중', 'C'), ('새이동_하루', 'D'), ('체험소비_후', 'E'), ('변화율_후', 'F'), ('순위_후', 'G'), ('추가소비_억', 'H')]):
    dC.cell(7 + i, 1, lab); dC.cell(7 + i, 2, f"=INDEX(${col}$2:${col}$4,$B$6)")
dC['A13'] = '순위 이름표'; dC['B13'] = '="시행 후 "&B11&"위"'
dC['A14'] = '자 이름표'; dC['B14'] = '="시행 후 "&TEXT(B9,"0.0")&"원"'
C_N, C_MOVE, C_SPEND, C_CHG, C_RANK, C_WON = ("'d_시나리오'!$B$7", "'d_시나리오'!$B$8", "'d_시나리오'!$B$9",
                                              "'d_시나리오'!$B$10", "'d_시나리오'!$B$11", "'d_시나리오'!$B$12")

# d_순위: 146곳 순위 띠 (문제·기대효과)
dR = data_sheet('d_순위')
dR.append(['순위', '나머지', '더많이줄어듦', '안동_지금', '가운데', '안동_시행후', '전체', '문제_이름표', '효과_이름표', '문제_높이', '효과_높이'])
MID = (len(EX_D) + 1) // 2
for k in range(1, len(EX_D) + 1):
    r = k + 1
    lab_p = f'안동 {NOW_RANK}위' if k == NOW_RANK else (f'가운데 {MID}위' if k == MID else '')
    lab_e = f'지금 {NOW_RANK}위' if k == NOW_RANK else (f'가운데 {MID}위' if k == MID else '')
    h_ = 2.2 if k == NOW_RANK else (1.6 if k == MID else 0)
    dR.append([k, 1 if (k > NOW_RANK and k != MID) else '=NA()', 1 if k < NOW_RANK else '=NA()',
               2.2 if k == NOW_RANK else '=NA()', 1.6 if k == MID else '=NA()',
               f"=IF(A{r}={C_RANK},2.4,NA())", 1, lab_p,
               f'=IF(A{r}={C_RANK},"시행 후 "&A{r}&"위","{lab_e}")', h_,
               f"=IF(A{r}={C_RANK},3.1,{h_})"])
nR = len(EX_D) + 1

# d_자: 기대효과 점 그림 (x, y)
dX = data_sheet('d_자')
dX.append(['계열', 'x', 'y'])
rows_x = [('트랙', 140, 1), ('트랙', 190, 1),                           # 2,3
          ('전국 중앙 수준', round(TARGET, 1), 0.45), ('전국 중앙 수준', round(TARGET, 1), 1.55),   # 4,5
          ('2024년', round(EX24, 1), 1),                                  # 6
          ('연결', round(EX26, 1), 1), ('연결', f"={C_SPEND}", 1),         # 7,8
          ('지금', round(EX26, 1), 1),                                    # 9
          ('시행 후', f"={C_SPEND}", 1)]                                   # 10
for row in rows_x: dX.append(list(row))
dX['E1'] = '이름표'
dX['E4'] = f'전국 중앙 수준 {TARGET:.1f}원'; dX['E6'] = f'2024년 {EX24:.1f}원'; dX['E9'] = f'지금 {EX26:.1f}원'

# d_진단: 144곳 (시·군 진단)
dD = data_sheet('d_진단')
LAB = {'체험문화': '체험·문화', '평균숙박일수': '숙박일수', '저녁전환율': '저녁 전환', '야간방문비중': '야간 방문'}


def tlabel(t):
    if not isinstance(t, str) or t.strip() in ('', '-'): return ''
    return ' · '.join(LAB.get(x.strip(), x.strip()) for x in t.split('·'))


def jong(w):
    c = ord(w[-1]) - 0xAC00
    return 0 <= c <= 11171 and c % 28 != 0


sgi = SG.set_index('시군')
rank146 = {r['시군']: i + 1 for i, r in sg.iterrows()}
dD.append(['시군', '짧은이름', '와과', '은는', '체험변화', '숙박일수', '저녁전환', '야간비중', 'p1', 'p2', 'p3', 'p4',
           '점수', '순위', '유형', '유형표시', '146순위', '방문변화', '정렬키'])
for i, r in DG.iterrows():
    nm = r['시군']; short = nm[:-1] if len(nm) > 2 and nm[-1] in '시군' else nm
    t = tlabel(r['유형'])
    rr = i + 2
    dD.append([nm, short, '과' if jong(short) else '와', '은' if jong(short) else '는',
               r['①체험문화_변화율'], r['②평균숙박일수'], r['③저녁전환율'], r['④야간방문비중'],
               r['①체험문화_변화율_문제백분위'], r['②평균숙박일수_문제백분위'], r['③저녁전환율_문제백분위'], r['④야간방문비중_문제백분위'],
               r['진단점수'], int(r['순위']), t, t or '문제 지표 없음', rank146.get(nm), sgi.loc[nm, '방문_변화율'] if nm in sgi.index else None,
               f"=IF(P{rr}='d_선택'!$B$9,E{rr}+ROW()/1E9,\"\")"])
nD = len(DG) + 1
DR = lambda col: f"'d_진단'!${col}$2:${col}${nD}"

# d_목록: 시·군 가나다순 (목록 칸)
dL = data_sheet('d_목록')
dL.append(['시군'])
for nm in sorted(DG['시군']): dL.append([nm])

# d_선택: 고른 시·군의 값 (4 시·군 진단!AC3 = 목록 칸)
dSel = data_sheet('d_선택')
SEL_D = f"'{S_D}'!$AC$3"
look = lambda col: f"INDEX({DR(col)},$B$3)"
sel_rows = [
    ('고른 시군', f"={SEL_D}"),                                   # B2
    ('행', f"=MATCH(B2,{DR('A')},0)"),                            # B3
    ('짧은이름', f"={look('B')}"), ('와과', f"={look('C')}"), ('은는', f"={look('D')}"),   # B4-6
    ('유형', f"={look('O')}"), ('유형없음표시', f"=IF(B7=\"\",\"없음\",B7)"),              # B7-8
    ('유형표시', f"={look('P')}"),                                # B9
    ('같은유형수', f"=COUNTIF({DR('P')},B9)"),                     # B10
    ('제목', '=IF(B7="",B4&B6&" 네 지표 모두 문제 구간 밖",IF(B10=1,B4&B5&" 같은 유형은 이곳뿐",B4&B5&" 같은 문제를 가진 곳 전국 "&(B10-1)&"곳"))'),  # B11
    ('체험변화', f"={look('E')}"), ('숙박', f"={look('F')}"), ('저녁', f"={look('G')}"), ('야간', f"={look('H')}"),    # B12-15
    ('p1', f"={look('I')}"), ('p2', f"={look('J')}"), ('p3', f"={look('K')}"), ('p4', f"={look('L')}"),            # B16-19
    ('점수', f"={look('M')}"), ('순위', f"={look('N')}"), ('146순위', f"={look('Q')}"), ('방문변화', f"={look('R')}"),  # B20-23
    ('내 정렬키', f"={look('S')}"), ('유형 안 순서', f"=COUNTIF({DR('S')},\"<\"&B24)+1"),                            # B24-25
    ('목록 제목', '=IF(B7="","문제 구간 밖인 곳 "&B10&"곳","같은 유형 "&B10&"곳")'),                                    # B26
    ('더 있음', '=IF(B10>8,"외 "&(B10-8)&"곳","")'),                                          # B27
    ('네 지표 제목', '=B4&"의 네 지표"'),                                                                              # B28
    ('유형 설명', '=B4&"의 유형("&B9&")은 144곳 중 "&B10&"곳이 같다."'),                                               # B29
]
dSel.append(['항목', '값'])
for lab, f_ in sel_rows: dSel.append([lab, f_])
SL = lambda r: f"'d_선택'!$B${r}"
# 같은 유형 목록 8줄 (행 32~39)
dSel['A31'] = '순서'; dSel['B31'] = '시군'; dSel['C31'] = '체험변화'; dSel['D31'] = '숙박'; dSel['E31'] = '점위치'
for k in range(1, 9):
    r = 31 + k
    dSel.cell(r, 1, k)
    name_f = (f'=IF({k}>$B$10,"",IF(AND({k}=8,$B$25>8),$B$2,INDEX({DR("A")},MATCH(SMALL({DR("S")},{k}),{DR("S")},0))))')
    dSel.cell(r, 2, name_f)
    dSel.cell(r, 3, f'=IF(B{r}="","",INDEX({DR("E")},MATCH(B{r},{DR("A")},0)))')
    dSel.cell(r, 4, f'=IF(B{r}="","",INDEX({DR("F")},MATCH(B{r},{DR("A")},0)))')
    dSel.cell(r, 5, f'=IF(B{r}="","",INT((MAX(-0.5999,MIN(0.5999,C{r}))+0.6)/0.1))')

# d_유형: 144곳 유형 분포 (막대: 오름차순이면 가장 큰 유형이 위)
dT = data_sheet('d_유형')
cnt = DG.assign(t=DG['유형'].map(lambda x: tlabel(x) or '문제 지표 없음'))['t'].value_counts().sort_values()
dT.append(['유형', '곳', '고른 유형'])
for i, (t, n) in enumerate(cnt.items()):
    dT.append([t, int(n), f"=IF(A{i + 2}={SL(9)},B{i + 2},NA())"]); dT.cell(i + 2, 2).number_format = '0"곳"'
nT = len(cnt) + 1

# d_지도, d_경계: 시·군 경계(윤곽선) + 중심점(색 점)
W_, lon0, lon1, lat0, lat1 = 560.0, 124.6, 131.0, 33.1, 38.65
c36 = math.cos(math.radians(36)); K = W_ / ((lon1 - lon0) * c36); H_ = (lat1 - lat0) * K
proj = lambda x, y: ((x - lon0) * c36 * K, (y - lat0) * K)          # y 위쪽이 북쪽


def rdp(pts, eps):
    keep = [False] * len(pts); keep[0] = keep[-1] = True; stack = [(0, len(pts) - 1)]
    while stack:
        s, e = stack.pop(); a, b = pts[s], pts[e]; dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
        im, dm = -1, 0.0
        for j in range(s + 1, e):
            p = pts[j]
            d = abs(dy * p[0] - dx * p[1] + b[0] * a[1] - b[1] * a[0]) / L if L > 1e-9 else math.hypot(p[0] - a[0], p[1] - a[1])
            if d > dm: im, dm = j, d
        if dm > eps:
            keep[im] = True; stack += [(s, im), (im, e)]
    return [p for p, k in zip(pts, keep) if k]


ALIAS = {'세종특별자치시': '세종시'}
cen, rings = {}, []
for f in GEO['features']:
    nm = ALIAS.get(f['properties']['name'], f['properties']['name'])
    g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    for poly in polys:
        ring = [proj(x, y) for x, y in poly[0]]
        ar = abs(sum(ring[i][0] * ring[i - 1][1] - ring[i - 1][0] * ring[i][1] for i in range(len(ring)))) / 2
        if ar < 2.0: continue
        s = rdp(ring, 0.9)
        if len(s) >= 4: rings.append(s)
        if nm not in cen or ar > cen[nm][0]:
            cen[nm] = (ar, sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring))
diag_names = set(DG['시군'])
assert diag_names <= set(cen), diag_names - set(cen)
dB = data_sheet('d_경계')
dB.append(['x', 'y'])
for s in rings:
    for x, y in s: dB.append([round(x, 1), round(y, 1)])
    dB.append([None, None])
nB = dB.max_row
dM = data_sheet('d_지도')
dM.append(['시군', 'x', 'y', '진단대상', '유형표시', '진단제외', '다른진단대상', '같은유형', '고른곳'])
for i, (nm, (_, x, y)) in enumerate(sorted(cen.items())):
    r = i + 2
    t = (tlabel(DG.loc[DG['시군'] == nm, '유형'].iloc[0]) or '문제 지표 없음') if nm in diag_names else ''
    dM.append([nm, round(x, 1), round(y, 1), 1 if nm in diag_names else 0, t,
               f"=IF(D{r}=0,C{r},NA())",
               f"=IF(AND(D{r}=1,E{r}<>{SL(9)},A{r}<>{SL(2)}),C{r},NA())",
               f"=IF(AND(D{r}=1,E{r}={SL(9)},A{r}<>{SL(2)}),C{r},NA())",
               f"=IF(A{r}={SL(2)},C{r},NA())"])
nM = len(cen) + 1

# ═════════════ 한눈에 ═════════════
ws = wsH; grid(ws, 36, 5.2)
header(ws, '안동 이어드림 · 데이터 대시보드',
       rich(('원도심에서 도는 돈과 월영교에 모이는 사람을 ', 22, True, INK), ('밤까지 잇는다', 22, True, BLUE)),
       '디지털 관광주민증 위 3단계 릴레이. 아래 칸을 누르면 그 화면으로 간다. 모든 효과는 시행 전 예측이다.')
H(ws, 6, 22)
cards = [(2, 12, '01 문제', S_P, '방문 1회당 체험·문화 소비', f"={AND_S('E')}", '+0.0%;−0.0%',
          [f'146개 시·군 중 {NOW_RANK}번째로 많이 줄었다', f'전국 중앙 {MINUS(f"{MED * 100:+.1f}")}%'],
          '빈 곳 세 군데: 1 원도심 혜택 0곳 · 2 19시 이후 버스 0회 · 3 월영교 주점 0곳'),
         (14, 24, '03 기대효과', S_E, '100명 중 2명 참여 시 방문당 체험·문화 소비', "='d_시나리오'!$E$2", '0.0"원"',
          [f'지금 {EX26:.1f}원에서 +{P50("기준", "지표1_증가율") * 100:.1f}%', f'월영교 저녁 이동 주말 하루 {P50("기준", "새이동_하루"):.0f}명'],
          '시행 전 예측. 참여율은 2명 · 4명 · 10명 중에서 고른다'),
         (26, 37, '04 우리 시·군 진단', S_D, '안동과 같은 문제 유형', f"=COUNTIF({DR('P')},\"체험·문화 · 숙박일수\")-1", '0"곳"',
          ['체험·문화 소비 하락 + 짧은 숙박', ' · '.join(s[:-1] for s in SAME)],
          f'시·군을 고르면 그 지역 진단이 한 장으로. 주민증 운영 {JM["운영지역수"]}개 지자체에 적용 가능')]
for r_, h_ in zip(range(7, 16), (26, 20, 52, 20, 20, 10, 40, 24, 8)): H(ws, r_, h_)
for c1, c2, lab, sheet, desc, val, fmt, lines, foot in cards:
    for r_ in range(7, 16):
        for c in range(c1, c2 + 1): ws.cell(r_, c).fill = FILL(CARD)
    a = M(ws, 7, c1, c2, lab, F(10, True, DEEP), AL('left', 'bottom', False, 1), CARD)
    a.hyperlink = Hyperlink(ref=a.coordinate, location=f"'{sheet}'!A1", display=lab)
    M(ws, 8, c1, c2, desc, F(10, False, MUTE), AL('left', 'center', False, 1), CARD)
    M(ws, 9, c1, c2, val, F(30, True, BLUE), AL('left', 'center', False, 1), CARD, fmt)
    M(ws, 10, c1, c2, lines[0], F(10.5), AL('left', 'center', False, 1), CARD)
    M(ws, 11, c1, c2, lines[1], F(10.5), AL('left', 'center', False, 1), CARD)
    hline(ws, 12, c1, c2, LINE)
    M(ws, 13, c1, c2, foot, F(9.5, False, MUTE), AL('left', 'center', True, 1), CARD)
    lk = M(ws, 14, c1, c2, '열기 →', F(10, True, DEEP), AL('left', 'center', False, 1), CARD)
    lk.hyperlink = Hyperlink(ref=lk.coordinate, location=f"'{sheet}'!A1", display='열기 →')
for c in (13, 25):
    M(ws, 9, c, c, '›', F(28, True, LIGHT), AL('center', 'center', False))
H(ws, 16, 26)
M(ws, 17, 2, 26, rich(('02 해법 · 릴레이 3단계  ', 11, True, INK), ('번호는 문제 화면의 빈 곳 번호와 같다', 10, False, MUTE)), al=AL('left', 'center', False))
link(ws, 17, 27, 37, '운영값과 근거 → 2 해법', S_S)
H(ws, 17, 22); H(ws, 18, 6); H(ws, 19, 46)
relay = [(2, 13, 1, '낮 · 원도심', f'식당 {OLD_REST}곳에서 식사 → 체험 10% 할인'),
         (14, 25, 2, '저녁 18:30~21:00', '원도심 → 월영교 택시, 늘면 셔틀'),
         (26, 37, 3, '밤 · 월영교', '문보트 + 21시 이후 식사·주점 팝업')]
for c1, c2, n, t1, t2 in relay:
    circle(ws, 19, c1, n)
    M(ws, 19, c1 + 1, c2 - 1 if c2 < 37 else c2, rich((t1 + '\n', 10.5, True, INK), (t2, 10, False, INK)), al=AL('left', 'center', True, 1), fill=PALE)
H(ws, 20, 20)
M(ws, 21, 2, 37, '쓰는 법', F(10.5, True)); H(ws, 21, 20)
tips = ['· 파란 칸(▼)을 누르면 목록에서 고를 수 있다. 3 기대효과는 참여율, 4 시·군 진단은 시·군을 고른다.',
        '· 숫자 오른쪽 위 빨간 삼각형에 마우스를 올리면 출처와 계산 방법이 보인다.',
        '· 처음 열었을 때의 숫자(참여 2%, 안동시)가 서식4에 쓴 숫자와 같다. 화면 아래 시트 탭으로도 이동할 수 있다.']
for i, t in enumerate(tips):
    M(ws, 22 + i, 2, 37, t, F(10), AL('left', 'center', False)); H(ws, 22 + i, 18)
H(ws, 25, 12)
M(ws, 26, 2, 37, f'출처: 한국관광 데이터랩, 한국철도공사, 코레일, 소상공인 상가정보, 안동시 버스정보시스템·주민증 자료, 팀 온라인 설문 {SV_N}명. 자세한 목록은 「출처」 시트.',
  F(9, False, MUTE), AL('left', 'center', False))
printing(ws, 37, 27)

# ═════════════ 1 문제 ═════════════
ws = wsP; grid(ws, 36, 5.2)
header(ws, '01 문제', rich(('방문은 늘었는데 ', 22, True, INK), ('체험·문화 소비는 줄었다', 22, True, BLUE)),
       '외지인 기준, 2024년 1~8월과 2026년 같은 기간 비교. 안동 숫자 옆에는 늘 전국 중앙값을 같이 둔다.', subw=25)
note_mark(ws, 4, 26, 37, '빨간 삼각형 숫자에 마우스를 올리면 출처')
H(ws, 6, 20); H(ws, 7, 20); H(ws, 8, 44); H(ws, 9, 20)
tile(ws, 7, 2, 12, '외지인 방문', f"={AND_S('B')}", '+0.0%;−0.0%',
     f'당일 방문 비중은 {MB["2019"]:.1f} → {MB["2025"]:.1f}%로 그대로 (2019 → 2025년)', INK,
     '외지인 방문 연인원(데이터랩 BDT_01_01_006), 2024년 1~8월 → 2026년 1~8월. 당일 방문(무박) 비중은 2019년과 2025년 비교', divider=False)
tile(ws, 7, 14, 24, '방문 1회당 체험·문화 소비', f"={AND_S('E')}", '+0.0%;−0.0%',
     f'{EX24:.1f}원 → {EX26:.1f}원 · 전국 중앙 {MINUS(f"{MED * 100:+.1f}")}%', BLUE,
     '외지인 신용카드 소비(데이터랩 BDT_02_01_003) 중 문화서비스·관광유원시설·기타레저(골프·스키·여행업·레저용품 쇼핑 제외) ÷ 외지인 방문 연인원(BDT_01_01_006)')
tile(ws, 7, 26, 37, '146개 시·군 중 감소폭', f"={AND_S('F')}", '0"위"', '1위 = 가장 많이 줄어든 곳', BLUE,
     f'같은 방식으로 계산한 {len(EX_D)}개 시·군의 변화율을 작은 순서로 세운 순위. 전국 중앙값 {MINUS(f"{MED * 100:+.1f}")}%')
H(ws, 10, 26)
M(ws, 11, 2, 18, '변화율, 안동과 전국 중앙', F(10.5, True)); M(ws, 11, 21, 37, f'{len(EX_D)}개 시·군을 감소폭 순서로 세우면', F(10.5, True)); H(ws, 11, 22)
for r_ in range(12, 20): H(ws, r_, 20)
ch = BarChart(); ch.type = 'bar'; ch.grouping = 'clustered'; ch.gapWidth = 60
s = Series(Reference(dPb, min_col=2, min_row=2, max_row=3), title='변화율')
for idx, col in ((0, BLUE), (1, INK)):
    pt = DataPoint(idx=idx, invertIfNegative=False); pt.graphicalProperties = gp(fill=col, noline=True); s.dPt.append(pt)
s.invertIfNegative = False
s.dLbls = labels(val=True, pos='outEnd', sz=1000)
ch.series.append(s)
ch.set_categories(Reference(dPb, min_col=1, min_row=2, max_row=3))
ch.x_axis.scaling.orientation = 'maxMin'
show_axis(ch.x_axis, 1000); ch.x_axis.tickLblPos = 'low'
show_axis(ch.y_axis, 900); ch.y_axis.scaling.min = -0.2; ch.y_axis.scaling.max = 0; ch.y_axis.majorUnit = 0.05
ch.y_axis.number_format = '0%;−0%'
bare(ch, 16.5, 5.6)
place(ws, ch, 2, 12, 18, 19)


def rank_strip(ws, box, cols, w, h, now_name, after=False):
    ch = BarChart(); ch.type = 'col'; ch.grouping = 'clustered'; ch.overlap = 100; ch.gapWidth = 40
    spec = [(2, '나머지', LINE), (3, '더 많이 줄어든 곳', LIGHT)] if not after else [(7, '전체', LINE)]
    spec += [(5, f'가운데 {MID}위', INK), (4, now_name, BLUE if not after else INK)]
    if after: spec.append((6, '시행 후', BLUE))
    spec.append((11 if after else 10, '이름표', None))                  # 투명 막대 + 범주 글자 = 이름표
    for col, name, color in spec:
        s = Series(Reference(dR, min_col=col, min_row=2, max_row=nR), title=name)
        if color: s.graphicalProperties = gp(fill=color, noline=True)
        else:
            s.graphicalProperties = gp(nofill=True, noline=True)
            s.dLbls = labels(cat=True, pos='outEnd', sz=950, color=DEEP if after else INK)
        ch.series.append(s)
    ch.set_categories(Reference(dR, min_col=9 if after else 8, min_row=2, max_row=nR))
    hide_axis(ch.x_axis); hide_axis(ch.y_axis); ch.y_axis.scaling.min = 0; ch.y_axis.scaling.max = 3.9
    bare(ch, w, h); full_plot(ch, 0, 0.05, 1, 0.95)
    place(ws, ch, *box)


rank_strip(ws, (21, 12, 37, 18), None, 16.8, 5.2, f'안동 {NOW_RANK}위')
M(ws, 19, 21, 29, '← 1위 가장 많이 줄어듦', F(9, False, MUTE), AL('left', 'center', False))
M(ws, 19, 30, 37, f'{len(EX_D)}위 →', F(9, False, MUTE), AL('right', 'center', False))
H(ws, 20, 26)
M(ws, 21, 2, 37, rich(('데이터가 가리키는 빈 곳 세 군데  ', 10.5, True, INK), ('번호는 해법·기대효과 화면의 번호와 같다', 10, False, MUTE)), al=AL('left', 'center', False)); H(ws, 21, 22)
H(ws, 22, 6); hline(ws, 22, 2, 37, LINE); H(ws, 23, 10)
clues = [(2, 12, 1, '원도심 (중구동)', '혜택 업체 0곳',
          f'외지인 방문의 {JUNGGU * 100:.1f}%로 읍면동 1위. 주민증 혜택 이용의 {VIEW_SHARE * 100:.0f}%는 관람지에서 생긴다', '',
          f'읍면동 외지인 방문 점유율: 데이터랩(2026년 1~8월). 혜택 업체: 안동시 디지털관광주민증 혜택업체 {JM["혜택업체"]}곳 주소(정보공개청구). 관람 비중: 주민증 혜택업체별 이용 실적'),
         (14, 24, 2, f'원도심 → 월영교 {Q["원도심_월영교_km"]:.1f}km', f'19시 이후 버스 {BUS["19시이후"]}회',
          f'잇는 시내버스는 112번 한 노선, 원도심 출발 막차 {BUS["막차"]}(평일)', '',
          f'안동시 버스정보시스템 {BIS_ROUTES}개 노선 시간표. 원도심과 월영교를 잇는 노선은 112번 하나'),
         (26, 37, 3, '월영교 반경 1km', f'주점 {WY_PUB}곳',
          f'영업 음식점 {WY_OPEN}곳 중 21시까지 식사 {WY_21}곳. 방문 점유율 {WY["방문점유율_pct"]:.2f}% 대비 소비 건수 {WY["방문객소비건수점유율_pct"]:.2f}%',
          '[철도공사 2022.4~6]',
          '음식점: 소상공인 상가(상권)정보 2026.6. 영업 종료 시각: 팀 확인(조사 16번, 조사일 기록 보완 중). 방문·소비 점유율: 한국철도공사 8대 도시 가명결합 분석(2022.4~6, 소비 = 건수)이라 데이터랩 숫자와 따로 본다')]
H(ws, 24, 20); H(ws, 25, 32); H(ws, 26, 40); H(ws, 27, 18)
for c1, c2, n, where, fact, detail, chip, mm in clues:
    circle(ws, 24, c1, n)
    M(ws, 24, c1 + 1, c2, where, F(10, False, MUTE), AL('left', 'center', False, 1))
    v = M(ws, 25, c1 + 1, c2, fact, F(18, True), AL('left', 'center', False, 1)); memo(v, mm, 300, 130)
    M(ws, 26, c1 + 1, c2, detail, F(10), AL('left', 'top', True, 1))
    if chip: M(ws, 27, c1 + 1, c2, chip, F(9, False, MUTE), AL('left', 'center', False, 1))
H(ws, 28, 24)
M(ws, 29, 2, 28, '감소분의 약 3분의 2는 문화서비스 업종의 계단식 하락이다. 원인은 단정하지 않는다.', F(9.5, False, MUTE), AL('left', 'center', False)); H(ws, 29, 18)
M(ws, 30, 2, 28, '출처: 한국관광 데이터랩 외지인 신용카드 소비(업종 중분류) ÷ 외지인 방문 연인원, 2024·2026년 1~8월', F(9.5, False, MUTE), AL('left', 'center', False)); H(ws, 30, 18)
link(ws, 29, 29, 37, '세 곳을 어떻게 잇나 → 2 해법', S_S)
printing(ws, 37, 31)

# ═════════════ 2 해법 (15분 = 1칸 시간 격자) ═════════════
ws = wsS; grid(ws, 44, 4.0)
col_t = lambda h: 2 + round((h - 12) * 4)                     # 12:00 = B열, 15분 = 1칸
header(ws, '02 해법', rich(('원도심의 돈과 월영교의 사람을 ', 22, True, INK), ('밤까지 잇는 3단계', 22, True, BLUE)),
       '디지털 관광주민증 위 릴레이. 곳 수·시간·혜택은 데이터로 정했고, 아직 정하지 못한 값은 따로 적었다.', subw=45)
H(ws, 6, 18)
hubs = [(2, 19, '원도심', '돈이 도는 곳', [
            (f'{JUNGGU * 100:.1f}%', '외지인 방문 읍면동 1위(중구동)', '데이터랩 2026.1~8'),
            (f'{OLD_FOOD}곳', f'반경 1km 음식점, 이 중 주점 {OLD_PUB}곳', '상가정보 2026.6'),
            (f'{OLD_RATIO:.2f}', '소비 전환 배율(소비 건수 점유율 ÷ 방문 점유율, 안동문화의거리)', '철도공사 2022.4~6')]),
        (28, 45, '월영교', '사람이 모이는 곳', [
            (f'{MANHYU:.1f}%', f'만휴정 방문객 중 월영교에도 간 비율(도산서원 {DOSAN:.1f}%)', '철도공사 2022.4~6'),
            (f'{WY["소비방문배율"]:.2f}', f'소비 전환 배율(방문 {WY["방문점유율_pct"]:.2f}% 대비 소비 건수 {WY["방문객소비건수점유율_pct"]:.2f}%)', '철도공사 2022.4~6'),
            (f'{WY_PUB}곳', f'반경 1km 주점(영업 음식점 {WY_OPEN}곳 중 21시 식사 {WY_21}곳)', '상가정보 + 팀 확인')])]
H(ws, 7, 30)
for r_ in (8, 9, 10): H(ws, r_, 36)
for c1, c2, name, role, facts in hubs:
    hline(ws, 7, c1, c2, INK, 'medium', top=True)
    M(ws, 7, c1, c2, rich((name + '  ', 14, True, INK), (role, 11, False, MUTE)), al=AL('left', 'center', False))
    for i, (v, t, src) in enumerate(facts):
        M(ws, 8 + i, c1, c1 + 4, v, F(18, True), AL('left', 'center', False))
        M(ws, 8 + i, c1 + 5, c2, rich((t + '  ', 10, False, INK), (f'[{src}]', 8.5, False, MUTE)), al=AL('left', 'center', True))
M(ws, 8, 20, 27, f'{Q["원도심_월영교_km"]:.1f}km', F(18, True, BLUE), AL('center', 'bottom', False))
hline(ws, 8, 20, 27, BLUE, 'medium')
M(ws, 9, 20, 27, f'잇는 시내버스 112번 한 노선\n19시 이후 {BUS["19시이후"]}회', F(10, False, INK), AL('center', 'center', True))
H(ws, 11, 26)
M(ws, 12, 2, 30, rich(('하루 시간표 위의 3단계  ', 10.5, True, INK), ('위 = 끊기는 것, 아래 = 사람이 움직이는 때', 10, False, MUTE)), al=AL('left', 'center', False))
M(ws, 12, 31, 45, rich(('■ ', 10, True, INK), ('끊기는 것   ', 9.5, False, MUTE), ('■ ', 10, True, BLUE), ('수요', 9.5, False, MUTE)), al=AL('right', 'center', False))
H(ws, 12, 22); H(ws, 13, 8)
# 행: 14 위 2단 이름표 · 15 선 · 16 위 1단 이름표 · 17 위 1단 막대 · 18 선 · 19 띠 · 20 시각 · 21 선 · 22 아래 1단 막대 · 23 아래 1단 이름표 · 24 아래 2단 막대 · 25 아래 2단 이름표
for r_, h_ in zip(range(14, 26), (22, 12, 22, 5, 10, 30, 18, 8, 5, 22, 5, 22)): H(ws, r_, h_)
BAND = 19
pins = [(18.75, 18.75, INK, 14, None, '18:45', '112번 원도심 출발 막차(평일)'),
        (20.0, 20.5, INK, 16, 17, '20:00~20:30', f'월영교 1km 음식점 {WY_OPEN}곳 중 {WY_EARLY}곳 영업 종료'),
        (21.0, 21.0, INK, 14, None, '21:00', f'월영교 1km 식사 가능 {WY_21}곳, 주점 {WY_PUB}곳'),
        (int(PEAK[:2]), int(PEAK[3:]), BLUE, 25, 24, f'{int(PEAK[:2])}~{int(PEAK[3:])}시', f'주말 안동역 승차 {PEAK_N:,}명, 저녁 중 최다(코레일)'),
        (20.0, 22.0, BLUE, 23, 22, '20~22시', f'당일 귀가자 {sv("Q13_당일귀가자중_20~22시")["pct"]:.0f}%가 귀가(설문)'),
        (21.0, 22.0, BLUE, 25, 24, '21~22시', '안동역 막차')]
for t0, t1, color, lab_r, bar_r, tm, tx in pins:
    c0 = col_t(t0)
    ws.cell(lab_r, c0).value = rich((tm + ' ', 9.5, True, color), (tx, 9.5, False, INK))
    ws.cell(lab_r, c0).alignment = AL('left', 'center', False)
    if bar_r:
        for c in range(c0, max(col_t(t1), c0 + 1)): ws.cell(bar_r, c).fill = FILL(color)
    if lab_r < BAND:
        vline(ws, lab_r + 1, BAND - 1, c0, color)
    else:
        vline(ws, BAND + 2, lab_r - 1, c0, color)
bands = [(12, 18.5, PALE, INK, '1  낮 · 원도심 식당에서 식사 → 체험'), (18.5, 21, BLUE, 'FFFFFF', '2  18:30~21:00 월영교로 이동'),
         (21, 23, DEEP, 'FFFFFF', '3  밤 · 월영교')]
for t0, t1, bg, fg, tx in bands:
    M(ws, BAND, col_t(t0), col_t(t1) - 1, tx, F(10.5, True, fg), AL('left', 'center', False, 1), bg)
for h in range(12, 23):
    M(ws, 20, col_t(h), col_t(h), f'{h}시', F(8.5, False, MUTE), AL('left', 'center', False))
H(ws, 26, 26)
M(ws, 27, 2, 45, '운영값과 그 값을 정한 데이터', F(10.5, True)); H(ws, 27, 22)
H(ws, 28, 6); hline(ws, 28, 2, 45, INK, 'medium'); H(ws, 29, 10)
steps = [(2, 15, 1, '낮 · 원도심 식당 → 체험', '식당에서 식사 후 영수증 QR 인증 → 체험 10% 할인과 체험 정보',
          [(f'식당 {OLD_REST}곳 (찜닭골목·문화의거리)', '방문 1위 원도심에 주민증 혜택 업체 0곳', f'데이터랩 읍면동 방문 + 안동시 혜택 업체 {JM["혜택업체"]}곳 주소'),
           ('할인 + 정보·예약 안내', f'유료 체험을 망설인 이유의 {sv("Q11_비가격_이유")["pct"]:.0f}%가 가격이 아닌 정보·예약·이동', f'팀 설문(응답 {sv("Q11_비가격_이유")["n"]}명)')]),
         (17, 30, 2, '저녁 · 원도심 → 월영교', '관광택시 저녁 배치로 월영교까지 이동, 이용이 늘면 셔틀',
          [('18:30 ~ 21:00', f'주말 안동역 승차는 저녁 중 {int(PEAK[:2])}~{int(PEAK[3:])}시가 가장 많고({PEAK_N:,}명) 막차는 21~22시. 당일 귀가자 {sv("Q13_당일귀가자중_20~22시")["pct"]:.0f}%가 20~22시 귀가',
            '코레일 안동역 승하차 + 팀 설문'),
           ('택시 먼저, 늘면 셔틀', f'19시 이후 버스 {BUS["19시이후"]}회. 시내버스 이용 방문자 {sv("Q3_버스불편_버스이용방문자")["pct"]:.0f}%가 불편', f'버스정보시스템 {BIS_ROUTES}개 노선 + 팀 설문')]),
         (32, 45, 3, '밤 · 월영교', '저녁 문보트 10% 할인 + 21시 이후 식사·주점 팝업(월영야행 부지 활용)',
          [('21시 이후 팝업', f'월영교 1km 21시 식사 가능 {WY_21}곳, 주점 {WY_PUB}곳. 방문객 {sv("Q9_월영교밤_부족_방문자")["pct"]:.0f}%가 20시 이후 식당·편의시설 부족',
            f'상가정보 + 팀 확인 + 팀 설문(방문 {SV_V}명)'),
           ('저녁 체험 = 문보트', f'저녁까지 운영이 확인된 체험은 {EXP_OPEN_EVENING}뿐', '체험 12곳 운영 시간 확인')])]
for r_, h_ in zip(range(30, 38), (26, 34, 24, 34, 16, 24, 34, 16)): H(ws, r_, h_)
for c1, c2, n, title, what, rows_ in steps:
    circle(ws, 30, c1, n)
    M(ws, 30, c1 + 1, c2, title, F(12, True), AL('left', 'center', False, 1))
    M(ws, 31, c1, c2, what, F(10), AL('left', 'center', True))
    for i, (v, why, src) in enumerate(rows_):
        r0 = 32 + i * 3
        hline(ws, r0, c1, c2, TRACK, top=True)
        M(ws, r0, c1, c2, v, F(12, True, DEEP), AL('left', 'bottom', False))
        M(ws, r0 + 1, c1, c2, why, F(10), AL('left', 'center', True))
        M(ws, r0 + 2, c1, c2, src, F(8.5, False, MUTE), AL('left', 'top', False))
H(ws, 38, 20); H(ws, 39, 56)
M(ws, 39, 2, 22, rich(('아직 정하지 않은 값\n', 10.5, True, INK),
                      ('팝업 부스 수 · 차량 대수 · 배차 간격. 이용량·회차 시간·견적을 확인한 뒤 정한다. 인증은 영수증 QR(누구나)과 주민증 조건형 혜택을 병행(조건형 가능 여부 확인 중).', 10, False, INK)),
  al=AL('left', 'center', True, 1), fill=CARD)
M(ws, 39, 25, 45, rich(('넓히는 방법\n', 10.5, True, INK),
                       ('식당을 4묶음으로 나눠 추첨 순서대로 참여시킨다. 먼저 연 묶음과 아직 안 연 묶음을 비교하면 운영하면서 효과를 바로 확인할 수 있다.', 10, False, INK)),
  al=AL('left', 'center', True, 1), fill=CARD)
H(ws, 40, 20)
M(ws, 41, 2, 34, '철도공사 숫자(2022.4~6, 소비 = 건수)는 데이터랩과 다른 체계라 [ ]로 구분했다. 영업 종료 시각은 팀 확인(조사일 기록 보완 중).', F(9.5, False, MUTE), AL('left', 'center', False)); H(ws, 41, 18)
M(ws, 42, 2, 34, f'출처: 한국관광 데이터랩, 한국철도공사 8대 도시 가명결합 분석, 코레일 안동역 승하차, 안동시 버스정보시스템, 소상공인 상가정보, 팀 온라인 설문 {SV_N}명', F(9.5, False, MUTE), AL('left', 'center', False)); H(ws, 42, 18)
link(ws, 41, 35, 45, '이렇게 운영하면 → 3 기대효과', S_E)
printing(ws, 46, 43)

# ═════════════ 3 기대효과 ═════════════
ws = wsE; grid(ws, 36, 5.2)
header(ws, '03 기대효과', f'="원도심 방문객 100명 중 "&TEXT({C_N},"0")&"명이 참여하면"',
       f'원도심 식당 {OLD_REST}곳 운영. 시행 전 예측, 1만 번 계산의 가운데 값(2026년 1~8월 자료를 연간으로 환산)', subw=27)
M(ws, 2, 29, 37, '참여율 ▼ 눌러서 고르기', F(9.5, False, MUTE), AL('left', 'bottom', False))
sel = M(ws, 3, 29, 37, OPTS[0], F(12, True, DEEP), AL('center', 'center', False), PALE,
        border=Border(left=S_(BLUE, 'medium'), right=S_(BLUE, 'medium'), top=S_(BLUE, 'medium'), bottom=S_(BLUE, 'medium')))
dv = DataValidation(type='list', formula1='"' + ','.join(OPTS) + '"', allow_blank=False, showDropDown=False)
dv.promptTitle = '참여율'; dv.prompt = '기준 · 흥행 · 목표 중에서 고른다'
ws.add_data_validation(dv); dv.add('AC3')
note_mark(ws, 4, 28, 37, '삼각형 숫자에 마우스를 올리면 계산 방법')
ws['AM3'] = f"={C_N}"; ws['AM3'].font = F(8, c='FFFFFF')           # 조건부 서식용(같은 시트 참조)
H(ws, 6, 18)
for r_ in range(7, 18): H(ws, r_, 26)
# 사람 100명 격자 (B8:K17)
white = S_('FFFFFF', 'thick')
for i in range(10):
    for j in range(10):
        c = ws.cell(8 + i, 2 + j); c.fill = FILL(TRACK); c.border = Border(left=white, right=white, top=white, bottom=white)
ws.conditional_formatting.add('B8:K17', FormulaRule(formula=['((ROW()-8)*10+COLUMN()-1)<=$AM$3'], fill=PatternFill(start_color=BLUE, end_color=BLUE, fill_type='solid')))
M(ws, 7, 2, 11, '원도심 방문객 100명', F(10, True), AL('left', 'center', False))
# 지금 → 시행 후
M(ws, 7, 14, 26, '지금 → 시행 후', F(10.5, True), AL('left', 'center', False))
M(ws, 7, 27, 37, rich(('■ ', 10, True, INK), ('실측 2026년 1~8월   ', 9.5, False, MUTE), ('□ ', 11, True, BLUE), ('예측 시행 전', 9.5, False, MUTE)), al=AL('right', 'center', False))
hline(ws, 7, 14, 37, INK, 'medium')
items = [(8, 1, '원도심 혜택 업체', '0곳', OLD_REST, '0"곳"', '찜닭골목·문화의거리 식당',
          f'원도심(찜닭골목·문화의거리) 관광 식당 수. 참여 식당은 4묶음으로 나눠 추첨 순서대로 연다. 기준(2%)일 때 식당 → 체험 인증 월 {P50("기준", "인증_월"):,.0f}건'),
         (10, 2, '월영교 저녁 이동', f'19시 이후 버스 {BUS["19시이후"]}회', f"={C_MOVE}", '0"명"', '주말 하루 새로 가는 인원',
          '주말 하루 원도심 → 월영교로 새로 가는 인원. 저녁 이동 배수 = 설문 이동 의향 × 실현율 0.33~0.40(선행연구). 모의실험 1만 번의 가운데 값'),
         (12, 3, '방문당 체험·문화 소비', f'{EX26:.1f}원', f"={C_SPEND}", '0.0"원"', None,
          f'지금 {EX26:.1f}원 × (1 + 방문당 체험·문화 소비 증가율). 체험 결제율 = 설문 의향 × 실현율 0.33~0.40, 체험 10% 할인액은 뺐다')]
for r0, n, lab, now, after, fmt, sub, mm in items:
    M(ws, r0, 14, 14, n, F(11, True, 'FFFFFF'), AL('center', 'center', False), BLUE)
    M(ws, r0, 15, 19, lab, F(10.5), AL('left', 'center', True, 1), r2=r0 + 1)
    M(ws, r0, 20, 24, now, F(15 if len(now) < 8 else 11, True, INK), AL('left', 'center', True), r2=r0 + 1)
    M(ws, r0, 25, 25, '→', F(13, False, MUTE), AL('center', 'center', False), r2=r0 + 1)
    v = M(ws, r0, 26, 30, after, F(22, True, BLUE), AL('left', 'center', False), fmt=fmt, r2=r0 + 1); memo(v, mm, 300, 120)
    if sub:
        M(ws, r0, 31, 37, sub, F(9.5, False, MUTE), AL('left', 'center', True), r2=r0 + 1)
    else:
        M(ws, r0, 31, 37, f'="2024년 대비 "&TEXT({C_CHG},"+0.0%;−0.0%")&" (지금 {MINUS(f"{(EX26 / EX24 - 1) * 100:+.1f}")}%)"', F(9.5, False, MUTE), AL('left', 'center', True), r2=r0 + 1)
    hline(ws, r0 + 1, 14, 37, TRACK)
M(ws, 14, 14, 37, rich(('3번을 자와 함께 보면  ', 10, True, INK), (f'점선 = 전국 중앙만큼만 줄었을 때({TARGET:.1f}원)', 9.5, False, MUTE)), al=AL('left', 'center', False))
# 자(점 그림)
ch = ScatterChart(); ch.scatterStyle = 'lineMarker'
def xy(r1, r2, name=None, line=None, lw=None, dash=None, marker=None, msize=None, mfill=None, mline=None, lab=None):
    s = Series(Reference(dX, min_col=3, min_row=r1, max_row=r2), Reference(dX, min_col=2, min_row=r1, max_row=r2), title=name)
    s.graphicalProperties = gp(line=line, w=lw, dash=dash) if line else gp(noline=True)
    if marker:
        s.marker.symbol = marker; s.marker.size = msize
        s.marker.graphicalProperties = gp(fill=mfill, line=mline or mfill, w=2) if mfill else gp(nofill=True, line=mline, w=2)
    else:
        s.marker.symbol = 'none'
    s.smooth = False
    if lab: s.dLbls = lab
    ch.series.append(s); return s
xy(2, 3, '트랙', TRACK, 2)
t = xy(4, 5, '전국 중앙 수준', INK, 1, 'dash')
t.dLbls = DataLabelList(dLbl=[DataLabel(idx=1, showSerName=True, showVal=False, showCatName=False, showLegendKey=False, showPercent=False, showBubbleSize=False, dLblPos='t', txPr=txp(850, INK))],
                        showVal=False, showSerName=False, showCatName=False, showLegendKey=False, showPercent=False, showBubbleSize=False)
t.tx = SeriesLabel(v=f'전국 중앙 수준 {TARGET:.1f}원')
xy(6, 6, f'2024년 {EX24:.1f}원', marker='diamond', msize=7, mfill=MUTE, lab=labels(ser_name=True, pos='b', sz=850, color=MUTE, b=False))
xy(7, 8, '연결', BLUE, 2.25)
xy(9, 9, f'지금 {EX26:.1f}원', marker='circle', msize=10, mfill=INK, lab=labels(ser_name=True, pos='b', sz=900, color=INK))
a = xy(10, 10, None, marker='circle', msize=10, mline=BLUE, lab=labels(ser_name=True, pos='t', sz=950, color=DEEP))
a.tx = ref_title('d_시나리오', '$B$14')
ch.x_axis.scaling.min = 140; ch.x_axis.scaling.max = 190; ch.x_axis.majorUnit = 10
show_axis(ch.x_axis, 850); ch.x_axis.number_format = '0"원"'
hide_axis(ch.y_axis); ch.y_axis.scaling.min = 0; ch.y_axis.scaling.max = 2
bare(ch, 23.5, 3.6)
place(ws, ch, 14, 15, 37, 18)
# 왼쪽 아래: 범례·설명·거꾸로 보면
M(ws, 18, 2, 11, f'="■ 참여 "&TEXT({C_N},"0")&"명   □ 참여하지 않음"', F(9.5, False, MUTE), AL('left', 'center', False)); H(ws, 18, 20)
M(ws, 19, 2, 11, '참여 = 원도심 식당에서 먹고 체험 할인을 받은 사람. 설문의 "하겠다"는 선행연구대로 33~40%만 실제로 한다고 보정했다.', F(9.5, False, MUTE), AL('left', 'top', True)); H(ws, 19, 48)
H(ws, 20, 10)
M(ws, 21, 2, 11, '거꾸로 보면, 몇 명이 참여해야 하나', F(10.5, True), AL('left', 'center', False)); hline(ws, 21, 2, 11, INK, 'medium', top=True); H(ws, 21, 24)
M(ws, 22, 2, 11, f'격차 {GAP:.1f}원 = 지금 {EX26:.1f}원과 전국 중앙 수준 {TARGET:.1f}원의 차이. 100명 중 몇 명이 필요한지', F(9.5, False, MUTE), AL('left', 'top', True)); H(ws, 22, 32)
for i, (lab, key) in enumerate([('격차의 4분의 1', '0.25'), ('격차의 절반', '0.5'), ('격차 전부', '1.0')]):
    r_ = 23 + i; H(ws, r_, 22)
    need = NEED[key] * 100
    M(ws, r_, 2, 6, lab, F(10), AL('left', 'center', False))
    M(ws, r_, 7, 9, f'=IF({C_N}>={need:.4f},"넘음","아직")', F(9.5, False, MUTE), AL('center', 'center', False))
    M(ws, r_, 10, 11, round(need, 1), F(13, True, INK), AL('right', 'center', False), fmt='0.0"명"')
    ws.conditional_formatting.add(f'G{r_}:K{r_}', FormulaRule(formula=[f'$AM$3>={need:.4f}'], font=Font(name=FN, bold=True, color=BLUE)))
M(ws, 26, 2, 11, '파랑 = 지금 고른 참여율로 넘는 선', F(9, False, MUTE), AL('left', 'center', False)); H(ws, 26, 18)
# 오른쪽 아래: 순위 띠
H(ws, 18, 20)
M(ws, 19, 14, 37, f'="146개 시·군 감소폭 순위 {NOW_RANK}위 → "&TEXT({C_RANK},"0")&"위  (다른 시·군이 그대로일 때)"', F(10, True), AL('left', 'bottom', False))
rank_strip(ws, (14, 20, 37, 26), None, 23.5, 4.2, f'지금 {NOW_RANK}위', after=True)
H(ws, 27, 22); hline(ws, 27, 2, 37, LINE)
H(ws, 28, 12); H(ws, 29, 44)
M(ws, 29, 2, 6, '안동에서 늘어나는\n소비(연간)', F(10.5, False, MUTE), AL('left', 'center', True))
v = M(ws, 29, 7, 12, f"={C_WON}", F(24, True, BLUE), AL('left', 'center', False), fmt='0.00"억 원"')
memo(v, '연간 = 2026년 1~8월 월평균 × 12. 체험 할인액과, 참여하지 않았어도 썼을 돈은 뺐다. 모의실험 1만 번의 가운데 값')
M(ws, 29, 13, 18, '할인액·원래 썼을 돈 제외', F(9.5, False, MUTE), AL('left', 'center', True))
M(ws, 29, 20, 24, '시행 후 확인', F(10.5, False, MUTE), AL('left', 'center', False))
v = M(ws, 29, 25, 37, rich((f'식당 {OLD_REST}곳을 4묶음으로 나눠 추첨 순서로 열면\n', 10.5, False, INK), (f'5개월 만에 {PW50 * 100:.0f}% 확률', 10.5, True, INK), ('로 효과를 판정', 10.5, False, INK)), al=AL('left', 'center', True))
memo(v, f'참여 업소 순차 확대 설계의 검정력(순차도입_검정력). 효과 크기가 +50%일 때 5개월 안에 효과를 가려낼 확률 {PW50 * 100:.0f}%')
H(ws, 30, 22)
M(ws, 31, 2, 28, '모의실험 범위는 가정한 분포에서 나온 범위이며 신뢰구간이 아니다. 시행 첫 달 실제 기록으로 다시 계산한다.', F(9.5, False, MUTE), AL('left', 'center', False)); H(ws, 31, 18)
M(ws, 32, 2, 28, '출처: 이어드림 기대효과 모의실험(주민증 이용 기록, 축제 방문객 소비, 체험 가격 27개, 팀 설문)', F(9.5, False, MUTE), AL('left', 'center', False)); H(ws, 32, 18)
link(ws, 31, 29, 37, '안동만의 문제인가 → 4 시·군 진단', S_D)
printing(ws, 37, 33)

# ═════════════ 4 시·군 진단 ═════════════
ws = wsD; grid(ws, 36, 5.2)
header(ws, '04 우리 시·군 진단', f"={SL(11)}",
       '144개 시·군을 같은 네 지표로 진단. 지표마다 하위 25%(문제 백분위 75 이상)면 문제로 본다.', subw=27)
M(ws, 2, 29, 37, '시·군 ▼ 눌러서 고르기', F(9.5, False, MUTE), AL('left', 'bottom', False))
M(ws, 3, 29, 37, '안동시', F(13, True, DEEP), AL('center', 'center', False), PALE,
  border=Border(left=S_(BLUE, 'medium'), right=S_(BLUE, 'medium'), top=S_(BLUE, 'medium'), bottom=S_(BLUE, 'medium')))
dv2 = DataValidation(type='list', formula1=f"'d_목록'!$A$2:$A${nD}", allow_blank=False)
dv2.promptTitle = '시·군'; dv2.prompt = '144개 시·군 중에서 고른다(가나다순)'
ws.add_data_validation(dv2); dv2.add('AC3')
note_mark(ws, 4, 28, 37, '삼각형 숫자에 마우스를 올리면 계산 방법')
ws['AM3'] = f"={SL(16)}"; ws['AM4'] = f"={SL(17)}"; ws['AM5'] = f"={SL(18)}"; ws['AM6'] = f"={SL(19)}"; ws['AM7'] = f"={SL(12)}"
for rr in range(3, 8): ws[f'AM{rr}'].font = F(8, c='FFFFFF')
H(ws, 6, 18); H(ws, 7, 20); H(ws, 8, 44); H(ws, 9, 20)
tile(ws, 7, 2, 10, '방문당 체험·문화 소비 변화', f"={SL(12)}", '+0.0%;−0.0%',
     f'="146곳 중 감소폭 "&{SL(22)}&"위 · 전국 중앙 {MINUS(f"{DMED["①체험문화_변화율"] * 100:+.1f}")}%"', INK,
     '방문당 체험·문화 소비 변화율(외지인 카드 소비 ÷ 외지인 방문, 2024 → 2026년 1~8월). 순위는 146개 시·군 중 많이 줄어든 순서', divider=False)
ws.conditional_formatting.add('B8', FormulaRule(formula=[f'$AM$7<{DMED["①체험문화_변화율"]:.6f}'], font=Font(name=FN, bold=True, color=BLUE)))
tile(ws, 7, 11, 19, '외지인 방문 변화', f"={SL(23)}", '+0.0%;−0.0%', '2024 → 2026년 1~8월', INK,
     '외지인 방문 연인원(데이터랩 BDT_01_01_006) 변화율')
tile(ws, 7, 20, 28, '진단 점수', f"={SL(20)}", '0.0', f'="144곳 중 "&{SL(21)}&"위 (100에 가까울수록 문제)"', INK,
     '네 지표의 문제 백분위를 같은 비중으로 평균. 가중치를 바꾸면 순위가 흔들리므로 점수보다 유형을 본다')
tile(ws, 7, 29, 37, '문제 유형', f"={SL(8)}", 'General', f'="같은 유형 "&{SL(10)}&"곳"', BLUE,
     '지표마다 144곳 중 하위 25%(문제 백분위 75 이상)에 들면 그 지표를 유형에 넣는다', vsz=15)
H(ws, 10, 24)
# 지도 (B~P), 오른쪽 (R~AK)
M(ws, 11, 2, 16, rich(('전국 지도  ', 10.5, True, INK), ('점 = 시·군 중심, 선 = 시·군 경계(2018)', 9.5, False, MUTE)), al=AL('left', 'center', False))
ch = ScatterChart(); ch.scatterStyle = 'lineMarker'
sb = Series(Reference(dB, min_col=2, min_row=2, max_row=nB), Reference(dB, min_col=1, min_row=2, max_row=nB), title='경계')
sb.graphicalProperties = gp(line='C9CED3', w=0.5); sb.marker.symbol = 'none'; sb.smooth = False
ch.series.append(sb)
for col, name, color, size in ((6, '진단 제외(광역시 자치구 등)', 'E3E6E9', 4), (7, '다른 진단 대상', 'B9BFC5', 5), (8, '같은 유형', BLUE, 8), (9, None, DEEP, 12)):
    s = Series(Reference(dM, min_col=col, min_row=2, max_row=nM), Reference(dM, min_col=2, min_row=2, max_row=nM), title=name)
    s.graphicalProperties = gp(noline=True); s.smooth = False
    s.marker.symbol = 'circle'; s.marker.size = size
    s.marker.graphicalProperties = gp(fill=color, line='FFFFFF' if col < 9 else INK, w=0.5 if col < 9 else 1.5)
    if name is None:
        s.tx = ref_title('d_선택', '$B$2')
        s.dLbls = labels(ser_name=True, pos='r', sz=1100, color=DEEP)
    ch.series.append(s)
ch.display_blanks = 'gap'
ch.x_axis.scaling.min = 0; ch.x_axis.scaling.max = W_; ch.y_axis.scaling.min = 0; ch.y_axis.scaling.max = round(H_)
hide_axis(ch.x_axis); hide_axis(ch.y_axis)
bare(ch, 12.8, 12.8 * H_ / W_); full_plot(ch)          # 지도는 비율 유지(한 칸 고정), 맥 좁은 열에서도 B~P 안에 들어가는 크기
ws.add_chart(ch, 'B12')
# 오른쪽: 네 지표
M(ws, 11, 18, 37, f"={SL(28)}", F(10.5, True), AL('left', 'center', False)); H(ws, 11, 22)
M(ws, 12, 18, 27, '오른쪽일수록 문제', F(9, False, MUTE), AL('left', 'center', False))
M(ws, 12, 28, 32, '전국 가운데', F(9, False, MUTE), AL('left', 'center', False))
M(ws, 12, 33, 37, '문제 구간', F(9, True, DEEP), AL('center', 'center', False)); H(ws, 12, 18)
ind = [('체험·문화 소비 변화', f'=TEXT({SL(12)},"+0.0%;−0.0%")&" (중앙 {MINUS(f"{DMED["①체험문화_변화율"] * 100:+.1f}")}%) · 문제 백분위 "&TEXT({SL(16)},"0")', '$AM$3'),
       ('평균 숙박일수', f'=TEXT({SL(13)},"0.00")&"일 (중앙 {DMED["②평균숙박일수"]:.2f}일) · 문제 백분위 "&TEXT({SL(17)},"0")', '$AM$4'),
       ('저녁 전환율', f'=TEXT({SL(14)},"0.00")&" (중앙 {DMED["③저녁전환율"]:.2f}) · 문제 백분위 "&TEXT({SL(18)},"0")', '$AM$5'),
       ('야간 방문 비중', f'=TEXT({SL(15)},"0.0%")&" (중앙 {DMED["④야간방문비중"] * 100:.1f}%) · 문제 백분위 "&TEXT({SL(19)},"0")', '$AM$6')]
for i, (name, val, pref) in enumerate(ind):
    r0 = 13 + i * 2; H(ws, r0, 20); H(ws, r0 + 1, 20)
    M(ws, r0, 18, 23, name, F(10, True), AL('left', 'bottom', False))
    M(ws, r0, 24, 37, val, F(9.5, False, MUTE), AL('left', 'bottom', False))
    for k in range(20):
        c = ws.cell(r0 + 1, 18 + k)
        c.value = f'=IF(INT(MIN({pref},99.99)/5)={k},"●","")'
        c.font = F(12, True, INK); c.alignment = AL('center', 'center', False)
        if k >= 15: c.fill = FILL(PALE)
        b = S_(TRACK)
        c.border = Border(left=S_(MUTE, 'dashed') if k == 10 else None, bottom=b)
    ws.conditional_formatting.add(f'R{r0 + 1}:AK{r0 + 1}', FormulaRule(formula=[f'{pref}>=75'], font=Font(name=FN, bold=True, color=BLUE)))
M(ws, 21, 18, 23, '0 좋음', F(8.5, False, MUTE), AL('left', 'center', False))
M(ws, 21, 28, 29, '50', F(8.5, False, MUTE), AL('left', 'center', False))
M(ws, 21, 33, 37, '100 나쁨', F(8.5, False, MUTE), AL('right', 'center', False)); H(ws, 21, 16)
H(ws, 22, 14)
# 같은 유형 목록
M(ws, 23, 18, 37, f"={SL(26)}&\"  (\"&{SL(9)}&\")\"", F(10.5, True), AL('left', 'center', False)); H(ws, 23, 22)
hdr = [(18, 20, '시·군', 'left'), (21, 32, '방문당 체험·문화 소비 변화 (−60% ~ +60%, 점선 = 0)', 'left'), (33, 35, '변화율', 'right'), (36, 37, '숙박일수', 'right')]
for c1, c2, t, h in hdr:
    M(ws, 24, c1, c2, t, F(8.5, False, MUTE), AL(h, 'center', False))
hline(ws, 24, 18, 37, INK, 'medium'); H(ws, 24, 18)
ws['AM8'] = f"={SL(2)}"; ws['AM8'].font = F(8, c='FFFFFF')
for k in range(8):
    r_ = 25 + k; dr = 32 + k; H(ws, r_, 21)
    M(ws, r_, 18, 20, f"='d_선택'!$B${dr}", F(10), AL('left', 'center', False, 1))
    for j in range(12):
        c = ws.cell(r_, 21 + j)
        c.value = f"=IF('d_선택'!$E${dr}={j},\"●\",\"\")"
        c.font = F(10, True, INK); c.alignment = AL('center', 'center', False)
        c.border = Border(left=S_(MUTE, 'dashed') if j == 6 else None, bottom=S_(TRACK))
    M(ws, r_, 33, 35, f"='d_선택'!$C${dr}", F(10, True), AL('right', 'center', False), fmt='+0.0%;−0.0%')
    M(ws, r_, 36, 37, f"='d_선택'!$D${dr}", F(10), AL('right', 'center', False), fmt='0.00"일"')
    ws.conditional_formatting.add(f'R{r_}:AK{r_}', FormulaRule(formula=[f'$R{r_}=$AM$8'], fill=PatternFill(start_color=PALE, end_color=PALE, fill_type='solid'), font=Font(name=FN, bold=True, color=DEEP)))
M(ws, 33, 18, 37, f"={SL(27)}", F(9, False, MUTE), AL('left', 'center', False)); H(ws, 33, 18)
M(ws, 34, 18, 37, None, F(9, False, MUTE), AL('left', 'center', False))
ws.cell(34, 18).value = rich(('지도 점 색  ', 9, True, MUTE), ('● ', 10, True, DEEP), ('고른 시·군   ', 9, False, MUTE), ('● ', 10, True, BLUE), ('같은 유형   ', 9, False, MUTE),
                             ('● ', 10, True, 'B9BFC5'), ('다른 진단 대상   ', 9, False, MUTE), ('● ', 10, True, 'E3E6E9'), ('진단 제외(광역시 자치구 등)', 9, False, MUTE))
H(ws, 34, 20)
for r_ in range(35, 37): H(ws, r_, 20)
# 유형 분포
H(ws, 37, 16); hline(ws, 37, 2, 37, LINE)
H(ws, 38, 10)
M(ws, 39, 2, 12, '144곳의 문제 유형', F(10.5, True), AL('left', 'center', False)); H(ws, 39, 22)
M(ws, 40, 2, 12, f"={SL(29)}", F(10), AL('left', 'top', True)); H(ws, 40, 36)
M(ws, 41, 2, 12, f'안동과 같은 유형 {len(SAME)}곳({"·".join(s[:-1] for s in SAME)})이 이어드림을 옮겨 쓸 1차 후보다. 디지털 관광주민증을 운영하는 {JM["운영지역수"]}개 지자체에도 같은 틀을 적용할 수 있다.',
  F(9.5, False, MUTE), AL('left', 'top', True)); H(ws, 41, 64)
for r_ in range(42, 50): H(ws, r_, 20)
ch = BarChart(); ch.type = 'bar'; ch.grouping = 'clustered'; ch.overlap = 100; ch.gapWidth = 45
s1 = Series(Reference(dT, min_col=2, min_row=2, max_row=nT), title='곳'); s1.graphicalProperties = gp(fill=LINE, noline=True)
s1.dLbls = labels(val=True, pos='outEnd', sz=900, color=INK, b=False)
s2 = Series(Reference(dT, min_col=3, min_row=2, max_row=nT), title='고른 유형'); s2.graphicalProperties = gp(fill=BLUE, noline=True)
ch.series.append(s1); ch.series.append(s2)
ch.set_categories(Reference(dT, min_col=1, min_row=2, max_row=nT))
show_axis(ch.x_axis, 900, line=LINE); hide_axis(ch.y_axis); ch.y_axis.scaling.min = 0
bare(ch, 23.5, 7.4)
place(ws, ch, 14, 39, 37, 49)
H(ws, 50, 18)
M(ws, 51, 2, 28, '문제 화면은 146곳, 진단은 네 지표가 모두 있고 방문 100만 명 이상인 144곳이다. 진단 점수는 네 지표를 같은 비중으로 평균했다.', F(9.5, False, MUTE), AL('left', 'center', False)); H(ws, 51, 18)
M(ws, 52, 2, 37, '출처: 한국관광 데이터랩(카드 소비·방문, 평균 숙박일수 LN_02_01_013, 시간대별 방문), 팀 전국 진단표. 체험·문화 2024→2026년 1~8월, 숙박일수 2025년, 저녁·야간 2026년 1~8월', F(9.5, False, MUTE), AL('left', 'center', False)); H(ws, 52, 18)
link(ws, 51, 29, 37, '처음으로 → 한눈에', S_HOME)
printing(ws, 37, 53)

# ═════════════ 출처 ═════════════
ws = wsR; ws.sheet_view.showGridLines = False; ws.sheet_view.zoomScale = 90
for col, w in zip('ABCDE', (2.5, 44, 30, 22, 30)): ws.column_dimensions[col].width = w
M(ws, 2, 2, 5, '데이터 출처', F(18, True), AL('left', 'center', False)); H(ws, 2, 32)
M(ws, 3, 2, 5, '대시보드 숫자는 아래 자료로 계산했다. 계산 스크립트는 공개 저장소 scripts/ 폴더에 있다.', F(10, False, MUTE), AL('left', 'center', False))
src = [('자료', '기관', '기간', '쓴 화면'),
       ('외지인 방문 연인원 (BDT_01_01_006)', '한국관광 데이터랩', '2024·2026년 1~8월', '문제, 시·군 진단'),
       ('외지인 신용카드 소비, 업종 중분류 (BDT_02_01_003)', '한국관광 데이터랩', '2024·2026년 1~8월', '문제, 시·군 진단'),
       ('읍면동별 외지인 방문', '한국관광 데이터랩', '2026년 1~8월', '문제, 해법'),
       ('평균 숙박일수 (LN_02_01_013)', '한국관광 데이터랩', '2025년', '시·군 진단'),
       ('시간대별 방문(저녁 전환율, 야간 방문 비중)', '한국관광 데이터랩', '2026년 1~8월', '시·군 진단'),
       ('당일 방문(무박) 비중', '한국관광 데이터랩', '2019·2025년', '문제'),
       ('8대 도시 가명결합 분석(안동 관광지 방문·소비)', '한국철도공사', '2022.4~6', '문제, 해법'),
       ('안동역 시간대별 승하차', '코레일', '2024.1~2026.8', '해법'),
       (f'시내버스 시간표 {BIS_ROUTES}개 노선', '안동시 버스정보시스템', '2026년', '문제, 해법'),
       ('상가(상권)정보 음식점', '소상공인시장진흥공단', '2026.6', '해법'),
       ('디지털관광주민증 혜택업체·이용 실적', '안동시(정보공개청구)', '2024.6~2026.8', '문제, 해법'),
       ('월영교 1km 음식점 영업 종료 시각', '팀 확인(조사 16번)', '조사일 기록 보완 중', '문제, 해법'),
       (f'온라인 설문 {SV_N}명(방문 경험 {SV_V}명)', '팀', '2026.9.23~24', '해법, 기대효과'),
       ('기대효과 모의실험 1만 번', '팀 분석(이어드림_시뮬레이션.py)', '2026년 1~8월 기준', '기대효과'),
       ('순차 확대 검정력', '팀 분석(이어드림_순차도입_검정력.py)', '-', '기대효과'),
       ('전국 진단표 144곳', '팀 분석(전국진단표.py)', '위 데이터랩 기간', '시·군 진단'),
       ('시·군 경계', 'southkorea-maps(2018 행정구역)', '2018', '시·군 진단 지도')]
for i, row in enumerate(src):
    r_ = 5 + i; H(ws, r_, 22)
    for j, v in enumerate(row):
        c = ws.cell(r_, 2 + j, v); c.font = F(10, i == 0, INK); c.alignment = AL('left', 'center', True)
        c.border = Border(bottom=S_(INK if i == 0 else TRACK, 'medium' if i == 0 else 'thin'))
M(ws, 5 + len(src) + 1, 2, 5, '만든 스크립트: scripts/요약대시보드.py (숫자는 앞단 JSON·CSV에서 읽는다. 이 파일을 손으로 고치지 않는다)', F(9.5, False, MUTE), AL('left', 'center', True))
H(ws, 5 + len(src) + 1, 30)
printing(ws, 5, 5 + len(src) + 3)
link(ws, 5 + len(src) + 2, 2, 3, '처음으로 → 한눈에', S_HOME, h='left')

# ═════════════ 마무리 ═════════════
for w_, col in ((wsH, None), (wsP, None), (wsS, None), (wsE, 'AC3'), (wsD, 'AC3'), (wsR, None)):
    protect(w_, [col] if col else [])
    w_.sheet_view.selection[0].activeCell = 'A1'; w_.sheet_view.selection[0].sqref = 'A1'
for w_, color in ((wsH, INK), (wsP, BLUE), (wsS, BLUE), (wsE, BLUE), (wsD, BLUE), (wsR, LINE)):
    w_.sheet_properties.tabColor = color
wb.active = 0
wb.calculation.fullCalcOnLoad = True
path = OUT / '안동이어드림_요약대시보드.xlsx'
wb.save(path)
print('저장:', path)
print(f'기준 {EX26:.1f} → {ex_after("기준")[0]:.1f}원, 순위 {NOW_RANK} → {ex_after("기준")[2]} / 목표 {ex_after("목표")[0]:.1f}원 {ex_after("목표")[2]}위, 격차 {GAP:.1f}원, 검정력 {PW50:.2f}, 경계 점 {nB}')
