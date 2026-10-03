# -*- coding: utf-8 -*-
"""서식4 흐름 참고자료 PDF: 데이터랩 첫 화면 느낌 + 팀 피드백 반영 (2026-09-29)

사용자 지시(9/29): "서식4의 흐름을 활용하고 피드백을 반영해서, 10페이지 정도로".
  흐름 = 팀 서식4(카톡 공유본) 네 칸: 1) 문제점 → 2) 데이터 활용 방안 → 3) 사업 개선·적용 → 4) 추진성과·기대효과.
  본문 문장은 팀 서식4 그대로 쓰되, 규칙에 걸리는 두 곳만 고친다(아래 FIX).
팀 피드백(9/29 카톡 PDF):
  1) 전체 톤 파랑, 부정(−)은 빨강, 긍정(+)은 파랑, 검정은 튀니 빼기 → 그림 팔레트는 scripts/보고서그림.py에서 바꿈
  2) 한국관광 데이터랩 첫 화면 느낌(연한 하늘색 띠 + 흰 카드 + 큰 증감 숫자)
  4) 문제점은 빨강(심각한 느낌)
  제목: 데이터 기반 21시 이후 소비 릴레이 '안동 이어드림': 원도심에서 월영교로
카드 숫자는 앞단 JSON에서 읽는다. 그림은 보고서그림 PNG, 제목·출처는 그림메타.json.
쪽 맞춤: 브라우저가 쪽마다 높이를 재서 그림 폭을 줄인다(인쇄 전 JS).
실행: .venv_pdf/bin/python scripts/그림메타_추출.py && .venv_pdf/bin/python scripts/서식4흐름_보고서.py
"""
import json, subprocess
from html import escape
from pathlib import Path

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
E, SC = Q['체험문화'], S['시나리오']
NAMES = ('기준', '흥행', '목표')
P = lambda n, k: SC[n][k]['P50']
now, y24 = E['안동_2026'], E['안동_2024']
m = lambda x, d=1: f'{x:.{d}f}'.replace('-', '−')
pct = {n: SC[n]['참여율'] * 100 for n in NAMES}
p83 = next(c['검정력'] for c in PW['확대안']['곡선'] if abs(c['효과'] - .5) < 1e-9) * 100
bus = Q['버스']['원도심→월영교']
wy = [r for r in Q['월영교조사'] if r['상태'] == '영업']
meal21 = sum(1 for r in wy if r['상권업종중분류명'].strip() != '비알코올' and r['영업종료'] >= '21:00')
jung = next(r for r in Q['혜택배치'] if r['행정동'] == '중구동')

# 9/30 팀 피드백(보고서 피드백.pdf): 5쪽 다음에 3-1) 3D 1인칭 체험 쪽 추가. 링크는 파랑 대신 잘 보이는 색, (바로보기)는 빨강
WEB_URL = 'https://andong-atlas-production.up.railway.app/'
WEB_DIR = ROOT / '보고서/웹소개_핵심이미지_20260930'          # 웹 캡처 동기화본(1280×720)
WEB_TEXT = ("본 프로젝트는 데이터로 분석한 안동 관광의 소비 단절 문제를 해결하기 위해 '안동이어드림' 현장 모델을 3D로 구현했다. "
            "다각도 및 1인칭 시점으로 프로세스를 시각화하여 데이터 기반 해결책의 현장 작동성을 직관적으로 검증하도록 설계했다.")
WEB_FIGS = [('w1', '05_릴레이_서비스_소개.png', '안동 이어드림 관광의 시작'), ('w2', '02_3D_하회마을_상세탐색.png', '안동 도심 살펴보기'),
            ('w3', '11_3D_야경_릴레이연결동선.png', '원도심에서 월영교까지 릴레이 동선(야경)'),   # 9/30 찐막 피드백: 사용자 캡처 추가
            ('w4', '07_릴레이_영수증QR_체험혜택.png', '식사 후 영수증 QR 인증장면'), ('w5', '08_릴레이_하회탈_전통체험.png', '안동 원도심 전통공방 탈 만들기 체험'),
            ('w6', '09_릴레이_월영밤마당_야간팝업.png', '월영교 야간 팝업 「월영 밤마당」')]

TITLE = "데이터 기반 21시 이후 소비 릴레이 '안동 이어드림': 원도심에서 월영교로"
TITLE_H = "데이터 기반 21시 이후 소비 릴레이<br>'안동 이어드림': 원도심에서 월영교로"


def ex_after(n):                                   # 보고서그림.py 34번 요약표와 같은 계산
    v = now * (1 + P(n, '지표1_증가율')); ch = (v / y24 - 1) * 100
    return v, ch, sum(1 for k, x in E['분포'].items() if k != '안동시' and x < ch) + 1


# ── 데이터랩 첫 화면식 숫자 카드: (이름, 기준, 큰 숫자, 단위, 설명, 부호) ──────────
KPI_PROB = [('방문 1회당\n체험·문화 소비', '2024 → 2026년 1~8월', m(E['안동_변화율']), '%', f'{y24:.1f}원 → {now:.1f}원', '−'),
            ('원도심 주민증\n혜택 업체', f"외지인 방문 1위 중구동({jung['방문점유율']:.1f}%)", str(jung['혜택업체']), '개소', '방문 1위 구역에 혜택 없음', '−'),
            ('원도심 → 월영교\n시내버스', '19시 이후 출발', str(bus['19시이후']), '회', f"112번 막차 {bus['막차']}", '−'),
            ('월영교 1km\n21시 이후 식사', f'영업 음식점 {len(wy)}곳 중', str(meal21), '곳', f"주점 {Q['반경1km업종']['월영교'].get('주점', 0)}곳", '−'),
            ('외지인\n방문 연인원', '2024 → 2026년 1~8월', f"+{Q['방문']['변화율']:.1f}", '%', '방문은 늘었다', '+')]
KPI_EFF = [('방문 1회당\n체험·문화 소비', f"참여 {pct['기준']:.0f}% (기준)", f"+{P('기준', '지표1_증가율') * 100:.1f}", '%', f"{now:.1f}원 → {ex_after('기준')[0]:.1f}원", '+'),
           ('원도심 혜택\n가맹점', '원도심 관광식당', '83', '개소', f"0개소 → 83개소 · 인증 월 {P('기준', '인증_월'):,.0f}건", '+'),
           ('주말 저녁\n월영교 유입', '주말 하루', f"+{P('기준', '새이동_하루'):.0f}", '명', f"야간 팝업 이용 {P('기준', '팝업_하루'):.0f}명", '+'),
           ('연간 순수\n추가 소비', f"참여 {pct['기준']:.0f}% (기준)", f"+{P('기준', '추가소비합') / 1e8:.2f}", '억 원', f"참여 {pct['목표']:.0f}% 시 {P('목표', '추가소비합') / 1e8:.2f}억 원", '+'),
           ('시범 운영\n효과 확인 확률', '식당 83곳 · 5개월', f'{p83:.0f}', '%', '체험 결제 +50%일 때', '+')]

# ── 팀 서식4 본문 (카톡 공유본). FIX = 규칙에 걸려 고친 곳 ─────────────────────
FIX = {'전국 평균 회복': '전국 중앙 추세 수준 회복',            # 179.7원은 전국 중앙값 추세로 계산한 값(그림 28과 같게)
       '시범 운영 효과 검증 확률 85% 달성': '시범 운영 시 효과 확인 확률 85%'}   # 검정력은 달성한 성과가 아님
SEC1 = [('방문 1회당 체험 소비액 -16.8% 급감, 원도심 주민증 혜택업체 0개소',
         ['외지인 방문객 증가에도 1회당 체험·문화 소비액 183.5원(2024년) → 152.7원(2026년), -16.8% 감소(하회마을 소비 전환 배율 0.06)',
          '외지인 방문 1위 구역 원도심(중구동, 점유율 12.5%)의 주민증 혜택 가맹점 0개소']),
        ('만휴정·도산서원 방문객 절반 이상이 월영교로 모이지만, 반경 1km 음식점 16곳 중 13곳(81%)이 21시 전 식사 마감·주점 0곳',
         ['저녁 시간대 월영교 집결 비율 만휴정 54.8%, 도산서원 54.2%',
          '21시까지 식사 가능 업소 3개소(18.8%), 주점 0개소(소비 전환 배율 0.40, 소비의 25.8% 편의점 집중)',
          '원도심~월영교(3.2km) 시내버스(112번) 막차 18:45 종료, 19시 이후 야간 소비 연결 단절']),
        ("21시 이후 야간 소비 단절 해소를 위한 데이터 기반 연계 프로그램 '안동 이어드림' 필요",
         ['쿠폰 나열식 정책으로 소상공인 참여·이용률 저조, 21시 이후 상권 마감 및 교통 단절로 야간 소비 유도 미흡',
          '한국관광 데이터랩·설문조사(103명) 분석 결과 동선·시간대별 소비 공백 확인',
          '원도심 식사 → 월영교 야간 이동 → 야간 팝업 체험의 3단계 연계'])]
SEC2 = [('혜택 공백 위치 진단', [('데이터랩', '읍면동별 외지인 방문 데이터'), ('안동시', '주민증 혜택업체 주소 데이터')],
         '매핑 분석', '원도심(방문 1위 구역) 내 주민증 혜택 공백 파악', [9]),
        ('야간 운영 시간대 결정', [('코레일', '안동역 시간대별 KTX 승하차 데이터'), ('안동시', '버스정보시스템(BIS) 노선 시간표'), ('자체 설문', '귀가 시각')],
         '시간대별 교통 공급·수요 교차 분석', '야간 대중교통 단절 타깃 시간대(18:30~21:00) 도출', [16]),
        ('야간 상권 공백 확인', [('소상공인시장진흥공단', '안동시 상가업소 정보'), ('현장 조사', '월영교 반경 1km 영업 실태')],
         '상가업소 정보 및 현장 조사 교차 검증', '21시 이후 식사 가능 업소 3개소 및 야간 인프라 부재 검증', [17]),
        ('사업 기대효과 모의실험', [('데이터랩', '신용카드 관광소비 데이터'), ('자체 설문', '방문객 103명 이용 의향 조사')],
         '데이터 융합 후 1만 회 반복 모의실험(몬테카를로 기법)', '사업 성과의 정량적 예측', [32])]
SEC3_SUM = "한국관광 데이터랩 및 설문조사(103명) 기반, '원도심 혜택 공백'과 '야간 동선 단절' 해결을 위한 3단계 소비 릴레이 '안동 이어드림' 추산 모델"
SEC3 = [('1단계 · 낮', '원도심 식사 → 체험 연계',
         ['원도심 관광식당 83개소(찜닭골목, 문화의거리 등) 방문객 대상',
          '식사 후 관내 체험상품(한지, 안동소주, 전통주, 목공예 등) 10% 할인쿠폰 즉시 발급',
          '참여 경로(3개): ① 영수증 QR 인증(주민증 없이 누구나 참여) ② 디지털관광주민증 제시(주민증 이용 실적 집계, 조건형 혜택 협의 중) ③ 식당 직원의 결제 시 직접 안내'],
         ['원도심(중구동) 외지인 방문 1위(점유율 12.5%, 음식점 764개소), 주민증 혜택업체 0개소',
          '체험 주저 이유의 83%가 가격이 아닌 정보·예약·이동 불편 → 즉시 발급·다중 경로 반영'], [26, 23]),
        ('2단계 · 저녁', '원도심 → 월영교 야간 이동',
         ['대중교통 종료 시간대(18:30~21:00) 관광택시 저녁 배치 및 수요대응형 셔틀버스 운영'],
         ['월영교행 시내버스(112번) 막차 18:45 종료, 19시 이후 대중교통 0회',
          '안동역 KTX 막차(21~22시), 당일 귀가자 58%가 20~22시 귀가 → 동선 설계 반영'], [25]),
        ('3단계 · 밤', '월영교 야간콘텐츠 및 식음 소비',
         ['월영교 도착 후 저녁 문보트 탑승(10% 할인)',
          '21시 이후 식사·주점 이용(월영야행 부지 팝업스토어 운영) 후 KTX·숙소 이동'],
         ['월영교 반경 1km 내 식당 16개소 중 21시까지 식사 가능 3개소(18.8%), 주점 0개소',
          '설문 응답자 53%가 20시 이후 주변 식당·편의시설 부족 지적 → 팝업스토어로 보완'], [19])]
SEC4_NOTE = '본 성과는 한국관광 데이터랩 데이터 및 설문조사(103명) 자료를 바탕으로 모의실험(1만 회 반복 계산)을 통해 도출한 사업 추진 시 기대 정량 예측 수치임'
SEC4 = [('방문당 체험·문화 소비액 +3.5% 증가',
         ["'안동 이어드림' 3단계 야간 릴레이 적용 시 방문 1회당 152.7원 → 158.0원(+3.5%), 목표 참여율 10% 달성 시 179.0원(+17.2%)으로 전국 평균 회복"]),
        ('원도심 혜택 가맹점 0개소 → 83개소 확대', ['체험 연결 인증 월 5,452건 예상, 주민증 월 이용 888건 → 약 1,150건(+30%) 증가 추산']),
        ('주말 저녁 월영교 유입 +110명 증가', ['19시 이후 대중교통 단절(0회) 보완으로 주말 하루 유입 110명, 야간 임시 매장 이용객 128명 창출']),
        ('지역 내 연간 순수 추가 소비 +1.56억 원 창출', ['지원금·기존 소비 대체분 제외 연간 1.56억 원 예측, 목표 참여율 10% 달성 시 6.91억 원 확대']),
        ('시범 운영 효과 검증 확률 85% 달성', ['원도심 식당 83개소 5개월 시범 시 85% 확률 검증, 유사 지자체 6개소·주민증 운영 52개 지자체로 확산 기대'])]
HEAD = [('응모작 제목', TITLE),
        ('활용 데이터 · 데이터랩(필수)', '지역별 관광 현황(외지인 방문자 요일·시간대, 읍면동 방문자), 신용카드 관광소비(업종별), 숙박 현황(평균 숙박일수), 중심-연관 관광지, 내비게이션 목적지 검색, 야간관광 현황, 축제 현황'),
        ('활용 데이터 · 타분야(선택)', '코레일 안동역 시간대별 승하차(2024.1~2026.8), 한국철도공사 8대 도시 가명결합 분석(2022), 소상공인 상가정보(2026.6), 안동시 디지털관광주민증 혜택업체·이용 건수(정보공개청구), 안동시 버스정보시스템 시간표, 관광객 온라인 설문(103명, 2026.9), 월영교 현장 실태 조사'),
        ('성과분야', '전략수립 및 기획 ■ · 상품 및 서비스 개발·개선 ■'),
        ('핵심성과', "데이터랩 기반의 '안동 이어드림' 3단계 야간 릴레이 개발로 안동시 방문당 체험·문화 소비 3.5% 증가(전국 대비 감소폭 20% 회복) 및 연간 추가 소비 1.56억 원 창출 예측"),
        ('계량성과', '온라인 설문조사 103명 실시(안동 방문 경험자 72명 중 체험 할인 쿠폰 이용 의향 79.2%[57명], 야간 셔틀 이용 의향 79.2%[57명], 월영교 야간 팝업 방문 의향 81.9%[59명] 확인)')]

T = {1: ('방문과 체험·문화 소비', '데이터랩'), 8: ('두 거점: 원도심과 월영교', '복합'),
     9: ('읍면동 방문과 혜택 업체', '정보공개'), 16: ('112번 원도심–월영교 시간표', 'BIS'), 17: ('월영교 1km 영업 종료 시각', '상가정보'),
     32: ('참여율 효과 곡선', '예측'), 26: ('3단계 릴레이', '운영안'), 23: ('유료 체험 망설임 이유', '설문'), 25: ('당일 귀가 시각', '설문'),
     19: ('업종 구성: 월영교와 원도심', '상가정보'), 28: ('참여율별 체험 소비 회복', '예측'),
     35: ('순차 확대 검정력', '모의실험'), 38: ('같은 문제 유형 지도', '진단표')}
SOURCES = [('한국관광 데이터랩', '이동통신 방문 연인원 (시·군, 읍면동)', 'BDT_01_01_006 · 2024~2026년 1~8월 월별', [1, 8, 9, 26, 38]),
           ('한국관광 데이터랩', '신용카드 외지인 소비 (업종 중분류)', 'BDT_02_01_003 · 2024~2026년 1~8월 월별', [1, 38]),
           ('한국관광 데이터랩', '평균 숙박일수', 'LN_02_01_013 (전국 진단표)', [38]),
           ('안동시 정보공개청구', '디지털 관광주민증 혜택업체 목록 · 업체별 이용 건수', '목록 2026.9.18 · 이용 2024.6~2026.8', [8, 9]),
           ('안동시 버스정보시스템(BIS)', '시내버스 112번 노선 시간표', '평일 시간표', [8, 16, 26]),
           ('소상공인시장진흥공단', '상가(상권)정보', '2026.6', [8, 17, 19, 26]),
           ('안동팀 확인', '지도 앱 영업시간', '2026.9.19', [8, 17]),
           ('안동팀 온라인 설문', '응답 103명 (안동 방문 경험 72명)', '2026.9.23~24', [23, 25]),
           ('안동팀 모의실험', '이어드림 기대효과 모의실험 1만 번', '시행 전 예측 · 원도심 식당 83곳 운영 · 연간 환산', [28, 32]),
           ('안동팀 모의실험', '순차 확대 검정력 1,000회', '식당 4묶음, 한 달씩 5개월', [35]),
           ('안동팀 전국 진단표', '144개 시·군 네 지표 진단', '2026.9.23', [38]),
           ('안동팀 3D 웹', '안동 이어드림 코스 3D 1인칭 체험 화면', '2026.9.30 캡처', [k for k, *_ in WEB_FIGS])]
used = sorted({n for *_, f in SOURCES for n in f if isinstance(n, int)})
assert used == sorted(T), (used, sorted(T))
DESC = [('보고서명', [TITLE + ' (서식4 참고자료)']), ('작성주체', ['2026 한국관광 데이터랩 활용 경진대회 안동팀']),
        ('구성', ['서식4 활용사례의 네 칸(1) 문제점 → 2) 데이터 활용 방안 → 3) 사업 개선·적용 → 4) 추진성과·기대효과) 순서. 칸마다 한 줄 메시지 → 서식4 문장 → 근거 그림 → 다음 칸으로 잇는 문장']),
        ('작성방법', ['방문 1회당 소비 = 신용카드 외지인 소비 ÷ 이동통신 방문 연인원 (1인당 소비가 아님)',
                  '체험·문화 = 문화서비스 · 관광유원시설 · 기타레저. 안동 값은 전국 시·군 중앙값과 함께 표시',
                  '기대효과 = 설문 의향 × 실현율(0.33~0.40)로 보정한 모의실험 1만 번의 가운데 값과 90% 범위']),
        ('색 표시', ['줄었거나 없는 값(부정)은 빨강, 늘어난 값(긍정)은 파랑']),
        ('유의사항', ['기대효과는 시행 전 예측이며 성과 실적이 아닙니다. 90% 범위는 신뢰구간이 아닙니다.',
                  '설문 의향 %는 참여율이 아닙니다. 순위 예측은 다른 시·군이 그대로일 때의 값입니다.',
                  '철도공사 8대 도시 자료는 데이터랩 수치와 체계가 달라 한 그림에 두지 않았습니다.'])]
NAV = ['1) 문제점', '2) 데이터 활용', '3) 사업 적용', '4) 기대효과']
IDEA = [('1단계 낮', '원도심 식사 → 체험', '낮 · 식사 뒤', '원도심 관광식당 83개소 영수증 인증 → 체험 10% 할인', '원도심 주민증 혜택 업체 0개소'),
        ('2단계 저녁', '원도심 → 월영교 이동', '18:30 ~ 21:00', '관광택시 저녁 배치 · 수요대응형 셔틀', '19시 이후 원도심 출발 112번 0회'),
        ('3단계 밤', '월영교 야간 소비', '21시 전후', '문보트 할인 · 월영야행 부지 팝업스토어', '월영교 1km 주점 0곳')]
LOGO = '''<span class="logo"><svg viewBox="0 0 40 40" width="30" height="30"><circle cx="20" cy="20" r="18" fill="#E6EEFB"/>
<path d="M6 24c6-9 14-11 28-8-10 0-17 4-22 12z" fill="#2D6BD9"/><path d="M10 29c7-5 13-6 22-4-7 1-12 3-16 7z" fill="#8FB0EA"/>
<circle cx="27" cy="11" r="3.2" fill="#E0443E"/></svg><b>안동 이어드림</b><i>데이터 리포트</i></span>'''
REL = '../보고서그림_20260928/'
fx = lambda t: next((t.replace(a, b) for a, b in FIX.items() if a in t), t)


def kpi_band(cards, active, title):
    cs = ''.join(f'''<div class="kc"><p class="kl">{escape(l).replace(chr(10), '<br>')}</p><p class="kb">{escape(b)}</p>
<p class="kv {'neg' if sg == '−' else 'pos'}">{escape(v)}<small>{u}</small></p><p class="ks">{escape(s)}</p></div>'''
                 for l, b, v, u, s, sg in cards)
    return f'<div class="band"><div class="bh"><b>{title}</b></div><div class="kcs">{cs}</div></div>'


# 9/29 팀 피드백 2차: 그림 번호는 보고서에 나오는 순서대로 1, 2, 3 … (그림 안 'EVIDENCE 08' 같은 머리말은 PDF에서만 잘라냄)
CROP = OUT / '_crop'
CROP.mkdir(exist_ok=True)
EB, HEAD_PX, SRC_PX = 80, 262, 92                    # 300dpi px: 머리말 줄 / 머리 전체(머리말·제목·부제·밑줄) / 바닥 출처 줄
NUM = {}


def cropped(no, body):
    from PIL import Image
    im = Image.open(FILES[no]); w, h = im.size
    out = CROP / f"{no:02d}_{'body' if body else 'eb'}.png"
    im.crop((0, HEAD_PX if body else EB, w, h - SRC_PX)).save(out)   # 9/29: 그림 속 출처 줄은 잘라 카드 출처와 겹치지 않게
    return f'_crop/{out.name}'


def card(no, body=False, label=None, cls=''):
    """그림 카드. body=True면 그림 속 제목·문장을 잘라 그래프만 크게(2) 쪽), 이름은 카드 머리에만."""
    NUM.setdefault(no, len(NUM) + 1)
    title, tag = T[no]
    head = (f'<h4><span class="k">{label[0]}</span>{escape(label[1])}</h4><p class="cn">그림 {NUM[no]} · {escape(title)}</p>' if label
            else f'<h4><span class="no">그림 {NUM[no]}</span>{escape(title)}</h4><span class="chip">{escape(tag)}</span>')
    return f'''<div class="card{' ' + cls if cls else ''}"><div class="ch{' ch2' if label else ''}">{head}</div>
<div class="img"><img class="fit" src="{cropped(no, body)}"></div><div class="srcl"><b></b>출처: {escape(META[no]['src'])}</div></div>'''


def web_card(key, fname, cap):
    from PIL import Image
    NUM.setdefault(key, len(NUM) + 1)
    out = CROP / f'{key}.jpg'
    Image.open(WEB_DIR / fname).convert('RGB').save(out, quality=90)
    return (f'<div class="card wc"><div class="img"><img src="_crop/{out.name}"></div>'
            f'<p class="wcap"><b>그림 {NUM[key]}</b>{escape(cap)}</p></div>')


def olist(items, red=False):
    return '<div class="ol">' + ''.join(f'<p class="o{" red" if red else ""}"><i>○</i> {escape(fx(h))}</p>' + ''.join(f'<p class="d">- {escape(fx(x))}</p>' for x in subs)
                                        for h, subs in items) + '</div>'


FLOW = ['1) 문제점', '2) 데이터 활용', '3) 사업 적용', '4) 기대효과']


def top(label, active):
    """쪽 머리 + 진행 띠(검증 영상의 아래 진행 띠를 따옴: 지금 칸은 파랑, 지난 칸은 연파랑)"""
    prog = ''.join(f'<span class="{"on" if k == active else ("done" if active is not None and k < active else "")}">{t}</span>' for k, t in enumerate(FLOW))
    return f'<div class="run">{LOGO}<span>서식4 활용사례 참고자료 · <b>{label}</b></span></div><div class="prog">{prog}</div>'


def msg(dark, blue, red=False):                       # 칸마다 한 줄 메시지(검증 영상 자막과 같은 두 톤). red = 문제 강조
    return f'<p class="msg{" red" if red else ""}">{dark} <b>{blue}</b></p>'


def bridge(text):                                     # 다음 칸으로 잇는 문장
    return f'<p class="bridge"><span>다음</span>{text}</p>'


def sec_title(no, name, red=False, note=''):
    return f'<div class="stt{" red" if red else ""}"><span class="sn">{no}</span><h2>{name}</h2>{f"<em>{note}</em>" if note else ""}</div>'


def page(inner, pno, total):
    return f'<section class="page"><div class="inner">{inner}</div><div class="foot"><span>{TITLE}</span><span>{pno} / {total}</span></div></section>'


def build():
    pages = []
    # 표지
    head = ''.join(f'<tr><th>{k}</th><td>{escape(v)}</td></tr>' for k, v in HEAD)
    idea = ('<table class="dt idea"><thead><tr><th>단계</th><th class="l">무엇을</th><th>언제</th><th class="l">어떻게</th><th class="l">지금 (근거)</th></tr></thead><tbody>'
            + ''.join(f'<tr><td class="c"><span class="stp">{k.split()[0]}</span></td><td class="l"><b>{n}</b></td><td class="c">{w}</td><td class="l">{h}</td><td class="l warn">{g}</td></tr>' for k, n, w, h, g in IDEA) + '</tbody></table>')
    pages.append(f'''<div class="run cover">{LOGO}<span>2026 한국관광 데이터랩 활용 경진대회 · 응모작 참고자료</span></div>
<h1>{TITLE_H}</h1>
<p class="meta">서식4 활용사례 참고자료</p>
<table class="hd">{head}</table>
{kpi_band(KPI_PROB, 0, '문제 한눈에')}
{kpi_band(KPI_EFF, 3, '기대효과 한눈에 <small>시행 전 예측</small>')}
<h3 class="h3">안동 이어드림 3단계</h3>{idea}''')
    # 1) 문제점: 줄고 있다 → 빈 곳 → 그래서 필요하다
    concl = (f'<div class="concl"><p class="o"><i>○</i> {escape(SEC1[2][0])}</p>' + ''.join(f'<p class="d">- {escape(x)}</p>' for x in SEC1[2][1]) + '</div>')
    # 9/30 찐막 피드백: 테마(번호·밑줄·○)는 다른 쪽처럼 파랑, 강조 글씨만 빨강
    pages.append(top('1) 문제점 또는 현안사항', 0) + sec_title('1)', '문제점 또는 현안사항')
                 + msg('방문객은 늘었는데,', '체험·문화 소비는 줄고 있다', red=True) + olist([SEC1[0]]) + card(1)
                 + msg('사람이 모이는 원도심엔 혜택이 없고,', '19시 이후 월영교로 가는 길이 끊긴다', red=True) + olist([SEC1[1]]) + card(8)
                 + concl + bridge('어디가, 언제 비어 있는지 데이터로 확인했다'))
    # 2) 데이터 활용: 한 쪽, 분석 1~4 격자 + 요약 표
    grid = ''.join(card(a[4][0], body=True, label=(f'분석 {i + 1}', f'{a[0]}'), cls='gc') for i, a in enumerate(SEC2))
    tg = lambda o: f'<span class="dtag{" dl" if o == "데이터랩" else ""}">{o}</span>'
    summ2 = ''.join(f'<tr><td class="c"><span class="k">분석 {i + 1}</span></td><td>{" + ".join(tg(o) + " " + escape(d) for o, d in a[1])}</td>'
                    f'<td>{escape(a[2])}</td><td class="res">{escape(a[3])}</td></tr>' for i, a in enumerate(SEC2))
    tbl2 = f'<table class="dt an2"><thead><tr><th>구분</th><th class="l">활용 데이터</th><th class="l">분석 방법</th><th class="l">도출 결과</th></tr></thead><tbody>{summ2}</tbody></table>'
    pages.append(top('2) 데이터 활용 방안', 1) + sec_title('2)', '현안사항 해결을 위한 데이터 활용 방안')
                 + msg('빈 곳은 데이터로 찾고,', '운영 시간과 장소도 데이터로 정했다') + f'<div class="g2">{grid}</div>' + tbl2
                 + bridge('찾아낸 공백(원도심 혜택 · 18:30~21:00 · 월영교 21시 이후)을 3단계 릴레이의 장소와 시간으로 옮겼다'))
    # 3) 사업 적용: 단계마다 근거 → 그림 → 단계 이름 → 추진 내용
    li = lambda xs: ''.join(f'<p>○ {escape(x)}</p>' for x in xs)
    def stage(st):
        k, name, do, why, figs = st
        return (f'<div class="why"><p class="wt">{k.split()[0]} 근거</p>{li(why)}</div>' + card(figs[-1], cls='sm')
                + f'<div class="an st"><div class="anh"><span class="k">{k}</span>{name}</div><table><tr><th>추진 내용</th><td>{li(do)}</td></tr></table></div>')
    summ = f'<div class="sum"><b>적용 사례 요약</b>{escape(SEC3_SUM)}</div>'
    pages.append(top('3) 사업 개선·적용', 2) + sec_title('3)', '데이터 활용을 통한 사업 개선 및 적용 사례')
                 + msg('낮의 원도심에서', '밤의 월영교까지 잇는다') + summ + card(SEC3[0][4][0], cls='sm') + stage(SEC3[0]))
    pages.append(top('3) 사업 개선·적용', 2) + sec_title('3)', '데이터 활용을 통한 사업 개선 및 적용 사례', note='계속') + stage(SEC3[1]) + stage(SEC3[2]))
    # 3-1) 3D 1인칭 체험 (9/30 팀 피드백: 5쪽 다음 새 쪽)
    webs = ''.join(web_card(*w) for w in WEB_FIGS)
    pages.append(top('3) 사업 개선·적용', 2)
                 + sec_title('3-1)', f'안동 이어드림 코스 3D 1인칭 체험 <a class="go" href="{WEB_URL}">(바로보기)</a>')
                 + f'<p class="lnk"><span>링크</span><a href="{WEB_URL}">{WEB_URL}</a></p>'
                 + f'<p class="webp">{escape(WEB_TEXT)}</p><div class="g2 wg">{webs}</div>'
                 + bridge('이 릴레이를 시행하면 무엇이 달라지는지, 시행하기 전에 먼저 계산했다'))
    # 4) 기대효과: 시행 전 계산 → 시행하면서 확인 → 확산
    heads = ''.join(f'<th class="{"hi" if i == 2 else ""}">{n} {pct[n]:.0f}%</th>' for i, n in enumerate(NAMES))
    rows = [('방문 1회당 체험·문화 소비', '원', f'{now:.1f}', *[f'{ex_after(n)[0]:.1f}' for n in NAMES]),
            ('2024년 대비 변화', '%', m(E['안동_변화율']), *[m(ex_after(n)[1]) for n in NAMES]),
            (f"{E['시군수']}개 시·군 중 감소폭 순위", '위', str(E['안동_감소순위']), *[str(ex_after(n)[2]) for n in NAMES]),
            ('월영교로 새로 가는 저녁 이동 (주말 하루)', '명', '-', *[f"{P(n, '새이동_하루'):.0f}" for n in NAMES]),
            ('안동 추가 소비 (연간)', '억 원', '-', *[f"{P(n, '추가소비합') / 1e8:.2f}" for n in NAMES])]
    body = ''.join(f'<tr><td class="l">{escape(r[0])}</td><td class="u">{r[1]}</td><td>{r[2]}</td>' + ''.join(f'<td class="{"hi" if j == 2 else ""}">{v}</td>' for j, v in enumerate(r[3:])) + '</tr>' for r in rows)
    eff = (f'<table class="dt"><thead><tr><th rowspan="2" class="l">지표</th><th rowspan="2">단위</th><th rowspan="2">지금<br><small>2026년 1~8월</small></th>'
           f'<th colspan="3">시행 후 예측 (원도심 방문객 중 참여율)</th></tr><tr>{heads}</tr></thead><tbody>{body}</tbody></table>')
    note = f'<p class="note4">※ {escape(SEC4_NOTE)}</p>'
    pages.append(top('4) 추진성과·기대효과', 3) + sec_title('4)', '추진성과 및 기대효과')
                 + msg('시행하기 전에,', '데이터로 먼저 계산했다') + note + olist(SEC4[:4]) + eff + card(28))
    pages.append(top('4) 추진성과·기대효과', 3) + sec_title('4)', '추진성과 및 기대효과', note='계속')
                 + msg('시행하면서 확인하고,', '같은 문제를 가진 곳으로 넓힌다') + olist(SEC4[4:]) + card(35) + card(38))
    # 데이터 설명
    desc = ''.join(f'<tr><th>{k}</th><td>{"".join(f"<div>▷ {escape(x)}</div>" for x in v)}</td></tr>' for k, v in DESC)
    srows = ''.join(f'<tr><td class="o">{escape(o)}</td><td>{escape(nm)}</td><td class="p">{escape(pr)}</td><td>{"".join(f"<span class=fl>{x}</span>" for x in sorted(NUM[n] for n in f))}</td></tr>' for o, nm, pr, f in SOURCES)
    pages.append(top('데이터 설명', None) + f'''<div class="gold"><span>데이터 설명</span></div>
<table class="desc"><thead><tr><th>구분</th><td>세부내용</td></tr></thead><tbody>{desc}</tbody></table>
<h3 class="h3">자료 출처</h3><table class="srct"><thead><tr><th style="width:25%">제공 기관</th><th style="width:33%">자료</th><th style="width:28%">기간 · 코드</th><th>그림</th></tr></thead><tbody>{srows}</tbody></table>
<p class="nt">※ 그림 번호는 이 보고서 안의 번호입니다. 그림의 숫자는 팀 분석 파일에서 자동으로 읽어 그렸고, 원자료 이용 조건은 각 제공 기관의 조건을 따릅니다.</p>
<p class="nt">※ 생성 코드: scripts/보고서그림.py, scripts/서식4흐름_보고서.py (공개 저장소 github.com/kysk2295/andong-datalab-2026)</p>''')
    total = len(pages)
    return ''.join(page(p, i + 1, total) for i, p in enumerate(pages)), total


CSS = '''
@page{size:210mm 297mm;margin:0}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Pretendard',sans-serif;color:#23272B;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page{width:210mm;height:297mm;position:relative;overflow:hidden;padding:9mm 0 0;page-break-after:always;background:#fff}
.page:last-child{page-break-after:auto}
.inner{height:274mm;overflow:hidden;padding:0 14mm}
.foot{position:absolute;left:14mm;right:14mm;bottom:5mm;display:flex;justify-content:space-between;font-size:6.5pt;color:#9AA2AA;border-top:1px solid #EEF1F4;padding-top:1.6mm}
.logo{display:inline-flex;align-items:center;gap:6px}.logo b{color:#1A4FA8;font-size:13.5pt;font-weight:800;letter-spacing:-.3px}
.logo i{font-style:normal;color:#2D6BD9;font-size:10.5pt;font-weight:600;margin-left:1px}
.util{display:flex;justify-content:flex-end;gap:14px;font-size:7pt;color:#7A828A;margin-bottom:1.5mm}
.gnb-top{display:flex;align-items:center;gap:10mm}
.search{width:62mm;height:8mm;border:1.5px solid #2D6BD9;border-radius:20px;font-size:7.5pt;color:#9AA2AA;display:flex;align-items:center;justify-content:space-between;padding:0 4mm}
.search span{color:#2D6BD9;font-size:12pt}
.team{margin-left:auto;font-size:7.5pt;color:#2D6BD9}
.gnb{display:flex;gap:6mm;font-size:9.5pt;font-weight:700;padding:3mm 0 2.6mm;border-top:1px solid #E3E8EE;border-bottom:1px solid #E3E8EE;margin-top:2mm}
.gnb small{color:#9AA2AA;font-size:6.5pt;margin-left:1px}
.alert{display:flex;align-items:center;gap:2.5mm;font-size:7.6pt;color:#34383C;margin:3mm 0 1mm}
.al{background:#2D6BD9;color:#fff;font-weight:700;border-radius:10px;padding:.6mm 2.6mm;font-size:6.8pt}
.alert .more{margin-left:auto;color:#8A939C;font-size:6.8pt}
h1{font-size:20pt;font-weight:800;letter-spacing:-.6px;line-height:1.3;margin:4mm 0 3mm}
table.hd{width:100%;border-collapse:collapse;font-size:7.4pt;border-top:2px solid #2D6BD9;margin-bottom:4mm}
.hd th{width:34mm;background:#F3F6FA;font-weight:700;color:#34383C;text-align:left;padding:1.4mm 2.5mm;border-bottom:1px solid #DDE3EA;vertical-align:top}
.hd td{padding:1.4mm 2.5mm;border-bottom:1px solid #E3E8EE;line-height:1.55;color:#34383C}
.band{margin:0 -14mm 3.5mm;padding:3.5mm 14mm 4mm;background:linear-gradient(180deg,#E4F2FC,#D6EBF8)}
.bh{display:flex;align-items:center;justify-content:space-between;margin-bottom:2.6mm}
.bh b{font-size:10pt;font-weight:800;color:#1A4FA8}.bh b small{font-size:7pt;font-weight:500;color:#5C7FB8;margin-left:1.5mm}
.pills{display:flex;gap:1.5mm;background:#fff;border-radius:20px;padding:1mm;box-shadow:0 1px 3px rgba(26,79,168,.12)}
.pill{font-size:6.8pt;padding:1mm 3mm;border-radius:14px;color:#5B6B80}.pill.on{background:#2D6BD9;color:#fff;font-weight:700}
.kcs{display:grid;grid-template-columns:repeat(5,1fr);gap:2.2mm}
.kc{background:#fff;border-radius:7px;padding:2.6mm 2.6mm 2mm;box-shadow:0 1px 4px rgba(26,79,168,.10);display:flex;flex-direction:column}
.kl{font-size:7.2pt;font-weight:800;line-height:1.3;color:#23272B;min-height:7mm}
.kb{font-size:5.9pt;color:#8A939C;margin-top:.6mm;min-height:4.6mm;line-height:1.3}
.kv{font-size:19pt;font-weight:900;letter-spacing:-.5px;line-height:1.05;margin-top:1.2mm}.kv small{font-size:8pt;font-weight:800;margin-left:.6mm}
.kv.neg{color:#E0443E}.kv.pos{color:#2D6BD9}
.ks{font-size:6.2pt;color:#4A5057;margin-top:1mm;line-height:1.35;flex:1}
.kf{display:flex;justify-content:space-between;font-size:5.8pt;color:#9AA2AA;border-top:1px solid #EEF1F4;margin-top:1.6mm;padding-top:1mm}
.run{display:flex;align-items:center;justify-content:space-between;height:9mm;border-bottom:1px solid #C9D3E0;margin-bottom:4mm;font-size:7pt;color:#7A828A}.run b{color:#23272B}
.run .logo svg{width:20px;height:20px}.run .logo b{font-size:10pt;color:#1A4FA8}.run .logo i{font-size:8.5pt}
.run.cover{border-bottom:2px solid #2D6BD9;margin-bottom:6mm}
.meta{font-size:8pt;color:#7A828A;margin:-1.5mm 0 4mm}
.nt{font-size:6.8pt;color:#6B7177;margin-top:2mm}
.topbar{display:flex;align-items:center;justify-content:space-between;height:10mm;border-bottom:1px solid #E3E8EE}
.topbar .logo svg{width:22px;height:22px}.topbar .logo b{font-size:11pt}.topbar .logo i{font-size:9pt}
.nvs{display:flex;gap:1.2mm}.nv{font-size:6.8pt;padding:.9mm 2.6mm;border:1px solid #CBD5E1;border-radius:3px;color:#5B6B80}.nv.on{background:#2D6BD9;border-color:#2D6BD9;color:#fff;font-weight:700}
.crumb{font-size:7pt;color:#7A828A;margin:2.2mm 0 1.2mm}.crumb b{color:#23272B}
.stt{display:flex;align-items:baseline;gap:2.5mm;padding-bottom:1.8mm;border-bottom:2px solid #2D6BD9;margin-bottom:3mm}
.stt .sn{font-size:15pt;font-weight:900;color:#2D6BD9}.stt h2{font-size:14pt;font-weight:800;letter-spacing:-.4px}.stt em{font-style:normal;font-size:7.4pt;color:#8A939C;margin-left:auto}
.stt.red{border-color:#E0443E}.stt.red .sn{color:#E0443E}
.ol{margin-bottom:2mm}
.ol .o{font-size:8.6pt;font-weight:800;line-height:1.5;margin-top:1.6mm;padding-left:3.6mm;text-indent:-3.6mm;color:#1A4FA8}
.ol .o{color:#23272B}.ol .o i{font-style:normal;color:#2D6BD9}.ol .o.red i{color:#E0443E}   /* 9/29 사용자: 빨간 글자는 과함 → 글자는 진한 색, 기호만 색 */
.ol .d{font-size:7.8pt;line-height:1.6;color:#34383C;padding-left:6.6mm;text-indent:-2.6mm}
.lead{font-size:7.6pt;color:#6B7177;margin-bottom:2.4mm}
.an{border:1px solid #DDE3EA;border-radius:6px;overflow:hidden;margin-bottom:2.4mm}
.anh{background:linear-gradient(180deg,#E4F2FC,#D9EDF9);padding:2mm 3mm;font-size:9pt;font-weight:800;color:#1A4FA8;display:flex;align-items:center;gap:2.4mm}
.anh .k{background:#2D6BD9;color:#fff;font-size:6.8pt;padding:.5mm 2.4mm;border-radius:10px;font-weight:700}
.an table{width:100%;border-collapse:collapse;font-size:7.6pt}
.an th{width:21mm;background:#F6F8FB;color:#4A5057;font-weight:600;text-align:left;padding:1.5mm 3mm;border-top:1px solid #E6EAF0;vertical-align:top}
.an td{padding:1.5mm 3mm;border-top:1px solid #E6EAF0;line-height:1.6;color:#34383C}.an td.res{font-weight:700;color:#1A4FA8}
.an td p{padding-left:3mm;text-indent:-3mm}
.an3 th{width:auto;background:#F6F8FB;font-size:6.8pt;padding:1mm 3mm}.an3 td{vertical-align:top;font-size:7.3pt;padding:1.3mm 3mm}.an3 td:nth-child(1){width:46%}.an3 td:nth-child(2){width:24%}
.dtag{display:inline-block;font-size:6.2pt;font-weight:700;padding:.2mm 1.6mm;border-radius:2px;border:1px solid #9AA7B8;color:#5B6B80;margin-right:.6mm;text-indent:0}
.dtag.dl{border-color:#2D6BD9;background:#2D6BD9;color:#fff}
.sum{background:#F3F8FD;border:1px solid #D6E6F6;border-radius:6px;padding:2.4mm 3.5mm;font-size:7.8pt;line-height:1.6;margin-bottom:2.6mm;color:#34383C}
.sum b{display:block;color:#1A4FA8;font-size:8.4pt;margin-bottom:.6mm}
.note4{font-size:7pt;color:#6B7177;line-height:1.55;background:#F6F8FB;border-radius:4px;padding:1.8mm 2.6mm}
table.dt{width:100%;border-collapse:collapse;font-size:7.4pt;border-top:2px solid #2D6BD9;margin:2.4mm 0 2.6mm}
.dt th{background:#F3F6FA;font-weight:700;padding:1.3mm 2mm;border:1px solid #DDE3EA;text-align:center}.dt th small{font-weight:500;color:#7A828A;font-size:6.2pt}
.dt td{padding:1.3mm 2mm;border:1px solid #E3E8EE;text-align:right;font-variant-numeric:tabular-nums}
.dt .l{text-align:left}.dt .c{text-align:center}.dt:not(.idea) .l{width:36%}
.idea td{padding:1.8mm 2mm}.idea .warn{font-weight:600}
.stp{display:inline-block;background:#2D6BD9;color:#fff;font-size:6.6pt;font-weight:800;border-radius:3mm;padding:.4mm 2.4mm}.dt td.u{text-align:center;color:#7A828A}.dt .hi{background:#EAF1FC;color:#1A4FA8;font-weight:800}.dt th.hi{background:#DCE8FB}
.card{border:1px solid #E3E8EE;border-radius:5px;padding:2.2mm 4mm 2.4mm;background:#fff;margin-bottom:2.6mm}
.ch{display:flex;align-items:center;gap:1.4mm;height:6mm;margin-bottom:1mm}
.ch h4{font-size:8.8pt;font-weight:800;margin-right:1.5mm;letter-spacing:-.2px}.ch .no{color:#2D6BD9;margin-right:1.6mm}
.chip{font-size:6.2pt;padding:.6mm 2mm;border:1px solid #2D6BD9;color:#2D6BD9;border-radius:2px;white-space:nowrap}.chip.on{background:#2D6BD9;color:#fff}
.links{margin-left:auto;font-size:6.2pt;color:#8A939C;white-space:nowrap}.links i{font-style:normal;color:#CBD5E1;margin:0 1mm}
.img{text-align:center}.img img{display:inline-block;width:100%}
.srcl{display:flex;gap:1.5mm;font-size:6.3pt;line-height:1.45;color:#5B6269;margin-top:1mm;padding-top:1mm;border-top:1px dashed #E3E8EE}
.srcl b{flex:none;width:1.4mm;height:1.4mm;background:#2D6BD9;margin-top:1mm}
.gold{display:flex;justify-content:space-between;align-items:center;background:linear-gradient(#E8C067,#E2B65A);border-radius:6px;padding:3mm 6mm;margin:3mm 0 3.5mm;font-size:10.5pt;font-weight:800;color:#3D2E10;box-shadow:0 1px 3px rgba(0,0,0,.12)}
.desc,.srct{width:100%;border-collapse:collapse;font-size:7.1pt;border-top:1.5px solid #34383C}
.desc th{width:18mm;background:#F6F7F9;font-weight:600;color:#4A5057;text-align:center;padding:1.5mm;border-bottom:1px solid #E6E9ED}
.desc thead th,.desc thead td{font-weight:700;color:#23272B;text-align:center;background:#F6F7F9}
.desc td{padding:1.5mm 2.5mm;border-bottom:1px solid #E6E9ED;line-height:1.55;color:#34383C}
.h3{font-size:9pt;font-weight:800;margin:4.5mm 0 2mm}
.srct th{background:#F6F7F9;padding:1.5mm 1.8mm;border-bottom:1px solid #E6E9ED;text-align:left}
.srct td{padding:1.3mm 1.8mm;border-bottom:1px solid #E6E9ED;vertical-align:top}.srct .o{font-weight:700}.srct .p{color:#6B7177}
.fl{display:inline-block;min-width:5mm;text-align:center;font-size:6.4pt;font-weight:700;color:#2D6BD9;border:1px solid #CFDAEA;border-radius:2px;margin:0 .8mm .5mm 0}
.lic{display:flex;align-items:center;gap:3mm;margin-top:2.6mm;font-size:6.8pt;color:#4A5057}
.open{display:inline-flex;align-items:center;border:1.4px solid #23272B;border-radius:3px;font-weight:900;font-size:7.5pt;padding-left:1.8mm;flex:none}
.open em{font-style:normal;background:#23272B;color:#fff;margin-left:1.8mm;padding:.6mm 1.8mm;font-size:6.5pt;font-weight:700}
/* 9/29 팀 피드백 2차: 글씨 키우고 그림은 조금 작게 */
.ol .o{font-size:9.6pt}.ol .d{font-size:8.7pt}
.lead{font-size:8.4pt;color:#4A5057}
.ch h4{font-size:9.8pt}.ch .no{margin-right:2mm}.chip{font-size:6.8pt}
.srcl{font-size:7pt}
.img img{width:90%}
.card.sm .img img{width:82%}
.sum{font-size:9.6pt;line-height:1.7}.sum b{font-size:10.2pt}
.an .anh{font-size:10pt}.an th{font-size:8.4pt;width:24mm}.an td{font-size:9pt;line-height:1.7}
.why{margin:2mm 0 2.2mm;padding:2.4mm 3.5mm;border-left:3px solid #9DB9E8;background:#F6F9FE;font-size:9pt;line-height:1.7;color:#34383C}
.why .wt{font-size:9.4pt;font-weight:800;color:#1A4FA8;margin-bottom:.6mm}.why p{padding-left:3.4mm;text-indent:-3.4mm}.why .wt{padding:0;text-indent:0}
.note4{font-size:8pt}
table.dt{font-size:8.2pt}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:3mm;margin-bottom:3mm}
.g2 .card{margin:0;padding:2.4mm 3mm}.g2 .img img{width:100%}
.ch2{display:block;height:auto;margin-bottom:1.6mm}.ch2 h4{font-size:10pt;display:flex;align-items:center;gap:2mm}
.ch2 .k,.an2 .k{background:#2D6BD9;color:#fff;font-size:7pt;padding:.5mm 2.4mm;border-radius:10px;font-weight:700;white-space:nowrap}
.ch2 .cn{font-size:7.4pt;color:#6B7177;margin-top:.8mm}
.an2 td{vertical-align:top;text-align:left;font-size:8pt;line-height:1.6}.an2 td.res{font-weight:700;color:#1A4FA8}.an2 td.c{text-align:center}
/* 9/30 3-1) 3D 체험 쪽: 링크는 진한 글자 + 밑줄(파랑 금지), (바로보기)는 빨강 */
.stt a.go{color:#E0443E;text-decoration:none;font-weight:800;margin-left:1.5mm}
.lnk{display:flex;align-items:center;gap:3mm;margin:3.5mm 0 4mm;font-size:14pt}
.lnk span{background:#34383C;color:#fff;font-size:11pt;font-weight:800;padding:.8mm 3.2mm;border-radius:3px}
.lnk a{color:#23272B;font-weight:800;text-decoration:underline;text-decoration-color:#E0443E;text-decoration-thickness:2px;text-underline-offset:3px}
.msg.red b{color:#E0443E}
.wg{grid-template-columns:1fr 1fr}.wc .img img{width:92%}
.webp{font-size:10pt;line-height:1.8;color:#34383C;background:#F6F8FB;border-radius:6px;padding:3.5mm 4.5mm;margin-bottom:5mm}
.wg{gap:5mm 4mm}.wc{padding:2.4mm}.wc .img img{width:100%;border-radius:3px}
.wcap{text-align:center;font-size:9pt;font-weight:700;color:#34383C;margin-top:2mm}.wcap b{color:#2D6BD9;margin-right:2mm}
/* 9/29 3차: 흐름 장치(진행 띠 · 한 줄 메시지 · 결론 상자 · 다음 문장) */
.prog{display:flex;gap:1.2mm;margin:-2mm 0 3.5mm}
.prog span{flex:1;border-top:2.4px solid #DCE2EA;padding-top:1mm;font-size:6.8pt;color:#9AA2AA;font-weight:600}
.prog span.done{border-color:#A9C2EE;color:#6F8DC4}.prog span.on{border-color:#2D6BD9;color:#1A4FA8;font-weight:800}
.msg{font-size:13pt;font-weight:800;letter-spacing:-.4px;line-height:1.35;margin:3.2mm 0 1.2mm;color:#23272B}.msg b{color:#2D6BD9;font-weight:800}
.concl{background:#F3F8FD;border:1px solid #D6E6F6;border-radius:6px;padding:2.4mm 3.5mm;margin-top:1mm}
.concl .o{font-size:9.6pt;font-weight:800;padding-left:3.6mm;text-indent:-3.6mm}.concl .o i{font-style:normal;color:#2D6BD9}
.concl .d{font-size:8.7pt;line-height:1.6;color:#34383C;padding-left:6.6mm;text-indent:-2.6mm}
.bridge{display:flex;align-items:center;gap:2mm;margin-top:2.6mm;font-size:9pt;font-weight:700;color:#1A4FA8}
.bridge span{background:#2D6BD9;color:#fff;font-size:7pt;padding:.4mm 2.2mm;border-radius:8px}
.bridge::before{content:'';flex:none}
'''
FIT_JS = '''<script>
// 쪽마다 내용이 넘치면 그 쪽 그림 폭을 같은 비율로 줄인다(최소 0.55배). 결과는 data-fit에 남긴다.
function fit(){document.querySelectorAll('.inner').forEach((box,i)=>{let s=1;
 for(let k=0;k<6;k++){const over=box.scrollHeight-box.clientHeight;if(over<=1)break;
  const imgs=[...box.querySelectorAll('img.fit')];const ih=imgs.reduce((a,im)=>a+im.getBoundingClientRect().height,0);if(!ih)break;
  const r=Math.max(0.55,(ih-over-3)/ih);s*=r;imgs.forEach(im=>{im.style.width=(im.getBoundingClientRect().width*r)+'px'})}
 box.dataset.fit=s.toFixed(2);box.dataset.over=Math.max(0,box.scrollHeight-box.clientHeight)})}
window.addEventListener('load',fit);
</script>'''

html, total = build()
h = OUT / '_서식4흐름.html'
h.write_text(f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{TITLE}</title><style>{CSS}</style></head><body>{html}{FIT_JS}</body></html>', encoding='utf-8')
pdf = OUT / '안동이어드림_서식4흐름_참고자료_20260929.pdf'
CH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
subprocess.run([CH, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', '--allow-file-access-from-files', '--virtual-time-budget=20000',
                '--run-all-compositor-stages-before-draw', f'--print-to-pdf={pdf}', h.as_uri()], check=True, capture_output=True)
dom = subprocess.run([CH, '--headless=new', '--disable-gpu', '--allow-file-access-from-files', '--virtual-time-budget=20000', '--dump-dom', h.as_uri()],
                     capture_output=True, text=True).stdout
import re
fits = re.findall(r'class="inner" data-fit="([\d.]+)" data-over="(\d+)"', dom)
n = subprocess.run(['/opt/homebrew/bin/pdfinfo', str(pdf)], capture_output=True, text=True).stdout.split('Pages:')[1].split()[0]
print(pdf.relative_to(ROOT), n, '쪽 (예상', total, '쪽)')
print('쪽별 그림 배율·넘침(px):', fits)
