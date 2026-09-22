"""안동 야간관광 문제 수치화 (2026-09-18)

출력: 보고서/야간문제_수치_20260918.csv 계열
데이터:
  - data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_{연도}.csv  (D1 정본, 외지인, 시간대 6구간)
  - data/datalab_추가/야간관광_BY_TH_NIGHT_TOUR_003_005.csv  (광역 야간검색 상위 관광지)
  - data/datalab_추가/야간관광_BY_TH_NIGHT_TOUR_003_006.csv  (카테고리별 야간검색 상위)
  - data/datalab_추가/야간관광_BY_TH_NIGHT_TOUR_001_009.csv  (동 단위 야간 방문 상위)
  - data/datalab_추가/야간관광_BY_TH_NIGHT_TOUR_002_009.csv  (동 단위 야간 소비 상위)
주의: 야간관광 지표는 시도(경북) 단위 + 상위 목록만 공개. 안동 시군 단위 야간 방문/소비 값은 없다.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / '보고서'
MIN_VISIT = 1_000_000          # 방문 연인원 100만 미만 시군구 제외
HOURS = ['00~06시', '06~11시', '11~14시', '14~18시', '18~21시', '21~24시']


def 시간대_점유(연도: int) -> pd.DataFrame:
    """외지인 1~8월 시간대별 방문 비중 + 방문계."""
    d = pd.read_csv(ROOT / f'data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_{연도}.csv')
    d.columns = [c.split(':')[-1] for c in d.columns]
    d = d[d['시간대'].notna() & (d['방문자유형별'] == '외지인(b)')]
    d = d[d['기준연월'].astype(str).str[4:6].astype(int) <= 8]     # 연도 간 비교를 위해 1~8월 고정
    g = d.groupby(['기초단체', '시간대'])['방문자 수'].sum().unstack()[HOURS]
    tot = g.sum(axis=1)
    sh = g.div(tot, axis=0) * 100
    sh['방문계'] = tot
    return sh[sh['방문계'] >= MIN_VISIT]


def 시간대_진단() -> pd.DataFrame:
    s26, s24 = 시간대_점유(2026), 시간대_점유(2024)
    s26 = s26.copy()
    s26['저녁전환율'] = s26['18~21시'] / s26['14~18시']          # 낮 방문객이 저녁까지 남는 정도
    s26['r_숙박'] = s26['00~06시'].rank(ascending=False)
    s26['r_저녁'] = s26['18~21시'].rank(ascending=False)
    s26['괴리'] = s26['r_저녁'] - s26['r_숙박']                   # 클수록 '자러는 오는데 저녁엔 안 나온다'
    n = len(s26)
    rows = []
    for col in ['00~06시', '18~21시', '21~24시', '저녁전환율', '괴리']:
        asc = False
        r = s26[col].rank(ascending=asc)
        rows.append({
            '지표': col, '안동': round(s26.loc['안동시', col], 3),
            '전국중앙': round(s26[col].median(), 3),
            '순위': int(r['안동시']), '대상수': n,
            '상위%': round(r['안동시'] / n * 100, 1),
            '2024_1-8': round(s24.loc['안동시', col], 3) if col in s24.columns else None,
        })
    return pd.DataFrame(rows), s26


def 야간검색_칸점유() -> pd.DataFrame:
    b = pd.read_csv(ROOT / 'data/datalab_추가/야간관광_BY_TH_NIGHT_TOUR_003_006.csv')
    g = b[b['조회_시도'] == 47]                                   # 경북
    t = g.pivot_table(index='SGG_NM', columns='조회기간', values='RNK', aggfunc='count').fillna(0).astype(int)
    t['합계'] = t.sum(axis=1)
    return t.sort_values('합계', ascending=False)


def 안동_야간검색() -> pd.DataFrame:
    b = pd.read_csv(ROOT / 'data/datalab_추가/야간관광_BY_TH_NIGHT_TOUR_003_006.csv')
    an = b[(b['조회_시도'] == 47) & (b['SGG_NM'] == '안동시')].copy()
    an['야간비율'] = (an['NIGHT_SRCH_CNT'] / an['SRCH_CNT'] * 100).round(1)
    return an[['조회기간', 'ITS_BRO_NM', 'KTO_CATE_MCLS_NM', 'RNK',
               'NIGHT_SRCH_CNT', 'SRCH_CNT', '야간비율']].sort_values(['ITS_BRO_NM', '조회기간'])


def 동단위_안동() -> tuple:
    v = pd.read_csv(ROOT / 'data/datalab_추가/야간관광_BY_TH_NIGHT_TOUR_001_009.csv')
    c = pd.read_csv(ROOT / 'data/datalab_추가/야간관광_BY_TH_NIGHT_TOUR_002_009.csv')
    return (v[v['SGG_NM'] == '안동시'][['조회기간', 'RNK', 'ADONG_NM', 'LRFRN_DIV_NM', 'NIGHT_TOU_NUM', 'TOU_NUM', 'RATE_NUM']],
            c[c['SGG_NM'] == '안동시'][['조회기간', 'RNK', 'ADONG_NM', 'LRFRN_DIV_NM', 'NIGHT_CNSM_AMT', 'CNSM_AMT', 'RATE_NUM']])


if __name__ == '__main__':
    진단, 전체 = 시간대_진단()
    print('■ 시간대 진단 (외지인, 1~8월)');  print(진단.to_string(index=False))
    진단.to_csv(OUT / '야간문제_시간대진단_20260918.csv', index=False, encoding='utf-8-sig')

    칸 = 야간검색_칸점유()
    print('\n■ 경북 야간검색 상위5 칸 점유 (9카테고리×5×3기간=135칸)');  print(칸.to_string())
    칸.to_csv(OUT / '야간문제_경북검색칸점유_20260918.csv', encoding='utf-8-sig')

    print('\n■ 안동 야간검색 POI');  print(안동_야간검색().to_string(index=False))
    방문, 소비 = 동단위_안동()
    print('\n■ 동 단위 야간 방문(안동)');  print(방문.to_string(index=False))
    print('\n■ 동 단위 야간 소비(안동)');  print(소비.to_string(index=False))
