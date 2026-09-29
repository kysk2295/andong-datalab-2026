"""Export the submitted report's values; never recalculate or modify the analysis."""
import hashlib
import json
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
sources = [ROOT/'보고서/성과도출_20260922/시뮬레이션결과.json', ROOT/'보고서/교수브리핑_20260922/수치.json']
s, q = [json.loads(p.read_text()) for p in sources]
c = q['체험문화']
resident = q['주민증']['월평균'][-1]['월평균']
added = s['p근거']['하한_주민증GLM'] * s['고정값']['중구동_월방문']
result = {
    'version': 1, 'exportedAt': '2026-09-29', 'restaurants': 83,
    'period': '2026년 1~8월 월평균의 연간 환산',
    'method': '시행 전 조건부 예측 · 1만 회 모의실험 · 체험 10% 할인과 기존 소비 차감 반영',
    'sources': [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources],
    'baseline': {'consumption2024': c['안동_2024'], 'consumption2026': c['안동_2026']},
    'resident': {'currentMonthly': resident, 'addedMonthly': added, 'afterMonthly': resident+added},
    'scenarios': s['시나리오'],
}
(APP/'public/data/report-effects.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print('Exported 3 report scenarios; 83 restaurants; source hashes recorded')
