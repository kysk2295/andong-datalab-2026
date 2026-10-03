# -*- coding: utf-8 -*-
"""팀 데이터 대시보드(참고자료 2) xlsx에 '출처' 탭을 끼워 넣는다 (2026-09-30)

openpyxl로 열어 저장하면 시·군·노선·관광지 드롭다운(x14 확장 데이터 유효성 검사)이 지워지므로,
xlsx(zip) 안의 XML에 시트 하나만 추가한다. 기존 시트·차트·메모·드롭다운은 바이트 그대로 둔다.
출처 내용은 대시보드 각 화면의 '출처' 줄과 셀 메모에서 옮겼다.
실행: .venv_pdf/bin/python scripts/대시보드_출처탭_추가.py <입력.xlsx> <출력.xlsx>
"""
import re, sys, zipfile
from xml.sax.saxutils import escape

SRC, DST = sys.argv[1], sys.argv[2]
NAME = '출처'
ROWS = [  # (자료, 기관, 기간, 쓴 화면)
    ('외지인 방문 연인원 (BDT_01_01_006)', '한국관광 데이터랩', '2024·2026년 1~8월', '한눈에, 시·군 진단'),
    ('외지인 신용카드 소비, 업종 중분류 (BDT_02_01_003)', '한국관광 데이터랩', '2024·2026년 1~8월', '한눈에, 시·군 진단'),
    ('평균 숙박일수 (LN_02_01_013)', '한국관광 데이터랩', '2025년', '시·군 진단'),
    ('시간대별 방문(저녁 전환율, 야간 방문 비중)', '한국관광 데이터랩', '2026년 1~8월', '시·군 진단'),
    ('전국 진단표 144개 시·군 (scripts/전국진단표.py)', '팀 분석', '2026.9.23', '한눈에, 시·군 진단'),
    ('안동역 월별·요일별·시간대별 승하차 (KTX-이음·새마을·무궁화)', '코레일 (팀원 취합)', '2024.1~2026.8', '운영 시간'),
    ('시내버스 시간표·노선·정류장 (46개 노선, 3,309개 정류장)', '안동시 버스정보시스템', '2026.9.22 조회', '한눈에, 버스'),
    ('112번 노선 선형·정류장', '안동시 버스정보시스템', '2026.9.29 수집', '버스'),
    ('지도 배경', 'OpenStreetMap contributors (ODbL) · OpenFreeMap', '2026.9.13', '버스'),
    ('행정동 경계', '통계청 SGIS (vuski/admdongkor)', '2026.7', '버스'),
    ('디지털관광주민증 혜택업체·이용 실적', '안동시 (정보공개청구)', '2024.6~2026.8', '한눈에'),
    ('상가(상권)정보 음식점, 반경 1km 업종 중분류', '소상공인시장진흥공단', '2026.6', '월영교'),
    ('월영교 1km 음식점 영업 종료 시각', '팀 확인 (조사 16번)', '조사일 기록 보완 중', '월영교'),
    ('8대 도시(안동) 관광 형태 분석, 가명결합 (소비 = 건수)', '한국철도공사', '2022.4~6', '월영교'),
    ('온라인 설문 103명 (방문 경험 72명, 편의 표본)', '팀 (구글폼)', '2026.9.23~24', '한눈에, 설문조사'),
    ('이어드림 기대효과 모의실험 1만 번 (scripts/이어드림_시뮬레이션.py)', '팀 분석', '2026.9', '한눈에'),
]
NOTES = ['· 한국철도공사 자료는 소비를 건수로 세어 데이터랩 숫자와 한 표에 올리지 않는다.',
         '· 설문 의향 %는 참여율이 아니다. 기대효과 계산에는 실현율 0.33~0.40으로 보정한 값만 쓴다.',
         '· 모든 효과는 시행 전 예측(모의실험 1만 번의 가운데 값)이며 시행 첫 달 기록으로 다시 계산한다.',
         '· 화면마다 숫자 오른쪽 위 빨간 삼각형(메모)과 「데이터 설명」에 계산 방법이 있다.']

z = zipfile.ZipFile(SRC)
files = {n: z.read(n) for n in z.namelist()}
wbx = files['xl/workbook.xml'].decode('utf-8')
assert f'name="{NAME}"' not in wbx, '이미 출처 탭이 있다'

# 1) 스타일 추가 (맑은 고딕, 대시보드 색)
st = files['xl/styles.xml'].decode('utf-8')
def add(tag, xml):
    global st
    m = re.search(rf'<{tag} count="(\d+)"', st); n = int(m.group(1))
    st = st.replace(m.group(0), f'<{tag} count="{n + len(xml)}"', 1)
    st = st.replace(f'</{tag}>', ''.join(xml) + f'</{tag}>', 1)
    return list(range(n, n + len(xml)))
f_hd, f_bd, f_nt = add('fonts', ['<font><b/><sz val="10.5"/><color rgb="FF34383C"/><name val="맑은 고딕"/><family val="2"/><charset val="129"/></font>',
                                  '<font><sz val="10.5"/><color rgb="FF34383C"/><name val="맑은 고딕"/><family val="2"/><charset val="129"/></font>',
                                  '<font><sz val="10"/><color rgb="FF6B7075"/><name val="맑은 고딕"/><family val="2"/><charset val="129"/></font>'])
(fl_hd,) = add('fills', ['<fill><patternFill patternType="solid"><fgColor rgb="FFE3F1FB"/><bgColor indexed="64"/></patternFill></fill>'])
b_hd, b_bd = add('borders', ['<border><left/><right/><top/><bottom style="medium"><color rgb="FF2D6BD9"/></bottom><diagonal/></border>',
                             '<border><left/><right/><top/><bottom style="thin"><color rgb="FFE3E8EE"/></bottom><diagonal/></border>'])
x_hd, x_bd, x_nt = add('cellXfs', [
    f'<xf numFmtId="0" fontId="{f_hd}" fillId="{fl_hd}" borderId="{b_hd}" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="center" indent="1"/></xf>',
    f'<xf numFmtId="0" fontId="{f_bd}" fillId="0" borderId="{b_bd}" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1"><alignment vertical="center" wrapText="1" indent="1"/></xf>',
    f'<xf numFmtId="0" fontId="{f_nt}" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment vertical="center"/></xf>'])
X_LABEL, X_TITLE, X_DESC = 27, 37, 35               # 한눈에 B2·B3·B4와 같은 스타일(화면 이름 · 제목 · 설명)
files['xl/styles.xml'] = st.encode('utf-8')

# 2) 시트 XML
def c(ref, text, s):
    return f'<c r="{ref}" s="{s}" t="inlineStr"><is><t xml:space="preserve">{escape(text)}</t></is></c>'
rows = [(2, 18, [c('B2', '출처', X_LABEL)]), (3, 36, [c('B3', '대시보드에 쓴 자료', X_TITLE)]),
        (4, 20, [c('B4', '대시보드 숫자는 아래 자료로 계산했다. 계산 스크립트는 공개 저장소 scripts/ 폴더에 있다.', X_DESC)]),
        (6, 26, [c(f'{k}6', h, x_hd) for k, h in zip('BCDE', ('자료', '기관', '기간', '쓴 화면'))])]
r = 7
for row in ROWS:
    rows.append((r, 24, [c(f'{k}{r}', v, x_bd) for k, v in zip('BCDE', row)])); r += 1
r += 1
for t in NOTES:
    rows.append((r, 18, [c(f'B{r}', t, x_nt)])); r += 1
last = r - 1
sd = ''.join(f'<row r="{n}" ht="{h}" customHeight="1">{"".join(cs)}</row>' for n, h, cs in rows)
sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
         '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
         '<sheetPr><pageSetUpPr fitToPage="1"/></sheetPr>'
         f'<dimension ref="B2:E{last}"/>'
         '<sheetViews><sheetView showGridLines="0" workbookViewId="0"/></sheetViews>'
         '<sheetFormatPr defaultRowHeight="16.5"/>'
         '<cols><col min="1" max="1" width="2.5" customWidth="1"/><col min="2" max="2" width="62" customWidth="1"/>'
         '<col min="3" max="3" width="36" customWidth="1"/><col min="4" max="4" width="22" customWidth="1"/><col min="5" max="5" width="24" customWidth="1"/></cols>'
         f'<sheetData>{sd}</sheetData>'
         '<pageMargins left="0.4" right="0.4" top="0.5" bottom="0.5" header="0.3" footer="0.3"/>'
         '<pageSetup paperSize="9" orientation="landscape" fitToHeight="0"/></worksheet>')
new_path = 'xl/worksheets/sheet_chulcheo.xml'
files[new_path] = sheet.encode('utf-8')

# 3) 통합 문서: '설문조사' 다음(숨긴 d_ 시트 앞)에 넣는다. 인쇄 영역 localSheetId는 0~5뿐이라 순서 영향 없음
ids = [int(x) for x in re.findall(r'sheetId="(\d+)"', wbx)]
rels = files['xl/_rels/workbook.xml.rels'].decode('utf-8')
rid = 'rIdChulcheo'
assert all(int(x) < 6 for x in re.findall(r'localSheetId="(\d+)"', wbx))
wbx = wbx.replace('<sheet name="설문조사"', '<sheet name="__TMP__"', 1)
m = re.search(r'<sheet name="__TMP__"[^>]*/>', wbx)
wbx = wbx.replace(m.group(0), m.group(0).replace('__TMP__', '설문조사') + f'<sheet name="{NAME}" sheetId="{max(ids) + 1}" r:id="{rid}"/>', 1)
files['xl/workbook.xml'] = wbx.encode('utf-8')
rels = rels.replace('</Relationships>', f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet_chulcheo.xml"/></Relationships>')
files['xl/_rels/workbook.xml.rels'] = rels.encode('utf-8')
ct = files['[Content_Types].xml'].decode('utf-8')
ct = ct.replace('</Types>', f'<Override PartName="/{new_path}" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
files['[Content_Types].xml'] = ct.encode('utf-8')
app = files['docProps/app.xml'].decode('utf-8')          # 문서 속성의 시트 목록도 맞춘다
app = re.sub(r'(<vt:lpstr>워크시트</vt:lpstr></vt:variant><vt:variant><vt:i4>)(\d+)', lambda mm: mm.group(1) + str(int(mm.group(2)) + 1), app)
app = re.sub(r'<TitlesOfParts><vt:vector size="(\d+)"', lambda mm: f'<TitlesOfParts><vt:vector size="{int(mm.group(1)) + 1}"', app)
app = app.replace('<vt:lpstr>설문조사</vt:lpstr>', f'<vt:lpstr>설문조사</vt:lpstr><vt:lpstr>{NAME}</vt:lpstr>', 1)
files['docProps/app.xml'] = app.encode('utf-8')

with zipfile.ZipFile(DST, 'w', zipfile.ZIP_DEFLATED) as out:
    for n in z.namelist():                               # 원래 순서 유지, 새 시트는 끝에
        out.writestr(z.getinfo(n), files[n])
    out.writestr(new_path, files[new_path])
print(DST, '출처 행', len(ROWS))
