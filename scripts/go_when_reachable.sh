#!/bin/zsh
# 데이터랩 접속이 열리는 순간 미확보분을 저속으로 수집한다.
# 사용: ./scripts/go_when_reachable.sh
cd /Users/koyunseo/한국관광데이터분석

echo "$(date '+%H:%M:%S') 접속 대기 시작 (30초 간격)"
while true; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 \
    -H 'User-Agent: Mozilla/5.0' \
    https://datalab.visitkorea.or.kr/datalab/portal/main/getMainForm.do)
  if [ "$code" = "200" ]; then
    echo "$(date '+%H:%M:%S') ✅ 접속 가능 — 수집 시작"
    break
  fi
  sleep 30
done

ip=$(curl -s --max-time 8 https://api.ipify.org)
echo "$(date '+%H:%M:%S') 현재 공인 IP: $ip"

# 1단계: API 저속 수집 (동시 1개 / 요청 간 2.5초)
echo "$(date '+%H:%M:%S') [1/2] API 수집 (저속)"
python3 -u scripts/resume_missing.py 2>&1 | tail -40

# 2단계: 셀레니움 — 세션 의존 화면 (비교 3종 + 검색순위)
echo "$(date '+%H:%M:%S') [2/2] 셀레니움 수집"
.venv_sel/bin/python scripts/selenium_collector.py 2>&1 | tail -40

echo "$(date '+%H:%M:%S') 전체 완료"
