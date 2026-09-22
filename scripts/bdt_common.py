"""한국관광데이터랩 빅데이터>이동통신 공통 HTTP 유틸 (stdlib only)."""
import json, urllib.parse, urllib.request, time

API = "https://datalab.visitkorea.or.kr/visualize/getTempleteData.do"

def headers(page="getMetcoAna"):
    return {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0",
            "Referer": f"https://datalab.visitkorea.or.kr/datalab/portal/bda/{page}.do"}

def fetch(qid, page="getMetcoAna", timeout=120, retries=2, **params):
    """returns (status, rows) ; status in ok/empty/nonjson/err"""
    body = {"qid": qid, "SGG_CD": "", "BASE_YM1": "202508", "BASE_YM2": "202607",
            "srchAreaDate": "1", "tabDiv": "1", "touDivCd": "2", "sggIntgYnFlag": "N"}
    body.update({k: str(v) for k, v in params.items()})
    data = urllib.parse.urlencode(body).encode()
    last = None
    for a in range(retries + 1):
        try:
            raw = urllib.request.urlopen(
                urllib.request.Request(API, data=data, headers=headers(page)),
                timeout=timeout).read().decode("utf-8", "replace")
            break
        except Exception as e:
            last = e
            if a == retries:
                return ("err:" + str(last)[:60], [])
            time.sleep(1.5 * (a + 1))
    if not raw.strip():
        return ("empty", [])
    try:
        obj = json.loads(raw)
    except Exception:
        return ("nonjson", [])
    rows = obj.get("list")
    if rows is None:
        return ("nolist:" + ",".join(list(obj.keys())[:5]), [])
    return ("ok", rows)
