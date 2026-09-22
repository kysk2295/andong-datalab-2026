import requests, re, json
S = requests.Session()
S.headers.update({'User-Agent':'Mozilla/5.0','X-Requested-With':'XMLHttpRequest',
 'Referer':'https://datalab.visitkorea.or.kr/datalab/portal/loc/getAreaDataForm.do'})
h = S.get('https://datalab.visitkorea.or.kr/datalab/portal/loc/getAreaDataForm.do', timeout=30).text
print('page len', len(h))
# look for js files and inline area code hints
for pat in ['sggList','areaList','SGG_CD','sidoList','getSggList','areaCd']:
    idx=[m.start() for m in re.finditer(pat,h)][:3]
    print(pat, idx)
for m in re.finditer(r'src="([^"]+\.js[^"]*)"', h):
    print('JS:', m.group(1))
