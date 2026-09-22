from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    KeepTogether,
    Flowable,
)


OUT = "관광폭염_임계점_지수_보고서.pdf"
FONT_PATH = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
pdfmetrics.registerFont(TTFont("Korean", FONT_PATH))

NAVY = colors.HexColor("#12304A")
BLUE = colors.HexColor("#1976A3")
TEAL = colors.HexColor("#167C80")
ORANGE = colors.HexColor("#E68A2E")
RED = colors.HexColor("#C94C4C")
INK = colors.HexColor("#22313F")
MUTED = colors.HexColor("#5E6B75")
LIGHT = colors.HexColor("#F3F7F9")
LINE = colors.HexColor("#D6E0E5")


def P(text, style):
    return Paragraph(text, style)


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="CoverTitle", fontName="Korean", fontSize=27, leading=34,
    textColor=NAVY, alignment=TA_LEFT, spaceAfter=10, wordWrap="CJK"))
styles.add(ParagraphStyle(
    name="CoverSub", fontName="Korean", fontSize=13, leading=20,
    textColor=BLUE, alignment=TA_LEFT, spaceAfter=18, wordWrap="CJK"))
styles.add(ParagraphStyle(
    name="H1K", fontName="Korean", fontSize=17, leading=23,
    textColor=NAVY, spaceBefore=10, spaceAfter=9, wordWrap="CJK"))
styles.add(ParagraphStyle(
    name="H2K", fontName="Korean", fontSize=11.5, leading=17,
    textColor=TEAL, spaceBefore=9, spaceAfter=5, wordWrap="CJK"))
styles.add(ParagraphStyle(
    name="BodyK", fontName="Korean", fontSize=9.2, leading=14.2,
    textColor=INK, spaceAfter=6, wordWrap="CJK"))
styles.add(ParagraphStyle(
    name="SmallK", fontName="Korean", fontSize=7.8, leading=11.2,
    textColor=MUTED, spaceAfter=3, wordWrap="CJK"))
styles.add(ParagraphStyle(
    name="CalloutK", fontName="Korean", fontSize=13, leading=20,
    textColor=NAVY, alignment=TA_LEFT, spaceAfter=3, wordWrap="CJK"))
styles.add(ParagraphStyle(
    name="TableK", fontName="Korean", fontSize=7.9, leading=10.8,
    textColor=INK, wordWrap="CJK"))
styles.add(ParagraphStyle(
    name="TableHeadK", fontName="Korean", fontSize=8, leading=11,
    textColor=colors.white, alignment=TA_CENTER, wordWrap="CJK"))
styles.add(ParagraphStyle(
    name="CenterK", fontName="Korean", fontSize=8.8, leading=12,
    textColor=INK, alignment=TA_CENTER, wordWrap="CJK"))


class Rule(Flowable):
    def __init__(self, width=150 * mm, color=LINE, thickness=0.7):
        Flowable.__init__(self)
        self.width = width
        self.height = 5
        self.color = color
        self.thickness = thickness

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 2, self.width, 2)


class FlowDiagram(Flowable):
    def __init__(self):
        Flowable.__init__(self)
        self.width = 170 * mm
        self.height = 45 * mm

    def draw(self):
        c = self.canv
        boxes = [
            (0, "폭염 관측", "기온·강수·특보"),
            (58, "수요 반응 측정", "방문자 지수 V(T)"),
            (116, "재배치 처방", "시간·장소·시기"),
        ]
        for i, (x, title, sub) in enumerate(boxes):
            c.setFillColor([colors.HexColor("#EAF4F8"), colors.HexColor("#E9F5F1"), colors.HexColor("#FFF3E5")][i])
            c.setStrokeColor([BLUE, TEAL, ORANGE][i])
            c.roundRect(x * mm, 14 * mm, 46 * mm, 22 * mm, 3 * mm, fill=1, stroke=1)
            c.setFillColor(NAVY)
            c.setFont("Korean", 9)
            c.drawCentredString(x * mm + 23 * mm, 27 * mm, title)
            c.setFillColor(MUTED)
            c.setFont("Korean", 7)
            c.drawCentredString(x * mm + 23 * mm, 20 * mm, sub)
            if i < 2:
                c.setStrokeColor(MUTED)
                c.setLineWidth(1)
                c.line((x + 46) * mm, 25 * mm, (x + 56) * mm, 25 * mm)
                c.line((x + 54) * mm, 27 * mm, (x + 56) * mm, 25 * mm)
                c.line((x + 54) * mm, 23 * mm, (x + 56) * mm, 25 * mm)


class Matrix(Flowable):
    def __init__(self):
        Flowable.__init__(self)
        self.width = 145 * mm
        self.height = 72 * mm

    def draw(self):
        c = self.canv
        x0, y0, w, h = 28 * mm, 10 * mm, 92 * mm, 52 * mm
        c.setStrokeColor(LINE)
        c.setFillColor(colors.white)
        c.rect(x0, y0, w, h, fill=1, stroke=1)
        c.setStrokeColor(NAVY)
        c.line(x0 + w / 2, y0, x0 + w / 2, y0 + h)
        c.line(x0, y0 + h / 2, x0 + w, y0 + h / 2)
        c.setFont("Korean", 7.5)
        c.setFillColor(MUTED)
        c.drawCentredString(x0 + w / 2, 2 * mm, "RPI 재배치 기회도 →")
        c.saveState()
        c.translate(7 * mm, y0 + h / 2)
        c.rotate(90)
        c.drawCentredString(0, 0, "HVI 폭염 취약도 →")
        c.restoreState()
        c.setFont("Korean", 8)
        c.setFillColor(NAVY)
        c.drawCentredString(x0 + 23 * mm, y0 + 39 * mm, "인프라 투자")
        c.drawCentredString(x0 + 69 * mm, y0 + 39 * mm, "최우선 활성화")
        c.drawCentredString(x0 + 23 * mm, y0 + 13 * mm, "관찰")
        c.drawCentredString(x0 + 69 * mm, y0 + 13 * mm, "여력 보유")
        c.setFillColor(ORANGE)
        c.setFont("Korean", 7)
        c.drawCentredString(x0 + 69 * mm, y0 + 31 * mm, "많이 잃는데 옮길 수 있는 곳")


def table(data, widths, header=True, row_heights=None):
    converted = []
    for ri, row in enumerate(data):
        converted.append([
            P(str(cell), styles["TableHeadK" if header and ri == 0 else "TableK"])
            for cell in row
        ])
    t = Table(converted, colWidths=widths, rowHeights=row_heights, repeatRows=1 if header else 0, hAlign="LEFT")
    cmds = [
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white)]
        if len(data) > 1:
            cmds += [("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT])]
    t.setStyle(TableStyle(cmds))
    return t


class ReportDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(filename, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                         topMargin=18 * mm, bottomMargin=17 * mm, title="관광 폭염 임계점 지수 보고서",
                         author="한국관광 데이터랩 활용 아이디어")
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="normal")
        self.addPageTemplates([PageTemplate(id="main", frames=frame, onPage=self._footer)])

    def _footer(self, canv, doc):
        if doc.page > 1:
            canv.saveState()
            canv.setStrokeColor(LINE)
            canv.line(self.leftMargin, 12 * mm, A4[0] - self.rightMargin, 12 * mm)
            canv.setFont("Korean", 7)
            canv.setFillColor(MUTED)
            canv.drawString(self.leftMargin, 7.5 * mm, "기온 임계점 지수 기반 여름 관광 재배치·활성화 전략")
            canv.drawRightString(A4[0] - self.rightMargin, 7.5 * mm, f"{doc.page}")
            canv.restoreState()


def build_story():
    S = []
    S += [Spacer(1, 20 * mm), P("기온 임계점 지수 기반<br/>여름 관광 재배치·활성화 전략", styles["CoverTitle"]),
          P("관광객이 사라지는 온도는 몇 도인가", styles["CoverSub"]), Rule(), Spacer(1, 8 * mm)]
    cover_box = Table([[P("폭염은 관광 수요를 없애는 것이 아니라 시간대와 장소를 이동시킨다.<br/><br/><b>문제는 수요가 아니라, 그 이동을 따라가지 못하는 관광 공급이다.</b>", styles["CalloutK"])]], colWidths=[170 * mm])
    cover_box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EAF4F8")), ("BOX", (0, 0), (-1, -1), 1, BLUE), ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    S += [cover_box, Spacer(1, 12 * mm),
          P("본 보고서는 한국관광 데이터랩 활용 아이디어를 바탕으로 작성한 정책·분석 설계안입니다. 실제 임계값과 효과 수치는 분석 수행 후 확정합니다.", styles["BodyK"]),
          Spacer(1, 16 * mm), P("작성일 2026년 9월 7일 · 버전 1.0", styles["SmallK"]), PageBreak()]

    S += [P("요약", styles["H1K"]),
          P("이 제안은 데이터랩의 일 단위 이동통신 방문자 데이터와 기상청 기상자료를 결합해, 관광 유형별로 방문 수요가 감소하기 시작하는 기온 임계점(T*)을 산출하는 연구다. 임계점을 기준으로 폭염 위험을 유형별로 다르게 판정하고, 축제·관광지의 운영시간과 개최시기를 재배치한다.", styles["BodyK"]),
          P("핵심 제안", styles["H2K"]),
          table([["구분", "제안 내용"], ["측정", "캠핑·해양·도심·실내 관광의 기온–방문자 반응곡선과 T* 산출"], ["판단", "HVI(취약도)와 RPI(재배치 기회도)로 우선순위 설정"], ["경보", "D-180 계획경보와 D-10 운영경보의 2트랙"], ["처방", "주간→야간, 요일·주차 이동, 8월→10월 시기 조정"], ["검증", "2023~2025 학습, 2026년 단독 백테스트 및 기상청 기준 비교"]], [28*mm, 142*mm]),
          Spacer(1, 8 * mm), P("이 보고서의 판단 기준", styles["H2K"]),
          P("안전은 중요한 부수 효과지만, 본 제안의 중심 문제는 안전관리 자체가 아니다. 핵심은 ‘관광 달력이 기후와 어긋나 수요–공급 미스매치가 발생한다’는 점이다.", styles["BodyK"]), PageBreak()]

    S += [P("1. 문제 정의", styles["H1K"]),
          P("2026년 여름에는 폭염으로 야외행사가 취소·연기되는 동시에, 일부 지역에서는 지역 전체 방문자와 야간 방문이 유지·증가하는 현상이 관찰됐다. 이는 관광객이 완전히 사라졌다는 설명만으로는 충분하지 않다는 뜻이다.", styles["BodyK"]),
          table([["관찰된 격차", "문서상 기초 근거", "해석"], ["동해안 해수욕장 방문객 -19.1%", "시즌 전체 699만 3,547명", "특정 야외 목적지 수요는 감소"], ["동해안 6개 시군 총 방문자 +0.7%(7월), -1.6%(8월)", "데이터랩 직접 조회 결과", "지역 단위 총량은 크게 무너지지 않음"], ["경포해수욕장 야간 방문 +5.5%", "강릉시 자료 인용", "시간대 이동 가능성"], ["2025년 9월 비중 하락·10월 비중 상승", "9개 지역 비교", "쾌적한 관광시기가 뒤로 이동하는 신호"]], [48*mm, 55*mm, 67*mm]),
          Spacer(1, 6 * mm),
          P("따라서 문제는 다음 한 문장으로 좁혀진다.", styles["BodyK"]),
          cover_box, Spacer(1, 4 * mm),
          P("<b>폭염일에 수요가 이동했는데도 축제는 낮에, 관광지는 야외에, 상권은 기존 영업시간에 머물러 있다.</b>", styles["BodyK"]),
          P("주의: 위 관찰값은 내부 조회 및 기사 인용을 바탕으로 한 기초 근거다. 발표 전 동일 기간·동일 공간 단위로 재산출해야 한다.", styles["SmallK"]), PageBreak()]

    S += [P("2. 연구의 차별성과 공백", styles["H1K"]),
          P("기존 연구는 관광 유형별 기후 민감도가 다르다는 사실을 보여주었지만, 월별 자료와 월 누적 폭염일수 중심이어서 ‘몇 도부터 수요가 꺾이는가’를 직접 제시하지 못했다. 본 연구는 일 단위 방문자와 일별 기상자료를 결합해 임계 기온을 추정하고, 그 결과를 사전 경보와 일정 설계에 연결한다.", styles["BodyK"]),
          table([["기존 접근", "본 제안"], ["폭염특보: 체감온도 33·35℃ 중심", "관광 수요가 감소하는 실측 임계점 T*"], ["월별 방문자·폭염일수", "일별 방문자·기온 구간·강수 통제"], ["전 국민 동일 기준", "캠핑·해양·도심·실내 유형별 기준"], ["사후 권고", "D-180 계획경보 + D-10 운영경보"], ["안전 중심", "관광 유치·소비·체류 활성화 중심"]], [75*mm, 95*mm]),
          Spacer(1, 6 * mm), P("핵심 방어 문장", styles["H2K"]),
          P("기상청은 몸이 위험한 온도를 알려주고, 이 연구는 관광 수요가 무너지는 온도를 알려준다. 두 기준은 목적과 대상이 다르다.", styles["CalloutK"]),
          P("본 제안이 안전 분야의 기존 수상작과 겹치지 않도록, 온열질환 저감은 파급력의 보조 효과로만 다루고 본 문제는 ‘기후와 관광 달력의 불일치’로 정의한다.", styles["BodyK"]), PageBreak()]

    S += [P("3. 데이터와 분석 설계", styles["H1K"]),
          P("연구의 기본 단위는 ‘지역 × 일’이다. 특화 데이터는 관광 유형을 분류하는 기준으로 사용하고, 실제 임계점 추정은 일 단위 방문자 데이터로 수행한다.", styles["BodyK"]),
          table([["데이터", "제공 단위", "활용"], ["데이터랩 이동통신 방문자(내국인)", "시군구·행정동·관광지점 / 일", "방문자 반응과 유형별 T*"], ["데이터랩 외국인 방문자", "시군구 / 일·월", "외국인 폭염 행동 보조 분석"], ["캠핑·해양·야간관광 특화 데이터", "월간·목록·분류 기준", "행정동 유형 분류"], ["기상청 ASOS·폭염특보", "관측지점 또는 특보구역 / 일", "기온·강수·특보 변수"], ["신한카드 소비", "시군구 / 월 / 6개 업종", "소비·숙박 성과 보조 지표"], ["축제 개최 정보", "축제별 / 월", "위험등급·시기 재배치 시뮬레이션"]], [48*mm, 48*mm, 74*mm]),
          Spacer(1, 6 * mm), P("분석 흐름", styles["H2K"]), FlowDiagram(),
          P("기준선은 같은 시군구·같은 요일·같은 주차의 비폭염일 평균으로 설정한다. 이 방식으로 주말·휴가철 효과를 줄이고, 강수량·공급 변화·열대야 등 혼란변수를 통제한다.", styles["BodyK"]),
          P("기온 구간 예시: 28℃ 미만 / 28–30℃ / 30–32℃ / 32–34℃ / 34–36℃ / 36℃ 이상", styles["SmallK"]), PageBreak()]

    S += [P("4. 임계점과 지수 체계", styles["H1K"]),
          P("방문자 지수 V(T)는 특정 기온 구간의 평균 방문자를 동일 조건 비폭염일 평균과 비교한 상대 지표다. 절대 방문자 수가 아니라 증감 추세를 사용하는 데이터랩의 권고에도 부합한다.", styles["BodyK"]),
          table([["지표", "정의"], ["V(T)", "기온구간 T의 평균 방문자 ÷ 동일 시군구·요일·주차 비폭염일 평균 방문자 × 100"], ["T*", "V(T)가 기준선 100 대비 통계적으로 유의하게 5% 이상 하락하기 시작하는 지점"], ["HVI", "폭염 임계 초과 빈도·유형 취약도·대응 인프라 부재·야간 대체 불가 등을 결합한 취약도"], ["RPI", "야간·실내 대체 가능성, 숙박 수용력, 비수기 여력을 결합한 재배치 기회도"]], [30*mm, 140*mm]),
          Spacer(1, 5 * mm), P("HVI–RPI 우선순위 매트릭스", styles["H2K"]), Matrix(),
          P("최우선 활성화 대상은 HVI가 높으면서 RPI도 높은 지역이다. 폭염으로 많이 잃지만, 야간·실내·숙박 등 대체 경로가 있어 비교적 적은 비용으로 수요를 포착할 수 있는 곳이다.", styles["BodyK"]), PageBreak()]

    S += [P("5. 관광 폭염경보 운영안", styles["H1K"]),
          P("경보는 절대 기온이 아니라 관광 유형별 T*와의 초과폭으로 발령한다. 같은 34℃라도 캠핑 축제와 해양 축제의 위험도가 다를 수 있도록 설계한다.", styles["BodyK"]),
          table([["등급", "발령 조건", "예상 반응", "권고 행동"], ["관심", "T* - 1℃ 이상", "경미한 감소 가능", "그늘·급수 확충, 안내 강화"], ["주의", "T* 초과", "수요 감소 시작", "주요 프로그램 야간 이동, 실내 대체 준비"], ["경계", "T* + 2℃ 초과 또는 주의 2일 연속", "유의한 감소", "주간 프로그램 축소, 의료·냉방 인력 배치"], ["심각", "T* + 4℃ 초과 또는 기상청 폭염경보 동시 발효", "대규모 감소·운영 차질", "개최 연기 검토, 사전 공지"]], [22*mm, 53*mm, 39*mm, 56*mm]),
          Spacer(1, 5 * mm), P("경보 2트랙", styles["H2K"]),
          table([["트랙", "시점", "입력", "가능한 결정"], ["계획경보", "D-180", "30년 평년값 + 최근 5년 추세", "축제 개최 시기·주차 조정"], ["운영경보", "D-10~D-3", "중기·단기예보와 실시간 특보", "시간대 이동·실내 전환·인력 배치"]], [28*mm, 25*mm, 62*mm, 55*mm]), PageBreak()]

    S += [P("6. 실행 처방과 성과지표", styles["H1K"]),
          P("일정 변경의 실현 가능성을 고려해 비용이 낮은 순서로 처방을 제시한다. 가장 빠른 처방은 축제를 취소하는 것이 아니라, 수요가 살아 있는 시간대로 옮기는 것이다.", styles["BodyK"]),
          table([["단계", "처방", "비용·시점", "검증 지표"], ["1", "주간 프로그램 → 야간 프로그램", "비용 0원, 당해 연도", "야간 방문자·1박 전환율·야간 소비"], ["2", "같은 달의 저위험 요일·주차로 이동", "소액, 차년도", "임계 초과일 감소·방문객 회복"], ["3", "8월 → 9~10월, 특히 10월 검토", "재계약·재홍보, 차년도 이상", "비수기 순증·숙박·지역 소비"]], [18*mm, 65*mm, 42*mm, 45*mm]),
          Spacer(1, 7 * mm), P("성과지표", styles["H2K"]),
          table([["축", "지표", "산출 방향"], ["유치", "비수기 이전 순증", "9~10월 증가분 - 8월 감소분"], ["유치", "폭염일 지역 내 잔류율", "타 시군 유출을 제외한 지역 내 잔류 비율"], ["소비", "야간 전환 시 1인 소비액 변화", "야간 비중 상승 구간의 소비액 변화"], ["체류", "1박 전환율", "숙박 방문자 ÷ 전체 방문자"], ["신뢰성", "Recall·Precision·F1", "2026년 실제 취소·감소 사례 백테스트"], ["정책", "기상청 기준 대비 개선폭", "동일 자료로 기준별 F1 비교"]], [28*mm, 55*mm, 87*mm]), PageBreak()]

    S += [P("7. 검증 설계", styles["H1K"]),
          P("이 연구는 결과가 기대와 다르더라도 다음 의사결정으로 이어지도록 설계한다. 유형별 임계점이 갈리면 차등 경보를 강화하고, 비슷하면 지역별 적응 차이로 축을 전환한다.", styles["BodyK"]),
          table([["검증 질문", "방법", "실패 또는 대안"], ["유형별 T*가 실제로 갈리는가?", "캠핑·해양·도심·실내 파일럿", "지역별 차이와 적응 효과 분석으로 전환"], ["지수가 실제로 맞히는가?", "2023~2025 학습 / 2026 단독 백테스트", "등급 기준·모형 단순화 및 재설정"], ["기상청 기준보다 나은가?", "33·35℃ 기준과 F1 비교", "개선폭 없으면 차별성 주장 축소"], ["야간 이동이 효과가 있는가?", "KBO 2026년 경기시간 이동 자연실험", "효과 없으면 2·3단 처방 중심"], ["수요가 이동인가 소멸인가?", "총량·유형·방문자 유출지 분해", "소멸이면 일정 조정과 손실 방어로 회귀"]], [45*mm, 70*mm, 55*mm]),
          Spacer(1, 6 * mm), P("백테스트 원칙", styles["H2K"]),
          P("2023~2025년 자료로 T*를 추정하고, 2026년 여름 자료는 검증용으로 남긴다. 실제 취소·축소·연기 사례는 발표용 정답지로, 동일조건 대비 방문객 -20% 이상인 날은 통계 검증용 정답지로 활용한다.", styles["BodyK"]),
          P("목표 예시: Recall 0.80 이상, Precision 0.60 이상, F1 0.70 이상, 오경보율 0.30 이하. 최종 목표치는 표본과 데이터 품질 확인 후 조정한다.", styles["SmallK"]), PageBreak()]

    S += [P("8. 기대 산출물과 활용 주체", styles["H1K"]),
          table([["산출물", "사용 주체", "활용 방식"], ["관광 유형별 임계 기온표", "한국관광공사·지자체", "여름철 관광 운영 기준"], ["HVI·RPI 지도와 2축 매트릭스", "지자체·행정안전부", "인력·쉼터·대체 콘텐츠 우선 배치"], ["쿨 시즌 캘린더", "축제 조직위", "차년도 개최 시기 결정"], ["폭염일 대체 관광 코스", "관광공사·지역 상권", "실내·야간·수변 목적지 추천"], ["나이트 패스·1박 전환 설계표", "축제 조직위·숙박업계", "야간 소비와 장기체류 연결"], ["백테스트 보고서·결합 데이터셋", "공모 심사·정책 담당자", "재현성과 성과 증빙"]], [45*mm, 45*mm, 80*mm]),
          Spacer(1, 8 * mm), P("추진 일정", styles["H2K"]),
          table([["단계", "기간", "핵심 작업"], ["1. 데이터 점검", "1주", "숙박 방문자·방문자 유출지·기상자료 조회 가능 여부 확인"], ["2. 파일럿", "2주", "동해안 6개 시군에서 캠핑·해양 T* 산출"], ["3. 모델·백테스트", "3~4주", "유형별 임계점, HVI·RPI, 2026년 검증"], ["4. 정책 패키지", "5주", "경보표·캘린더·재배치 카드·발표자료 완성"]], [32*mm, 25*mm, 113*mm]), PageBreak()]

    S += [P("9. 리스크와 대응", styles["H1K"]),
          table([["리스크", "대응 원칙"], ["기온 효과와 강수·요일 효과 혼재", "강수량·요일·주차·열대야·공급 변화를 통제"], ["ASOS 관측지점과 시군구 불일치", "최근접 관측소 매핑 또는 특보구역 중심 분석"], ["특화 데이터가 월 단위", "특화 데이터는 유형 분류에 사용하고, 방문자 임계점은 일 단위 KT 자료로 추정"], ["T*가 유형별로 다르지 않음", "지역별 적응 효과를 보조 축으로 전환"], ["야간도 감소", "시각 이동 처방을 폐기하고 요일·시기 이동 중심으로 전환"], ["상관관계를 인과로 오해", "‘조정 가능한 상관 변수’로 표현하고 자연실험·백테스트로 검증"], ["동일기간·동일공간 자료 부족", "발표 전 기간 정합성 재산출 및 한계 공개"]], [60*mm, 110*mm]),
          Spacer(1, 8 * mm), P("결론", styles["H1K"]),
          P("이 아이디어의 본질은 폭염을 없애는 것이 아니다. 이미 이동하고 있는 관광 수요를 측정하고, 그 수요가 머물 수 있는 시간·장소·계절로 관광 공급을 옮기는 것이다.", styles["CalloutK"]),
          P("T*는 측정 도구이고, HVI·RPI는 우선순위 도구이며, 최종 성과는 방문객 유치·소비·1박 체류의 증가로 평가한다. 분석 결과가 나오는 즉시 이 보고서는 ‘제안서’에서 ‘검증된 운영 기준’으로 전환될 수 있다.", styles["BodyK"]),
          Spacer(1, 5 * mm), P("주요 참고자료", styles["H2K"]),
          P("한국관광 데이터랩 메타정보·지역별 관광 현황·특화 데이터 메뉴; 기상청 기상자료개방포털 및 폭염특보·ASOS 일자료; 임정민(2025) ‘기후 요소가 관광·레저 활동 유형별 수요에 미치는 영향’; 한국관광공사 ‘2023 문화관광축제 빅데이터 분석 보고서’; 문화체육관광부 성과관리 전략계획(2024~2028); 행정안전부 여름철 축제·공연 안전관리 자료; 내부 문서 ‘폭염경보_최종정리’, ‘폭염경보_활성화_리프레이밍’, ‘폭염경보_활용사례_6종’.", styles["SmallK"]),
          Spacer(1, 4 * mm), P("표기 안내: [확인]은 원문 또는 조회 결과 확인, [검증]은 본 분석에서 산출할 값, ‘○○’은 실제 분석 후 기입할 값이다.", styles["SmallK"])]
    return S


if __name__ == "__main__":
    ReportDoc(OUT).build(build_story())
    print(OUT)
