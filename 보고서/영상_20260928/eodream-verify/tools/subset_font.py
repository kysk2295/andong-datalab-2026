"""영상에 쓰인 글자만 남긴 Pretendard(가변) 부분 글꼴 → assets/fonts/Pretendard-sub.ttf

렌더 묶음은 2MB 넘는 글꼴을 안에 넣지 않으므로(원본 6.4MB) 쓰는 글자만 남긴다.
index.html·assets/data.js 문구를 바꾸면 다시 실행한다: .venv_pdf/bin/python tools/subset_font.py (프로젝트 폴더에서)
"""
from pathlib import Path
from fontTools import subset

P = Path(__file__).resolve().parents[1]
chars = set()
for f in ('index.html', 'assets/data.js'):
    chars |= set((P / f).read_text(encoding='utf-8'))
chars |= set('0123456789.,%+−-→←↺~·:()[]\'" 억원명곳회번개월')
opts = subset.Options(); opts.layout_features = ['*']; opts.name_IDs = ['*']; opts.notdef_outline = True
font = subset.load_font(str(P / 'assets/fonts/PretendardVariable.ttf'), opts)
sub = subset.Subsetter(opts); sub.populate(text=''.join(sorted(chars))); sub.subset(font)
out = P / 'assets/fonts/Pretendard-sub.ttf'
subset.save_font(font, str(out), opts)
print(out, f'{out.stat().st_size / 1024:.0f}KB', len(chars), '글자')
