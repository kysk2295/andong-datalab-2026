# -*- coding: utf-8 -*-
"""교수님 브리핑 HTML(교수브리핑_PDF생성.py 산출물)을 워드 변환용 블록 JSON으로 바꾼다.

HTML이 정본이다. 이 스크립트는 구조(제목·문단·목록·표·그림·캡션)와 글자 꾸밈(굵게·형광펜·초록 출처·작은 주석)만 옮긴다.
출력: 보고서/교수브리핑_20260922/docx_blocks.json → scripts/교수브리핑_docx.js
"""
import json
from html.parser import HTMLParser
from pathlib import Path

D = Path(__file__).resolve().parent.parent / '보고서/교수브리핑_20260922'


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.cur = None           # 현재 모으는 문단(runs 리스트를 가진 dict)
        self.fmt = []             # 열린 인라인 꾸밈 스택
        self.lists = []           # [{'type':'ul'|'ol','id':n}]
        self.list_id = 0
        self.table = None
        self.row = None
        self.cell = None
        self.cls_stack = []

    # ── 도우미 ──
    def start_para(self, kind, **kw):
        self.cur = {'kind': kind, 'runs': [], **kw}

    def end_para(self):
        if self.cur is None:
            return
        runs = self.cur['runs']
        while runs and runs[0].get('text', '').strip() == '' and not runs[0].get('br'):
            runs.pop(0)
        if runs:
            if self.cell is not None:
                self.cell['paras'].append(self.cur)
            else:
                self.blocks.append(self.cur)
        self.cur = None

    def styles(self):
        st = {}
        for f in self.fmt:
            st.update(f)
        return st

    # ── 태그 ──
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get('class', '') or ''
        self.cls_stack.append((tag, cls))
        if tag == 'h1':
            self.start_para('h1')
        elif tag == 'h2':
            self.start_para('h2')
        elif tag == 'h3':
            self.end_para()
            self.start_para('h3')
        elif tag == 'p':
            self.end_para()
            if self.cell is not None:
                self.start_para('cellp')
            elif 'cap' in cls:
                self.start_para('cap')
            elif 'byline' in cls:
                self.start_para('byline')
            elif 'ins' in cls:
                self.start_para('ins')
            elif 'note' in cls:
                self.start_para('note')
            elif 'stage-t' in cls:
                self.start_para('stage')
            elif self.in_cls('flow'):
                self.start_para('flow')
            else:
                self.start_para('p')
        elif tag in ('ul', 'ol'):
            self.end_para()
            self.list_id += 1
            self.lists.append({'type': tag, 'id': self.list_id})
        elif tag == 'li':
            self.end_para()
            L = self.lists[-1]
            self.start_para('li', list=L['type'], level=len(self.lists) - 1, list_id=L['id'],
                            note='note' in cls)
        elif tag == 'table':
            self.end_para()
            self.table = {'kind': 'table', 'left': 'left' in cls, 'rows': []}
        elif tag == 'tr':
            self.row = {'hl': 'hl' in cls, 'cells': [], 'head': False}
        elif tag in ('td', 'th'):
            self.cell = {'paras': [], 'th': tag == 'th'}
            if tag == 'th':
                self.row['head'] = True
            self.start_para('cellp')
        elif tag == 'img':
            self.end_para()
            self.blocks.append({'kind': 'img', 'src': a['src'].replace('.svg', '.png')})
        elif tag == 'br':
            if self.cur is not None:
                self.cur['runs'].append({'br': True})
        elif tag == 'b':
            self.fmt.append({'bold': True})
        elif tag == 'span':
            f = {}
            if 'hd' in cls:
                f = {'bold': True, 'shade': 'FFE599'}
            elif 'mark' in cls:
                f = {'shade': 'FFF2CC'}
            elif 'src' in cls:
                f = {'bold': True, 'color': '38761D'}
            elif 'note' in cls:
                f = {'small': True, 'color': '444444'}
            elif self.cur is not None and self.cur['kind'] == 'ins':
                f = {'shade': 'FFF2CC'}
            self.fmt.append(f)
        elif tag == 'div' and self.cur is not None:
            self.end_para()

    def in_cls(self, name):
        return any(name in c.split() for _, c in self.cls_stack)

    def handle_endtag(self, tag):
        while self.cls_stack:
            t, _ = self.cls_stack.pop()
            if t == tag:
                break
        if tag in ('h1', 'h2', 'h3', 'p', 'li'):
            self.end_para()
        elif tag in ('ul', 'ol'):
            self.end_para()
            self.lists.pop()
        elif tag in ('td', 'th'):
            self.end_para()
            self.row['cells'].append(self.cell)
            self.cell = None
        elif tag == 'tr':
            self.table['rows'].append(self.row)
            self.row = None
        elif tag == 'table':
            self.blocks.append(self.table)
            self.table = None
        elif tag in ('b', 'span'):
            if self.fmt:
                self.fmt.pop()

    def handle_data(self, data):
        if self.cur is None:
            if not data.strip():
                return
            self.start_para('p')
        text = ' '.join(data.split('\n'))
        if not text:
            return
        self.cur['runs'].append({'text': text, **self.styles()})


html = (D / '교수브리핑.html').read_text(encoding='utf-8')
body = html[html.index('<body>') + 6: html.index('</body>')]
p = P()
p.feed(body)
p.end_para()
(D / 'docx_blocks.json').write_text(json.dumps(p.blocks, ensure_ascii=False, indent=0), encoding='utf-8')
print(len(p.blocks), 'blocks', {k: sum(1 for b in p.blocks if b['kind'] == k) for k in {b['kind'] for b in p.blocks}})
