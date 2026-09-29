"""Prepare local reference photos from the user-supplied Google Doc exports."""
from pathlib import Path
from PIL import Image
import json,hashlib
root=Path(__file__).resolve().parents[1];source=root/'artifacts/relay/v7/references/document';out=root/'public/assets/relay/document';out.mkdir(parents=True,exist_ok=True)
url='https://docs.google.com/document/d/18C0Zfe5nR-f3OHJefg6_L5hkgm1nxPLvOmn8GTXJFSs/edit?tab=t.c29xob5u8w8x'
captions={1:{7:'안동구시장 입구와 아케이드',2:'찜닭골목 입구',3:'골목 점포와 조리대',1:'안동찜닭 안내 간판',11:'식당 내부 · 벽돌 벽과 검은 의자',9:'식당 목재 칸막이',12:'좌식 식사 공간',4:'현장 메뉴판 참고',17:'당면을 들어 올리는 식사 시점',6:'양념이 묻은 찜닭 근접 모습',8:'찜닭 한 상',10:'찜닭과 당면의 질감'},3:{22:'도자기 접시 완성 예시',13:'물레와 손동작',20:'도자기 잔',9:'접시에 색칠하는 과정',26:'안동한지 제조 현장',12:'한지 제조 도구'},4:{53:'월영교 야경',19:'월영교 난간과 야간 조명',21:'월영교와 월영정',55:'달빛 아래 목교',46:'해질녘 다리의 보행 시점',56:'월영정의 기둥과 지붕',20:'월영교 전경',31:'월영교와 수상 체험',50:'수상 체험 참고',27:'배에 탑승한 시점',54:'황포돛배',33:'문보트',14:'문보트 야간 선착장',12:'선착장 동선',58:'월영교 진입 산책길',41:'야간 산책로',38:'축제 배치도 참고',44:'행사 부스 배치도 참고'}}
concept={3:{21,10,5,25,14,19}}
records=[]
for stage in range(1,5):
 folder=source/f'stage-{stage}';catalog=json.loads((folder/'catalog.json').read_text())
 for i,row in enumerate(catalog):
  p=folder/row['file'];num=int(p.stem.replace('image',''));im=Image.open(p).convert('RGB');im.thumbnail((1440,1440));name=f'stage-{stage}-{p.stem}.webp';im.save(out/name,'WEBP',quality=88)
  thumb=im.copy();thumb.thumbnail((400,320));thumb.save(out/('thumb-'+name),'WEBP',quality=79)
  kind='구성 예시' if stage==2 or num in concept.get(stage,set()) else '문서 참고 사진'
  default={1:'찜닭골목 · 간판과 공간 참고',2:'영수증 인증 · 화면 및 안내물 예시',3:'전통 공예 · 공간과 도구 참고',4:'월영교·야시장 · 공간과 부스 참고'}[stage]
  data=(out/name).read_bytes();records.append(dict(id=f'doc-{stage}-{num}',stage=stage,caption=captions.get(stage,{}).get(num,default),kind=kind,file='/assets/relay/document/'+name,thumbnail='/assets/relay/document/thumb-'+name,sourceUrl=url,sourceTab=f'{stage}단계',credit='사용자 제공 기획 문서 · 원출처 권리 유지',license='원출처·이용허락 개별 확인 필요',width=im.width,height=im.height,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
(root/'public/data/relay-document-photos.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
print(len(records),'reference images;',sum(r['bytes'] for r in records),'bytes')
