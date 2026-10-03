# -*- coding: utf-8 -*-
"""요약 대시보드 엑셀 (2026-09-28 처음, 2026-09-29 재구성)

9/29 사용자 결정: 한눈에 + 옛 통합 대시보드(교수님_통합대시보드.py)의 5개 화면(시·군 진단 · 운영 시간 · 버스 · 월영교 · 설문조사)만 남긴다.
  옛 1 문제 · 2 해법 · 3 기대효과 · 4 시·군 진단 · 출처 화면은 뺐다. 옛 화면의 조절 칸·계산은 그대로 옮기고, 디자인은 이 파일 양식으로 통일.
디자인(9/29 팀 피드백): 전체 파랑 톤, 데이터랩 첫 화면처럼 하늘색 띠 위 흰 숫자 카드, 줄었거나 문제인 것 = 빨강, 좋아진 것 = 파랑,
  검정 도형 대신 회색. 차트는 테두리·제목 없이 칸 제목 아래에 둔다.
누르면 나오는 것: 파란 테두리 입력 칸(▼ 목록·숫자), 숫자 메모(빨간 삼각형), 화면 아래 「표로 보기」(파랑)·「데이터 설명」(노랑) 접기 칸
  (엑셀 행 그룹, 왼쪽 여백 + 로 펼침, 매크로 없음 → 화면 시트는 잠그지 않는다).
숫자 입력: 교수브리핑 수치.json · 시뮬레이션결과.json · 전국진단표.csv/json · 설문 정제 csv·집계 json ·
          코레일 안동역 승하차 · 조사/01 버스 시간표 · 조사/04 정류장 · 철도공사 방문소비갭.csv
출력: 보고서/요약대시보드/안동이어드림_요약대시보드.xlsx (생성 후 엑셀로 한 번 저장해 계산값을 넣는다)
"""
import json, math, re
from pathlib import Path
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, Protection
from openpyxl.comments import Comment
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.hyperlink import Hyperlink
from openpyxl.worksheet.properties import Outline
from openpyxl.drawing.image import Image as XLImage
import importlib.util
from openpyxl.formatting.rule import FormulaRule
from openpyxl.utils import get_column_letter as CL
from openpyxl.chart import BarChart, LineChart, ScatterChart, Reference, Series
from openpyxl.chart.axis import ChartLines
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.marker import DataPoint
from openpyxl.chart.shapes import GraphicalProperties
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
DGJ = J('보고서/전국진단_20260923/전국진단.json')
SV = J('data/설문/설문_집계.json')
DG = pd.read_csv(ROOT / '보고서/전국진단_20260923/전국진단표.csv')
DG = DG.rename(columns={DG.columns[0]: '시군'})
RAIL = pd.read_csv(ROOT / 'data/external/철도공사_8대도시/안동_관광지_방문소비갭.csv')

# ═════════════ 숫자 (모두 앞단 결과에서 읽는다) ═════════════
E = Q['체험문화']
EX24, EX26 = E['안동_2024'], E['안동_2026']
EXCH = EX26 / EX24 - 1
MED = E['중앙_변화율'] / 100 if abs(E['중앙_변화율']) > 1 else E['중앙_변화율']
NOW_RANK = E['안동_감소순위']
BUS = Q['버스']['원도심→월영교']
JM = Q['주민증']
R1 = Q['반경1km업종']
rail = RAIL.set_index('관광지명'); WY = rail.loc['월영교']
SC = SIM['시나리오']
P50 = lambda n, k: SC[n][k]['P50']
EFF_AFTER = EX26 * (1 + P50('기준', '지표1_증가율'))
SAME = [s for s in DGJ['안동과_같은_유형'] if s != '안동시']
SV_N, SV_V = SV['표본']['응답'], SV['표본']['3년내_방문_예']
OLD_REST = 83                                 # 원도심 관광 식당 수(찜닭골목·문화의거리), 파라미터추정
BIS_ROUTES = 46                               # 안동시 버스정보시스템 노선 수(조사/01)
MANHYU, DOSAN = 54.8, 54.2                    # 철도공사 8대 도시: 만휴정·도산서원 방문자의 월영교 동시 방문 비율
st_ = Q['안동역_주말승차']; PEAK = max((k for k in st_ if int(k[:2]) >= 17), key=st_.get)   # 저녁 중 최다(하루 최다는 15~16시)

# ═════════════ 스타일 ═════════════
FN = '맑은 고딕'
BLUE, DEEP, LIGHT, PALE = '2D6BD9', '1A4FA8', 'A8C4F0', 'EAF1FC'
INK, MUTE, LINE, TRACK, SOFT = '34383C', '6B7075', 'D5D9DC', 'ECEEF0', '7FA6EC'
RED, RED_LIGHT = 'E03C31', 'F2A7A1'                          # 줄었거나 문제인 것(9/29 피드백)
GRAY, GRAY_L = '9AA1A8', 'C9CED3'                            # 비교 기준: 검정 대신
SKY, WHITE = 'E3F1FB', 'FFFFFF'                              # 데이터랩 첫 화면처럼 하늘색 띠 + 흰 카드
AMBER, AMBER_PALE = 'FFCB5C', 'FFF7E3'                       # 데이터랩 「데이터 설명」 띠
F = lambda sz=10.5, b=False, c=INK: Font(name=FN, size=sz, bold=b, color=c)
IF = lambda sz=10.5, b=False, c=INK: InlineFont(rFont=FN, sz=sz, b=b, color=c)
FILL = lambda c: PatternFill('solid', fgColor=c)
AL = lambda h='left', v='center', w=True, ind=0: Alignment(horizontal=h, vertical=v, wrap_text=w, indent=ind)
S_ = lambda c, s='thin': Side(style=s, color=c)
MINUS = lambda s: s.replace('-', '−')
PCT = '+0.0%;−0.0%;0.0%'


def grid(ws, n=36, w=5.2):
    ws.column_dimensions['A'].width = 2.5
    for c in range(2, 2 + n):
        ws.column_dimensions[CL(c)].width = w
    ws.sheet_view.showGridLines = False
    ws.sheet_view.showRowColHeaders = False
    ws.sheet_view.zoomScale = 100


def H(ws, r, pt):
    ws.row_dimensions[r].height = pt


def M(ws, r, c1, c2=None, v=None, font=None, al=None, fill=None, fmt=None, r2=None, border=None):
    """(r, c1)~(r2, c2) 칸에 값을 쓰고 합친다. 채우기는 합칠 칸 전체에 준다."""
    c2 = c2 or c1; r2 = r2 or r
    cell = ws.cell(r, c1)
    if v is not None: cell.value = v
    cell.font = font or F()
    cell.alignment = al or AL()
    if fill:
        for rr in range(r, r2 + 1):
            for cc in range(c1, c2 + 1): ws.cell(rr, cc).fill = FILL(fill)
    if fmt: cell.number_format = fmt
    if border: cell.border = border
    if c2 > c1 or r2 > r:
        ws.merge_cells(start_row=r, start_column=c1, end_row=r2, end_column=c2)
    return cell


def rich(*parts):
    return CellRichText(*[TextBlock(IF(*p[1:]), p[0]) for p in parts])


def memo(cell, text, w=300, h=120):
    c = Comment(text, '안동 이어드림'); c.width, c.height = w, h
    cell.comment = c


def hline(ws, r, c1, c2, color=LINE, style='thin', top=False):
    for c in range(c1, c2 + 1):
        b = ws.cell(r, c).border
        ws.cell(r, c).border = Border(left=b.left, right=b.right, top=S_(color, style) if top else b.top, bottom=b.bottom if top else S_(color, style))


def header(ws, label, title, sub, accent=BLUE):
    H(ws, 1, 12)
    M(ws, 2, 2, 24, label, F(10, True, DEEP if accent == BLUE else accent), AL('left', 'bottom', False)); H(ws, 2, 20)
    M(ws, 3, 2, 37, title, F(22, True, INK), AL('left', 'center', False)); H(ws, 3, 38)
    M(ws, 4, 2, 37, sub, F(10.5, False, MUTE), AL('left', 'center', False)); H(ws, 4, 20)
    H(ws, 5, 4)
    for c in (2, 3): ws.cell(5, c).fill = FILL(accent)


def section(ws, r, c1, c2, title, note=None, h=24):
    parts = [(title + ('  ' if note else ''), 10.5, True, INK)]
    if note: parts.append((note, 9.5, False, MUTE))
    M(ws, r, c1, c2, rich(*parts), al=AL('left', 'center', False)); H(ws, r, h)


def controls(ws, row, items, hint=None):
    """조절 칸. row = 이름, row+1 = 파란 테두리 입력 칸.
    items = [(c1, c2, 이름, 기본값, 서식, 목록식 | None, (종류, 최소, 최대) | None, 도움말)]. 입력 칸 참조식 목록을 돌려준다."""
    H(ws, row, 18); H(ws, row + 1, 28)
    refs, last = [], 0
    med = S_(BLUE, 'medium')
    for c1, c2, lab, val, fmt, opts, rng, tip in items:
        M(ws, row, c1, c2, lab, F(9.5, True, MUTE), AL('left', 'bottom', False))
        cell = M(ws, row + 1, c1, c2, val, F(12, True, DEEP), AL('center', 'center', False), PALE, fmt=fmt)
        for c in range(c1, c2 + 1):
            ws.cell(row + 1, c).border = Border(top=med, bottom=med, left=med if c == c1 else None, right=med if c == c2 else None)
        if opts:
            dv = DataValidation(type='list', formula1=opts, allow_blank=False, showDropDown=False)
            dv.error = '목록에서 고른다'
        else:
            dv = DataValidation(type=rng[0], operator='between', formula1=str(rng[1]), formula2=str(rng[2]), allow_blank=False)
            dv.error = f'{rng[1]}~{rng[2]} 사이 값을 넣는다'
        dv.showErrorMessage = True; dv.showInputMessage = True
        dv.promptTitle = lab[:30]; dv.prompt = tip[:250]
        ws.add_data_validation(dv); dv.add(cell.coordinate)
        refs.append(f"'{ws.title}'!${CL(c1)}${row + 1}")
        last = max(last, c2)
    if hint:
        M(ws, row + 1, last + 2, 37, rich(('◥ ', 9, False, RED), (hint, 9.5, False, MUTE)), al=AL('right', 'center', True))
    return refs


def tile(ws, r, c1, c2, label, value, fmt, sub, color=INK, memo_text=None, vsz=24):
    """하늘색 띠 위 흰 카드 하나. 카드 사이는 하늘색 굵은 선으로 띄운다."""
    M(ws, r, c1, c2, label, F(10, True, INK), AL('left', 'bottom', False, 1), WHITE)
    v = M(ws, r + 1, c1, c2, value, F(vsz, True, color), AL('left', 'center', False, 1), WHITE, fmt=fmt)
    M(ws, r + 2, c1, c2, sub, F(9, False, MUTE), AL('left', 'top', True, 1), WHITE)
    gap = S_(SKY, 'thick')
    for rr in range(r, r + 3):
        for c in (c1, c2):
            b = ws.cell(rr, c).border
            ws.cell(rr, c).border = Border(left=gap if c == c1 else b.left, right=gap if c == c2 else b.right, top=b.top, bottom=b.bottom)
    if memo_text: memo(v, memo_text)
    return v


def sky_band(ws, r1, r2, c1=1, c2=38):
    for rr in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            ws.cell(rr, c).fill = FILL(SKY)


def tiles_row(ws, r, cards):
    """r = 띠 첫 행. 카드 4장(열 2-10, 11-19, 20-28, 29-37). (다음 행, 값 칸 목록)을 돌려준다."""
    for k, h_ in enumerate((10, 22, 42, 30, 10)): H(ws, r + k, h_)
    sky_band(ws, r, r + 4)
    cells = [tile(ws, r + 1, c1, c2, *card) for (c1, c2), card in zip([(2, 10), (11, 19), (20, 28), (29, 37)], cards)]
    return r + 5, cells


def sign_cf(ws, cell):
    """부호에 따라 빨강(줄음)·파랑(늘음)."""
    ws.conditional_formatting.add(cell, FormulaRule(formula=[f'AND(ISNUMBER({cell}),{cell}<0)'], font=Font(name=FN, bold=True, color=RED)))
    ws.conditional_formatting.add(cell, FormulaRule(formula=[f'AND(ISNUMBER({cell}),{cell}>0)'], font=Font(name=FN, bold=True, color=BLUE)))


def font_cf(ws, cell, formula, color):
    ws.conditional_formatting.add(cell, FormulaRule(formula=[formula], font=Font(name=FN, bold=True, color=color)))


def fold_bar(ws, r, title, hint, kind='data', c1=2, c2=37):
    """접기 칸 머리. kind='data' = 파랑 「표로 보기」, 'note' = 노랑 「데이터 설명」(데이터랩 띠)."""
    fill, tc, hc = (SKY, DEEP, MUTE) if kind == 'data' else (AMBER, INK, INK)
    M(ws, r, c1, c2, rich((title + '  ▼', 11, True, tc), ('     ' + hint, 9.5, False, hc)), al=AL('left', 'center', False, 1), fill=fill)
    H(ws, r, 28)
    ws.row_dimensions[r].collapsed = True


def fold_rows(ws, r1, r2):
    for rr in range(r1, r2 + 1):
        ws.row_dimensions[rr].outlineLevel = 1
        ws.row_dimensions[rr].hidden = True
    ws.sheet_properties.outlinePr = Outline(summaryBelow=False, summaryRight=True)
    ws.sheet_format.outlineLevelRow = 1


def fold_table(ws, r, title, hint, cols, head, rows):
    """「표로 보기」: 머리 + 접힌 표. cols = [(시작열, 끝열, 정렬, 서식)]. 다음 행을 돌려준다."""
    fold_bar(ws, r, title, hint + '. 왼쪽 여백의 [+] 를 누르면 펼쳐진다')
    hr = r + 1
    for (a, b, h, _), t in zip(cols, head):
        M(ws, hr, a, b, t, F(9, True, MUTE), AL(h, 'center', True))
    hline(ws, hr, 2, 37, BLUE, 'medium'); H(ws, hr, 30)
    for i, row in enumerate(rows):
        rr = hr + 1 + i
        for (a, b, h, fmt), v in zip(cols, row):
            M(ws, rr, a, b, v, F(10), AL(h, 'center', False), fmt=fmt)
        hline(ws, rr, 2, 37, TRACK); H(ws, rr, 18)
    end = hr + len(rows)
    fold_rows(ws, r + 1, end)
    return end + 1


def details(ws, r, items, split=7):
    """데이터랩 「데이터 설명」 띠 + 접힌 설명 줄. items = [(항목, 설명)]. 다음 행을 돌려준다."""
    fold_bar(ws, r, '데이터 설명', '계산 방법·기간·출처. 왼쪽 여백의 [+] 를 누르면 펼쳐지고 [−] 를 누르면 접힌다', kind='note')
    per_line = (37 - 2 - split + 1) * 5.2 / 1.95
    for i, (lab, text) in enumerate(items):
        rr = r + 1 + i
        M(ws, rr, 2, 1 + split, lab, F(10, True, INK), AL('left', 'center', True, 1), AMBER_PALE)
        M(ws, rr, 2 + split, 37, text, F(10, False, INK), AL('left', 'center', True), AMBER_PALE)
        hline(ws, rr, 2, 37, 'F3E3B5')
        H(ws, rr, 15 * max(1, math.ceil(len(text) / per_line)) + 8)
    fold_rows(ws, r + 1, r + len(items))
    return r + 1 + len(items)


def src(ws, r, text, c1=2, c2=37, h=18):
    """화면에 늘 보이는 출처 한 줄(데이터랩 그림 아래 출처 표기처럼)."""
    M(ws, r, c1, c2, rich(('출처  ', 8.5, True, MUTE), (text, 8.5, False, MUTE)), al=AL('left', 'center', False)); H(ws, r, h)


def survey_line(ws, r, text):
    M(ws, r, 2, 37, rich(('설문  ', 9.5, True, DEEP), (text, 9.5, False, INK)), al=AL('left', 'center', True, 1), fill=PALE)
    H(ws, r, 34)


def printing(ws, last_row):
    ws.print_area = f'A1:AL{last_row}'
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


def bare(ch):
    ch.legend = None
    ch.graphical_properties = gp(nofill=True, noline=True)
    ch.plot_area.graphicalProperties = gp(nofill=True, noline=True)
    ch.roundedCorners = False
    return ch


def labels(pos=None, sz=850, color=INK, b=False, fmt=None):
    d = DataLabelList(showSerName=False, showVal=True, showCatName=False, showLegendKey=False, showPercent=False)
    d.txPr = txp(sz, color, b)
    if pos: d.position = pos
    if fmt: d.numFmt = fmt
    return d


def hide_axis(ax):
    ax.delete = True
    ax.majorGridlines = None


def show_axis(ax, sz=850, line=LINE, grid=False, fmt=None):
    ax.delete = False
    ax.majorGridlines = ChartLines(spPr=gp(line=TRACK, w=0.75)) if grid else None
    ax.txPr = txp(sz, MUTE)
    ax.graphicalProperties = gp(line=line, w=0.75) if line else gp(noline=True)
    if fmt: ax.number_format = fmt


def place(ws, ch, c1, r1, c2, r2):
    """차트를 칸 범위(c1~c2열, r1~r2행)에 묶는다. 맥·윈도 엑셀의 열 너비 차이에도 칸 안에 머문다."""
    ch.anchor = TwoCellAnchor(editAs='twoCell', _from=AnchorMarker(col=c1 - 1, row=r1 - 1), to=AnchorMarker(col=c2, row=r2))
    ws.add_chart(ch)


def bar_series(ref, title, color):
    s = Series(ref, title=title); s.graphicalProperties = gp(fill=color, noline=True); s.invertIfNegative = False
    return s


def line_series(ref, title, color, w=2.25):
    s = Series(ref, title=title); s.graphicalProperties = gp(line=color, w=w)
    s.marker.symbol = 'none'; s.smooth = False
    return s


def pts(sh, xc, yc, r1, r2, title, color, size, edge=None):
    s = Series(Reference(sh, min_col=yc, min_row=r1, max_row=r2), Reference(sh, min_col=xc, min_row=r1, max_row=r2), title=title)
    s.graphicalProperties = gp(noline=True); s.smooth = False
    s.marker.symbol = 'circle'; s.marker.size = size
    s.marker.graphicalProperties = gp(fill=color, line=edge or color, w=0.75)
    return s


def legend_cell(ws, r, c1, c2, items, h='left'):
    parts = []
    for mark, color, text in items:
        parts += [(mark + ' ', 10, True, color), (text + '    ', 9.5, False, MUTE)]
    M(ws, r, c1, c2, rich(*parts), al=AL(h, 'center', False))


def rows_h(ws, r, n, h=20):
    for k in range(n): H(ws, r + k, h)


def write_df(ws, df, r0=1, c0=1):
    for j, col in enumerate(df.columns):
        ws.cell(r0, c0 + j, col)
    for i, row in enumerate(df.itertuples(index=False), 1):
        for j, v in enumerate(row):
            v = None if (isinstance(v, float) and np.isnan(v)) else (v.item() if hasattr(v, 'item') else v)
            ws.cell(r0 + i, c0 + j, v)
    return r0 + len(df)


wb = Workbook()
S_HOME, S_DG, S_TIME, S_BUS, S_WY, S_SV = '한눈에', '시·군 진단', '운영 시간', '버스', '월영교', '설문조사'
wsH = wb.active; wsH.title = S_HOME
wsD, wsT, wsB, wsW, wsV = (wb.create_sheet(n) for n in (S_DG, S_TIME, S_BUS, S_WY, S_SV))
SCREENS = [wsD, wsT, wsB, wsW, wsV]


def data_sheet(name):
    ws = wb.create_sheet(name); ws.sheet_state = 'hidden'
    return ws


def nav(ws, r):
    """화면 맨 위 이동 줄. 지금 화면은 파란 칸, 나머지는 누르면 그 화면으로 간다."""
    M(ws, r, 2, 4, '화면', F(9, True, MUTE), AL('left', 'center', False))
    c = 5
    for sh in [wsH] + SCREENS:
        cur = sh is ws
        cell = M(ws, r, c, c + 4, sh.title, F(9.5, True, WHITE if cur else DEEP), AL('center', 'center', False), BLUE if cur else PALE)
        if not cur:
            cell.hyperlink = Hyperlink(ref=cell.coordinate, location=f"'{sh.title}'!A1", display=sh.title)
        c += 5
    H(ws, r, 22)


# ═════════════════════════════════════════════════════════
# 시·군 진단 (옛 8_전국진단)
# ═════════════════════════════════════════════════════════
ws = wsD; grid(ws)
header(ws, '시·군 진단', rich(('안동과 ', 22, True, INK), ('같은 문제를 가진 시·군', 22, True, BLUE), (' 찾기', 22, True, INK)),
       f'{len(DG)}개 시·군을 네 지표로 진단한다. 시·군을 고르면 위치와 문제 유형이 나오고, 가중치를 바꾸면 순위가 얼마나 흔들리는지 보인다.')
nav(ws, 6)
IND = ['①체험문화_변화율', '②평균숙박일수', '③저녁전환율', '④야간방문비중']
dDg = data_sheet('d_진단'); nD = len(DG) + 1
dDg.append(['시군', '체험', '숙박', '저녁', '야간', '문제①', '문제②', '문제③', '문제④', '점수', '순위', '유형', '정렬키'])
for i, (_, rw) in enumerate(DG.iterrows(), 2):
    dDg.cell(i, 1, rw['시군'])
    for j, c in enumerate(IND): dDg.cell(i, 2 + j, float(rw[c]))
dL = data_sheet('d_목록'); dL.append(['시군'])
for nm in sorted(DG['시군']): dL.append([nm])
H(ws, 7, 8)
ref_sel, *wref = controls(ws, 8, [
    (2, 9, '시·군 ▼', '안동시', None, f"='d_목록'!$A$2:$A${nD}", None, f'{len(DG)}개 시·군 중에서 고른다(가나다순)'),
    (11, 16, '가중치 · 체험·문화', 1, '0.0', None, ('decimal', 0, 10), '0~10. 0이면 이 지표를 빼고 계산한다'),
    (18, 23, '가중치 · 숙박일수', 1, '0.0', None, ('decimal', 0, 10), '0~10'),
    (25, 30, '가중치 · 저녁 전환', 1, '0.0', None, ('decimal', 0, 10), '0~10'),
    (32, 37, '가중치 · 야간 방문', 1, '0.0', None, ('decimal', 0, 10), '0~10')])
WSUM = '+'.join(wref)
for i in range(2, nD + 1):
    for j in range(4):
        col = CL(2 + j)
        dDg.cell(i, 6 + j, f"=100*(1-(COUNTIF(${col}$2:${col}${nD},\"<\"&{col}{i})+1)/COUNT(${col}$2:${col}${nD}))")
    dDg.cell(i, 10, f"=IF(({WSUM})<=0,AVERAGE(F{i}:I{i}),(F{i}*{wref[0]}+G{i}*{wref[1]}+H{i}*{wref[2]}+I{i}*{wref[3]})/({WSUM}))")
    dDg.cell(i, 11, f"=RANK(J{i},$J$2:$J${nD},0)")
    dDg.cell(i, 12, f'=SUBSTITUTE(TRIM(IF(F{i}>=75,"체험·문화 ","")&IF(G{i}>=75,"숙박일수 ","")&IF(H{i}>=75,"저녁전환 ","")&IF(I{i}>=75,"야간방문",""))," "," · ")')
    dDg.cell(i, 13, f"=J{i}-ROW()/1E7")                          # 같은 점수일 때 순서를 가르는 키
DR = lambda col: f"'d_진단'!${col}$2:${col}${nD}"
L = lambda col: f"INDEX({DR(col)},MATCH({ref_sel},{DR('A')},0))"
LA = lambda col: f"INDEX({DR(col)},MATCH(\"안동시\",{DR('A')},0))"
r0, tc = tiles_row(ws, 10, [
    ('진단 점수 (100에 가까울수록 문제)', f"={L('J')}", '0.0', f'="{len(DG)}곳 중 "&{L("K")}&"위 · 가중치 반영"', DEEP,
     '네 지표의 문제 백분위를 가중치로 평균한 값. 가중치를 바꾸면 순위가 흔들리므로 점수보다 유형을 본다'),
    ('문제 유형 (하위 25%인 지표)', f'=IF({L("L")}="","해당 없음",{L("L")})', '@', f'="같은 유형 "&COUNTIF({DR("L")},{L("L")})&"곳"', RED,
     '지표마다 문제 백분위 75 이상(하위 25%)이면 유형에 넣는다. 유형은 가중치와 상관없다'),
    ('방문당 체험·문화 소비 변화', f"={L('B')}", PCT, f'="문제 백분위 "&TEXT({L("F")},"0")&" · 중앙 "&TEXT(MEDIAN({DR("B")}),"+0.0%;−0.0%")', INK,
     '외지인 카드 소비(문화서비스·관광유원시설·기타레저) ÷ 외지인 방문, 2024 → 2026년 1~8월'),
    ('평균 숙박일수', f"={L('C')}", '0.00"일"', f'="문제 백분위 "&TEXT({L("G")},"0")&" · 중앙 "&TEXT(MEDIAN({DR("C")}),"0.00")&"일"', INK,
     '데이터랩 LN_02_01_013, 2025년')])
tc[1].font = F(15, True, RED)
sign_cf(ws, tc[2].coordinate)
r = r0; src(ws, r, '한국관광 데이터랩(외지인 카드 소비·방문 BDT_02_01_003·BDT_01_01_006, 평균 숙박일수 LN_02_01_013, 시간대별 방문) → 팀 전국 진단표 144곳'); r += 1; H(ws, r, 10); r += 1
section(ws, r, 2, 18, '네 지표의 문제 백분위', '75 이상 = 하위 25%')
section(ws, r, 21, 37, '체험·문화 소비 변화 × 숙박일수', '왼쪽 아래일수록 안동과 같은 유형')
r += 1
legend_cell(ws, r, 2, 18, [('■', BLUE, '고른 시·군'), ('■', GRAY_L, '안동')])
legend_cell(ws, r, 21, 37, [('●', BLUE, '고른 시·군'), ('●', RED, '안동'), ('●', GRAY_L, '다른 시·군')]); H(ws, r, 18)
r += 1
dPc = data_sheet('d_진단비교')
dPc.append(['지표', '고른 시·군', '안동'])
for j, lab in enumerate(['체험·문화', '숙박일수', '저녁 전환', '야간 방문']):
    col = CL(6 + j); dPc.append([lab, f"={L(col)}", f"={LA(col)}"])
    for cc in (2, 3): dPc.cell(j + 2, cc).number_format = '0'
ch = BarChart(); ch.type = 'col'; ch.grouping = 'clustered'; ch.gapWidth = 70; ch.overlap = -10
ch.series.append(bar_series(Reference(dPc, min_col=2, min_row=2, max_row=5), '고른 시·군', BLUE))
ch.series.append(bar_series(Reference(dPc, min_col=3, min_row=2, max_row=5), '안동', GRAY_L))
ch.series[0].dLbls = labels(pos='outEnd', fmt='0', color=DEEP, b=True)
ch.set_categories(Reference(dPc, min_col=1, min_row=2, max_row=5))
show_axis(ch.x_axis, 950); show_axis(ch.y_axis, 850, line=None, grid=True)
ch.y_axis.scaling.min = 0; ch.y_axis.scaling.max = 100; ch.y_axis.majorUnit = 25
bare(ch); place(ws, ch, 2, r, 18, r + 11)
dPc['A7'] = '점'; dPc['B7'] = 'x'; dPc['C7'] = 'y'
dPc['A8'] = '고른'; dPc['B8'] = f"={L('B')}"; dPc['C8'] = f"={L('C')}"
dPc['A9'] = '안동'; dPc['B9'] = f"={LA('B')}"; dPc['C9'] = f"={LA('C')}"
sc = ScatterChart(); sc.scatterStyle = 'lineMarker'
sc.series.append(pts(dDg, 2, 3, 2, nD, '시·군', GRAY_L, 5))
sc.series.append(pts(dPc, 2, 3, 9, 9, '안동', RED, 10, WHITE))
sc.series.append(pts(dPc, 2, 3, 8, 8, '고른', BLUE, 10, WHITE))
show_axis(sc.x_axis, 850, fmt='0%'); show_axis(sc.y_axis, 850, line=None, grid=True, fmt='0.0')
sc.x_axis.scaling.min = -0.6; sc.x_axis.scaling.max = 1.0; sc.x_axis.majorUnit = 0.2
sc.y_axis.scaling.min = 2; sc.y_axis.scaling.max = 5.5; sc.y_axis.majorUnit = 0.5
bare(sc); place(ws, sc, 21, r, 37, r + 11)
rows_h(ws, r, 12)
r += 12
src(ws, r, '팀 전국 진단표(scripts/전국진단표.py), 데이터랩 2024·2026년 1~8월·2025년 자료', 2, 19)
M(ws, r, 21, 28, '가로 = 체험·문화 소비 변화', F(8.5, False, MUTE), AL('left', 'center', False))
M(ws, r, 29, 37, '세로 = 평균 숙박일수(일)', F(8.5, False, MUTE), AL('right', 'center', False)); H(ws, r, 16)
r += 1; H(ws, r, 18); r += 1
section(ws, r, 2, 21, '진단 점수 상위 10곳', '가중치를 바꾸면 바로 바뀐다')
section(ws, r, 24, 37, '안동과 같은 유형')
r += 1
top = [(2, 3, 'center'), (4, 9, 'left'), (10, 12, 'right'), (14, 21, 'left')]
for (a, b, h), t in zip(top, ['순위', '시·군', '점수', '유형']):
    M(ws, r, a, b, t, F(9, True, MUTE), AL(h, 'center', False))
hline(ws, r, 2, 21, BLUE, 'medium'); H(ws, r, 20)
M(ws, r, 24, 37, rich((f'{len(SAME)}곳  ', 18, True, RED), ('체험·문화 소비 하락 + 짧은 숙박', 10, False, MUTE)), al=AL('left', 'center', False), r2=r + 1)
M(ws, r + 2, 24, 37, ' · '.join(s[:-1] for s in SAME), F(11, True, INK), AL('left', 'center', True), r2=r + 3)
M(ws, r + 4, 24, 37, f'이어드림 방식을 옮겨 쓸 1차 후보. 디지털 관광주민증을 운영하는 {JM["운영지역수"]}개 지자체에도 같은 틀을 적용할 수 있다.',
  F(9.5, False, MUTE), AL('left', 'top', True), r2=r + 6)
M(ws, r + 7, 24, 37, rich(('가중치를 무작위로 바꾸면 ', 9.5, False, MUTE), ('안동 순위는 18~100위', 9.5, True, INK), ('로 흔들린다. 그래서 점수보다 유형으로 읽는다.', 9.5, False, MUTE)),
  al=AL('left', 'top', True), r2=r + 9)
ws['AM9'] = f"={ref_sel}"; ws['AM9'].font = F(8, c=WHITE)                # 조건부 서식용(같은 시트 참조)
for k in range(1, 11):
    rr = r + k
    key = f"MATCH(LARGE({DR('M')},{k}),{DR('M')},0)"
    M(ws, rr, 2, 3, k, F(10, False, MUTE), AL('center', 'center', False))
    M(ws, rr, 4, 9, f"=INDEX({DR('A')},{key})", F(10.5, True), AL('left', 'center', False))
    M(ws, rr, 10, 12, f"=INDEX({DR('J')},{key})", F(10.5), AL('right', 'center', False), fmt='0.0')
    M(ws, rr, 14, 21, f"=INDEX({DR('L')},{key})", F(9.5, False, MUTE), AL('left', 'center', False))
    hline(ws, rr, 2, 21, TRACK); H(ws, rr, 20)
    ws.conditional_formatting.add(f'D{rr}', FormulaRule(formula=[f'$D{rr}="안동시"'], font=Font(name=FN, bold=True, color=RED)))
    ws.conditional_formatting.add(f'B{rr}:U{rr}', FormulaRule(formula=[f'$D{rr}=$AM$9'], fill=PatternFill(start_color=PALE, end_color=PALE, fill_type='solid'), font=Font(name=FN, bold=True, color=DEEP)))
r += 11; src(ws, r, '팀 전국 진단표. 점수는 위 파란 칸 가중치로 다시 계산', 2, 21); r += 1; H(ws, r, 12); r += 1
r = fold_table(ws, r, f'{len(DG)}곳 전체 표로 보기', '네 지표 값·점수·순위·유형(가중치 반영, 진단표 순서)',
               [(2, 6, 'left', None), (7, 10, 'right', PCT), (11, 13, 'right', '0.00'), (14, 16, 'right', '0.00'), (17, 19, 'right', '0.0%'),
                (20, 22, 'right', '0.0'), (23, 24, 'right', '0'), (25, 37, 'left', None)],
               ['시·군', '체험·문화 변화', '숙박일수', '저녁 전환율', '야간 방문', '점수', '순위', '유형'],
               [[f"='d_진단'!A{i}", f"='d_진단'!B{i}", f"='d_진단'!C{i}", f"='d_진단'!D{i}", f"='d_진단'!E{i}",
                 f"='d_진단'!J{i}", f"='d_진단'!K{i}", f"='d_진단'!L{i}"] for i in range(2, nD + 1)])
H(ws, r, 8); r += 1
r = details(ws, r, [
    ('진단 대상', f'{len(DG)}개 시·군: 네 지표가 모두 있고 방문 100만 명 이상, 광역시 자치구 제외. 체험·문화 변화 순위(146곳)와 대상이 다르다'),
    ('네 지표', '① 방문당 체험·문화 소비 변화율(2024 → 2026년 1~8월) ② 평균 숙박일수(LN_02_01_013, 2025년) ③ 저녁 전환율 = 18~21시 방문 ÷ 14~18시 방문 ④ 야간(21~24시) 방문 비중(BDT_01_01_006, 2026년 1~8월). 모두 낮을수록 문제'),
    ('문제 백분위', f'지표마다 {len(DG)}곳 중 그 값보다 낮은 곳의 비율로 0(좋음)~100(나쁨)을 매긴다. 75 이상 = 하위 25% = 문제'),
    ('점수·순위', '네 문제 백분위를 가중치로 평균. 가중치 합이 0이면 같은 비중으로 계산한다. 탐색 지표이며 정책 효과 점수가 아니다'),
    ('출처', '한국관광 데이터랩(카드 소비·방문, 평균 숙박일수, 시간대별 방문), 팀 전국 진단표(scripts/전국진단표.py)'),
])
printing(ws, r)

# ═════════════════════════════════════════════════════════
# 운영 시간 (옛 3_운영시간)
# ═════════════════════════════════════════════════════════
ws = wsT; grid(ws)
header(ws, '운영 시간', rich(('안동역 막차에 맞춘 ', 22, True, INK), ('18:30~21:00', 22, True, BLUE)),
       f'주말 저녁 승차는 {int(PEAK[:2])}~{int(PEAK[3:])}시가 가장 많고(하루 최다는 오후) 막차는 21~22시다. 릴레이 시작·종료 시각을 바꿔 창 안에 드는 승차를 본다.')
nav(ws, 6)
st = pd.read_csv(ROOT / 'data/external/팀원취합_정제/안동역_승하차_월별_열차종류별_long.csv')
st['연'] = st['연월'].str[:4].astype(int); st['월'] = st['연월'].str[5:7].astype(int)
st = st[st['월'] <= 8]
g1 = st.groupby(['연', '구분', '열차종류', '승하차', '시간대'])['인원'].sum().reset_index()
g2 = st.groupby(['연', '구분', '승하차', '시간대'])['인원'].sum().reset_index(); g2['열차종류'] = '전체'
ga = pd.concat([g1, g2])
ga['키'] = ga['연'].astype(str) + '|' + ga['구분'] + '|' + ga['열차종류'] + '|' + ga['승하차'] + '|' + ga['시간대']
dE = data_sheet('d_역'); write_df(dE, ga[['키', '인원']]); nE = len(ga) + 1
H(ws, 7, 8)
ref_y, ref_g, ref_t, ref_s, ref_e = controls(ws, 8, [
    (2, 6, '연도 ▼', '2026', None, '"2024,2025,2026"', None, '1~8월 합계로 비교한다'),
    (8, 13, '요일 ▼', '주말', None, '"평일,주말,공휴일,명절대수송"', None, '코레일 요일 구분'),
    (15, 20, '열차 ▼', '전체', None, '"전체,KTX-이음,새마을,무궁화"', None, '열차 종류'),
    (22, 26, '릴레이 시작(시)', 18.5, '0.0', None, ('decimal', 12, 24), '18.5 = 18:30'),
    (28, 32, '릴레이 종료(시)', 21, '0.0', None, ('decimal', 12, 24), '21 = 21:00')], hint='18.5 = 18:30')
dT = data_sheet('d_역계산')
dT.append(['시간대', '시', '승차', '하차', '창 안 승차', '창 밖 승차'])
for i, h in enumerate(range(5, 24), 2):
    key = f'{h:02d}-{h + 1:02d}'
    dT.cell(i, 1, f'{h:02d}시'); dT.cell(i, 2, h)
    for col, sb in ((3, '승차'), (4, '하차')):
        dT.cell(i, col, f"=SUMIFS('d_역'!$B$2:$B${nE},'d_역'!$A$2:$A${nE},{ref_y}&\"|\"&{ref_g}&\"|\"&{ref_t}&\"|{sb}|{key}\")")
    dT.cell(i, 5, f'=IF(AND(B{i}+1>{ref_s},B{i}<{ref_e}),C{i},NA())')
    dT.cell(i, 6, f'=IF(AND(B{i}+1>{ref_s},B{i}<{ref_e}),NA(),C{i})')
LAST = "LOOKUP(2,1/('d_역계산'!$C$2:$C$20>0),'d_역계산'!$B$2:$B$20)"
r0, tc = tiles_row(ws, 10, [
    ('저녁(17~22시) 최대 승차 시간대', "=INDEX('d_역계산'!$A$14:$A$18,MATCH(MAX('d_역계산'!$C$14:$C$18),'d_역계산'!$C$14:$C$18,0))", '@',
     "=\"승차 \"&TEXT(MAX('d_역계산'!$C$14:$C$18),\"#,##0\")&\"명 (1~8월 합계)\"", BLUE,
     '고른 연도·요일·열차의 1~8월 합계에서 17~22시 중 승차가 가장 많은 시간대. 하루 전체 최다가 아니다'),
    ('마지막 승차 시간대(막차)', f"=INDEX('d_역계산'!$A$2:$A$20,MATCH({LAST},'d_역계산'!$B$2:$B$20,0))", '@',
     "=\"22시 이후 승차 \"&TEXT(SUM('d_역계산'!$C$19:$C$20),\"#,##0\")&\"명\"", RED, '승차가 1명 이상인 마지막 시간대 = 열차 시각표상 막차'),
    ('릴레이 창 안 승차 비중', f"=SUMIFS('d_역계산'!$C$2:$C$20,'d_역계산'!$B$2:$B$20,\">=\"&INT({ref_s}),'d_역계산'!$B$2:$B$20,\"<\"&{ref_e})/SUM('d_역계산'!$C$2:$C$20)", '0.0%',
     f'="창 "&TEXT({ref_s}/24,"hh:mm")&"~"&TEXT({ref_e}/24,"hh:mm")&" 승차 ÷ 하루 승차"', BLUE, '시작 시각이 걸친 시간대부터 종료 시각 전 시간대까지의 승차 합 ÷ 하루 승차 합'),
    ('종료 후 막차까지 여유', f"=MAX(0,{LAST}+1-{ref_e})", '0.0"시간"',
     f'=IF({ref_e}>{LAST}+1,"막차 이후 → 귀가 수단 없음",IF({ref_e}>{LAST},"막차 시간대와 겹침 → 여유 없음","막차 전에 끝남"))', DEEP,
     '막차 시간대가 끝나는 시각 − 릴레이 종료 시각')])
font_cf(ws, tc[3].coordinate, f'{tc[3].coordinate}<=0', RED)
r = r0; src(ws, r, '코레일 안동역 월별·요일별·시간대별 승하차(KTX-이음·새마을·무궁화, 2024.1~2026.8, 팀원 취합), 1~8월 합계'); r += 1; H(ws, r, 10); r += 1
section(ws, r, 2, 26, '안동역 시간대별 승차', '고른 연도·요일·열차, 1~8월 합계')
legend_cell(ws, r, 27, 37, [('■', BLUE, '릴레이 창 안'), ('■', LINE, '창 밖')], h='right')
r += 1
ch = BarChart(); ch.type = 'col'; ch.grouping = 'clustered'; ch.overlap = 100; ch.gapWidth = 35
ch.series.append(bar_series(Reference(dT, min_col=6, min_row=2, max_row=20), '창 밖', LINE))
ch.series.append(bar_series(Reference(dT, min_col=5, min_row=2, max_row=20), '창 안', BLUE))
ch.set_categories(Reference(dT, min_col=1, min_row=2, max_row=20))
show_axis(ch.x_axis, 850); show_axis(ch.y_axis, 800, line=None, grid=True, fmt='#,##0')
bare(ch); place(ws, ch, 2, r, 37, r + 11)
rows_h(ws, r, 12)
r += 12; src(ws, r, '코레일 안동역 시간대별 승하차(2024.1~2026.8, 팀원 취합). 승차에는 주민이 섞여 있다'); r += 1; H(ws, r, 10); r += 1
section(ws, r, 2, 26, '안동역 시간대별 하차(도착)', '같은 조건')
legend_cell(ws, r, 27, 37, [('━', DEEP, '하차')], h='right')
r += 1
ch = LineChart()
ch.series.append(line_series(Reference(dT, min_col=4, min_row=2, max_row=20), '하차', DEEP))
ch.set_categories(Reference(dT, min_col=1, min_row=2, max_row=20))
show_axis(ch.x_axis, 850); show_axis(ch.y_axis, 800, line=None, grid=True, fmt='#,##0')
bare(ch); place(ws, ch, 2, r, 37, r + 7)
rows_h(ws, r, 8)
r += 8; src(ws, r, '코레일 안동역 시간대별 승하차(2024.1~2026.8, 팀원 취합)'); r += 1; H(ws, r, 10); r += 1
q13 = SV['Q13_당일귀가자중_20~22시']
survey_line(ws, r, f"당일 귀가한 방문자 {q13['n']}명 중 {q13['k']}명({q13['pct']:.0f}%)이 20~22시 막차 시간대에 귀가했다. 릴레이가 21시 전에 끝나야 하는 이유와 같은 방향이다.")
r += 1; H(ws, r, 14); r += 1
r = fold_table(ws, r, '시간대별 승하차 표로 보기', '위 그래프의 숫자(고른 조건 그대로)',
               [(2, 7, 'left', None), (8, 14, 'right', '#,##0'), (15, 21, 'right', '#,##0'), (22, 28, 'right', '#,##0'), (29, 37, 'left', None)],
               ['시간대', '승차', '하차', '릴레이 창 안 승차', ''],
               [[f"='d_역계산'!A{i}", f"='d_역계산'!C{i}", f"='d_역계산'!D{i}", f"=IFERROR('d_역계산'!E{i},\"\")",
                 f"=IF(ISNUMBER('d_역계산'!E{i}),\"창 안\",\"\")&IF(AND('d_역계산'!C{i}>0,N('d_역계산'!C{i + 1})=0),\"  막차 시간대\",\"\")"] for i in range(2, 21)])
H(ws, r, 8); r += 1
r = details(ws, r, [
    ('읽는 법', '시간 분포에는 열차 시각표가 반영된다(22시 이후 0 = 열차가 없음). 릴레이는 막차 전에 역에 닿도록 18:30에 시작해 21:00에 끝낸다'),
    ('주의', '승차 인원에는 주민이 섞여 있어 "관광객"이라 부르지 않는다. 값은 그 달 해당 요일 전체의 합이다. 떠나는 시각이 아니라 주말 안동역 승차 분포로 읽는다'),
    ('출처', '코레일 안동역 월별·요일별·시간대별 승하차(KTX-이음·새마을·무궁화, 2024.1~2026.8, 팀원 취합). 연도 간 비교를 위해 1~8월만 합산'),
])
printing(ws, r)

# ═════════════════════════════════════════════════════════
# 버스 (옛 4_버스)
# ═════════════════════════════════════════════════════════
ws = wsB; grid(ws)
header(ws, '버스', rich(('19시 이후 원도심 → 월영교 버스 ', 22, True, INK), (f'{BUS["19시이후"]}회', 22, True, RED)),
       '안동역 ↔ 원도심은 밤 10시까지 다니지만 원도심 → 월영교는 112번 한 노선뿐이다. 노선을 고르고, 저녁 운행을 더해 본다.', accent=RED)
nav(ws, 6)
bus = pd.read_excel(ROOT / '조사/01_시내버스_노선시간표.xlsx', sheet_name='출발시각_전체')
bus['노선번호'] = bus['노선번호'].astype(str)
bus['시'] = pd.to_numeric(bus['시(時)'], errors='coerce')
bus['시각'] = bus['출발시각'].astype(str).str[:5]
bus['시각값'] = bus['시각'].map(lambda t: int(t[:2]) / 24 + int(t[3:5]) / 1440 if re.match(r'\d\d:\d\d', t) else None)
bg = bus.groupby(['노선번호', '시간표 구분', '시']).size().reset_index(name='회')
bg['키'] = bg['노선번호'] + '|' + bg['시간표 구분'] + '|' + bg['시'].astype(int).astype(str)
dBs = data_sheet('d_버스'); write_df(dBs, bg[['키', '회']]); nBs = len(bg) + 1
dB2 = data_sheet('d_버스출발'); write_df(dB2, bus[['노선번호', '시간표 구분', '시각값']]); nB2 = len(bus) + 1
routes = sorted(bus['노선번호'].unique(), key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else 0, x))
dRt = data_sheet('d_노선목록'); write_df(dRt, pd.DataFrame({'노선': routes}))
seg = pd.read_excel(ROOT / '조사/01_시내버스_노선시간표.xlsx', sheet_name='시간대별_운행(평일)')
seg = seg.rename(columns={seg.columns[0]: '구간'})
seg = seg[seg['구간'].astype(str).str.contains('→')].reset_index(drop=True)
stops = pd.read_excel(ROOT / '조사/04_BIS정류장_위치.xlsx', sheet_name='안동_전체_정류장')
N_BIT = int((stops['안내기 설치 여부'] == '설치').sum())
H(ws, 7, 8)
ref_r, ref_k, ref_x = controls(ws, 8, [
    (2, 7, '노선 ▼', '112', None, f"='d_노선목록'!$A$2:$A${len(routes) + 1}", None, f'안동 시내버스 {len(routes)}개 노선'),
    (9, 15, '시간표 ▼', '평일', None, '"평일,공휴일(일요일)"', None, '공휴일 시간표가 없는 노선이 많다'),
    (17, 24, '19~21시 원도심→월영교 추가(회)', 0, '0"회"', None, ('whole', 0, 20), '관광택시 저녁 배치나 셔틀로 몇 회를 채우면 어떻게 바뀌는지 보는 가정 값')],
    hint='추가 운행은 택시·셔틀로 채운다고 본 가정 값. 0 = 지금')
jw = list(seg['구간']).index('원도심→월영교')
iA = 3 + list(seg['구간']).index('안동역→원도심'); iB = 3 + list(seg['구간']).index('원도심→안동역')
dBc = data_sheet('d_버스계산')
dBc.append(['시', '선택 노선'] + list(seg['구간']) + ['원도심→월영교(추가 반영)'])
XC = 3 + len(seg)
for i, h in enumerate(range(5, 24), 2):
    dBc.cell(i, 1, f'{h:02d}시')
    dBc.cell(i, 2, f"=SUMIFS('d_버스'!$B$2:$B${nBs},'d_버스'!$A$2:$A${nBs},{ref_r}&\"|\"&{ref_k}&\"|{h}\")")
    for j, sname in enumerate(seg['구간']):
        v = seg.loc[seg['구간'] == sname, f'{h:02d}시'].values
        dBc.cell(i, 3 + j, float(v[0]) if len(v) and pd.notna(v[0]) else 0)
    dBc.cell(i, XC, f"={CL(3 + jw)}{i}+IF(AND({h}>=19,{h}<21),{ref_x}/2,0)")
dB2.cell(1, 4, '선택 노선 시각')                                   # 첫차·막차 보조 열(MINIFS 없는 엑셀 2016에서도 동작)
for i in range(2, nB2 + 1):
    dB2.cell(i, 4, f'=IF(AND(A{i}&""={ref_r}&"",B{i}={ref_k}),C{i},"")')
r0, tc = tiles_row(ws, 10, [
    ('고른 노선 운행 횟수', "=SUM('d_버스계산'!$B$2:$B$20)", '0"회"',
     f"=IF(SUM('d_버스계산'!$B$2:$B$20)=0,\"이 시간표에는 운행 없음\",\"첫차 \"&TEXT(MIN('d_버스출발'!$D$2:$D${nB2}),\"hh:mm\")&\" · 막차 \"&TEXT(MAX('d_버스출발'!$D$2:$D${nB2}),\"hh:mm\"))",
     DEEP, '고른 노선·시간표의 하루 기점 출발 횟수. 첫차·막차는 기점 출발 시각'),
    ('원도심 → 월영교 19시 이후', f"=SUM('d_버스계산'!${CL(XC)}$16:${CL(XC)}$20)", '0"회"', f'추가 전 {BUS["19시이후"]}회 · 112번 원도심 출발 막차 {BUS["막차"]}(평일)', RED,
     '평일 시간표 기준 19시 이후 원도심 → 월영교 운행 + 위 추가 운행 칸 값'),
    ('안동역 → 원도심 19시 이후', f"=SUM('d_버스계산'!${CL(iA)}$16:${CL(iA)}$20)", '0"회"', '막차 22:10 · 원도심 → 안동역 막차 22:40', BLUE,
     '평일 시간표 기준 구간별 운행 횟수(조사 01)'),
    ('버스정보 안내기 있는 정류장', N_BIT, '#,##0"곳"', f'전체 {len(stops):,}곳 중 · 월영교 500m 4곳 중 1곳', DEEP,
     '안동시 버스정보시스템 정류장 목록의 안내기 설치 여부(bitYn)')])
font_cf(ws, tc[1].coordinate, f'{tc[1].coordinate}>0', BLUE)
r = r0; src(ws, r, '안동시 버스정보시스템 공개 시간표·노선·정류장(2026-09-22 조회, 46개 노선·3,309개 정류장, 안내기 = bitYn)'); r += 1; H(ws, r, 10); r += 1
section(ws, r, 2, 18, '고른 노선의 시간대별 출발', '기점 출발 횟수')
section(ws, r, 21, 37, '구간별 시간대 운행', '평일, 기점 출발')
r += 1
legend_cell(ws, r, 2, 18, [('■', BLUE, '고른 노선')])
legend_cell(ws, r, 21, 37, [('━', RED, '원도심→월영교(추가 반영)'), ('━', GRAY, '안동역→원도심'), ('━', LINE, '원도심→안동역')]); H(ws, r, 18)
r += 1
ch = BarChart(); ch.type = 'col'; ch.gapWidth = 40
ch.series.append(bar_series(Reference(dBc, min_col=2, min_row=2, max_row=20), '고른 노선', BLUE))
ch.set_categories(Reference(dBc, min_col=1, min_row=2, max_row=20))
show_axis(ch.x_axis, 800); show_axis(ch.y_axis, 800, line=None, grid=True, fmt='0')
bare(ch); place(ws, ch, 2, r, 18, r + 9)
ch = LineChart()
ch.series.append(line_series(Reference(dBc, min_col=iB, min_row=2, max_row=20), '원도심→안동역', LINE))
ch.series.append(line_series(Reference(dBc, min_col=iA, min_row=2, max_row=20), '안동역→원도심', GRAY))
ch.series.append(line_series(Reference(dBc, min_col=XC, min_row=2, max_row=20), '원도심→월영교', RED, 2.75))
ch.set_categories(Reference(dBc, min_col=1, min_row=2, max_row=20))
show_axis(ch.x_axis, 800); show_axis(ch.y_axis, 800, line=None, grid=True, fmt='0')
bare(ch); place(ws, ch, 21, r, 37, r + 9)
rows_h(ws, r, 10)
r += 10; src(ws, r, '안동시 버스정보시스템 시간표(2026-09-22 조회), 조사 01 시간대별 운행표. 시각은 기점 출발 기준'); r += 1; H(ws, r, 12); r += 1
section(ws, r, 2, 26, '안동 시내 지도 위 112번 노선', '원도심과 월영교를 잇는 유일한 시내버스')
r += 1
legend_cell(ws, r, 2, 37, [('━', RED, '112번 노선(모든 방향)'), ('○', RED, '112번 정류장'), ('●', DEEP, '안동역·원도심·월영교'), ('■', 'A9C8EC', '낙동강·안동호'), ('┅', GRAY, '행정동 경계')]); H(ws, r, 18)
r += 1
spec = importlib.util.spec_from_file_location('지도', ROOT / 'scripts/요약대시보드_지도.py'); mp = importlib.util.module_from_spec(spec); spec.loader.exec_module(mp)
png = mp.make_map(OUT / '그림/버스_112번_지도.png', km=Q['원도심_월영교_km'], last_bus=BUS['막차'], after19=BUS['19시이후'])
img = XLImage(str(png)); img.width, img.height = 1000, round(1000 * img.height / img.width)
img.anchor = f'B{r}'; ws.add_image(img)
MAP_ROWS = math.ceil(img.height * 0.75 / 20) + 1
M(ws, r, 29, 37, '지도 읽는 법', F(10, True), AL('left', 'bottom', False))
M(ws, r + 1, 29, 37, '빨간 선이 112번이 실제로 다니는 길이다(버스정보시스템 노선 선형, 모든 방향). 흰 점은 정류장.\n\n'
  f'원도심에서 월영교까지 {Q["원도심_월영교_km"]:.1f}km. 이 길을 잇는 시내버스는 112번 하나이고, 원도심 출발 막차는 {BUS["막차"]}(평일)다.\n\n'
  '안동역·터미널은 원도심에서 서쪽으로 떨어져 있어 역 → 원도심 → 월영교가 버스 한 번으로 이어지지 않는다.',
  F(10), AL('left', 'top', True), r2=r + 12)
rows_h(ws, r, MAP_ROWS)
r += MAP_ROWS; src(ws, r, '지도 © OpenStreetMap contributors(ODbL)·OpenFreeMap 2026-09-13 · 행정동 경계 통계청 SGIS(vuski/admdongkor 2026.7) · 112번 노선 선형·정류장 안동시 버스정보시스템(2026-09-29 수집)'); r += 1; H(ws, r, 10); r += 1
q3 = SV['Q3_버스불편_버스이용방문자']; q4w = SV['Q4_포기한곳_방문자']['야간 명소(월영교)']
survey_line(ws, r, f"시내버스로 다닌 방문자 {q3['n']}명 중 {q3['k']}명({q3['pct']:.0f}%)이 불편했다. 이동이 불편해 포기한 곳 1위는 월영교 같은 야간 명소({q4w['pct']:.0f}%, {q4w['k']}/{q4w['n']}명).")
r += 1; H(ws, r, 14); r += 1
r = fold_table(ws, r, '시간대별 운행 표로 보기', '고른 노선과 주요 구간의 시간대별 기점 출발 횟수',
               [(2, 6, 'left', None), (7, 12, 'right', '0'), (13, 19, 'right', '0'), (20, 26, 'right', '0'), (27, 37, 'right', '0')],
               ['시간대', '고른 노선', '안동역→원도심', '원도심→안동역', '원도심→월영교(추가 반영)'],
               [[f"='d_버스계산'!A{i}", f"='d_버스계산'!B{i}", f"='d_버스계산'!{CL(iA)}{i}", f"='d_버스계산'!{CL(iB)}{i}", f"='d_버스계산'!{CL(XC)}{i}"] for i in range(2, 21)])
H(ws, r, 8); r += 1
r = details(ws, r, [
    ('읽는 법', '버스 시각은 기점 출발 시각이라 구간 통과는 더 늦다. 공휴일 시간표가 없는 노선이 많아 토요일 운행은 단정하지 않는다'),
    ('추가 운행 칸', '관광택시 저녁 배치나 셔틀로 19~21시에 몇 회를 채우면 그래프가 어떻게 바뀌는지 보는 가정이다. 차량 대수·배차 간격은 이용량·회차 시간·견적 없이 정하지 않는다'),
    ('출처', f'안동시 버스정보시스템 공개 시간표·노선·정류장(2026-09-22 조회, {BIS_ROUTES}개 노선·{len(stops):,}개 정류장, 안내기 = bitYn), 국토교통부 전국 버스정류장 위치정보(대조)'),
])
printing(ws, r)

# ═════════════════════════════════════════════════════════
# 월영교 (옛 5_월영교)
# ═════════════════════════════════════════════════════════
ws = wsW; grid(ws)
wy = pd.DataFrame(Q['월영교조사'])
wy['업종'] = wy['상권업종중분류명'].str.strip().replace({'비알코올': '카페'})
wy['종료값'] = wy['영업종료'].map(lambda t: int(t[:2]) + int(t[3:5]) / 60 if isinstance(t, str) and re.match(r'\d\d:\d\d', t) else np.nan)
wy = wy[wy['상태'] == '영업'].sort_values('종료값').reset_index(drop=True)
N_OPEN = len(wy)
WY_PUB = R1['월영교'].get('주점', 0)
header(ws, '월영교', rich(('사람은 모이지만 ', 22, True, INK), ('21시 이후 식사·주점이 거의 없다', 22, True, RED)),
       f'외곽 관광지 방문자의 {MANHYU:.1f}%가 월영교에 들르지만 소비 전환 배율은 {WY["소비방문배율"]:.2f}. 팝업 부스를 넣어 빈자리를 채워 본다(부스 수는 가정).', accent=RED)
nav(ws, 6)
dW = data_sheet('d_철도'); write_df(dW, RAIL[['관광지명', '방문점유율_pct', '방문객소비건수점유율_pct', '소비방문배율']]); nW = len(RAIL) + 1
H(ws, 7, 8)
ref_b, ref_z, ref_rl = controls(ws, 8, [
    (2, 7, '팝업 식사·주점 부스(개)', 0, '0"개"', None, ('whole', 0, 50), '0 = 지금 상태. 부스 수는 처리량·부지 조건 확인 뒤 정한다(가정 값)'),
    (9, 14, '팝업 종료 시각(시)', 22, '0"시"', None, ('whole', 18, 24), '21시 이후까지 열어야 식사 가능한 곳에 들어간다'),
    (16, 24, '관광지 ▼', '월영교', None, f"='d_철도'!$A$2:$A${nW}", None, '소비 전환 배율을 볼 관광지')],
    hint='부스 수는 가정 값. 0 = 지금 상태')
dM = data_sheet('d_월영교')
dM.append(['업체', '업종', '영업 종료(시)', '식사 가능', '21시 전 종료', '21시 이후'])
for _, rw in wy.iterrows():
    dM.append([rw['상호명'], rw['업종'], rw['종료값'], 1 if rw['업종'] in ('한식', '서양식') else 0])
nM = len(wy) + 1
dM.cell(nM + 1, 1, '팝업 부스'); dM.cell(nM + 1, 2, '팝업'); dM.cell(nM + 1, 3, f"=IF({ref_b}>0,{ref_z},NA())"); dM.cell(nM + 1, 4, 1)
for i in range(2, nM + 2):
    dM.cell(i, 5, f'=IF(AND(ISNUMBER(C{i}),C{i}<21),C{i},NA())')
    dM.cell(i, 6, f'=IF(AND(ISNUMBER(C{i}),C{i}>=21),C{i},NA())')
BASE21 = f"COUNTIFS('d_월영교'!$D$2:$D${nM},1,'d_월영교'!$C$2:$C${nM},\">=21\")"
RL = lambda col: f"INDEX('d_철도'!${col}$2:${col}${nW},MATCH({ref_rl},'d_철도'!$A$2:$A${nW},0))"
r0, tc = tiles_row(ws, 10, [
    ('21시까지 식사 가능한 곳', f"={BASE21}+IF({ref_z}>=21,{ref_b},0)", '0"곳"',
     f"=\"영업 {N_OPEN}곳 중 · 팝업 전 \"&{BASE21}&\"곳\"", RED, '월영교 반경 1km 영업 음식점 중 한식·서양식이면서 21시 이후까지 여는 곳 + 21시 이후까지 여는 팝업 부스'),
    ('주점', f"=IF({ref_z}>=21,{ref_b},0)", '0"곳"', f"팝업 전 {WY_PUB}곳 · 원도심 1km는 {sum(R1['원도심'].values())}곳 중 {R1['원도심'].get('주점', 0)}곳", RED,
     '소상공인 상가정보(2026.6) 반경 1km 업종 중분류 기준 + 팝업 부스'),
    ('고른 관광지 소비 전환 배율', f"={RL('D')}", '0.00',
     f"=\"방문 \"&TEXT({RL('B')},\"0.0\")&\"% vs 소비 건수 \"&TEXT({RL('C')},\"0.0\")&\"% (2022.4~6)\"", INK,
     '소비 건수 점유율 ÷ 방문 점유율. 1보다 작으면 방문만큼 쓰지 않는 곳. 한국철도공사 8대 도시 가명결합 분석(소비 = 건수)이라 데이터랩 숫자와 따로 본다'),
    ('외곽 방문자 중 월영교도 방문', MANHYU / 100, '0.0%', f'만휴정 {MANHYU:.1f}% · 도산서원 {DOSAN:.1f}% (철도공사)', BLUE,
     '한국철도공사 8대 도시(안동) 관광 형태 분석(2022.4~6) 연관 규칙: 만휴정·도산서원 방문자의 월영교 동시 방문 비율')])
for c_ in (tc[0].coordinate, tc[1].coordinate):
    font_cf(ws, c_, f'{ref_b.split("!")[1]}>0', BLUE)
font_cf(ws, tc[2].coordinate, f'{tc[2].coordinate}<1', RED)
font_cf(ws, tc[2].coordinate, f'{tc[2].coordinate}>=1', BLUE)
r = r0; src(ws, r, '소상공인 상가(상권)정보 2026.6(반경 1km) · 팀 확인(영업 종료, 조사 16번) · 한국철도공사 8대 도시(안동) 관광 형태 분석 2022.4~6(소비 = 건수)'); r += 1; H(ws, r, 10); r += 1
section(ws, r, 2, 18, '월영교 1km 영업 음식점의 문 닫는 시각', '맨 아래 = 팝업')
section(ws, r, 21, 37, '음식점 업종 구성', '월영교 1km vs 원도심 1km')
r += 1
legend_cell(ws, r, 2, 18, [('■', RED_LIGHT, '21시 전 종료'), ('■', BLUE, '21시 이후까지')])
legend_cell(ws, r, 21, 37, [('■', RED, f'월영교 1km {sum(R1["월영교"].values())}곳'), ('■', GRAY_L, f'원도심 1km {sum(R1["원도심"].values())}곳')]); H(ws, r, 18)
r += 1
ch = BarChart(); ch.type = 'bar'; ch.grouping = 'clustered'; ch.overlap = 100; ch.gapWidth = 40
ch.series.append(bar_series(Reference(dM, min_col=5, min_row=2, max_row=nM + 1), '21시 전', RED_LIGHT))
ch.series.append(bar_series(Reference(dM, min_col=6, min_row=2, max_row=nM + 1), '21시 이후', BLUE))
ch.set_categories(Reference(dM, min_col=1, min_row=2, max_row=nM + 1)); ch.x_axis.scaling.orientation = 'maxMin'
show_axis(ch.x_axis, 800); show_axis(ch.y_axis, 800, line=None, grid=True, fmt='0"시"')
ch.y_axis.scaling.min = 17; ch.y_axis.scaling.max = 24; ch.y_axis.majorUnit = 1
bare(ch); place(ws, ch, 2, r, 18, r + 13)
KIND = [('한식', ['한식']), ('카페', ['비알코올']), ('주점', ['주점']), ('서양식', ['서양식']), ('기타', None)]
NAMED = [k for _, ks in KIND if ks for k in ks]
dK = data_sheet('d_업종구성'); dK.append(['업종', '월영교 1km', '원도심 1km'])
for nm_, keys in KIND:
    row = [nm_]
    for area in ('월영교', '원도심'):
        d_ = R1[area]; tot = sum(d_.values())
        v = sum(d_.get(k, 0) for k in keys) if keys else tot - sum(d_.get(k, 0) for k in NAMED)
        row.append(v / tot)
    dK.append(row)
    for cc in (2, 3): dK.cell(dK.max_row, cc).number_format = '0%'
ch = BarChart(); ch.type = 'col'; ch.gapWidth = 60; ch.overlap = -5
ch.series.append(bar_series(Reference(dK, min_col=2, min_row=2, max_row=6), '월영교', RED))
ch.series.append(bar_series(Reference(dK, min_col=3, min_row=2, max_row=6), '원도심', GRAY_L))
for s_ in ch.series: s_.dLbls = labels(pos='outEnd', fmt='0%', sz=800)
ch.set_categories(Reference(dK, min_col=1, min_row=2, max_row=6))
show_axis(ch.x_axis, 900); show_axis(ch.y_axis, 800, line=None, grid=True, fmt='0%')
bare(ch); place(ws, ch, 21, r, 37, r + 13)
rows_h(ws, r, 14)
r += 14
src(ws, r, '소상공인 상가정보 2026.6(반경 1km), 문 닫는 시각은 팀 확인(조사 16번, 조사일 기록 보완 중)', 2, 19)
src(ws, r, f'소상공인 상가(상권)정보 2026.6, 반경 1km 업종 중분류', 21, 37); r += 1; H(ws, r, 12); r += 1
section(ws, r, 2, 26, '관광지별 방문 vs 소비 점유율', '철도공사 2022.4~6, 소비 = 건수')
legend_cell(ws, r, 27, 37, [('■', GRAY_L, '방문 점유율'), ('■', BLUE, '소비 건수 점유율')], h='right')
r += 1
ch = BarChart(); ch.type = 'bar'; ch.gapWidth = 50
ch.series.append(bar_series(Reference(dW, min_col=2, min_row=2, max_row=nW), '방문', GRAY_L))
ch.series.append(bar_series(Reference(dW, min_col=3, min_row=2, max_row=nW), '소비', BLUE))
ch.set_categories(Reference(dW, min_col=1, min_row=2, max_row=nW)); ch.x_axis.scaling.orientation = 'maxMin'
show_axis(ch.x_axis, 800); show_axis(ch.y_axis, 800, line=None, grid=True, fmt='0"%"')
bare(ch); place(ws, ch, 2, r, 37, r + 15)
rows_h(ws, r, 16)
r += 16; src(ws, r, '한국철도공사 8대 도시(안동) 관광 형태 분석, 가명결합, 2022.4~6. 소비 = 건수라 데이터랩 숫자와 한 표에 올리지 않는다'); r += 1; H(ws, r, 10); r += 1
q9, q9c = SV['Q9_월영교밤_부족_방문자'], SV['Q9_월영교밤_충분_방문자']
survey_line(ws, r, f"20시 이후 월영교 주변 식당·편의시설이 부족했다 {q9['pct']:.0f}%({q9['k']}/{q9['n']}명), 충분했다 {q9c['pct']:.0f}%. "
                   f"21~23시 팝업 포차는 방문자 {SV['Q10_야간팝업포차']['방문자_top2']['pct']:.0f}%가 긍정(의향이지 이용률이 아니다).")
r += 1; H(ws, r, 14); r += 1
r = fold_table(ws, r, f'월영교 1km 영업 음식점 {N_OPEN}곳 표로 보기', '업종·문 닫는 시각(팀 확인)',
               [(2, 13, 'left', None), (14, 19, 'left', None), (20, 25, 'right', None), (26, 37, 'left', None)],
               ['업체', '업종', '문 닫는 시각', '21시 이후 식사'],
               [[rw['상호명'], rw['업종'], rw['영업종료'] if isinstance(rw['영업종료'], str) else '-',
                 '가능' if (rw['업종'] in ('한식', '서양식') and rw['종료값'] >= 21) else ''] for _, rw in wy.iterrows()])
H(ws, r, 8); r += 1
r = fold_table(ws, r, '관광지별 방문·소비 표로 보기', '방문 점유율, 소비 건수 점유율, 소비 전환 배율',
               [(2, 13, 'left', None), (14, 20, 'right', '0.00"%"'), (21, 27, 'right', '0.00"%"'), (28, 37, 'right', '0.00')],
               ['관광지', '방문 점유율', '소비 건수 점유율', '소비 전환 배율'],
               [[f"='d_철도'!A{i}", f"='d_철도'!B{i}", f"='d_철도'!C{i}", f"='d_철도'!D{i}"] for i in range(2, nW + 1)])
H(ws, r, 8); r += 1
r = details(ws, r, [
    ('읽는 법', '월영교는 외곽을 돈 방문객이 돌아오며 모이는 곳인데, 반경 1km 식당 대부분이 20:30 전에 닫고 22시 이후엔 카페만 남으며 주점은 없다. 18시 이후 운영하는 체험은 문보트·황포돛배뿐이다'),
    ('팝업 칸', '팝업은 21시 이후 식사·주류를 채우는 자리다. 부스 수는 처리량·부지 조건을 확인한 뒤 정하며 위 칸은 가정 값이다'),
    ('영업 종료 시각', '팀 확인(조사 16번). 조사일·방법 기록은 보완 중이다'),
    ('출처', '소상공인 상가(상권)정보(2026.6), 팀 확인(영업 종료), 한국철도공사 8대 도시(안동) 관광 형태 분석(2022.4~6, 소비는 건수)'),
])
printing(ws, r)

# ═════════════════════════════════════════════════════════
# 설문조사 (옛 10_설문)
# ═════════════════════════════════════════════════════════
ws = wsV; grid(ws)
header(ws, '설문조사', rich(('방문객이 직접 말한 ', 22, True, INK), ('불편', 22, True, RED), ('과 ', 22, True, INK), ('의향', 22, True, BLUE)),
       f'팀 온라인 설문 {SV_N}명(방문 경험 {SV_V}명, 2026.9.23~24). 응답자 범위와 이동수단을 바꿔 본다. 불편은 근거로 읽고, 의향은 참여율로 쓰지 않는다.')
nav(ws, 6)
svd = pd.read_csv(ROOT / 'data/설문/안동관광온라인설문_응답_정제.csv')
LK = {'매우있다': 5, '매우 있다': 5, '있다': 4, '보통이다': 3, '별로없다': 2, '별로 없다': 2, '별로없다(자차/렌터카 이용 등)': 2, '전혀없다': 1, '전혀 없다': 1}
q2 = svd['Q2_주_이동수단'].fillna('')
q4s = svd['Q4_이동불편_포기한곳'].fillna('')
K11 = {'체험 정보가 부족해서': '정보 부족', '줄을 오래 서거나 예약하기 불편해서': '줄·예약 불편', '다음 장소로 이동할 시간이 부족해서': '이동 시간 부족', '가격이 부담스러워서': '가격 부담'}
K13 = {'18시 이전': '18시 이전', '18시 ~ 20시': '18-20시', '20시 ~ 22시 (막차 시간대)': '20-22시(막차)', '당일 귀가 안 함 (안동에서 숙박)': '숙박'}
dSv = data_sheet('d_설문')
dSv.append(['방문', '이동', '버스주이용', 'Q3', '포기_외곽', '포기_월영교', '포기_원도심', '포기_없음', 'Q4응답', 'Q9', 'Q11', 'Q13', 'Q6', 'Q8', 'Q10', 'Q12'])
for i_, rw in svd.iterrows():
    mode = '자가용' if q2[i_] == '자가용 / 렌터카' else ('미응답' if q2[i_] == '' else '차 없음')
    q9v = rw['Q9_월영교_밤_식당편의']
    q9c_ = '부족' if q9v in ('부족했다', '매우부족했다') else ('보통' if q9v == '보통이다' else ('충분' if q9v == '충분하다' else '미응답'))
    q11 = rw['Q11_유료체험_망설임']; q11c = K11.get(q11, '미응답' if pd.isna(q11) else '기타')
    dSv.append([rw['Q1_3년내_방문'], mode, int(q2[i_] == '대중교통 (시내버스 등)'), rw['Q3_대중교통_불편'] if pd.notna(rw['Q3_대중교통_불편']) else '미응답',
                int('외곽 관광지' in q4s[i_]), int('야간 명소' in q4s[i_]), int('원도심의 밤' in q4s[i_]), int(q4s[i_].startswith('없음')), int(q4s[i_] != ''),
                q9c_, q11c, K13.get(rw['Q13_귀가_교통_시간대'], '미응답')] +
               [LK.get(rw[c], 0) for c in ('Q6_영수증_체험쿠폰_의향', 'Q8_야간택시셔틀_의향', 'Q10_야간팝업포차_의향', 'Q12_영수증_축제혜택_의향')])
nSv = len(svd) + 1
H(ws, 7, 8)
ref_sp, ref_md = controls(ws, 8, [
    (2, 8, '응답자 범위 ▼', '방문자만', None, '"방문자만,전체"', None, "안 가 본 응답자도 뒤 문항에 답해서 경험 문항은 '방문자만'이 기본"),
    (10, 16, '이동수단 ▼', '전체', None, '"전체,자가용·렌터카,차 없음"', None, '주 이동수단으로 나눠 본다')])
rg = lambda col: f"'d_설문'!${col}$2:${col}${nSv}"
dSc = data_sheet('d_설문계산')
dSc['A1'] = '방문 조건'; dSc['B1'] = f'=IF({ref_sp}="방문자만","예","*")'
dSc['A2'] = '이동 조건'; dSc['B2'] = f'=IF({ref_md}="전체","*",IF({ref_md}="자가용·렌터카","자가용","차 없음"))'
BASE = f"{rg('A')},'d_설문계산'!$B$1,{rg('B')},'d_설문계산'!$B$2"
cnt = lambda extra='': f"COUNTIFS({BASE}{',' + extra if extra else ''})"
dSc['A3'] = '고른 응답자 수'; dSc['B3'] = '=' + cnt()
M(ws, 9, 18, 37, "=\"고른 응답자 \"&'d_설문계산'!$B$3&\"명\"", F(12, True, DEEP), AL('left', 'center', False))


def pct_card(lab, num, den, sub_txt, color, mm):
    return (lab, f"=IFERROR({cnt(num)}/{cnt(den)},\"해당 없음\")", '0%', f"=\"{sub_txt} \"&{cnt(num)}&\"명 / \"&{cnt(den)}&\"명\"", color, mm)


r0, tc = tiles_row(ws, 10, [
    pct_card('시내버스 이용자 중 "불편했다"', f"{rg('C')},1,{rg('D')},\"불편했다\"", f"{rg('C')},1", '주 이동수단이 시내버스인 사람 중', RED, '3번 문항. 주 이동수단이 시내버스인 응답자 중 "불편했다"'),
    pct_card('이동이 불편해 야간 명소(월영교) 포기', f"{rg('I')},1,{rg('F')},1", f"{rg('I')},1", '포기한 곳 문항 응답자 중', RED, '4번 문항(중복 선택). 이동이 불편해 가고 싶었지만 못 간 곳'),
    pct_card('20시 이후 월영교 식당·편의시설 부족', f"{rg('J')},\"부족\"", f"{rg('J')},\"<>미응답\"", '부족·매우 부족', RED, '9번 문항'),
    pct_card('당일 귀가자 중 20~22시(막차) 귀가', f"{rg('L')},\"20-22시(막차)\"", f"{rg('L')},\"<>미응답\",{rg('L')},\"<>숙박\"", '숙박자 제외', DEEP, '13번 문항. 숙박한 사람은 뺐다')])
r = r0; src(ws, r, '팀 온라인 설문(구글폼, 2026.9.23~24, 응답 103명·방문 경험 72명, 편의 표본)'); r += 1; H(ws, r, 10); r += 1
IT = [('M', '체험 쿠폰(영수증 인증)'), ('N', '야간 택시·셔틀(18:30~21:00)'), ('O', '월영교 야간 팝업(21~23시)'), ('P', '축제 혜택(영수증)')]
LV = [(5, '매우 있다', DEEP), (4, '있다', SOFT), (3, '보통', LINE), (2, '별로 없다', RED_LIGHT), (1, '전혀 없다', RED)]
section(ws, r, 2, 20, '이용 의향 (5점)', '고른 응답자 중 비율. 의향은 참여율이 아니다')
legend_cell(ws, r, 21, 37, [('■', c, t) for _, t, c in LV], h='right')
r += 1
dSc['D1'] = '문항'
for j, (_, t, _c) in enumerate(LV): dSc.cell(1, 5 + j, t)
for i, (col, t) in enumerate(IT, 2):
    dSc.cell(i, 4, t)
    for j, (v, _t, _c) in enumerate(LV):
        dSc.cell(i, 5 + j, f"=IFERROR({cnt(f'{rg(col)},{v}')}/{cnt(f'{rg(col)},\">0\"')},0)").number_format = '0%'
ch = BarChart(); ch.type = 'bar'; ch.grouping = 'percentStacked'; ch.overlap = 100; ch.gapWidth = 45
for j, (_v, t, colr) in enumerate(LV):
    s_ = bar_series(Reference(dSc, min_col=5 + j, min_row=2, max_row=5), t, colr)
    if j in (0, 1): s_.dLbls = labels(fmt='0%', sz=800, color=WHITE if j == 0 else INK, b=True, pos='ctr')
    ch.series.append(s_)
ch.set_categories(Reference(dSc, min_col=4, min_row=2, max_row=5)); ch.x_axis.scaling.orientation = 'maxMin'
show_axis(ch.x_axis, 900); show_axis(ch.y_axis, 800, line=None, fmt='0%')
bare(ch); place(ws, ch, 2, r, 37, r + 8)
rows_h(ws, r, 9)
r += 9; src(ws, r, f'팀 온라인 설문 6·8·10·12번 문항(5점 척도), 2026.9.23~24, 응답 {SV_N}명'); r += 1; H(ws, r, 12); r += 1
section(ws, r, 2, 18, '이동이 불편해 포기한 곳', '중복 선택')
section(ws, r, 21, 37, '유료 체험을 망설인 가장 큰 이유', '가격보다 정보·예약·시간')
r += 1
dSc['K1'] = '포기한 곳'; dSc['L1'] = '비율'
for i, (col, t) in enumerate((('E', '외곽 관광지(하회·도산)'), ('F', '야간 명소(월영교)'), ('G', '원도심 밤 가게·식당'), ('H', '없음(모두 방문)')), 2):
    dSc.cell(i, 11, t); dSc.cell(i, 12).number_format = '0%'; dSc.cell(i, 12, f"=IFERROR({cnt(f'{rg(col)},1,' + rg('I') + ',1')}/{cnt(rg('I') + ',1')},0)")
ch = BarChart(); ch.type = 'bar'; ch.gapWidth = 50
s_ = bar_series(Reference(dSc, min_col=12, min_row=2, max_row=5), '비율', RED); s_.dLbls = labels(pos='outEnd', fmt='0%', b=True)
dp = DataPoint(idx=3, invertIfNegative=False); dp.graphicalProperties = gp(fill=GRAY_L, noline=True); s_.dPt.append(dp)
ch.series.append(s_)
ch.set_categories(Reference(dSc, min_col=11, min_row=2, max_row=5)); ch.x_axis.scaling.orientation = 'maxMin'
show_axis(ch.x_axis, 850); hide_axis(ch.y_axis); ch.y_axis.scaling.min = 0
bare(ch); place(ws, ch, 2, r, 18, r + 7)
dSc['N1'] = '망설임 이유'; dSc['O1'] = '비율'
for i, t in enumerate(['정보 부족', '줄·예약 불편', '이동 시간 부족', '가격 부담', '기타'], 2):
    dSc.cell(i, 14, t); dSc.cell(i, 15).number_format = '0%'; dSc.cell(i, 15, f"=IFERROR({cnt(rg('K') + ',\"' + t + '\"')}/{cnt(rg('K') + ',\"<>미응답\"')},0)")
ch = BarChart(); ch.type = 'bar'; ch.gapWidth = 50
s_ = bar_series(Reference(dSc, min_col=15, min_row=2, max_row=6), '비율', BLUE); s_.dLbls = labels(pos='outEnd', fmt='0%', b=True)
dp = DataPoint(idx=3, invertIfNegative=False); dp.graphicalProperties = gp(fill=GRAY_L, noline=True); s_.dPt.append(dp)
ch.series.append(s_)
ch.set_categories(Reference(dSc, min_col=14, min_row=2, max_row=6)); ch.x_axis.scaling.orientation = 'maxMin'
show_axis(ch.x_axis, 850); hide_axis(ch.y_axis); ch.y_axis.scaling.min = 0
bare(ch); place(ws, ch, 21, r, 37, r + 7)
rows_h(ws, r, 8)
r += 8; src(ws, r, '팀 온라인 설문 4번(중복 선택)·11번 문항, 2026.9.23~24'); r += 1; H(ws, r, 10); r += 1
wt = SV['이동수단_가중_방문자']
survey_line(ws, r, '응답한 방문자 중 차 없는 사람이 46%로 실제(철도공사 추정 철도+버스 10.5%)보다 많다. 10.5 : 89.5로 다시 가중하면 긍정(있다+매우 있다)은 '
                   f"체험 쿠폰 {wt['Q6_영수증_체험쿠폰_의향']['가중_top2']:.0f}% · 셔틀 {wt['Q8_야간택시셔틀_의향']['가중_top2']:.0f}% · "
                   f"팝업 {wt['Q10_야간팝업포차_의향']['가중_top2']:.0f}% · 축제 혜택 {wt['Q12_영수증_축제혜택_의향']['가중_top2']:.0f}%.")
r += 1; H(ws, r, 14); r += 1
r = fold_table(ws, r, '의향 5점 분포 표로 보기', '고른 응답자 중 비율',
               [(2, 12, 'left', None)] + [(13 + 5 * j, 17 + 5 * j, 'right', '0%') for j in range(5)],
               ['문항'] + [t for _, t, _ in LV],
               [[f"='d_설문계산'!D{i}"] + [f"='d_설문계산'!{CL(5 + j)}{i}" for j in range(5)] for i in range(2, 6)])
H(ws, r, 8); r += 1
r = fold_table(ws, r, '포기한 곳 · 망설인 이유 표로 보기', '고른 응답자 중 비율',
               [(2, 12, 'left', None), (13, 17, 'right', '0%'), (21, 31, 'left', None), (32, 37, 'right', '0%')],
               ['포기한 곳', '비율', '망설인 이유', '비율'],
               [[f"=IF('d_설문계산'!K{i}=\"\",\"\",'d_설문계산'!K{i})", f"=IF('d_설문계산'!K{i}=\"\",\"\",'d_설문계산'!L{i})",
                 f"='d_설문계산'!N{i}", f"='d_설문계산'!O{i}"] for i in range(2, 7)])
H(ws, r, 8); r += 1
r = details(ws, r, [
    ('읽는 법', '"불편했다·부족했다·막차에 귀가"는 방문 경험이라 기존 데이터(112번 막차 18:45, 월영교 1km 주점 0곳, 안동역 막차 21~22시)를 뒷받침하는 근거로 쓴다'),
    ('의향', '"이용하겠다"는 의향이라 참여율로 바로 쓰지 않는다. 기대효과 모의실험에서는 체험 결제율과 저녁 이동 배수 두 곳에만 실현율(0.33~0.40)로 보정해 쓴다'),
    ('가격', f'가격 때문에 망설인다는 응답은 {SV["Q11_가격_이유"]["pct"]:.0f}%뿐이라 1단계 혜택은 할인 폭(10%)보다 체험 정보·예약·동선을 잇는 데 무게를 둔다'),
    ('출처', f'팀 온라인 설문(구글폼, 2026-09-23~24, 응답 {SV_N}명, 편의 표본, 인구통계·개인정보 문항 없음). 정제 scripts/설문_정제.py · 집계 scripts/설문_분석.py'),
])
printing(ws, r)

# ═════════════════════════════════════════════════════════
# 한눈에
# ═════════════════════════════════════════════════════════
ws = wsH; grid(ws)
header(ws, '안동 이어드림 · 데이터 대시보드',
       rich(('데이터 기반 21시 이후 소비 릴레이 ', 22, True, INK), ('‘안동 이어드림’', 22, True, BLUE), (': 원도심에서 월영교로', 22, True, INK)),
       '디지털 관광주민증 위 3단계 릴레이. 아래 칸을 누르면 그 화면으로 간다. 모든 효과는 시행 전 예측이다.')
cards = [(2, 12, '01 문제', None, '방문 1회당 체험·문화 소비', EXCH, '+0.0%;−0.0%', RED,
          [f'146개 시·군 중 {NOW_RANK}번째로 많이 줄었다', f'전국 중앙 {MINUS(f"{MED * 100:+.1f}")}%'],
          f'빈 곳 세 군데: 1 원도심 혜택 0곳 · 2 19시 이후 버스 {BUS["19시이후"]}회 · 3 월영교 주점 {WY_PUB}곳'),
         (14, 24, '02 기대효과', None, '100명 중 2명 참여 시 방문당 체험·문화 소비', EFF_AFTER, '0.0"원"', BLUE,
          [f'지금 {EX26:.1f}원에서 +{P50("기준", "지표1_증가율") * 100:.1f}%', f'월영교 저녁 이동 주말 하루 {P50("기준", "새이동_하루"):.0f}명'],
          '시행 전 예측, 1만 번 계산의 가운데 값'),
         (26, 37, '03 우리 시·군 진단', S_DG, '안동과 같은 문제 유형', len(SAME), '0"곳"', BLUE,
          ['체험·문화 소비 하락 + 짧은 숙박', ' · '.join(s[:-1] for s in SAME)],
          f'시·군을 고르면 그 지역 진단이 나온다. 주민증 운영 {JM["운영지역수"]}개 지자체에 적용 가능')]
for r_, h_ in zip(range(6, 17), (14, 26, 20, 52, 20, 20, 10, 40, 24, 8, 14)): H(ws, r_, h_)
sky_band(ws, 6, 16)
for c1, c2, lab, sheet, desc, val, fmt, color, lines, foot in cards:
    for r_ in range(7, 16):
        for c in range(c1, c2 + 1): ws.cell(r_, c).fill = FILL(WHITE)
    M(ws, 7, c1, c2, lab, F(10.5, True, DEEP if color == BLUE else color), AL('left', 'bottom', False, 1), WHITE)
    M(ws, 8, c1, c2, desc, F(10, False, MUTE), AL('left', 'center', False, 1), WHITE)
    M(ws, 9, c1, c2, val, F(30, True, color), AL('left', 'center', False, 1), WHITE, fmt)
    M(ws, 10, c1, c2, lines[0], F(10.5), AL('left', 'center', False, 1), WHITE)
    M(ws, 11, c1, c2, lines[1], F(10.5), AL('left', 'center', False, 1), WHITE)
    hline(ws, 12, c1, c2, TRACK)
    M(ws, 13, c1, c2, foot, F(9.5, False, MUTE), AL('left', 'center', True, 1), WHITE)
    if sheet:
        lk = M(ws, 14, c1, c2, '열기 +', F(10, True, DEEP), AL('right', 'center', False, 1), WHITE)
        lk.hyperlink = Hyperlink(ref=lk.coordinate, location=f"'{sheet}'!A1", display='열기 +')
for c in (13, 25):
    M(ws, 9, c, c, '›', F(28, True, SOFT), AL('center', 'center', False), SKY)
memo(ws.cell(9, 2), '외지인 신용카드 소비(데이터랩 BDT_02_01_003) 중 문화서비스·관광유원시설·기타레저 ÷ 외지인 방문 연인원(BDT_01_01_006), 2024 → 2026년 1~8월')
memo(ws.cell(9, 14), '원도심 방문객 100명 중 2명이 참여할 때. 체험 결제율·저녁 이동 배수 = 설문 의향 × 실현율 0.33~0.40, 체험 10% 할인액은 뺐다. 모의실험 1만 번의 가운데 값')
H(ws, 17, 24)
M(ws, 18, 2, 37, rich(('릴레이 3단계  ', 11, True, INK), ('번호를 누르면 근거 화면으로 간다', 10, False, MUTE)), al=AL('left', 'center', False)); H(ws, 18, 22)
H(ws, 19, 6); H(ws, 20, 46)
relay = [(2, 13, 1, '낮 · 원도심', f'식당 {OLD_REST}곳에서 식사 → 체험 10% 할인', S_SV),
         (14, 25, 2, '저녁 18:30~21:00', '원도심 → 월영교 택시, 늘면 셔틀', S_TIME),
         (26, 37, 3, '밤 · 월영교', '문보트 + 21시 이후 식사·주점 팝업', S_WY)]
for c1, c2, n, t1, t2, sheet in relay:
    cc = M(ws, 20, c1, c1, n, F(11, True, WHITE), AL('center', 'center', False), BLUE)
    cc.hyperlink = Hyperlink(ref=cc.coordinate, location=f"'{sheet}'!A1", display=str(n))
    M(ws, 20, c1 + 1, c2 - 1 if c2 < 37 else c2, rich((t1 + '\n', 10.5, True, INK), (t2, 10, False, INK)), al=AL('left', 'center', True, 1), fill=PALE)
H(ws, 21, 24)
M(ws, 22, 2, 37, rich(('화면 바로가기  ', 11, True, INK), ('칸을 누르면 그 화면으로 간다. 화면마다 파란 칸으로 조건을 바꿀 수 있다', 10, False, MUTE)), al=AL('left', 'center', False)); H(ws, 22, 22)
navs = [(S_DG, f'{len(SAME)}곳', '안동과 같은 유형', '시·군 · 가중치', BLUE),
        (S_TIME, '18:30~21:00', '안동역 막차 21~22시', '연도 · 요일 · 열차 · 시작·종료', BLUE),
        (S_BUS, f'{BUS["19시이후"]}회', '19시 이후 원도심 → 월영교', '노선 · 시간표 · 추가 운행', RED),
        (S_WY, f'{WY_PUB}곳', '월영교 1km 주점', '팝업 부스 · 종료 시각 · 관광지', RED),
        (S_SV, f'{SV_N}명', f'팀 설문(방문 경험 {SV_V}명)', '응답자 범위 · 이동수단', DEEP)]
sky_band(ws, 23, 28)
for r_, h_ in zip(range(23, 29), (8, 22, 34, 20, 20, 8)): H(ws, r_, h_)
for (c1, c2), (sheet, big, what, ctrl, color) in zip([(2, 8), (9, 15), (16, 22), (23, 29), (30, 37)], navs):
    for r_ in range(24, 28):
        for c in range(c1, c2 + 1): ws.cell(r_, c).fill = FILL(WHITE)
    a = M(ws, 24, c1, c2, sheet + '  →', F(10.5, True, DEEP), AL('left', 'bottom', False, 1), WHITE)
    a.hyperlink = Hyperlink(ref=a.coordinate, location=f"'{sheet}'!A1", display=sheet)
    M(ws, 25, c1, c2, big, F(18, True, color), AL('left', 'center', False, 1), WHITE)
    M(ws, 26, c1, c2, what, F(9.5), AL('left', 'center', False, 1), WHITE)
    M(ws, 27, c1, c2, '▼ ' + ctrl, F(8.5, False, MUTE), AL('left', 'center', False, 1), WHITE)
    for rr in range(24, 28):
        for c in (c1, c2):
            b = ws.cell(rr, c).border
            ws.cell(rr, c).border = Border(left=S_(SKY, 'thick') if c == c1 else b.left, right=S_(SKY, 'thick') if c == c2 else b.right)
H(ws, 29, 16)
M(ws, 30, 2, 37, '쓰는 법', F(10.5, True)); H(ws, 30, 20)
tips = ['· 파란 테두리 칸은 누르면 ▼ 목록이 나오거나 숫자를 바꿀 수 있다. 바꾸면 카드·그래프·표가 바로 바뀐다.',
        '· 숫자 오른쪽 위 빨간 삼각형에 마우스를 올리면 출처와 계산 방법이 보인다.',
        '· 화면 아래 파란 띠(표로 보기)와 노란 띠(데이터 설명)는 왼쪽 여백의 [+] 를 누르면 펼쳐진다.',
        '· 빨강 = 줄었거나 문제인 것, 파랑 = 늘었거나 좋아진 것.']
for i, t in enumerate(tips):
    M(ws, 31 + i, 2, 37, t, F(10), AL('left', 'center', False)); H(ws, 31 + i, 18)
H(ws, 35, 12)
M(ws, 36, 2, 37, f'출처: 한국관광 데이터랩, 한국철도공사, 코레일, 소상공인 상가정보, 안동시 버스정보시스템·주민증 자료, 팀 온라인 설문 {SV_N}명. 자세한 출처는 화면마다 「데이터 설명」.',
  F(9, False, MUTE), AL('left', 'center', False))
printing(ws, 37)

# ═════════════ 마무리 ═════════════
wsH.sheet_properties.tabColor = DEEP
for sh in SCREENS:                        # 접기 칸(+)이 먹도록 화면 시트는 잠그지 않는다
    sh.sheet_properties.tabColor = RED if sh in (wsB, wsW) else BLUE
wsH.protection.sheet = True; wsH.protection.formatColumns = True; wsH.protection.formatRows = True
for sh in [wsH] + SCREENS:
    sh.sheet_view.selection[0].activeCell = 'A1'; sh.sheet_view.selection[0].sqref = 'A1'
wb.active = 0
wb.calculation.fullCalcOnLoad = True
path = OUT / '안동이어드림_요약대시보드.xlsx'
wb.save(path)
print('저장:', path.relative_to(ROOT), [s.title for s in wb.worksheets if s.sheet_state == 'visible'])
