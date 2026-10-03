import sys, urllib.request
source=sys.stdin.read()
request=urllib.request.Request('http://127.0.0.1:6287',source.encode(),method='POST')
try:
    with urllib.request.urlopen(request,timeout=1800) as r: print(r.read().decode()[:4000])
except urllib.error.HTTPError as e:
    print(e.read().decode()[:4000]);sys.exit(1)
