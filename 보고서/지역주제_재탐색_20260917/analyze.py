from pathlib import Path
import time
import duckdb
import numpy as np
import polars as pl

start = time.monotonic()
root = Path(__file__).resolve().parents[2]
out = Path(__file__).resolve().parent
con = duckdb.connect()
con.execute('SET threads=4')
frames = []
for year in [2024, 2025, 2026]:
    file = root / f'data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_{year}.csv'
    frame = con.execute('''SELECT "R:기초단체" region, "R:기준연월" ym,
        SUM("V:방문자 수") visits FROM read_csv_auto(?)
        WHERE "C:방문자유형별"='외지인(b)' AND "C:시간대" IS NOT NULL
        GROUP BY 1,2''', [str(file)]).pl()
    frames.append(frame)
visits = pl.concat(frames)
cardfile = root / 'data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv'
card_recent = pl.read_csv(cardfile).unique()
card_history = pl.read_csv(root / 'data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2019·2020·2025_BDT_02_01_003_35.csv').unique()
card = pl.concat([card_recent.filter(pl.col('BASE_DATE')//100 != 2025), card_history.filter(pl.col('BASE_DATE')//100 == 2025)], how='diagonal_relaxed').unique()
# A municipality name without province is insufficient for duplicate district names.
ambiguous = card.filter(pl.col('KTO_TOB_MCLS_NM')=='관광총소비').group_by(['SGG_NM','BASE_DATE']).len().filter(pl.col('len')>1)['SGG_NM'].unique().to_list()
card = card.filter(~pl.col('SGG_NM').is_in(ambiguous))
spend = card.filter(pl.col('KTO_TOB_MCLS_NM')=='관광총소비').select(pl.col('SGG_NM').alias('region'),pl.col('BASE_DATE').alias('ym'),(pl.col('CNSM_AMT')*1000).alias('spend'))
monthly = visits.join(spend,on=['region','ym']).with_columns((pl.col('ym')//100).alias('year'),(pl.col('ym')%100).alias('month')).filter(pl.col('region').str.contains('(시|군)$'))
monthly.write_csv(out/'월별_방문소비.csv')
ytd = monthly.filter(pl.col('month')<=8).group_by(['region','year']).agg(pl.col('visits').sum(),pl.col('spend').sum(),pl.len().alias('months')).with_columns((pl.col('spend')/pl.col('visits')).alias('spend_per_visit'))
a = ytd.filter((pl.col('year')==2024)&(pl.col('months')==8)).drop('year')
b = ytd.filter((pl.col('year')==2026)&(pl.col('months')==8)).drop('year')
compare = a.join(b,on='region',suffix='_26').with_columns(((pl.col('visits_26')/pl.col('visits')-1)*100).alias('visit_change'),((pl.col('spend_26')/pl.col('spend')-1)*100).alias('spend_change'),((pl.col('spend_per_visit_26')/pl.col('spend_per_visit')-1)*100).alias('per_visit_change'))
compare.sort('per_visit_change').write_csv(out/'전국_시군_방문소비_재계산.csv')
# Industry changes locate the measured deficit; they do not establish its cause.
industries = card.filter((pl.col('BASE_DATE')%100<=8)&(pl.col('KTO_TOB_MCLS_NM')!='관광총소비')).with_columns((pl.col('BASE_DATE')//100).alias('year')).group_by(['SGG_NM','KTO_TOB_MCLS_NM','year']).agg(pl.col('CNSM_AMT').sum())
ia=industries.filter(pl.col('year')==2024).drop('year')
ib=industries.filter(pl.col('year')==2026).drop('year')
ic=ia.join(ib,on=['SGG_NM','KTO_TOB_MCLS_NM'],suffix='_26').with_columns(((pl.col('CNSM_AMT_26')-pl.col('CNSM_AMT'))/1e5).alias('change_억원'),((pl.col('CNSM_AMT_26')/pl.col('CNSM_AMT')-1)*100).alias('change_pct'))
ic.write_csv(out/'업종별_증감.csv')
# 2024 and 2025 complete-year seasonality, with monthly rates adjusted for month length.
season = monthly.filter(pl.col('year').is_in([2024,2025])).with_columns(pl.col('ym').cast(pl.String).str.to_date('%Y%m').dt.month_end().dt.day().alias('days'))
season=season.group_by(['region','year']).agg(pl.len().alias('months'),pl.col('visits').sum().alias('annual_visits'),(pl.col('visits').top_k(3).sum()/pl.col('visits').sum()*100).alias('top3_visit_share'),(pl.col('spend').top_k(3).sum()/pl.col('spend').sum()*100).alias('top3_spend_share'),((pl.col('visits')/pl.col('days')).std(ddof=0)/(pl.col('visits')/pl.col('days')).mean()).alias('daily_rate_cv')).filter(pl.col('months')==12)
season.sort(['year','top3_visit_share'],descending=[True,True]).write_csv(out/'계절집중도.csv')
f=pl.read_csv(root/'data/축제_전체/축제별_방문자_밀집_통합.csv',infer_schema_length=10000)
fa=f.filter(pl.col('BASE_YEAR')==2024).select('FSTV_ID',pl.col('TOT_OUT').alias('out24'),pl.col('외지인소비').alias('spend24'),pl.col('FSTV_PERD_CNT').alias('days24'))
fb=f.filter(pl.col('BASE_YEAR')==2025).select('FSTV_ID','FSTV_REPS_NM','SGG_NM',pl.col('TOT_OUT').alias('out25'),pl.col('외지인소비').alias('spend25'),pl.col('FSTV_PERD_CNT').alias('days25'))
fc=fa.join(fb,on='FSTV_ID').filter((pl.col('out24')>0)&(pl.col('spend24')>0)&(pl.col('out25')>0)&(pl.col('spend25')>0)).with_columns(((pl.col('out25')/pl.col('out24')-1)*100).alias('visits_change'),((pl.col('spend25')/pl.col('spend24')-1)*100).alias('spend_change'),(((pl.col('spend25')/pl.col('out25'))/(pl.col('spend24')/pl.col('out24'))-1)*100).alias('per_visit_change'),((pl.col('out25')/pl.col('days25'))/(pl.col('out24')/pl.col('days24'))*100-100).alias('daily_visits_change'))
fc.sort('per_visit_change').write_csv(out/'축제_2024_2025_비교.csv')
old=pl.read_csv(root/'보고서/M1_방문소비_매트릭스_초벌.csv').rename({'':'region'})
check=compare.join(old,on='region')
error=float((check['per_visit_change']-check['방문당소비%']).abs().max())
assert error<1e-8, error
print('Regions',compare.height,'matched previous',check.height,'max percentage-point difference',error)
print('Median changes',compare.select('visit_change','spend_change','per_visit_change').median().write_csv())
print('Consumption mismatch',compare.filter((pl.col('visit_change')>0)&(pl.col('per_visit_change')<0)).height)
print(compare.sort('per_visit_change').select('region','visit_change','spend_change','per_visit_change').head(15).write_csv())
print('SEASONALITY 2025')
print(season.filter(pl.col('year')==2025).sort('top3_visit_share',descending=True).head(15).write_csv())
print('FESTIVALS comparable',fc.height)
print(fc.filter((pl.col('visits_change')>0)&(pl.col('per_visit_change')<0)).sort('per_visit_change').write_csv())
print('Seconds',round(time.monotonic()-start,2))
(out/'검증.txt').write_text(f'Regions={compare.height}\nMonthly rows={monthly.height}\nMatched prior={check.height}\nMax discrepancy={error}\nFestival pairs={fc.height}\nSeconds={time.monotonic()-start:.2f}\n',encoding='utf-8')
# Separate recovery from persistent deterioration using all three matching Jan-Aug windows.
trends=ytd.sort('region','year').with_columns(((pl.col('spend_per_visit')/pl.col('spend_per_visit').shift(1).over('region')-1)*100).alias('per_visit_yoy'),((pl.col('visits')/pl.col('visits').shift(1).over('region')-1)*100).alias('visits_yoy'),((pl.col('spend')/pl.col('spend').shift(1).over('region')-1)*100).alias('spend_yoy'))
trends.write_csv(out/'연도별_1월8월_추세.csv')
transport=ic.filter(pl.col('KTO_TOB_MCLS_NM')=='육상운송').select(pl.col('SGG_NM').alias('region'),'CNSM_AMT','CNSM_AMT_26')
sensitivity=compare.join(transport,on='region').with_columns((pl.col('spend')-pl.col('CNSM_AMT')*1000).alias('nontransport24'),(pl.col('spend_26')-pl.col('CNSM_AMT_26')*1000).alias('nontransport26')).with_columns(((pl.col('nontransport26')/pl.col('nontransport24')-1)*100).alias('nontransport_spend_change'),(((pl.col('nontransport26')/pl.col('visits_26'))/(pl.col('nontransport24')/pl.col('visits'))-1)*100).alias('nontransport_per_visit_change'))
sensitivity.select('region','spend_change','per_visit_change','nontransport_spend_change','nontransport_per_visit_change').write_csv(out/'육상운송제외_민감도.csv')
# Source schema and coverage audit, not a claim to verify the vendor's estimation model.
coverage=monthly.group_by('year').agg(pl.col('month').unique().sort(),pl.col('region').n_unique().alias('regions'))
coverage.write_json(out/'기간범위.json')
assert not monthly.select('region','ym').is_duplicated().any()
assert not fc['FSTV_ID'].is_duplicated().any()
assert len(season.filter(pl.col('year')==2025))>100
assert np.isfinite(compare['per_visit_change'].to_numpy()).all()

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_path=Path('/System/Library/Fonts/AppleSDGothicNeo.ttc')
if font_path.exists():
    font_manager.fontManager.addfont(str(font_path))
    plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font_path)).get_name()
plt.rcParams['axes.unicode_minus']=False
fig,ax=plt.subplots(figsize=(11,7),dpi=180)
fig.set_facecolor('#faf9f5'); ax.set_facecolor('#faf9f5')
ax.scatter(compare['visit_change'],compare['spend_change'],s=24,c='#b8bfbd',alpha=.65)
ax.plot([-25,40],[-25,40],color='#b3aba2',ls='--',lw=1)
chosen=['안동시','인제군','함양군','익산시','울릉군','태안군']
shifts={'안동시':(8,-17),'인제군':(-43,12),'함양군':(8,8),'익산시':(8,-15),'울릉군':(8,8),'태안군':(8,8)}
for row in compare.filter(pl.col('region').is_in(chosen)).to_dicts():
    color='#b44933' if row['region'] in ['인제군','울릉군'] else '#25645b'
    ax.scatter(row['visit_change'],row['spend_change'],s=65,c=color,zorder=3)
    ax.annotate(row['region'],(row['visit_change'],row['spend_change']),xytext=shifts[row['region']],textcoords='offset points',fontsize=11,color=color)
ax.axhline(0,color='#777',lw=.6); ax.axvline(0,color='#777',lw=.6)
ax.margins(x=.08, y=.08)
ax.set_xlabel('외지인 방문 연인원 변화 (%)',fontsize=12);ax.set_ylabel('외지인 카드 관광소비 변화 (%)',fontsize=12)
fig.suptitle('방문 증가와 소비 증가는 같은 성과가 아니다',x=.08,y=.97,ha='left',fontsize=20)
fig.text(.08,.915,'2024년 1~8월 대비 2026년 1~8월 · 비교 가능한 145개 시·군',fontsize=11,color='#555')
fig.text(.125,.015,'점선 아래: 방문당 소비 감소. 개별 관광객 지출·정책 인과효과를 의미하지 않음. 출처: 보유 한국관광 데이터랩 원자료 재계산',fontsize=9,color='#555')
ax.spines[['top','right']].set_visible(False)
fig.tight_layout(rect=[0,.04,1,.89]);fig.savefig(out/'지역비교.png');plt.close(fig)
print('All audits passed; saved chart and sensitivity tables.')
