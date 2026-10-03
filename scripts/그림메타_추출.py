# -*- coding: utf-8 -*-
"""보고서그림.py의 그림 제목·부제·출처를 JSON으로 뽑는다 (PNG는 저장하지 않음, savefig를 가로챔)
출력: 보고서/그림보고서_20260929/그림메타.json → scripts/그림보고서_PDF.py가 읽음
실행: .venv_pdf/bin/python scripts/그림메타_추출.py
"""
import json, runpy, sys
from pathlib import Path
import matplotlib; matplotlib.use('Agg')
from matplotlib.figure import Figure
ROOT = Path(__file__).resolve().parent.parent
META = []
def fake(self, *a, **k):
    t = [x.get_text() for x in self.texts]
    META.append({'no': int(self._nm[:2]), 'file': self._nm + '.png', 'sec': self._nm.split('_')[1],
                 'title': (t[1] + t[2]).replace('  ', ' ').strip(), 'dark': t[1].strip(), 'accent': t[2].strip(), 'sub': t[3], 'src': t[4].removeprefix('출처: ').removeprefix('근거: ')})
Figure.savefig = fake
sys.argv = ['x']
runpy.run_path(str(ROOT / 'scripts/보고서그림.py'), run_name='__main__')
(ROOT / '보고서/그림보고서_20260929').mkdir(exist_ok=True)
(ROOT / '보고서/그림보고서_20260929/그림메타.json').write_text(json.dumps(META, ensure_ascii=False, indent=1), encoding='utf-8')
print(len(META))
