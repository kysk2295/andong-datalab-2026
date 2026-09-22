// 교수님 브리핑 워드판 (2026-09-22). 입력: 보고서/교수브리핑_20260922/docx_blocks.json (scripts/교수브리핑_docx블록.py)
// 실행: NODE_PATH=<docx 설치 폴더>/node_modules node scripts/교수브리핑_docx.js
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType,
  AlignmentType, BorderStyle, ShadingType, LevelFormat, VerticalAlign,
} = require('docx');

const D = path.join(__dirname, '..', '보고서', '교수브리핑_20260922');
const B = JSON.parse(fs.readFileSync(path.join(D, 'docx_blocks.json'), 'utf8'));
const OUT = path.join(D, '안동이어드림_교수브리핑_20260922.docx');

const MM = 56.7;
const MARGIN_LR = Math.round(22 * MM);
const CONTENT_W = 11906 - 2 * MARGIN_LR;
const FONT = { ascii: 'Arial', hAnsi: 'Arial', eastAsia: '맑은 고딕', cs: 'Arial' };
const BASE = 21;   // 10.5pt
const SMALL = 19;  // 9.5pt

function runs(rs, extra = {}) {
  const out = [];
  for (const r of rs) {
    if (r.br) { out.push(new TextRun({ break: 1 })); continue; }
    const text = r.text.replace(/\s+/g, ' ');
    const o = { text, font: FONT, size: extra.size || (r.small ? SMALL : BASE) };
    if (r.bold || extra.bold) o.bold = true;
    if (r.color || extra.color) o.color = r.color || extra.color;
    if (r.shade) o.shading = { type: ShadingType.CLEAR, color: 'auto', fill: r.shade };
    out.push(new TextRun(o));
  }
  // 문단 끝 공백 정리
  return out;
}

const SP = { line: 372 };  // 줄간격 약 1.55
function para(b) {
  switch (b.kind) {
    case 'h1': return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80 }, children: runs(b.runs, { bold: true, size: 34 }) });
    case 'byline': return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 }, children: runs(b.runs, { size: SMALL, color: '555555' }) });
    case 'h2': return new Paragraph({ keepNext: true, outlineLevel: 0, spacing: { before: 480, after: 160 }, children: runs(b.runs, { bold: true, size: 26 }) });
    case 'h3': return new Paragraph({ keepNext: true, outlineLevel: 1, spacing: { before: 240, after: 100 }, children: runs(b.runs, { bold: true, size: 22 }) });
    case 'cap': return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 280 }, children: runs(b.runs, { size: SMALL }) });
    case 'note': return new Paragraph({ spacing: { ...SP, after: 140 }, children: runs(b.runs, { size: SMALL, color: '444444' }) });
    case 'ins': return new Paragraph({ spacing: { ...SP, before: 120, after: 160 }, children: runs(b.runs, { bold: true }) });
    case 'stage': return new Paragraph({ keepNext: true, spacing: { before: 160, after: 80 }, children: runs(b.runs, { bold: true }) });
    case 'flow': return new Paragraph({ indent: { left: 280 }, spacing: { ...SP, after: 60 }, children: runs(b.runs) });
    case 'li': return new Paragraph({
      numbering: { reference: b.list === 'ol' ? 'ol' : 'ul', level: Math.min(b.level, 1), instance: b.list_id },
      spacing: { ...SP, after: 60 },
      children: runs(b.runs, b.note ? { size: SMALL, color: '444444' } : {}),
    });
    default: return new Paragraph({ spacing: { ...SP, after: 140 }, children: runs(b.runs) });
  }
}

function textLen(cell) {
  return cell.paras.map(p => p.runs.map(r => r.text || '').join('')).join(' ').length;
}

const border = { style: BorderStyle.SINGLE, size: 6, color: '000000' };
const borders = { top: border, bottom: border, left: border, right: border };
function table(t) {
  const ncol = Math.max(...t.rows.map(r => r.cells.length));
  const weights = Array.from({ length: ncol }, (_, i) => {
    const m = Math.max(...t.rows.map(r => (r.cells[i] ? textLen(r.cells[i]) : 0)));
    return Math.min(m, 46) + 6;
  });
  const sum = weights.reduce((a, b) => a + b, 0);
  const widths = weights.map(w => Math.round(CONTENT_W * w / sum));
  widths[widths.length - 1] += CONTENT_W - widths.reduce((a, b) => a + b, 0);
  const rows = t.rows.map((r, ri) => new TableRow({
    tableHeader: r.head,
    cantSplit: true,
    children: r.cells.map((c, ci) => new TableCell({
      width: { size: widths[ci], type: WidthType.DXA },
      borders,
      verticalAlign: VerticalAlign.CENTER,
      margins: { top: 50, bottom: 50, left: 100, right: 100 },
      shading: r.hl ? { type: ShadingType.CLEAR, color: 'auto', fill: 'FFF2CC' } : undefined,
      children: (c.paras.length ? c.paras : [{ runs: [{ text: '' }] }]).map(p => new Paragraph({
        alignment: (t.left && !c.th) ? AlignmentType.LEFT : AlignmentType.CENTER,
        spacing: { line: 300 },
        children: runs(p.runs, { size: SMALL, bold: c.th || undefined }),
      })),
    })),
  }));
  return new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: widths, rows });
}

function pngSize(buf) { return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) }; }
function image(b) {
  const buf = fs.readFileSync(path.join(D, b.src));
  const { w, h } = pngSize(buf);
  const W = 600;
  return new Paragraph({
    alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120 },
    children: [new ImageRun({ type: 'png', data: buf, transformation: { width: W, height: Math.round(W * h / w) } })],
  });
}

const children = [];
for (const b of B) {
  if (b.kind === 'table') children.push(table(b));
  else if (b.kind === 'img') children.push(image(b));
  else children.push(para(b));
}

const lv = (level, fmt, text, left) => ({
  level, format: fmt, text, alignment: AlignmentType.LEFT,
  style: { paragraph: { indent: { left, hanging: 280 } } },
});
const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: BASE } } } },
  numbering: {
    config: [
      { reference: 'ul', levels: [lv(0, LevelFormat.BULLET, '•', 560), lv(1, LevelFormat.BULLET, '◦', 1000)] },
      { reference: 'ol', levels: [lv(0, LevelFormat.DECIMAL, '%1.', 560), lv(1, LevelFormat.BULLET, '◦', 1000)] },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: Math.round(22 * MM), bottom: Math.round(20 * MM), left: MARGIN_LR, right: MARGIN_LR } } },
    children,
  }],
});
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(OUT, buf); console.log('DOCX →', OUT, Math.round(buf.length / 1024), 'KB'); });
