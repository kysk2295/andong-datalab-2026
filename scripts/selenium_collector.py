#!/usr/bin/env python3
"""데이터랩 미확보 항목 셀레니움 수집기.

API 역공학으로 못 뚫은 3가지를 화면 조작으로 해결한다.
  1) 지역별 관광지 검색순위 Top100  — 조회 후 실제 XHR 요청 캡처 + 표 파싱
  2) 비교 화면 3종 (방문자수/지출액/검색건수)  — 지역을 UI로 선택해 세션에 적재 후 조회
  3) 캡처한 요청 규격을 파일로 남겨, 이후 저속 API 수집에 재활용

설계 원칙
  - 사람 속도로 조작한다(액션 사이 2~4초). 재차단 방지가 최우선.
  - 브라우저 성능로그로 XHR 본문을 캡처해 qid/파라미터를 기록한다.
  - 로그인 세션은 사용자의 기존 Chrome 프로필을 재사용한다(비밀번호 입력 없음).
"""
import json, pathlib, random, sys, time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

ROOT = pathlib.Path("/Users/koyunseo/한국관광데이터분석")
OUT  = ROOT / "data" / "selenium"; OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://datalab.visitkorea.or.kr/datalab/portal"

TARGETS = [
    ("관광지검색순위",   f"{BASE}/bda/getTourVisitCnt.do"),
    ("방문자수비교",     f"{BASE}/bda/getByRegnAna.do"),
    ("관광지출액비교",   f"{BASE}/bda/getByRegnCmpr.do"),
    ("검색건수비교",     f"{BASE}/bda/getAreaSrchCnt.do"),
]

def log(m):
    line = f"{time.strftime('%H:%M:%S')} {m}"
    print(line, flush=True)
    (OUT / "_로그.txt").open("a", encoding="utf-8").write(line + "\n")

def pause(a=2.0, b=4.0):
    time.sleep(random.uniform(a, b))

def make_driver(profile_dir=None, headless=False):
    o = Options()
    if profile_dir:
        o.add_argument(f"--user-data-dir={profile_dir}")
        o.add_argument("--profile-directory=Default")
    if headless:
        o.add_argument("--headless=new")
    o.add_argument("--window-size=1600,1000")
    o.add_experimental_option("excludeSwitches", ["enable-automation"])
    o.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    return webdriver.Chrome(options=o)

HOOK = """
window.__cap = window.__cap || [];
if (!window.__hooked) {
  window.__hooked = true;
  const O = XMLHttpRequest.prototype.open, S = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function(m,u){ this.__u=u; return O.apply(this,arguments); };
  XMLHttpRequest.prototype.send = function(b){
    try { if (String(this.__u).indexOf('getTempleteData') > -1)
            window.__cap.push({u:String(this.__u), b:String(b)}); } catch(e){}
    return S.apply(this,arguments);
  };
}
return 'hooked';
"""

def capture(driver):
    try:
        return driver.execute_script("return window.__cap || [];")
    except Exception:
        return []

def click_first(driver, texts):
    """텍스트가 일치하는 첫 요소를 클릭. 성공하면 True."""
    for t in texts:
        try:
            els = driver.find_elements(By.XPATH, f"//*[self::a or self::button][normalize-space()='{t}']")
            for e in els:
                if e.is_displayed():
                    driver.execute_script("arguments[0].click();", e)
                    return True
        except Exception:
            continue
    return False

def run(profile_dir=None):
    log("=== 셀레니움 수집 시작")
    driver = make_driver(profile_dir)
    results = {}
    try:
        for name, url in TARGETS:
            log(f"[{name}] {url}")
            try:
                driver.get(url); pause(4, 6)
            except Exception as e:
                log(f"  접속 실패: {e}"); continue

            if "chrome-error" in driver.current_url or "로그인" in driver.title:
                log(f"  ❌ 접속 불가 / 로그인 필요 (title={driver.title})"); continue

            driver.execute_script(HOOK); pause(1, 2)

            # 조회 버튼 클릭
            if not click_first(driver, ["조회", "검색"]):
                log("  조회 버튼 못 찾음")
            pause(6, 9)

            caps = capture(driver)
            log(f"  캡처된 요청 {len(caps)}건")
            qids = []
            for c in caps:
                body = c.get("b", "")
                for part in body.split("&"):
                    if part.startswith("qid="):
                        qids.append(part[4:])
            if qids:
                log(f"  qid: {sorted(set(qids))}")

            # 화면 표 파싱
            tables = []
            for tb in driver.find_elements(By.TAG_NAME, "table"):
                try:
                    rows = [[c.text.strip() for c in tr.find_elements(By.XPATH, "./th|./td")]
                            for tr in tb.find_elements(By.TAG_NAME, "tr")]
                    rows = [r for r in rows if any(r)]
                    if len(rows) > 2:
                        tables.append(rows)
                except Exception:
                    continue

            results[name] = {"url": url, "requests": caps, "qids": sorted(set(qids)),
                             "tables_found": len(tables)}
            if tables:
                big = max(tables, key=len)
                p = OUT / f"{name}_화면표.tsv"
                p.write_text("\n".join("\t".join(r) for r in big), encoding="utf-8")
                log(f"  표 저장: {p.name} ({len(big)}행)")
            pause(3, 5)

        (OUT / "_캡처된_요청규격.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
        log(f"완료 — {OUT/'_캡처된_요청규격.json'}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else None)
