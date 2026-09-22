"""안동팀 작업 목록(아티팩트 5qmzPDhi1xzAmnUFWg2StE) 3장 '온라인에서 받는 것' 6~11번 수집 결과를 엑셀로 만든다.

원자료: data/external/작업목록_6-11_수집_20260921/  (2026-09-21 웹 수집본)
출력:   조사/06_야간관광명소100선.xlsx … 조사/11_안동관광택시_운영정보.xlsx

규칙(작업 목록 2장): 모든 행에 출처 URL·게시일·조사일, 빈칸은 추정하지 않고 '못 찾음/명시 없음',
'무엇을(열)'을 첫 행에 그대로. 계산값은 엑셀 수식으로 넣는다.
"""
import csv
import datetime as dt
import html as H
import re
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/external/작업목록_6-11_수집_20260921"
OUT = ROOT / "조사"
TODAY = dt.date(2026, 9, 21)

FONT = Font(name="Arial", size=10)
BOLD = Font(name="Arial", size=10, bold=True)
LINK = Font(name="Arial", size=10, color="0563C1", underline="single")
HEAD_FILL = PatternFill("solid", fgColor="D9D9D9")
NOTE_FILL = PatternFill("solid", fgColor="FFF2CC")
WRAP = Alignment(wrap_text=True, vertical="top")


# ───────────────────────── 공통 ─────────────────────────
def write_table(ws, header, rows, widths=None, link_cols=(), date_cols=(), time_cols=(), num_cols=None):
    """header 1행 + rows. link_cols: 하이퍼링크 열 이름, date/time_cols: 서식 적용 열 이름."""
    ws.append(header)
    for c in ws[1]:
        c.font, c.fill, c.alignment = BOLD, HEAD_FILL, Alignment(wrap_text=True, vertical="center")
    for r in rows:
        ws.append(list(r))
    idx = {h: i + 1 for i, h in enumerate(header)}
    num_cols = num_cols or {}
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for c in row:
            c.font, c.alignment = FONT, WRAP
    for name in link_cols:
        col = idx[name]
        for r in range(2, ws.max_row + 1):
            c = ws.cell(r, col)
            if isinstance(c.value, str) and c.value.startswith("http"):
                c.hyperlink, c.font = c.value, LINK
    for name in date_cols:
        for r in range(2, ws.max_row + 1):
            ws.cell(r, idx[name]).number_format = "yyyy-mm-dd"
    for name in time_cols:
        for r in range(2, ws.max_row + 1):
            ws.cell(r, idx[name]).number_format = "hh:mm"
    for name, fmt in num_cols.items():
        for r in range(2, ws.max_row + 1):
            ws.cell(r, idx[name]).number_format = fmt
    if widths:
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(header))}{ws.max_row}"
    return idx


def notes_sheet(wb, title, lines):
    """출처·메모 시트: (구분, 내용) 두 열."""
    ws = wb.create_sheet(title)
    ws.append(["구분", "내용"])
    for c in ws[1]:
        c.font, c.fill = BOLD, HEAD_FILL
    for k, v in lines:
        ws.append([k, v])
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font, c.alignment = FONT, WRAP
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 120
    return ws


def html_text(s):
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"<br\s*/?>", " / ", s, flags=re.I)
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def norm(x):
    return re.sub(r"[\s()\[\]·,'‘’\"“”\-&.:]", "", str(x)).lower()


# ───────────────────────── 06 야간관광 명소 100선 ─────────────────────────
def build_06():
    src_lat = "https://www.latimes.kr/news/articleView.html?idxno=51248"
    src_vk = "https://korean.visitkorea.or.kr/detail/rem_detail.do?cotid=ec1515b2-8a5c-45c9-99dc-a8c23fea9f9b"

    # (1) 문체부 발표 표(Landscape Times 전재): 권역·시도·명소·기간·종류, rowspan 전개
    s = (RAW / "06_야간관광100선/latimes_51248_문체부표.html").read_text(encoding="utf-8")
    t = s[s.find("<table"): s.find("</table>") + 8]
    # 셀 안 태그를 공백 없이 벗긴다(공백으로 바꾸면 '축제/이벤트'가 '축제 / 이벤트'가 돼 집계가 어긋남)
    cell = lambda c: re.sub(r"\s*([()/·‧])\s*", r"\1", re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", "", c))).strip())
    lat, region, sido = [], None, None
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", t, flags=re.S)[1:]:
        cells = [cell(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, flags=re.S)]
        if len(cells) == 5:
            region, sido = cells[0].replace(" ", ""), cells[1]
            cells = cells[2:]
        elif len(cells) == 4:
            sido = cells[0]
            cells = cells[1:]
        lat.append({"권역": region, "시도": re.sub(r"\s*\(\d+\)", "", sido), "명소": cells[0],
                    "기간": cells[1].replace("‧", "·"), "유형": cells[2]})
    assert len(lat) == 100, len(lat)

    # (2) 대한민국 구석구석 공식 목록: 번호 시도 [시군] 명소
    metro = {"서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종"}
    vk = []
    for line in (RAW / "06_야간관광100선/구석구석_밤밤곡곡100_목록.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        left, url = [x.strip() for x in line.split("|", 1)]
        num, rest = left.split(" ", 1)
        tok = rest.split(" ")
        sd = tok[0]
        if sd in metro:
            sg, name = "", " ".join(tok[1:])
        else:
            sg, name = tok[1], " ".join(tok[2:])
        vk.append({"번호": int(num), "시도": sd, "시군": sg, "명소": name, "url": url})
    assert len(vk) == 100

    # (3) 이름 매칭(같은 시도 안에서): 정규화 일치 → 포함관계 → 수동
    manual = {"DDP": "동대문디자인플라자", "한강불빛공연과 드론라이트쇼": "한강불빛공연(드론라이트쇼)"}
    used, out = set(), []
    for v in vk:
        cands = [i for i, l in enumerate(lat) if l["시도"] == v["시도"] and i not in used]
        target = manual.get(v["명소"], v["명소"])
        hit = [i for i in cands if norm(lat[i]["명소"]) == norm(target)]
        if not hit:
            hit = [i for i in cands if norm(target) in norm(lat[i]["명소"]) or norm(lat[i]["명소"]) in norm(target)]
        assert len(hit) == 1, (v, [lat[i]["명소"] for i in hit])
        i = hit[0]
        used.add(i)
        l = lat[i]
        note = "특별·광역시: 원문에 구 표기 없음" if v["시도"] in metro else ""
        if norm(l["명소"]) != norm(v["명소"]):
            note = (note + "; " if note else "") + f"발표 표기와 다름"
        out.append([v["시도"], v["시군"], v["명소"], l["유형"], l["기간"], l["권역"], l["명소"],
                    v["번호"], v["url"] or "(구석구석 상세 링크 없음)", src_vk,
                    "2023-10-31 등록 · 2024-02-19 수정", src_lat, "2023-11-08", TODAY, note])
    order = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원",
             "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
    out.sort(key=lambda r: (order.index(r[0]), r[1], r[2]))

    wb = Workbook()
    ws = wb.active
    ws.title = "100선"
    header = ["시도", "시군", "명소명", "유형", "운영기간", "권역", "문체부 발표 표기", "구석구석 번호",
              "구석구석 상세 URL", "출처 URL", "게시일", "보조 출처 URL(유형·기간)", "보조 게시일", "조사일", "비고"]
    write_table(ws, header, out, widths=[6, 7, 30, 12, 16, 8, 30, 8, 30, 30, 20, 30, 11, 11, 26],
                link_cols=["구석구석 상세 URL", "출처 URL", "보조 출처 URL(유형·기간)"], date_cols=["조사일"])

    # 집계(수식)
    ag = wb.create_sheet("집계")
    types = ["야간경관", "축제/이벤트", "투어프로그램", "유원시설", "미디어아트", "야시장"]
    ag.append(["시도 \\ 유형"] + types + ["합계"])
    for sd in order:
        r = ag.max_row + 1
        ag.append([sd] + [f"=COUNTIFS('100선'!$A:$A,$A{r},'100선'!$D:$D,{get_column_letter(j + 2)}$1)"
                          for j in range(len(types))] + [f"=SUM(B{r}:G{r})"])
    last = ag.max_row
    ag.append(["합계"] + [f"=SUM({get_column_letter(j)}2:{get_column_letter(j)}{last})" for j in range(2, 9)])
    tot_row = ag.max_row
    ag.append([])
    ag.append(["검증: 전체 행 수", "=COUNTA('100선'!C:C)-1", "← 100이어야 함"])
    ag.append([])
    start = ag.max_row + 1
    ag.append(["경북 시군", "명소 수", "명소명(참고)"])
    gb = pd.DataFrame(out, columns=header)
    gb = gb[gb["시도"] == "경북"].groupby("시군")["명소명"].apply(list)
    for sg, names in sorted(gb.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        r = ag.max_row + 1
        ag.append([sg, f"=COUNTIFS('100선'!$A:$A,\"경북\",'100선'!$B:$B,$A{r})", ", ".join(names)])
    ag.append([])
    ag.append(["운영기간", "명소 수"])
    for p in sorted(set(r[4] for r in out)):
        r = ag.max_row + 1
        ag.append([p, f"=COUNTIFS('100선'!$E:$E,$A{r})"])
    for row in ag.iter_rows():
        for c in row:
            c.font = FONT
    for c in list(ag[1]) + list(ag[tot_row]) + list(ag[start]):
        c.font = BOLD
    ag.column_dimensions["A"].width = 26
    for col in "BCDEFGH":
        ag.column_dimensions[col].width = 12
    ag.column_dimensions["C"].width = 14

    notes_sheet(wb, "출처·메모", [
        ("정식 명칭", "「대한민국 밤밤곡곡 100」(문화체육관광부·한국관광공사, 2023-11-08 발표). 작업 목록의 '야간관광 명소 100선'과 같은 것."),
        ("출처 1 (시도·시군·명소명)", f"대한민국 구석구석 '[야간관광지] 밤이 더 아름다운 대한민국! 대한민국 밤밤곡곡 100' {src_vk} (등록 2023-10-31, 수정 2024-02-19). 페이지의 '전체' 탭 100곳을 그대로 옮김."),
        ("출처 2 (유형·운영기간·권역)", f"Landscape Times 2023-11-08 김지운 기자, 문체부 발표 표 전재 {src_lat}. 공식 페이지에는 유형·기간 열이 없어 이 표로 보완."),
        ("결합 방법", "같은 시도 안에서 명소명을 공백·기호 제거 후 일치 → 포함관계로 1:1 매칭(100건 전부 매칭, 수동 2건: DDP=동대문디자인플라자, 한강불빛공연과 드론라이트쇼=한강불빛공연(드론라이트쇼)). 발표 표기와 이름이 다른 곳은 비고에 '발표 표기와 다름'."),
        ("시군 빈칸", "서울·부산·대구·인천·광주·대전·울산·세종은 공식 목록에 구가 없어 비워 둠(추정하지 않음)."),
        ("주의", "Landscape Times 표만 보고 시군을 짐작하면 틀린다: 예) 나오라쇼 '나이트 오브 라이트'는 공식 목록상 강원 '원주'."),
        ("기존 파일", "조사/12_야간관광명소100선.csv(2026-09-14, 안동·비교 도시 11행)는 이 파일의 부분집합이다."),
        ("조사일", "2026-09-21"),
    ])
    path = OUT / "06_야간관광명소100선.xlsx"
    wb.save(path)
    return path, out


# ───────────────────────── 07 2026 탈춤축제 프로그램 ─────────────────────────
COUNTRIES = {"뉴질랜드", "대만", "라트비아", "러시아", "리투아니아", "말레이시아", "멕시코", "몽골", "벨기에", "불가리아",
             "스리랑카", "이스라엘", "이탈리아", "인도", "일본", "중국", "콜롬비아", "콜럼비아", "타타르스탄", "태국",
             "튀르키예", "폴란드", "필리핀", "야쿠티아", "사하공화국"}


def is_foreign(name):
    toks = [re.sub(r"[\d\s()]|ODA", "", t) for t in name.split("/")]
    return all(t in COUNTRIES for t in toks if t) and any(toks)


def region_of(place):
    if place.startswith("하회마을"):
        return "하회마을"
    if place.startswith("중앙선1942"):
        return "중앙선1942(안동역)"
    if place.startswith("원도심"):
        return "원도심"
    if place.startswith("탈춤공원") or place.startswith("탈춤공연장"):
        return "탈춤공원"
    if place.startswith("안동시전역"):
        return "시장·기타(안동시 전역)"
    return "기타"


def build_07():
    base = "https://www.maskdance.com/2024/sub7/sub1.asp?ymd="
    sched = pd.read_csv(RAW / "07_탈춤축제/행사일정표_일자별_원자료.csv", dtype=str)
    cats = pd.read_csv(RAW / "07_탈춤축제/프로그램분류_원자료.csv", dtype=str)
    # 누리집이 '사자놀음/사자놀이'를 섞어 쓴다(같은 회차) → 매칭할 때만 같은 말로 본다
    cat_rows = [(norm(r["name"]).replace("놀음", "놀이"), r["category"], r["name"]) for _, r in cats.iterrows()]
    prio = ["공연-한국탈춤", "공연-하회마을행사", "공연-마당극&창작극", "공연-민속놀이", "공연-외국탈춤",
            "공연-자유참가작", "연계", "전시"]

    def classify(name, place):
        n = name
        if "배우기" in n:
            return "체험", "체험"
        if "퍼레이드" in n:
            return "퍼레이드", "공연"
        if "개막식" in n or "폐막식" in n:
            return "개막식/폐막식", "공연"
        if "경연대회" in n or "TaLooK" in n or "챌린지" in n:
            return "경연", "공연"
        if "대동난장" in n:
            return "참여 프로그램(대동난장)", "공연"
        if any(k in n for k in ("노인의 날", "노인의날", "안동의날", "안동의 날", "기념식", "증류주")):
            return "행사(기념식·시상 등)", "기타"
        if place.startswith("하회마을"):
            return "관광지 프로그램(하회마을)", "공연"
        if is_foreign(n):
            return "공연-외국탈춤(해외공연단)", "공연"
        if any(k in n for k in ("탈놀이단", "시장놀이패", "시장가면", "탈춤외전", "이매 장가", "대학생 탈춤")):
            return "현장 이벤트", "공연"
        nn = norm(n).replace("놀음", "놀이")
        hits = [c for k, c, _ in cat_rows if k == nn]
        if not hits:
            hits = [c for k, c, _ in cat_rows if len(nn) >= 3 and (nn in k or k in nn)]
        if hits:
            c = sorted(set(hits), key=lambda x: prio.index(x) if x in prio else 99)[0]
            return c, ("기타" if c == "전시" else "공연")
        return "미분류(분류 목록에 없음)", "미분류"

    ticket_fee = "유료: 탈춤공연장 관람권 현장 일반 8,000원·학생 6,000원(무료: 6세 이하·기초수급자·장애인·국가유공자)"
    ticket_rsv = "사전예매(8/18~9/17) 종료 → 축제 기간 지정 매표소에서 구매·교환(1매 1회, 공연 후 전원 퇴장)"
    rows = []
    for _, r in sched.iterrows():
        d = dt.datetime.strptime(r["date"], "%Y%m%d").date()
        m = re.match(r"(\d{1,2}):(\d{2})\s*~\s*(?:(\d{1,2}):(\d{2}))?", r["time"])
        st = dt.time(int(m.group(1)), int(m.group(2)))
        en = dt.time(int(m.group(3)), int(m.group(4))) if m.group(3) else None
        place = r["place"]
        cat, typ = classify(r["name"], place)
        if place.startswith("탈춤공연장"):
            fee, rsv = ticket_fee, ticket_rsv
            note = "요금 적용 무대: 공식 입장권 안내엔 무대 미명시, 판매처 상품명 '탈춤공연장 공연관람권'(2025 NOL)으로 확인"
        else:
            fee, rsv, note = "공식 안내에 표기 없음", "공식 안내에 표기 없음", ""
        if place.startswith("하회마을"):
            note = "하회마을 입장료 별도 여부는 확인 필요"
        rows.append([r["name"], typ, place, d, st, en, fee, rsv, None, None, cat, region_of(place), None,
                     base + r["date"], "페이지 게시일 미표기(리플릿 PDF 2026-09-21 생성)", TODAY, note])

    wb = Workbook()
    ws = wb.active
    ws.title = "프로그램_일정"
    header = ["프로그램명", "유형", "장소", "날짜", "시작시각", "종료시각", "요금", "예약 여부",
              "야간(18시 이후 시작)", "21시 이후 종료", "공식분류", "권역", "요일", "출처 URL", "게시일", "조사일", "비고"]
    idx = write_table(ws, header, rows,
                      widths=[30, 7, 22, 11, 8, 8, 28, 28, 10, 10, 22, 16, 5, 30, 22, 11, 30],
                      link_cols=["출처 URL"], date_cols=["날짜", "조사일"], time_cols=["시작시각", "종료시각"])
    D, E, F = (get_column_letter(idx[k]) for k in ("날짜", "시작시각", "종료시각"))
    for r in range(2, ws.max_row + 1):
        ws.cell(r, idx["야간(18시 이후 시작)"]).value = f'=IF({E}{r}>=TIME(18,0,0),"Y","")'
        ws.cell(r, idx["21시 이후 종료"]).value = f'=IF(AND(ISNUMBER({F}{r}),{F}{r}>TIME(21,0,0)),"Y","")'
        ws.cell(r, idx["요일"]).value = f'=CHOOSE(WEEKDAY({D}{r}),"일","월","화","수","목","금","토")'
    n_sched = ws.max_row

    # 기간형·먹거리
    per = wb.create_sheet("기간형·먹거리")
    base2 = "https://www.maskdance.com"
    per_rows = []
    sched_names = {norm(x) for x in sched["name"]}

    def in_schedule(name):  # 날짜별 일정표에 이미 회차가 있는 연계 행사는 빼서 중복을 막는다
        k = norm(name)
        return any(k == s or (len(s) >= 3 and s in k) or (len(k) >= 3 and k in s) for s in sched_names)

    def is_period(when):
        return bool(re.search(r"\d{1,2}\.\s*\d{1,2}\.?\s*~\s*\d{1,2}\.\s*\d{1,2}", when)) or "축제기간" in when

    for _, r in cats[cats["category"].isin(["전시", "연계"])].iterrows():
        # 일정표에 회차가 있거나(이름이 달라도) 시각이 정해진 단일 행사는 '프로그램_일정' 쪽에 있으므로 뺀다
        if in_schedule(r["name"]) or (not is_period(r["when"]) and re.search(r"\d{1,2}:\d{2}", r["when"])):
            continue
        per_rows.append([r["name"], "먹거리" if any(k in r["name"] for k in ("객주로드", "전통주", "소주")) else
                         ("체험" if "체험" in r["name"] else "기타"),
                         r["place"], r["when"], r["category"], base2 + r["href"], "페이지 게시일 미표기", TODAY, ""])
    per_rows += [
        ["탈춤식당(축제 먹거리)", "먹거리", "메인무대 서쪽 대형 그늘막 내부", "축제 기간", "리플릿 '춤추는 탈, 춤추는 맛 탈춤식당'",
         "https://www.maskdance.com/gears_pds/book/123/2026_leaflet_ko%20(2).pdf", "2026-09-21(PDF 생성)", TODAY, "리플릿 2쪽 화면 확인"],
        ["2026 산성마을의 추석", "기타", "한국문화테마파크 산성마을", "2026-09-24~09-27", "리플릿",
         "https://www.maskdance.com/gears_pds/book/123/2026_leaflet_ko%20(2).pdf", "2026-09-21(PDF 생성)", TODAY,
         "공연·전통놀이·떡메치기·소원 적기·포토존(리플릿 문구)"],
        ["탈춤·탈랄라 댄스 따라 배우기(상시 안내)", "체험", "탈춤공원 버스킹 무대", "2026-09-25~10-04 11:00~17:00", "리플릿·체험",
         "https://www.maskdance.com/2024/sub2/sub3_3.asp", "페이지 게시일 미표기", TODAY, "회차별 시간은 '프로그램_일정' 시트"],
    ]
    write_table(per, ["프로그램명", "유형", "장소", "기간·시간", "공식분류", "출처 URL", "게시일", "조사일", "비고"], per_rows,
                widths=[36, 8, 26, 30, 14, 40, 20, 11, 40], link_cols=["출처 URL"], date_cols=["조사일"])
    for r in range(2, per.max_row + 1):
        if "객주로드" in str(per.cell(r, 1).value):
            per.cell(r, 9).value = "버스킹·길거리 객잔·이벤트, '흥해라 청춘': 지역 수제맥주·생맥주 판매, 쉼터(상세 페이지 문구)"

    # 야간 집계(수식)
    ag = wb.create_sheet("야간 집계")
    S = "'프로그램_일정'"
    col = {k: get_column_letter(v) for k, v in idx.items()}
    rng = lambda k: f"{S}!${col[k]}$2:${col[k]}${n_sched}"
    ag.append(["날짜", "요일", "전체 일정 수", "18시 이후 시작", "21시 이후 종료", "18시 이후 비중"])
    for d in sorted(set(r[3] for r in rows)):
        r = ag.max_row + 1
        ag.append([d, f'=CHOOSE(WEEKDAY(A{r}),"일","월","화","수","목","금","토")',
                   f"=COUNTIFS({rng('날짜')},A{r})",
                   f'=COUNTIFS({rng("날짜")},A{r},{rng("야간(18시 이후 시작)")},"Y")',
                   f'=COUNTIFS({rng("날짜")},A{r},{rng("21시 이후 종료")},"Y")',
                   f"=IF(C{r}=0,\"\",D{r}/C{r})"])
        ag.cell(r, 1).number_format = "yyyy-mm-dd"
        ag.cell(r, 6).number_format = "0.0%"
    last = ag.max_row
    ag.append(["합계", "", f"=SUM(C2:C{last})", f"=SUM(D2:D{last})", f"=SUM(E2:E{last})", f"=IF(C{last+1}=0,\"\",D{last+1}/C{last+1})"])
    ag.cell(ag.max_row, 6).number_format = "0.0%"
    ag.append([])
    h2 = ag.max_row + 1
    ag.append(["권역", "", "전체 일정 수", "18시 이후 시작", "21시 이후 종료", "18시 이후 비중"])
    for reg in ["탈춤공원", "중앙선1942(안동역)", "원도심", "시장·기타(안동시 전역)", "하회마을", "기타"]:
        r = ag.max_row + 1
        ag.append([reg, "", f"=COUNTIFS({rng('권역')},A{r})",
                   f'=COUNTIFS({rng("권역")},A{r},{rng("야간(18시 이후 시작)")},"Y")',
                   f'=COUNTIFS({rng("권역")},A{r},{rng("21시 이후 종료")},"Y")', f"=IF(C{r}=0,\"\",D{r}/C{r})"])
        ag.cell(r, 6).number_format = "0.0%"
    ag.append([])
    h3 = ag.max_row + 1
    ag.append(["유형", "", "전체 일정 수", "18시 이후 시작", "21시 이후 종료", "18시 이후 비중"])
    for typ in ["공연", "체험", "기타", "미분류"]:
        r = ag.max_row + 1
        ag.append([typ, "", f"=COUNTIFS({rng('유형')},A{r})",
                   f'=COUNTIFS({rng("유형")},A{r},{rng("야간(18시 이후 시작)")},"Y")',
                   f'=COUNTIFS({rng("유형")},A{r},{rng("21시 이후 종료")},"Y")', f"=IF(C{r}=0,\"\",D{r}/C{r})"])
        ag.cell(r, 6).number_format = "0.0%"
    for row in ag.iter_rows():
        for c in row:
            c.font = FONT
    for rr in (1, last + 1, h2, h3):
        for c in ag[rr]:
            c.font = BOLD
    for k, w in zip("ABCDEF", [22, 6, 13, 14, 14, 14]):
        ag.column_dimensions[k].width = w

    # 셔틀버스(원문 표 그대로, 1행=1회 출발)
    sh = wb.create_sheet("셔틀버스")
    s_url = "https://www.maskdance.com/2024/sub7/sub5.asp"
    wk, hol, sy = "평일(9.24·9.28·9.29·9.30·10.1)", "휴일(9.25·9.26·9.27·10.2)", "선유줄불놀이일(9.26·10.3·10.4)"
    hol2 = "휴일(9.25·9.27·10.2)"
    t1 = ["10:00", "11:00", "13:00", "14:00", "15:00", "16:00", "17:00"]
    srows = []
    for day, dest, times in [(wk, "하회마을매표소", t1), (hol, "하회마을매표소", t1 + ["19:00", "20:00"]),
                             (sy, "안동간고등어숯불가든 본점", t1 + ["19:00", "20:00"])]:
        for tm in times:
            srows.append(["1구간", day, "탈춤축제장", dest, tm])
    for day, stop, a, b in [
        (wk, "하회마을매표소", ["10:00", "11:00", "13:00", "14:00", "15:00", "16:00", "17:30"],
         ["10:30", "11:30", "13:30", "14:30", "15:30", "16:30", "18:00"]),
        (hol2, "하회마을매표소", ["10:00", "11:00", "13:00", "14:00", "15:00", "16:00", "17:30", "19:30", "20:00", "21:00"],
         ["10:30", "11:30", "13:30", "14:30", "15:30", "16:30", "18:00", "20:00", "20:30", "21:30"]),
        (sy, "안동간고등어숯불가든 본점", ["10:00", "11:00", "13:00", "14:00", "15:00", "16:00", "17:30", "19:30", "20:00", "21:00"],
         ["10:30", "11:30", "13:30", "14:30", "15:30", "16:30", "18:00", "20:00", "20:30", "21:30"])]:
        for tm in a:
            srows.append(["2구간", day, stop, "안동시외버스터미널(안동역) → 탈춤축제장", tm])
        for tm in b:
            srows.append(["2구간", day, "안동시외버스터미널(안동역)", "탈춤축제장", tm])
    srows = [r + [s_url, "페이지 게시일 미표기", TODAY,
                  "원문 표 순서대로 전사. 휴게시간 12:00~12:59·18:00~18:59(원문 '운행' 표기는 오기로 보이나 그대로 둠)"] for r in srows]
    write_table(sh, ["구간", "운행일 구분", "출발 정류장", "도착(경유)", "출발 시각", "출처 URL", "게시일", "조사일", "비고"],
                srows, widths=[7, 28, 24, 34, 9, 34, 18, 11, 50], link_cols=["출처 URL"], date_cols=["조사일"])

    # 요금·운영 규정
    rule = wb.create_sheet("요금·운영 규정")
    t_url = "https://www.maskdance.com/2024/sub7/sub2.asp"
    faq = "https://www.maskdance.com/2024/sub4/sub4.asp"
    leaf = "https://www.maskdance.com/gears_pds/book/123/2026_leaflet_ko%20(2).pdf"
    rrows = [
        ["입장권", "일반권 현장 8,000원 / 예매 6,000원(탈춤사랑쿠폰 2,000원 페이백)", t_url, "미표기", "화면 그대로"],
        ["입장권", "학생권 현장 6,000원 / 예매 4,000원", t_url, "미표기", ""],
        ["입장권", "무료관람: 미취학아동(6세 이하)·기초생활수급자·장애인·국가유공자", t_url, "미표기", ""],
        ["입장권", "예매권은 축제기간 지정 매표소에서 당회 입장권으로 교환 후 입장, 교환 시 탈춤사랑쿠폰(2,000원) 지급 / 공연 관람은 1매 1회(공연 후 전원 퇴장)", t_url, "미표기", ""],
        ["입장권 적용 무대", "판매처 상품명 '2025 안동국제탈춤페스티벌 탈춤공연장 공연관람권'(NOL 티켓). 2026 공식 안내엔 무대 미명시", "https://tickets.interpark.com/goods/25014153", "2025", "2026 상품명은 미확인"],
        ["사전예매", "2026-08-18~09-17, 네이버·카카오톡·쿠팡 / 시청 종합민원실·24개 읍면동·지정 판매처", "https://biz.heraldcorp.com/article/10844864", "2026-08-19", "헤럴드경제"],
        ["탈춤사랑쿠폰 사용처", "축제장 인근 원도심(음식의거리, 중앙문화의거리상점가, 남서상점가, 구시장, 중앙신시장 구역 및 주변)의 사용 가능 표지 부착 상가", faq, "미표기", "원도심 식당 연결(1단계)과 직접 관련"],
        ["문화의 거리 도로통제", "신한은행~삼보빌딩, 음식의길 남측 입구~파리바게트 안동중앙점 입구 / 2026-09-22~10-06 매일 17:00~24:00", leaf, "2026-09-21(PDF 생성)", "리플릿(최신). FAQ는 '9.16 10:00~10.7 23:00'로 다름 → 리플릿 우선, 현장 확인 필요"],
        ["문화의 거리 도로통제(FAQ)", "삼산우체국~삼보빌딩, 음식의길 남측 입구~파리바게트 안동중앙점 입구 / 9.16.(수) 10:00~10.7.(수) 23:00", faq, "미표기", "리플릿과 기간·구간 다름"],
        ["벚꽃도로 도로통제", "탈춤공원 뒤편 벚꽃도로(축제장길 200) / 2026-09-16 10:00~10-07 23:00", leaf, "2026-09-21(PDF 생성)", "FAQ와 동일"],
        ["탈놀이 대동난장", "2026-09-26·09-27·09-30·10-03, 19시~ 중앙선1942 메인무대", faq, "미표기", ""],
        ["하회선유줄불놀이", "2026-09-26(토)·10-03(토)·10-04(일) 19:00~21:00, 하회마을 만송정 일원. 요금·예약 표기 없음", "https://www.maskdance.com/2024/sub2/sub1_9.asp", "미표기", "반값여행 지정관광지(지역축제)에도 포함"],
        ["개막식", "2026-09-25(금) 19:00~ 중앙선1942 메인무대(FAQ) / 리플릿은 '18:00~ 메인무대, 개막식 퍼레이드 포함'", faq, "미표기", "퍼레이드 포함 여부에 따라 시작 시각 표기가 다름"],
        ["폐막식", "2026-10-04(일) 20:30~ 중앙선1942 메인무대(탈놀이 경연대회 결승과 함께)", faq, "미표기", ""],
    ]
    write_table(rule, ["항목", "내용", "출처 URL", "게시일", "조사일", "비고"], [[a, b, c, d, TODAY, e] for a, b, c, d, e in rrows],
                widths=[20, 80, 40, 18, 11, 40], link_cols=["출처 URL"], date_cols=["조사일"])

    # 리플릿 대조(탈춤공연장, 9/25~9/29 — 리플릿 2쪽 왼쪽 표를 화면으로 읽은 시각)
    leaflet_times = {"20260925": ["16:30"],
                     "20260926": ["10:00", "11:30", "13:00", "14:30", "16:00", "17:30", "19:00", "20:30"],
                     "20260927": ["10:00", "11:30", "13:00", "14:30", "16:00", "17:30", "19:00", "20:30"],
                     "20260928": ["10:00", "13:30", "15:30", "17:00", "18:30", "20:00"],
                     "20260929": ["10:00", "11:30", "13:30", "15:00", "16:30", "18:30", "20:00"]}
    check = []
    for d, lt in leaflet_times.items():
        web = sorted(re.match(r"(\d{1,2}:\d{2})", x).group(1).zfill(5)
                     for x in sched[(sched["date"] == d) & (sched["place"].str.startswith("탈춤공연장"))]["time"])
        check.append((d, lt, web, sorted(lt) == web))

    unmatched = sorted(set(r[0] for r in rows if r[1] == "미분류"))
    notes_sheet(wb, "출처·메모", [
        ("축제", "2026 안동국제탈춤페스티벌, 2026-09-24(목)~10-04(일) 11일, 주제 '가면의 기억, 모두의 춤'. 주관 한국정신문화재단(054-840-3424)."),
        ("일정 출처", "공식 누리집 행사일정표 날짜별 페이지(https://www.maskdance.com/2024/sub7/sub1.asp?ymd=YYYYMMDD) 11일치 전부. 시간·행사명·장소는 원문 그대로. 원문 표 413행."),
        ("유형 열", "작업 목록의 유형(공연/체험/야간/먹거리) 중 '야간'은 시간 조건이라 별도 열(야간(18시 이후 시작), 21시 이후 종료)로 분리. 유형 = 공연/체험/기타/미분류. 먹거리는 날짜별 일정표에 회차가 없어 '기간형·먹거리' 시트에 둠."),
        ("공식분류 규칙", "리플릿 2쪽 '축제 프로그램' 8분류(개막식·공연·퍼레이드·경연·전시·체험·현장 이벤트·관광지 프로그램) + 누리집 프로그램 메뉴 목록(한국탈춤·외국탈춤·마당극&창작극·자유참가작·민속놀이·하회마을행사·전시·연계, 187개 이름)에 이름을 맞춤. 체험 = 탈춤따라 배우기·탈랄라댄스 배우기(리플릿 체험 목록). 목록에 없는 이름은 미분류로 두고 추정하지 않음."),
        ("미분류 이름", ", ".join(unmatched) if unmatched else "없음"),
        ("요금·예약", "탈춤공연장 공연만 유료(관람권). 공식 입장권 안내엔 적용 무대가 명시돼 있지 않아 판매처 상품명(2025 NOL '탈춤공연장 공연관람권')으로 확인. 다른 무대·체험은 공식 안내에 요금·예약 표기가 없어 '표기 없음'으로 둠(무료라고 단정하지 않음)."),
        ("리플릿 대조", "; ".join(f"{d}: {'일치' if ok else '불일치'}(리플릿 {len(lt)}회/누리집 {len(web)}회)" for d, lt, web, ok in check)
         + " — 탈춤공연장 공연 시각을 리플릿 2쪽 표(9/25~9/29)와 대조."),
        ("리플릿", "2026_leaflet_ko (2).pdf, 2026-09-21 10:57 생성(오늘 오전 갱신본). 글자가 그림이라 화면으로 읽음. 원본·캡처는 data/external/작업목록_6-11_수집_20260921/07_탈춤축제/."),
        ("야간 참고", "선유줄불놀이(9/26·10/3·10/4 19~21시, 하회)일에는 셔틀 1구간 종점이 하회마을매표소 → 안동간고등어숯불가든 본점으로 바뀜. 셔틀 막차: 터미널(안동역) 21:30 출발(휴일·선유일), 평일은 18:00."),
        ("조사일", "2026-09-21"),
    ])
    path = OUT / "07_탈춤축제2026_프로그램.xlsx"
    wb.save(path)
    return path, rows, check, unmatched


# ───────────────────────── 08 안동 반값여행 ─────────────────────────
def build_08():
    pdf_note = "안동시 공고 제2026-2170호(2026-09-10 수정 공고), 팀 보유 PDF data/팀원취합/2026 안동반값여행 공고문.pdf"
    home = "https://andonghalftour.kr"
    aju = "https://www.ajunews.com/view/20260917163314884"
    budget_nf = ("못 찾음 — 찾아본 곳: 공고문 원문, 안동시 선정 보도(천지일보·아시아투데이 2026-08-11), "
                 "문체부 하반기 시행 보도(소셜포커스 2026-08-28), 1차 마감 보도(아주경제 2026-09-17)")
    auth = ("안동시 지정 관광지 1개소 이상 방문 사진(신청대표자·구성원 얼굴 모두 + 랜드마크·간판 노출) + "
            "모바일 안동사랑상품권(CHAK) 대표자 명의 결제 영수증. 여행 종료 후 14일 이내 정산 신청")
    rate = "50%(청년 70%) 모바일 안동사랑상품권 환급. 최소 소비 10만원, 최대 환급 개인 10만·팀 20만·가족 2~5인 20만~50만·청년 14만원('유형별 한도' 시트)"
    rows = [
        ["1차", "2026-09-14(월) 10:00 선착순(여행일 3일 전까지 온라인 사전신청)", "2026-09-17(목)~10-31(토)", auth,
         "36곳('지정관광지' 시트)", rate, "약 5,000명(선착순)", budget_nf, "6,715명 신청, 접수 5시간여 만에 마감(배정 예산 조기 소진)",
         f"{home} / {aju}", "공고 2026-09-10 / 기사 2026-09-17", TODAY, "1차 신청 건수 = 아주경제(안동시 발표 인용). '건'이 아니라 '명'으로 보도됨"],
        ["2차", "2026-10-12(월) 10:00", "2026-10-15(목)~11-30(월)", auth, "36곳('지정관광지' 시트)", rate,
         "공고: '1회차 사업예산에 따라 변동 가능' / 기사: '1차 참여자의 실제 여행 여부와 환급 실적 등에 따라 조정'", budget_nf, "해당 없음(미시작)",
         f"{home} / {aju}", "공고 2026-09-10 / 기사 2026-09-17", TODAY, ""],
    ]
    wb = Workbook()
    ws = wb.active
    ws.title = "조건·실적"
    write_table(ws, ["차수", "신청 기간", "여행 기간", "인증 조건", "지정 관광지 목록", "환급률·한도", "선착순 인원", "사업 예산",
                     "1차 신청 건수", "출처 URL", "게시일", "조사일", "비고"], rows,
                widths=[6, 26, 20, 40, 16, 40, 26, 34, 26, 40, 20, 11, 30], date_cols=["조사일"])

    lim = wb.create_sheet("유형별 한도")
    lim_rows = [["개인", "1인 한정", 0.5, 100000, 200000, None, 100000], ["팀", "2인 이상", 0.5, 100000, 400000, None, 200000],
                ["가족 2인", "동일 주거지 2인", 0.5, 100000, 400000, None, 200000], ["가족 3인", "동일 주거지 3인", 0.5, 100000, 600000, None, 300000],
                ["가족 4인", "동일 주거지 4인", 0.5, 100000, 800000, None, 400000], ["가족 5인", "동일 주거지 5인", 0.5, 100000, 1000000, None, 500000],
                ["청년(만19~34세)", "1인 한정", 0.7, 100000, 200000, None, 140000]]
    write_table(lim, ["유형", "인원 구성", "환급률", "최소 소비액(원)", "최대 소비액(원)", "최대 환급액(계산, 원)", "최대 환급액(공고, 원)",
                      "일치", "출처", "조사일"], [r + [None, pdf_note, TODAY] for r in lim_rows],
                widths=[16, 18, 8, 14, 14, 18, 18, 8, 60, 11], date_cols=["조사일"],
                num_cols={"환급률": "0%", "최소 소비액(원)": "#,##0", "최대 소비액(원)": "#,##0", "최대 환급액(계산, 원)": "#,##0", "최대 환급액(공고, 원)": "#,##0"})
    for r in range(2, lim.max_row + 1):
        lim.cell(r, 6).value = f"=E{r}*C{r}"
        lim.cell(r, 8).value = f'=IF(F{r}=G{r},"일치","확인")'
    lim.append([])
    lim.append(["메모", "환급액은 실제 인정 소비금액 기준 5,000원 단위. 청년은 청년 유형 신청 시에만 70%. 여행유형별 중복 지원 불가. 문체부 발표(단체 최대 20만원)와 달리 안동은 가족 5인까지 최대 50만원."])
    for c in lim[lim.max_row]:
        c.font = FONT

    spots = [("하회마을권역", "하회마을, 병산서원, 부용대, 체화정, 하회세계탈박물관"),
             ("북서부권", "봉정사, 이천동 마애여래입상(제비원 석불), 연미사"),
             ("원도심 및 안동댐권", "찜닭골목, 태사묘, 임청각, 법흥사지 칠층전탑, 월영교, 안동시립박물관, 유교랜드"),
             ("도산권", "도산서원, 한국국학진흥원, 예끼마을, 선성현문화단지, 선성수상길, 안동국제컨벤션센터, 한국문화테마파크, 이육사문학관, 군자마을, 고산정, 농암종택, 경북산림과학박물관"),
             ("남서부권", "권정생동화나라, 단호샌드파크 캠핑장"),
             ("남동부권", "만휴정, 묵계서원, 경상북도독립운동기념관, 안동포타운, 금소생태공원"),
             ("지역축제", "안동국제탈춤페스티벌, 하회선유줄불놀이")]
    sp = wb.create_sheet("지정관광지")
    sp_rows = []
    for reg, names in spots:
        for n in [x.strip() for x in re.split(r",\s*(?![^()]*\))", names)]:
            sp_rows.append([reg, n, "기획 2단계(월영교) 장소" if n == "월영교" else "", pdf_note, "2026-09-10", TODAY])
    write_table(sp, ["권역", "지정 관광지", "비고", "출처", "게시일", "조사일"], sp_rows, widths=[18, 30, 22, 60, 11, 11], date_cols=["조사일"])
    n_sp = sp.max_row
    sp.append([])
    sp.append(["권역별 개수", "", "", "", "", ""])
    for reg, _ in spots:
        r = sp.max_row + 1
        sp.append([reg, f"=COUNTIF($A$2:$A${n_sp},A{r})"])
    r = sp.max_row + 1
    sp.append(["합계", f"=SUM(B{n_sp + 3}:B{r - 1})"])
    for row in sp.iter_rows(min_row=n_sp + 1):
        for c in row:
            c.font = FONT

    cons = wb.create_sheet("소비 인정 기준")
    crow = [["관광소비 인정", "도서/문화/공연/오락 · 숙박업 · 음식점 · 카페/베이커리 · 편의점/슈퍼/마트"],
            ["관광소비 불인정", "가전/통신 · 미용/뷰티/위생 · 부동산 · 산모/육아 · 스포츠/헬스 · 의류/잡화/안경 · 자동차/자전거 · 주방/가전/인테리어 · 주유소 · 학원/교육 · 의료/보건"],
            ["교통비", "안동시 관광택시 및 시티투어 교통비만 인정(톨게이트비·시외버스·기차요금 불인정) → 11번 관광택시와 연결"],
            ["결제 수단", "모바일 안동사랑상품권(CHAK) 대표자 명의 결제. 충전 불가 시 대표자 명의 카드 1개 인정. 온라인 공연 예약 등 미가맹점은 카드 예외 인정"],
            ["숙박", "카드 결제 내역·현금영수증 인정(예약확인서·간이영수증·계좌이체 불인정), 쿠폰·포인트 등 비현금 결제분 불인정"],
            ["지원금", "정산 승인 후 14일 이내 지급, 안동사랑상품권 가맹점·사이버안동장터 사용, 사용기한 2027-04-30(미사용 시 환수)"],
            ["지원 제외", "안동시 및 연접 시군(영주·예천·의성·청송·영양·봉화) 주민, 국내·외 거주 외국인"]]
    write_table(cons, ["구분", "내용", "출처", "조사일"], [r + [pdf_note, TODAY] for r in crow], widths=[16, 100, 50, 11], date_cols=["조사일"])

    notes_sheet(wb, "출처·메모", [
        ("공고", pdf_note + ". 신청·정산은 공식 누리집 https://andonghalftour.kr 에서만(전화·메일·우편 불가). 문의 1660-1748."),
        ("1차 실적", "아주경제 2026-09-17 16:37 '안동 반값여행, 접수 5시간 만에 1차 마감…6715명 신청' https://www.ajunews.com/view/20260917163314884"),
        ("전국 맥락", "2026 하반기 지역사랑 휴가지원 13곳(밀양·거창·완도·영광 + 화천·고성(경남)·산청·함양·안동·영천·서천·태안·장흥). 소셜포커스 2026-08-28 https://www.socialfocus.co.kr/news/articleView.html?idxno=23937"),
        ("사업 예산", "못 찾음 — 위 '조건·실적' 시트에 찾아본 곳 기록. 안동시 관광과(054-840-5000 대표) 또는 정보공개청구로 확인 필요."),
        ("관광택시 연계", "티머니GO 앱 '여행/생활 → 반값여행 → 안동관광택시' 경로로 관광택시 5만원 할인 예약 가능(관광택시 공지 2026-07-27). 11번 파일 참조."),
        ("조사일", "2026-09-21"),
    ])
    path = OUT / "08_안동반값여행_조건실적.xlsx"
    wb.save(path)
    return path


# ───────────────────────── 09 안동사랑상품권 ─────────────────────────
def build_09():
    wb = Workbook()
    ws = wb.active
    ws.title = "월별"
    api1 = "https://www.data.go.kr/data/15108292/openapi.do"
    api2 = "https://www.data.go.kr/data/15108296/openapi.do"
    write_table(ws, ["연월", "발행액", "사용액", "가맹점 수", "출처 URL", "게시일", "조사일", "비고"], [
        ["2024-01~2026-08(목표)", "못 찾음", "못 찾음", "못 찾음", api1, "2025-12-04(데이터셋 수정일)", TODAY,
         "공개 보도·안동시 누리집에 월별 수치 없음. 한국조폐공사 '지역사랑상품권_결제정보'(월별 결제금액·건수, 시군구 47170)와 "
         "'운영정보'(월별 모바일 충전액·지류 판매액·회수액)가 정답 자료 — 저장된 데이터포털 키가 이 두 데이터셋에 활용신청이 안 돼 있어 403(SERVICE_KEY_IS_NOT_REGISTERED_ERROR). "
         "활용신청(자동승인) 후 바로 수집 가능. 'API 수집방법' 시트 참조"],
    ], widths=[20, 10, 10, 10, 44, 24, 11, 110], link_cols=["출처 URL"], date_cols=["조사일"])

    yr = wb.create_sheet("연간 공개수치")
    yrows = [
        ["2023", 1000, "", "", "지류 6,103 / 모바일 2,766 / 카드형 4,675", "", "지류 20만 / 모바일·카드 60만",
         "https://www.kyongbuk.co.kr/news/articleView.html?idxno=2120766", "2023-01-01", TODAY,
         "경북일보. 최근 3년 누적 발행 1,545억원(기사). 가맹점 수는 이 기사 시점 값"],
        ["2025", 1900, 582, 1358, "", "10% + 결제액 10% 추가 적립(월 최대 4만원, 7~8월)", "지류 30만 / 모바일 40만",
         "https://www.metroseoul.co.kr/article/20250629500129", "2025-06-29", TODAY,
         "메트로신문·브릿지경제(2025-06-30): 하반기 1,400억 추가 발행, 연 총 1,900억. 기사의 구성(582+1,358=1,940억)이 총액과 안 맞음 → 원문 그대로, 안동시 확인 필요"],
        ["2026", 1790, 400, 1390, "", "12%(지류 10→12%), 모바일은 가맹점 결제 시 3% 추가 적립", "지류 20만 / 모바일 40만",
         "https://www.kbmaeil.com/article/20260227500074", "2026-02-27", TODAY, "경북매일. 발행 '계획' 규모이며 실제 판매·사용액 아님"],
    ]
    write_table(yr, ["연도", "발행 규모(억원)", "지류(억원)", "모바일(억원)", "가맹점 수", "할인·적립", "월 구매한도(원)",
                     "출처 URL", "게시일", "조사일", "비고"], yrows,
                widths=[7, 12, 10, 11, 30, 30, 22, 44, 11, 11, 60], link_cols=["출처 URL"], date_cols=["조사일"],
                num_cols={"발행 규모(억원)": "#,##0", "지류(억원)": "#,##0", "모바일(억원)": "#,##0"})
    yr.cell(1, 12).value = "지류+모바일(계산)"
    yr.cell(1, 12).font, yr.cell(1, 12).fill = BOLD, HEAD_FILL
    for r in range(2, yr.max_row + 1):
        yr.cell(r, 12).value = f'=IF(AND(ISNUMBER(C{r}),ISNUMBER(D{r})),C{r}+D{r},"")'
        yr.cell(r, 12).number_format = "#,##0"
        yr.cell(r, 12).font = FONT
    yr.column_dimensions["L"].width = 14

    dl = wb.create_sheet("데이터랩_지역화폐관광소비")
    d = pd.read_csv(ROOT / "data/datalab_추가/지역화폐_관광소비_월별_LN_03_03_058_01.csv", dtype={"BASE_DATE": str})
    d = d[d["SGG_NM"] == "경상북도 안동시"].sort_values("BASE_DATE")
    drows = [[f"{b[:4]}-{b[4:]}", float(a), float(t), float(p), None, "https://datalab.visitkorea.or.kr", "월별 공개", TODAY]
             for b, a, t, p in zip(d["BASE_DATE"], d["CARD_AMT"], d["TOTL_CARD_AMT"], d["CARD_PER"])]
    write_table(dl, ["연월", "지역화폐 관광소비(CARD_AMT)", "관광소비 전체(TOTL_CARD_AMT)", "비중(원자료 CARD_PER, %)",
                     "비중(계산)", "출처 URL", "게시일", "조사일"], drows,
                widths=[9, 20, 22, 18, 11, 32, 10, 11], link_cols=["출처 URL"], date_cols=["조사일"],
                num_cols={"지역화폐 관광소비(CARD_AMT)": "#,##0", "관광소비 전체(TOTL_CARD_AMT)": "#,##0"})
    for r in range(2, dl.max_row + 1):
        dl.cell(r, 5).value = f'=IF(C{r}=0,"",B{r}/C{r})'
        dl.cell(r, 5).number_format = "0.00%"
    dl.append([])
    dl.append(["주의", "한국관광 데이터랩 '지역화폐 관광소비 추이'(LN_03_03_058_01) — 관광소비 중 지역화폐로 결제된 부분만이다. 안동사랑상품권 전체 발행·사용액이 아니다. 단위는 원자료에 표기가 없어 비중만 해석할 것. 로컬 원본: data/datalab_추가/지역화폐_관광소비_월별_LN_03_03_058_01.csv(2026-09-14 수집)."])
    for c in dl[dl.max_row]:
        c.font, c.fill = FONT, NOTE_FILL

    ap = wb.create_sheet("API 수집방법")
    arows = [["결제정보(월별 결제금액·건수, 성·연령, 읍면동)", api1, "https://apis.data.go.kr/B190001/localGiftsPaymentV3/paymentsV3",
              "crtr_ym(기준연월), usage_rgn_cd(사용처지역코드 5자리, 안동=47170), stlm_amt(결제금액), stlm_nocs(결제건수), mbl_use_amt, card_use_amt, emd_cd/emd_nm",
              "403 SERVICE_KEY_IS_NOT_REGISTERED_ERROR(2026-09-21 시험)", "활용신청(자동승인) 필요"],
             ["운영정보(월별 모바일 충전액·가입자, 지류 판매·회수액)", api2, "https://apis.data.go.kr/B190001/localGiftsOperateV2/operationsV2",
              "crtr_ym, usage_rgn_cd, mbl_chg_amt(휴대충전금액), mbl_joiner_cnt, ppr_ntsl_amt(지류판매액), ppr_rtrvl_amt(지류회수액), card_pblcn_qty",
              "403 SERVICE_KEY_IS_NOT_REGISTERED_ERROR(2026-09-21 시험)", "활용신청(자동승인) 필요"]]
    write_table(ap, ["데이터", "데이터포털 페이지", "요청 주소", "주요 필드", "시험 결과", "필요 조치"], arows,
                widths=[34, 44, 58, 70, 36, 22], link_cols=["데이터포털 페이지"])
    notes_sheet(wb, "출처·메모", [
        ("결론", "작업 목록이 요구한 '월별 발행액·사용액·가맹점 수'는 공개 보도·안동시 누리집에서 찾지 못했다. 연 단위 발행 '계획'만 보도된다."),
        ("찾아본 곳", "안동시 누리집 안동사랑상품권 메뉴(상품권 안내·가맹점 조회·판매대행점), 경북일보 2023-01-01, 메트로신문 2025-06-29, 브릿지경제 2025-06-30, 경북매일 2026-02-27, 대구일보 등 검색, 공공데이터포털 조폐공사 데이터셋 2종, 지방재정365(작업 목록 제시 출처, 월별 표 미확인)."),
        ("다음 단계", "공공데이터포털에서 15108292·15108296 두 데이터셋 '활용신청'(자동승인)만 하면 같은 키로 2020년 이후 월별 안동(47170) 값을 받을 수 있다."),
        ("반값여행과의 관계", "반값여행 환급은 모바일 안동사랑상품권(정책수당)으로 지급 → 9~11월 조폐공사 결제정보·데이터랩 지역화폐 관광소비가 사후 효과 지표 후보(작업 목록 ⑥)."),
        ("조사일", "2026-09-21"),
    ])
    path = OUT / "09_안동사랑상품권.xlsx"
    wb.save(path)
    return path


# ───────────────────────── 10 야시장·푸드트럭 운영 사례 ─────────────────────────
def build_10():
    NF = "못 찾음"
    rows = [
        ["서울밤도깨비야시장(2017)", 500, "3/24~10/29 주말 운영(요일·시간은 기사에 없음)", 4400000, 11200000000, None, NF, "서울 6곳(여의도·반포·청계천·DDP·청계광장·마포문화비축기지)", "2017",
         "https://edaily.co.kr/News/Read?mediaCodeNo=257&newsId=02824086616096856", "2017-10-26", TODAY,
         "부스 = 푸드트럭 177대 + 핸드메이드 323팀. 방문객 440만여 명은 9월 말 기준 누적(이데일리)"],
        ["서울밤도깨비야시장(2018)", 506, "3~10월 267회", 4280000, 11700000000, None, NF, "서울 6곳", "2018",
         "https://www.hankookilbo.com/news/article/201901071724395270", "2019-01-07", TODAY, "부스 = 푸드트럭 189대 + 수제품 상인 317팀(한국일보)"],
        ["대구 서문야시장(2026)", 26, "3~12월 금·토 19:00~23:30, 일 19:00~22:30", 1400000, NF, None, NF, "대구 중구 서문시장", "2026(방문객은 2025)",
         "https://info.daegu.go.kr/newshome/mtnmain.php?mtnkey=articleview&mkey=scatelist&mkey2=1&aid=276517", "2026-03-26", TODAY,
         "매대 운영자 26명(개장 기준). 모집 공고는 30명(음식 24·푸드트럭 6). 방문객 140만은 '지난해 연간 방문객 140만 명 돌파' — 칠성 포함 여부 불명확"],
        ["대구 칠성야시장(2026)", 10, "3~11월 금·토·일(시간은 서문과 같은 문장)", NF, NF, None, NF, "대구 북구 칠성시장", "2026",
         "https://info.daegu.go.kr/newshome/mtnmain.php?mtnkey=articleview&mkey=scatelist&mkey2=1&aid=276517", "2026-03-26", TODAY,
         "모집 22명(음식 18·푸드트럭 4) 대비 개장 10명 — 모집 대비 운영자 부족(뉴시스 2026-01-19 모집 기사)"],
        ["부산 부평깡통야시장", 27, "매일 19:30~24:00(2016 기준)", NF, NF, None, NF, "부산 중구 부평깡통시장", "2016",
         "https://www.busan.go.kr/news/storyreport/view?dataNo=56491", "2016-10-01", TODAY, "입구부터 110m에 매대 27개(부산시 스토리리포트). 2013년 상설 야시장 1호. 최신 수치 못 찾음"],
        ["전주 남부시장 한옥마을 야시장", 35, "금·토 18:00~(동절기 22시·하절기 24시까지, 2015 기준) / 금·토 17:00~23:00(전주시 2024 공지)", NF, NF, None, NF,
         "전북 전주 남부시장 1층 아케이드", "2015(판매대)·2017(방문객)",
         "https://korean.visitkorea.or.kr/detail/rem_detail.do?cotid=d6bebbb5-29ce-434c-9645-8cdfe6c90543", "2014-12-04 등록·2015-10-16 수정", TODAY,
         "이동판매대 35개(구석구석). 1일 방문객 금 7,000~9,000명·토 9,000~12,000명(전라일보 2017-11-05, 상인 조사 인용) — 연간 아님. 운영시간 출처 https://tour.jeonju.go.kr/board/view.jeonju?boardId=BBS_0000046&menuCd=DOM_000000113001000000&paging=ok&startPage=1&dataSid=13946"],
        ["진주 올빰야시장", 15, "토 18:00~23:00(7월 휴장)", NF, NF, None, NF, "경남 진주 논개시장 일원", "2024",
         "https://www.newsis.com/view/NISX20240529_0002752213", "2024-05-29", TODAY, "음식 매대 15개, 매주 2,000여 명(주간 값, 연간 아님). 2022년부터 진주시 운영"],
        ["강릉 월화거리야시장(2026)", 41, "금·토 18:00~23:00(10/31까지)", NF, NF, None, NF, "강원 강릉 월화거리", "2026",
         "https://www.seoul.co.kr/news/society/2026/05/26/20260526500067", "2026-05-26", TODAY, "매대 41개 = 식품 21 + 프리마켓 20(서울신문)"],
        ["함양 한들 미니포차 야시장(2026)", 14, "토 18:00~22:00", NF, NF, None, NF, "경남 함양 원도심", "2026",
         "https://www.ohmynews.com/NWS_Web/View/at_pg.aspx?CNTN_CD=A0003257828&PAGE_CD=N0002&CMPT_CD=M0117", "2026-08-10", TODAY,
         "14개 팀. 방문객 수치 없음 — '지난해 대비 두 배 가까이', '약 60%가 외지 관광객'(오마이뉴스). 인구감소지역 소도시 사례"],
        ["(참고) 중기부 전통시장육성 문화관광형", "", "", "", "", None, "시장당 2년간 최대 10억원(국비 50%·지방비 50%, 재정자주도에 따라 국비 차등)",
         "전국 공모", "2026년도 사업", "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/view.do?pblancId=PBLN_000000000115511",
         "2025-10-13(공고일)", TODAY, "중소벤처기업부 공고 제2025-538호. 야시장은 문화관광형시장 유형화 핵심 요소 중 하나 — 야시장 전용 예산 아님"],
    ]
    wb = Workbook()
    ws = wb.active
    ws.title = "사례"
    header = ["사업명", "부스 수", "운영 요일·시간", "연 방문객", "총 매출", "부스당 매출", "운영 예산", "지역", "기준 시점",
              "출처 URL", "게시일", "조사일", "비고"]
    write_table(ws, header, rows, widths=[30, 8, 34, 12, 16, 14, 30, 26, 14, 40, 16, 11, 60], link_cols=["출처 URL"],
                date_cols=["조사일"], num_cols={"부스 수": "#,##0", "연 방문객": "#,##0", "총 매출": "#,##0", "부스당 매출": "#,##0"})
    for r in range(2, ws.max_row + 1):
        ws.cell(r, 6).value = f'=IF(AND(ISNUMBER(B{r}),ISNUMBER(E{r}),N(B{r})>0),E{r}/B{r},"계산 불가")'
    ws.cell(1, 6).value = "부스당 매출"
    notes_sheet(wb, "출처·메모", [
        ("부스당 매출", "공개된 부스별 매출은 없어 '총 매출 ÷ 부스 수'를 수식으로 계산(평균, 원). 서울밤도깨비야시장만 계산 가능. 여러 장소·7개월 합계라 월영교 팝업에 그대로 쓰면 안 됨."),
        ("단위", "총 매출·부스당 매출: 원 / 연 방문객: 명(누적 연인원). 주간·1일 방문객은 비고에만 적음."),
        ("운영 예산", "개별 야시장 예산은 모두 못 찾음. 찾아본 곳: 서울시 뉴스(2025 전통시장 야간·음식문화 행사), 대구시 뉴스·대구전통시장진흥재단 모집 공고, 부산시 스토리리포트, 전주시 관광 공지, 진주·함양 보도, 중기부 2026 전통시장 지원사업 공고(문화관광형 한도만 확인)."),
        ("최신성", "부평깡통(2016)·전주 판매대(2015)·방문객(2017)은 오래된 값. 서울밤도깨비는 2019년 이후 결산 보도를 못 찾음."),
        ("작업 목록 용도", "④ 야간 팝업 구성안의 부스 수·운영 요일 참고용. '부스 수를 먼저 정해 놓고 근거를 맞추지 않는다'는 원칙에 따라 비교 범위(14~41개, 주말 2~3일)만 참고."),
        ("조사일", "2026-09-21"),
    ])
    path = OUT / "10_야시장_운영사례.xlsx"
    wb.save(path)
    return path


# ───────────────────────── 11 안동관광택시 ─────────────────────────
def build_11():
    home = "https://andongtourtaxi.com"
    fee = "https://andongtourtaxi.com/home/sub3/sub1.php"
    course = "https://andongtourtaxi.com/home/sub4/sub1.php"
    n192 = "https://andongtourtaxi.com/home/sub5/sub1.php?id=192"
    n194 = "https://andongtourtaxi.com/home/sub5/sub1.php?id=194"
    n88 = "https://andongtourtaxi.com/home/sub5/sub1.php?id=88"
    row = ["사단법인 안동시관광협의회(대표 박창근) — 안동시 관광택시 사업",
           "명시 없음 — 누리집 기사 소개 13명(1명은 소스에서 숨김 처리). 1인 1차량 여부 미기재",
           "못 찾음", "못 찾음",
           "4개 권역(하회·도산·동부·시내) × 5시간/7시간, 현재 노출 9개 코스('코스' 시트). 출발·도착 안동역(또는 협의)",
           "승용 5시간 125,000원(초과 1시간 25,000원), 승합(11인승) 5시간 300,000원(초과 50,000원). 안동역 10km 초과 출발·도착 시 승용 +20,000·승합 +40,000원. 현재 할인: '경북방문의 해 in 안동'(승용 95,000·승합 240,000원), 티머니GO 예약 5만원 할인(7/27~예산 소진)",
           "누리집 온라인 예약(로그인 필요) → 택시 배정 → 확정 문자 / 티머니GO 앱 '여행/생활 → 반값여행 → 안동관광택시' / 취소는 전화 054-855-0515",
           "명시 없음 — 요금은 '택시 1대당 4인 기준', 티머니GO는 '성인 1매당 최대 4명(성인 1명 = 차량 1대)'",
           "명시 없음 — 현재 화면에는 마감 규정 없음(‘최소 3일 전 예약’ 문구는 소스에서 숨김 처리). 2024-01-18 안동시 보도는 '최소 3일 전 누리집 예약'. '금요일 17시 이후 예약은 다음 주 월요일 확인', '예약 당일 자정까지 미입금 시 취소'",
           f"{fee} / {course} / {n192} / {n194}", "요금 페이지 미표기 / 공지 2026-07-27", TODAY,
           "운영시각: 요금 페이지의 '문의가능시간 평일 9~18시'는 상담 시간이지 운행 시간이 아님. 최소 이용 5시간, 대기·식사시간 포함. 안동시 내에서만 운행(타 지역 불가)"]
    wb = Workbook()
    ws = wb.active
    ws.title = "운영정보"
    write_table(ws, ["운영 주체", "차량 대수", "운영 시작시각", "운영 종료시각", "코스·경유지", "요금", "예약 방법", "최소 인원",
                     "예약 마감 시점", "출처 URL", "게시일", "조사일", "비고"], [row],
                widths=[26, 26, 10, 10, 34, 50, 40, 30, 50, 40, 20, 11, 50], date_cols=["조사일"])

    cs = wb.create_sheet("코스")
    crs = [["하회권역", "5시간", 4, 65, 5, "안동역 → 병산서원 → 하회마을 → 하회별신굿탈놀이 → 부용대 → 안동역", "현재 노출"],
           ["하회권역", "7시간", 5, 85, 7, "안동역 → 병산서원 → 하회마을 → 하회별신굿탈놀이 → 부용대 → 봉정사 → 안동역", "현재 노출"],
           ["도산권역", "5시간 A", 6, 85, 5, "안동역 → 노송정종택 → 퇴계종택 → 계상서당 → 한서암 → 퇴계선생 묘 → 도산서원 → 안동역", "현재 노출(2025 개편 '특별 코스')"],
           ["도산권역", "5시간 B", 6, 60, 5, "안동역 → 도산서원 → 예끼마을 → 선성수상길 → 선성현문화단지 → 월영교 → 안동역", "현재 노출. 방문지 수는 표기값(낙강물길공원은 소스에서 숨김)"],
           ["도산권역", "7시간", 8, 95, 7, "안동역 → 이육사문학관 → 도산서원 → 국학진흥원 → 예끼마을 → 선성수상길 → 선성현문화단지 → 월영교 → 안동역", "현재 노출. 낙강물길공원 숨김"],
           ["동부권역", "5시간", 4, 100, 5, "안동역 → 안동포타운 → 만휴정 → 묵계서원 → 독립운동기념관 → 안동역", "현재 노출"],
           ["동부권역", "7시간", 6, 105, 7, "안동역 → 안동포타운 → 만휴정 → 묵계서원 → 독립운동기념관 → 월영교 → 안동역", "현재 노출. 낙강물길공원 숨김"],
           ["시내권역", "5시간", 5, 17, 5, "안동역 → 태사묘 → 임청각 → 월영교 → 시립박물관 → 안동역", "현재 노출. 낙강물길공원 숨김"],
           ["시내권역", "7시간", 7, 73, 7, "안동역 → 봉정사 → 이천동석불상 → 태사묘 → 임청각 → 월영교 → 시립박물관 → 안동역", "현재 노출. 낙강물길공원 숨김"],
           ["전통주 코스(과거)", "7시간 A", 5, 71, 7, "안동역·호텔 → 하회마을 → 병산서원 → 브랜드관 잔잔(17:00) → 안동구시장 → 월영교(자유석식) → 안동역·호텔", "화면 비노출(소스 주석). 2025-10-31·11-01 운영 예정으로 적혀 있던 야간형 코스"],
           ["전통주 코스(과거)", "7시간 B", 5, 61, 7, "안동역·호텔 → 조옥화명인 안동소주 체험(13:50) → 봉정사 → 낙강물길공원 → 안동 구시장 → 월영교(자유석식) → 안동역·호텔", "화면 비노출(소스 주석). 2025-11-07·11-08 운영 예정"]]
    write_table(cs, ["권역", "코스", "방문지 수(표기)", "이동거리(km, 약)", "소요시간(시간, 약)", "경유지(순서)", "노출 상태", "월영교 포함",
                     "출처 URL", "조사일"], [r + [None, course, TODAY] for r in crs],
                widths=[16, 9, 10, 12, 12, 80, 44, 10, 40, 11], link_cols=["출처 URL"], date_cols=["조사일"])
    for r in range(2, cs.max_row + 1):
        cs.cell(r, 8).value = f'=IF(ISNUMBER(SEARCH("월영교",F{r})),"Y","")'
    n = cs.max_row
    cs.append([])
    cs.append(["현재 노출 9개 코스 중 월영교 포함", f'=COUNTIFS(G2:G{n},"현재 노출*",H2:H{n},"Y")'])
    for c in cs[cs.max_row]:
        c.font = BOLD

    fe = wb.create_sheet("요금·할인")
    frows = [["기본 5시간", "승용", 125000, 0, "상시", fee, "미표기"],
             ["기본 5시간", "승합(11인승)", 300000, 0, "상시", fee, "미표기"],
             ["초과 1시간당", "승용", 25000, 0, "상시", fee, "미표기"],
             ["초과 1시간당", "승합(11인승)", 50000, 0, "상시", fee, "미표기"],
             ["안동역 10km 초과 추가비(하회마을·경북도청·예끼마을·만휴정 등)", "승용", 20000, 0, "상시", fee, "미표기"],
             ["안동역 10km 초과 추가비", "승합(11인승)", 40000, 0, "상시", fee, "미표기"],
             ["경북방문의 해 in 안동 할인(현재 적용)", "승용", 125000, 30000, "2026-07-27 공지 기준 적용 중", n192, "2026-07-27"],
             ["경북방문의 해 in 안동 할인(현재 적용)", "승합(11인승)", 300000, 60000, "2026-07-27 공지 기준 적용 중", n192, "2026-07-27"],
             ["티머니GO 예약 할인", "승용", 125000, 50000, "2026-07-27~예산 소진 시", n194, "2026-07-27"],
             ["(과거) 누리집 개설 시 요금", "승용", 100000, 0, "2024-01 보도 기준", n88, "2024-01-18"],
             ["(과거) 누리집 개설 시 요금", "승합", 250000, 0, "2024-01 보도 기준", n88, "2024-01-18"]]
    write_table(fe, ["구분", "차종", "정상가(원)", "할인액(원)", "할인가(원, 계산)", "적용 기간·조건", "출처 URL", "게시일", "조사일", "비고"],
                [r[:4] + [None] + r[4:] + [TODAY, ""] for r in frows],
                widths=[44, 12, 12, 12, 14, 28, 44, 11, 11, 60], link_cols=["출처 URL"], date_cols=["조사일"],
                num_cols={"정상가(원)": "#,##0", "할인액(원)": "#,##0", "할인가(원, 계산)": "#,##0"})
    for r in range(2, fe.max_row + 1):
        fe.cell(r, 5).value = f"=C{r}-D{r}"
    fe.cell(9, 10).value = "공지 제목은 '3만원 할인'이나 승합 할인가는 300,000 → 240,000원(6만원 차이). 공지 원문 할인가 기준으로 할인액 입력"
    fe.cell(10, 10).value = "공지에 할인가 미표기 — 정상가−5만원 계산값. 승합 적용 여부 미표기. 다른 할인과 중복 여부 미표기"
    fe.cell(8, 10).value = "공지 원문 할인가 95,000원"
    for r in (8, 9, 10):
        fe.cell(r, 10).font = FONT
        fe.cell(r, 10).alignment = WRAP
    fe.append([])
    fe.append(["종료된 할인(예산 소진)", "사계절축제연계 30,000원 할인, 틈만나면 안동 30,000원 할인 — 공지 2026-07-27"])
    for c in fe[fe.max_row]:
        c.font = FONT

    nt = wb.create_sheet("공지 이력")
    nrows = [["2026-07-27", "안동관광택시, 티머니GO 예약하면 5만원 할인!", "티머니GO 앱 '여행/생활→반값여행→안동관광택시' 검색, 7/27~예산 소진, 성인 1매당 최대 4명", n194],
             ["2026-07-27", "안동관광택시 할인 혜택 변경 운영 안내", "현재: 경북방문의 해 in 안동 할인 / 종료: 사계절축제연계·틈만나면 안동(예산 소진)", n192],
             ["2026-07-08", "2026년 안동 수(水)페스타 축제 연계 특별 할인 프로모션 안내", "제목만 확인", "https://andongtourtaxi.com/home/sub5/sub1.php?id=190"],
             ["2026-04-21", "2026년 차전장군노국공주 축제 연계 특별 할인 프로모션 안내", "제목만 확인", "https://andongtourtaxi.com/home/sub5/sub1.php?id=170"],
             ["2026-03-31", "2026년 봄맞이 안동관광택시 특별 할인 프로모션 안내", "제목만 확인", "https://andongtourtaxi.com/home/sub5/sub1.php?id=166"],
             ["2026-03-12", "2026년 '틈만나면,안동' 안동관광택시 특별 프로모션 안내", "제목만 확인", "https://andongtourtaxi.com/home/sub5/sub1.php?id=163"],
             ["2026-02-02", "2026년 안동관광택시 요금 안내", "2월은 누리집 요금, 3월부터 사업 시작·할인 이벤트 예정", "https://andongtourtaxi.com/home/sub5/sub1.php?id=161"],
             ["2024-01-18", "안동시, 「안동관광택시」 누리집 개설 보도", "최소 3일 전 누리집 예약, 기본 5시간 10만원(승합 25만원), 초과 2만원(승합 5만원), 다국어", n88]]
    write_table(nt, ["게시일", "제목", "핵심 내용", "출처 URL", "조사일"], [r + [TODAY] for r in nrows],
                widths=[11, 56, 70, 50, 11], link_cols=["출처 URL"], date_cols=["조사일"])
    notes_sheet(wb, "출처·메모", [
        ("운영 시작·종료시각", "못 찾음 — 찾아본 곳: 누리집 요금안내·관광코스·공지 16건 목록(본문 4건), 매일신문 2025-01-05 코스 개편 기사, 안동시 2024-01-18 보도. 예약 화면(출발 가능 시각 선택)은 로그인이 필요해 보지 못함 → 054-855-0515(평일 9~18시) 문의 또는 팀원이 로그인해 예약 화면 캡처."),
        ("숨김 처리", "누리집 HTML 소스에 주석 처리된 항목(최소 3일 전 예약 문구, 기사 1명, 낙강물길공원, 2025 전통주 코스)은 화면에 안 보인다. '코스' 시트에 노출 상태를 따로 적음."),
        ("야간 관련", "현재 코스는 5·7시간 주간형. 2025년 10~11월 전통주 코스는 17:00 이후 구시장·월영교 석식으로 끝나는 야간형이었다(화면 비노출 소스 기록). 2단계 저녁 이동 수단 검토 시 참고."),
        ("반값여행 연계", "반값여행 교통비 인정은 관광택시·시티투어만(공고 제2026-2170호). 티머니GO 할인 경로가 '반값여행' 메뉴 아래."),
        ("찾지 않는 것", "가동률·빈 시간은 대외비(작업 목록 6장). 운행 실적은 19번 정보공개청구 대상."),
        ("조사일", "2026-09-21"),
    ])
    path = OUT / "11_안동관광택시_운영정보.xlsx"
    wb.save(path)
    return path


if __name__ == "__main__":
    p6, out6 = build_06()
    print(p6.name, len(out6), "rows")
    p7, rows7, check7, un7 = build_07()
    print(p7.name, len(rows7), "rows; leaflet check:", [(d, ok) for d, _, _, ok in check7])
    print("  미분류:", len(un7), un7)
    typ = pd.Series([r[1] for r in rows7]).value_counts()
    print("  유형:", typ.to_dict())
    print(build_08().name)
    print(build_09().name)
    print(build_10().name)
    print(build_11().name)
