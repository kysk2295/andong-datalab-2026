import requests, json
S = requests.Session()
S.headers.update({
 'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36',
 'X-Requested-With':'XMLHttpRequest',
 'Referer':'https://datalab.visitkorea.or.kr/datalab/portal/loc/getAreaDataForm.do',
 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
})
S.get('https://datalab.visitkorea.or.kr/datalab/portal/loc/getAreaDataForm.do', timeout=30)
body = dict(SGG_CD='51150', SGG_NM='강원특별자치도 강릉시',
  BASE_YM1='202506', BASE_YM2='202608', tabDiv='2', srchAreaDate='1',
  dispYn='Y', touDivCd='1', srchTypeText='', sggIntgYnFlag='N',
  sggIntgYnFlag2='N', yearOverGlobal='N', qid='LN_03_01_002', BASE_YR='2018')
r = S.post('https://datalab.visitkorea.or.kr/visualize/getTempleteData.do', data=body, timeout=30)
print('status', r.status_code, 'len', len(r.text))
print(r.text[:600])
