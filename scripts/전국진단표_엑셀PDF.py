# -*- coding: utf-8 -*-
"""⑦ 전국 진단표 — 엑셀 계산표 + 2쪽 요약 PDF (2026-09-23)

입력: 보고서/전국진단_20260923/전국진단표.csv · 전국진단.json (scripts/전국진단표.py)
엑셀: 가중치(노란 칸)를 바꾸면 144개 시·군 점수·순위·유형이 다시 계산되고, 「우리 시군 계산」에 네 값을 넣으면 위치가 나온다.
"""
import json, re, subprocess
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter as CL

ROOT = Path(__file__).resolve().parent.parent
O = ROOT / '보고서/전국진단_20260923'
T = pd.read_csv(O / '전국진단표.csv', index_col=0)
R = json.loads((O / '전국진단.json').read_text(encoding='utf-8'))
IND = ['①체험문화_변화율', '②평균숙박일수', '③저녁전환율', '④야간방문비중']
NM = ['체험·문화 소비 변화율', '평균 숙박일수', '저녁 전환율', '야간 방문 비중']
N = len(T)

FN = '맑은 고딕'
f_in, f_c, f_l = Font(name=FN, size=10, color='0000FF'), Font(name=FN, size=10), Font(name=FN, size=10, color='008000')
f_b, f_h, f_s = Font(name=FN, size=10, bold=True), Font(name=FN, size=13, bold=True), Font(name=FN, size=9, color='666666')
YEL, HEAD = PatternFill('solid', fgColor='FFFF00'), PatternFill('solid', fgColor='FFF2A8')
HL = PatternFill('solid', fgColor='FFF2CC')
sd = Side(style='thin', color='000000'); BOX = Border(left=sd, right=sd, top=sd, bottom=sd)
WRAP = Alignment(wrap_text=True, vertical='top')


def put(ws, ref, v, font=f_c, fmt=None, fill=None, box=True):
    c = ws[ref]; c.value = v; c.font = font; c.alignment = WRAP
    if fmt: c.number_format = fmt
    if fill: c.fill = fill
    if box: c.border = BOX
    return c


def header(ws, row, labels):
    for j, h in enumerate(labels, 1):
        c = ws.cell(row, j, h); c.font = f_b; c.fill = HEAD; c.border = BOX; c.alignment = WRAP


wb = Workbook()
ws = wb.active; ws.title = '사용법'
for i, t in enumerate([
    ('안동 이어드림 · ⑦ 전국 진단표', f_h), ('', None),
    ('무엇을 하나', f_b),
    ('전국 시·군이 "방문은 오는데 소비·체류로 안 이어지는" 문제를 네 지표로 스스로 진단하는 탐색 지표다. 정책 효과 점수가 아니라, 추가 진단이 필요한 곳과 문제 유형을 골라낸다.', None),
    (f'대상: 네 지표가 모두 있는 시·군 {N}곳(외지인 방문 연인원 2026년 1~8월 100만 이상, 광역시 자치구 제외).', None), ('', None),
    ('쓰는 법', f_b),
    ('1. 「가중치」에서 네 지표의 가중치를 바꾸면 「진단표」의 점수·순위가 다시 계산된다(기본 같은 가중치).', None),
    ('2. 「우리 시군 계산」에 우리 시·군의 네 값을 넣으면 문제 백분위, 진단 점수, 전국 순위, 유형이 나온다. 예시로 안동 값이 들어 있다.', None),
    ('3. 「유형」 시트에서 같은 문제 조합을 가진 시·군 목록을 본다. 유형 = 문제 백분위 75 이상(하위 25%)인 지표의 조합.', None), ('', None),
    ('읽는 법', f_b),
    ('문제 백분위: 0 = 전국에서 가장 좋음, 100 = 가장 나쁨. 네 지표 모두 값이 낮을수록 문제로 본다.', None),
    ('가중치에 따라 순위가 크게 흔들리는 곳이 많다(「진단표」 순위 P10~P90). 그래서 점수 하나보다 유형으로 읽는다.', None),
    ('노란 칸 = 바꿔 넣는 값 · 파란 글자 = 데이터로 계산한 고정값 · 검은 글자 = 수식', None),
], 1):
    c = ws.cell(i, 1, t[0]); c.font = t[1] or f_c; c.alignment = Alignment(wrap_text=True)
ws.column_dimensions['A'].width = 125

wg = wb.create_sheet('가중치')
put(wg, 'A1', '가중치 — 노란 칸만 바꾼다 (합이 1이 아니어도 자동으로 나눈다)', f_h, box=False)
header(wg, 3, ['지표', '가중치', '정의', '출처'])
DEF = [('외지인 방문당 체험·문화 소비(문화서비스+관광유원시설+기타레저)의 2024→2026 1~8월 변화율. 낮을수록 문제', '데이터랩 BDT_02_01_003(외지인 카드) ÷ BDT_01_01_006(방문)'),
       ('숙박 방문객의 평균 숙박일수(2025 월평균). 짧을수록 문제', '데이터랩 LN_02_01_013'),
       ('18~21시 방문 ÷ 14~18시 방문(2026 1~8월). 낮 방문객이 저녁까지 남는 정도. 낮을수록 문제', '데이터랩 BDT_01_01_006 시간대'),
       ('21~24시 방문 ÷ 06~24시 방문(2026 1~8월). 낮을수록 문제', '데이터랩 BDT_01_01_006 시간대')]
for i, (nm, (d, s)) in enumerate(zip(NM, DEF), 4):
    put(wg, f'A{i}', nm, f_b); put(wg, f'B{i}', 0.25, f_in, '0.00', YEL); put(wg, f'C{i}', d); put(wg, f'D{i}', s)
put(wg, 'A8', '합계', f_b); put(wg, 'B8', '=SUM(B4:B7)', f_c, '0.00')
for col, w in zip('ABCD', (22, 10, 70, 44)): wg.column_dimensions[col].width = w

wt = wb.create_sheet('진단표')
put(wt, 'A1', f'전국 {N}개 시·군 진단표 (가중치를 바꾸면 점수·순위·유형이 다시 계산된다)', f_h, box=False)
hd = ['시·군'] + NM + [f'{n}\n문제 백분위' for n in NM] + ['진단 점수', '순위', '유형', '순위 P10\n(가중치 무작위)', '순위 P90', '상위 20 안에\n드는 비율']
header(wt, 3, hd)
r0, r1 = 4, 3 + N
fmts = ['0.0%', '0.00', '0.000', '0.0%']
for k, (sg, row) in enumerate(T.iterrows()):
    r = r0 + k
    fill = HL if sg == '안동시' else None
    put(wt, f'A{r}', sg, f_b if sg == '안동시' else f_c, fill=fill)
    for j, c in enumerate(IND):
        put(wt, f'{CL(2 + j)}{r}', float(row[c]), f_in, fmts[j], fill)
        col = CL(2 + j)
        put(wt, f'{CL(6 + j)}{r}', f'=100*(1-(COUNTIF(${col}${r0}:${col}${r1},"<"&{col}{r})+1)/COUNT(${col}${r0}:${col}${r1}))', f_c, '0', fill)
    put(wt, f'J{r}', f'=SUMPRODUCT(F{r}:I{r},TRANSPOSE(가중치!$B$4:$B$7))/가중치!$B$8' if False else
        f'=(F{r}*가중치!$B$4+G{r}*가중치!$B$5+H{r}*가중치!$B$6+I{r}*가중치!$B$7)/가중치!$B$8', f_c, '0.0', fill)
    put(wt, f'K{r}', f'=RANK(J{r},$J${r0}:$J${r1},0)', f_c, '0', fill)
    put(wt, f'L{r}', f'=IF(F{r}>=75,"체험 ","")&IF(G{r}>=75,"숙박 ","")&IF(H{r}>=75,"저녁 ","")&IF(I{r}>=75,"야간","")', f_c, None, fill)
    put(wt, f'M{r}', int(row['순위_P10']), f_in, '0', fill); put(wt, f'N{r}', int(row['순위_P90']), f_in, '0', fill)
    put(wt, f'O{r}', float(row['상위20_비율']), f_in, '0%', fill)
for j, w in enumerate([12, 11, 10, 10, 10, 11, 11, 11, 11, 9, 7, 22, 10, 9, 11], 1):
    wt.column_dimensions[CL(j)].width = w
wt.freeze_panes = 'B4'

wu = wb.create_sheet('우리 시군 계산', 1)
put(wu, 'A1', '우리 시·군 계산 — 노란 칸에 네 값을 넣는다 (예시: 안동)', f_h, box=False)
header(wu, 3, ['지표', '우리 값', '전국 중앙', '문제 백분위', '해석'])
a = T.loc['안동시']
for i, (nm, c, fm) in enumerate(zip(NM, IND, fmts), 4):
    col = CL(2 + IND.index(c))
    rng_ = f'진단표!${col}${r0}:${col}${r1}'
    put(wu, f'A{i}', nm, f_b); put(wu, f'B{i}', float(a[c]), f_in, fm, YEL)
    put(wu, f'C{i}', f'=MEDIAN({rng_})', f_l, fm)
    put(wu, f'D{i}', f'=100*(1-(COUNTIF({rng_},"<"&B{i})+1)/(COUNT({rng_})+1))', f_c, '0')
    put(wu, f'E{i}', f'=IF(D{i}>=75,"하위 25%: 이 지표가 문제",IF(D{i}<=25,"상위 25%: 강점","중간"))', f_c)
put(wu, 'A9', '진단 점수', f_b); put(wu, 'B9', '=(D4*가중치!B4+D5*가중치!B5+D6*가중치!B6+D7*가중치!B7)/가중치!B8', f_c, '0.0')
put(wu, 'A10', f'전국 {N}곳 중 순위', f_b); put(wu, 'B10', f'=COUNTIF(진단표!$J${r0}:$J${r1},">"&B9)+1', f_c, '0')
put(wu, 'A11', '유형', f_b); put(wu, 'B11', '=IF(D4>=75,"체험 ","")&IF(D5>=75,"숙박 ","")&IF(D6>=75,"저녁 ","")&IF(D7>=75,"야간","")', f_c)
put(wu, 'A12', '같은 유형 시·군 수', f_b); put(wu, 'B12', f'=IF(B11="","-",COUNTIF(진단표!$L${r0}:$L${r1},B11))', f_c)
put(wu, 'A14', '※ 유형이 같은 시·군 목록은 「유형」 시트. 이 표는 추가 진단이 필요한 곳을 찾는 탐색 지표이며 정책 효과 점수가 아니다.', f_s, box=False)
for col, w in zip('ABCDE', (26, 12, 12, 12, 30)): wu.column_dimensions[col].width = w
img = XLImage(str(O / 'g8_안동위치.png')); img.width, img.height = 720, 336
wu.add_image(img, 'G3')

wy = wb.create_sheet('유형')
put(wy, 'A1', '문제 유형별 시·군 (기본 가중치, 문제 백분위 75 이상인 지표의 조합)', f_h, box=False)
header(wy, 3, ['유형', '시·군 수', '시·군'])
grp = T.groupby('유형').apply(lambda d: list(d.index)).sort_values(key=lambda s: -s.str.len())
for i, (ty, lst) in enumerate(grp.items(), 4):
    lab = ty.replace('체험문화', '체험').replace('평균숙박일수', '숙박').replace('저녁전환율', '저녁').replace('야간방문비중', '야간') if ty != '-' else '해당 없음'
    put(wy, f'A{i}', lab, f_b, fill=HL if '안동시' in lst else None); put(wy, f'B{i}', len(lst)); put(wy, f'C{i}', ', '.join(lst), fill=HL if '안동시' in lst else None)
for col, w in zip('ABC', (24, 9, 120)): wy.column_dimensions[col].width = w

xl = O / '안동이어드림_전국진단표.xlsx'
wb.save(xl)
print(xl.relative_to(ROOT))

# ── 2쪽 요약 PDF ───────────────────────────────────────────────────
CSS = (ROOT / 'scripts/교수브리핑_PDF생성.py').read_text(encoding='utf-8').split('CSS = """')[1].split('"""')[0]


def table(head, rows, cls='', hl=()):
    th = ''.join(f'<th>{h}</th>' for h in head)
    tr = ''.join(f'<tr{" class=hl" if i in hl else ""}>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for i, r in enumerate(rows))
    return f'<table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'


def cap(t): return f'<p class="cap">&lt; {t} &gt;</p>'
def sec(no, t): return f'<h2><span class="hd">{no} {t}</span></h2>'


pf = [lambda v: f'{v * 100:+.1f}%', lambda v: f'{v:.2f}일', lambda v: f'{v:.3f}', lambda v: f'{v * 100:.1f}%']
t_ind = table(['지표', '정의', '안동', f'시·군 중앙({N}곳)', '문제 백분위'],
              [[nm, DEF[i][0].split('. ')[0], pf[i](a[c]), pf[i](T[c].median()), f"{a[c + '_문제백분위']:.0f}"] for i, (nm, c) in enumerate(zip(NM, IND))],
              'nw', hl=(0, 1))
same = [s for s in R['안동과_같은_유형']]
sub = T.loc[same]
t_same = table(['시·군'] + NM + ['진단 점수'],
               [[s] + [pf[i](sub.loc[s, c]) for i, c in enumerate(IND)] + [f"{sub.loc[s, '진단점수']:.0f}"] for s in same], 'nw',
               hl=tuple(i for i, s in enumerate(same) if s == '안동시'))
top = T.head(10)
t_top = table(['순위', '시·군', '유형(하위 25% 지표)', '진단 점수', '가중치를 흔든 순위(P10~P90)'],
              [[int(r['순위']), s, r['유형'].replace('체험문화', '체험').replace('평균숙박일수', '숙박').replace('저녁전환율', '저녁').replace('야간방문비중', '야간'),
                f"{r['진단점수']:.0f}", f"{int(r['순위_P10'])}~{int(r['순위_P90'])}위"] for s, r in top.iterrows()], 'nw')
cnt = T['유형'].value_counts()

body = f'''
<h1>⑦ 전국 진단표: 안동과 같은 문제를 가진 시·군 찾기</h1>
<p class="byline">2026. 9. 23 · 안동팀 · 엑셀 계산표 「안동이어드림_전국진단표.xlsx」와 함께 제출</p>
{sec('01', '무엇을 하나')}
<p>전국 시·군이 "방문은 오는데 소비·체류로 안 이어지는" 문제를 네 지표로 스스로 진단하는 표다. 우리 시·군 값 네 개를 넣으면 전국 {N}곳 가운데 위치와 문제 유형이 나온다. 정책 효과 점수가 아니라 <b>추가 진단이 필요한 곳과 같은 문제를 가진 곳을 골라내는 탐색 지표</b>다.</p>
{t_ind}
{cap('표 [tInd] 네 지표와 안동의 위치 (문제 백분위 0 = 가장 좋음, 100 = 가장 나쁨)')}
<div class="fig"><img src="g8_안동위치.png">{cap('그림 1 네 지표의 전국 분포(회색 점 = 시·군, 점선 = 중앙값)와 안동(빨강)')}</div>
<p class="ins">=> <span>안동은 체험·문화 소비 변화(문제 백분위 {a['①체험문화_변화율_문제백분위']:.0f})와 숙박일수({a['②평균숙박일수_문제백분위']:.0f})에서 하위권이고, 저녁·야간 방문은 오히려 중앙보다 좋다. 사람이 저녁까지 남는데 체험·숙박 소비로 이어지지 않는 유형이다.</span></p>

{sec('02', '점수보다 유형으로 읽는다')}
<p>네 지표를 같은 가중치로 합친 진단 점수에서 안동은 {N}곳 중 {int(a['순위'])}위지만, 가중치를 무작위로 1,000번 바꾸면 {int(a['순위_P10'])}~{int(a['순위_P90'])}위로 크게 흔들린다. 점수 하나로 순위를 매기면 가중치를 어떻게 정했느냐가 결론을 좌우한다. 그래서 하위 25%인 지표의 조합, 즉 <b>문제 유형</b>으로 읽는다. 안동의 유형("체험 · 숙박")을 가진 시·군은 {len(same)}곳이다.</p>
{t_same}
{cap('표 [tSame] 안동과 같은 유형(체험·문화 소비 하락 + 짧은 숙박)의 시·군')}
<p class="ins">=> <span>이 {len(same)}곳이 이어드림 방식(사람이 모이는 곳의 식음을 체험·저녁 소비로 잇기)을 먼저 적용해 볼 확산 후보다. 영덕·울진·강릉·양양(동해안)과 남해처럼 관광형 시·군이 많고, 광명은 도시형이라 성격이 달라 개별 확인이 필요하다.</span></p>
{t_top}
{cap('표 [tTop] 진단 점수 상위 10곳과 가중치 민감도')}
<p class="note">유형 분포: 해당 없음 {cnt.get('-', 0)}곳, 숙박만 {cnt.get('평균숙박일수', 0)}곳, 체험만 {cnt.get('체험문화', 0)}곳, 저녁·야간 {cnt.get('저녁전환율 · 야간방문비중', 0)}곳, 체험·저녁·야간 {cnt.get('체험문화 · 저녁전환율 · 야간방문비중', 0)}곳, 체험·숙박 {cnt.get('체험문화 · 평균숙박일수', 0)}곳 등.</p>

{sec('03', '한계')}
<ul>
<li>탐색 지표다. 문제 백분위가 높다고 그 지역 정책이 실패했다는 뜻이 아니며, 원인은 지역마다 따로 진단해야 한다.</li>
<li>체험·문화 소비의 관광유원시설 업종은 전국 절반 가까이가 10원 미만인 결함 업종이다. 한 시설의 휴관·요금 변경에도 크게 움직일 수 있어 개별 확인이 필요하다.</li>
<li>시간대 지표는 이동통신 방문 기준이라 주민·업무 방문이 섞인다. 기간은 2026년 1~8월(체험·문화는 2024년 같은 기간과 비교), 숙박일수는 2025년이다.</li>
<li>광역시 자치구는 뺐다. 시·군 {N}곳 기준이라 237곳 기준의 이전 수치(저녁 전환율 전국 중앙 0.559 등)와 중앙값이 다르다.</li>
</ul>
'''
HTML = f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>안동 이어드림 전국 진단표</title><style>{CSS}</style></head><body>{body}</body></html>'
_o = re.findall(r'&lt; 표 \[(\w+)\]', HTML); _n = {k: i + 1 for i, k in enumerate(_o)}
HTML = re.sub(r'표 \[(\w+)\]', lambda m: f'표 {_n[m.group(1)]}', HTML)
assert '—' not in HTML and '–' not in HTML
h = O / '전국진단표.html'; h.write_text(HTML, encoding='utf-8')
pdf = O / '안동이어드림_전국진단표_20260923.pdf'
subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                '--virtual-time-budget=10000', '--run-all-compositor-stages-before-draw', f'--print-to-pdf={pdf}', h.as_uri()], check=True, capture_output=True)
print(pdf.relative_to(ROOT), f'{pdf.stat().st_size / 1024:.0f} KB')
