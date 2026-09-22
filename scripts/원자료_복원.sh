#!/usr/bin/env bash
# 깃에는 100MB 넘는 원자료가 압축본(.csv.gz)으로만 올라가 있다.
# 원격(클라우드)에서 처음 작업할 때 한 번 실행하면 같은 경로에 원래 .csv를 풀어 둔다.
# 이미 풀린 파일은 건너뛴다. 사용법: bash scripts/원자료_복원.sh
set -euo pipefail
cd "$(dirname "$0")/.."

found=0
while IFS= read -r -d '' gz; do
  csv="${gz%.gz}"
  found=$((found + 1))
  if [ -f "$csv" ]; then
    echo "있음  $csv"
  else
    gunzip -k "$gz"
    echo "풀기  $csv"
  fi
done < <(find data -name '*.csv.gz' -print0)

echo "압축본 ${found}개 확인 완료"
