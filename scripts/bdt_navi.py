"""한국관광 데이터랩 빅데이터>내비게이션 계열 수집기 (stdlib only)."""
import json, urllib.parse, urllib.request, urllib.error, http.cookiejar, time, csv, os, sys, threading
from concurrent.futures import ThreadPoolExecutor

_CJ = http.cookiejar.CookieJar()
_OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_CJ))
_LOCK = threading.Lock()
_LAST = [0.0]
MIN_GAP = 2.0   # 요청 간 최소 간격(초) - 공공서버 배려

def warm():
    """세션 쿠키 확보"""
    try:
        _OPENER.open(urllib.request.Request(
            "https://datalab.visitkorea.or.kr/datalab/portal/main/getMainForm.do",
            headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
    except Exception as e:
        print("warm fail", e)

def _throttle():
    with _LOCK:
        d = MIN_GAP - (time.time() - _LAST[0])
        if d > 0:
            time.sleep(d)
        _LAST[0] = time.time()

API = "https://datalab.visitkorea.or.kr/visualize/getTempleteData.do"
OUT = "/Users/koyunseo/한국관광데이터분석/data/bdt/내비게이션"

DEFAULTS = {"SGG_CD": "", "BASE_YM1": "202508", "BASE_YM2": "202607",
            "srchAreaDate": "1", "tabDiv": "1", "touDivCd": "2", "sggIntgYnFlag": "N"}

def headers(page):
    return {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0",
            "Referer": f"https://datalab.visitkorea.or.kr/datalab/portal/bda/{page}.do"}

def fetch(qid, page="getDomInqCnt", timeout=120, retries=2, base=None, **params):
    body = dict(DEFAULTS if base is None else base)
    body["qid"] = qid
    body.update({k: ("" if v is None else str(v)) for k, v in params.items()})
    data = urllib.parse.urlencode(body).encode()
    for a in range(retries + 1):
        try:
            _throttle()
            raw = _OPENER.open(
                urllib.request.Request(API, data=data, headers=headers(page)),
                timeout=timeout).read().decode("utf-8", "replace")
            break
        except Exception as e:
            if a == retries:
                return ("err:" + str(e)[:70], [], body)
            time.sleep(1.5 * (a + 1))
    if not raw.strip():
        return ("empty", [], body)
    try:
        obj = json.loads(raw)
    except Exception:
        return ("nonjson", [], body)
    rows = obj.get("list")
    if rows is None:
        return ("nolist:" + ",".join(list(obj.keys())[:6]), [], body)
    return ("ok", rows, body)

def save_csv(rows, path):
    if not rows:
        return 0
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return len(rows)

def pmap(fn, items, workers=3):
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, items))
