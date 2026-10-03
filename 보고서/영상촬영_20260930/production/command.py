import sys, urllib.request
source=sys.stdin.read()
request=urllib.request.Request('http://127.0.0.1:6187',source.encode(),method='POST')
try:
    with urllib.request.urlopen(request,timeout=240) as r: print(r.read().decode())
except urllib.error.HTTPError as e:
    print(e.read().decode());sys.exit(1)
