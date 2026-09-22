import csv
import glob
import os
from collections import defaultdict


def pct(a, b):
    if a in (None, 0) or b is None:
        return None
    return (b - a) / a * 100


print("=== 월영교 연간 검색 ===")
p = "보고서/안동교통/29_안동_관광지검색Top100_연도별.csv"
with open(p, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
w = [r for r in rows if r.get("ITS_BRO_NM") == "월영교"]
print(w[0] if w else "none")
