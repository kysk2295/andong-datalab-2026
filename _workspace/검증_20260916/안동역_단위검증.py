import pandas as pd, calendar
d = pd.read_csv('data/external/팀원취합_정제/안동역_승하차_월별_열차종류별_long.csv')
d['연'] = d['연월'].str[:4].astype(int)
d['월'] = d['연월'].str[5:7].astype(int)
wmap = {'월':0,'화':1,'수':2,'목':3,'금':4,'토':5,'일':6}
s = d[d['승하차'] == '승차'].copy()
print('전체 승차 합계', int(s['인원'].sum()))
s = s[s['구분'].isin(['평일','주말'])]

def nd(r):
    last = calendar.monthrange(r['연'], r['월'])[1]
    return sum(1 for day in range(1, last+1) if calendar.weekday(r['연'], r['월'], day) == wmap[r['요일']])

s['일수'] = s.apply(nd, axis=1)
agg = s.groupby(['연월','구분','요일','시간대','일수'], as_index=False)['인원'].sum()
agg['일평균'] = agg['인원'] / agg['일수']
n19 = s[s['시간대'] == '19-20']
for lbl in ['평일','주말']:
    cells = n19[n19['구분'] == lbl]
    nz = cells[cells['인원'] > 0]
    print(lbl, '열차종류별 셀', len(cells), '양수', len(nz), '양수셀 평균(브리프 방식)', round(nz['인원'].mean(), 1))

a19 = agg[agg['시간대'] == '19-20']
for lbl in ['평일','주말']:
    cells = a19[a19['구분'] == lbl]
    nz = cells[cells['인원'] > 0]
    print(lbl, '전열차합산 월x요일 셀', len(cells), '양수', len(nz),
          '| 월합 평균', round(cells['인원'].mean(), 1),
          '| 1일평균(전체)', round(cells['일평균'].mean(), 2),
          '| 1일평균(양수월만)', round(nz['일평균'].mean(), 2))

print('전체기간 19-20시 총 승차', {lbl: int(a19[a19['구분'] == lbl]['인원'].sum()) for lbl in ['평일','주말']})
print('전체기간 해당 일수', {lbl: int(a19[a19['구분'] == lbl]['일수'].sum()) for lbl in ['평일','주말']})
for lbl in ['평일','주말']:
    c = a19[a19['구분'] == lbl]
    print(lbl, '총승차/총일수 =', round(c['인원'].sum() / c['일수'].sum(), 1), '명/일')
