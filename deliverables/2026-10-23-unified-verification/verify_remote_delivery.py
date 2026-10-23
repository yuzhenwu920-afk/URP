"""Download the published collection and validate every delivered byte."""
from pathlib import Path
import concurrent.futures,datetime,hashlib,json,time,urllib.request,zipfile

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'analysis/remote_downloads'

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def download(url,path):
 path.parent.mkdir(parents=True,exist_ok=True)
 for attempt in range(3):
  try:
   n=0
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'URP-delivery-verification'}),timeout=60) as r,path.open('wb') as f:
    status=r.status
    while True:
     b=r.read(4*1024*1024)
     if not b:break
     f.write(b);n+=len(b)
   assert status==200 and n>0
   return n
  except Exception:
   if attempt==2:raise
 print('Downloaded',path.name,n,flush=True)

def main():
 info=json.loads((ROOT/'analysis/PUBLISHED_CURRENT.json').read_text())
 delivery=ROOT/'delivery'
 manifest={}
 # The published copy includes the relocatable-rebuild verification as well.
 published=Path('/workspace/URP')/info['Delivery_path']
 for line in (published/'SHA256SUMS.txt').read_text().splitlines():
  h,n=line.split('  ',1);manifest[n]=h
 path=CACHE/'URP_All_Stages_20261023.zip'
 start=time.monotonic();size=download(info['All_stage_URL'],path)
 print('Collection downloaded',size,'bytes; checking CRC and all payload SHA256 values',flush=True)
 actual={}
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  names=[n for n in z.namelist() if not n.endswith('/')]
  prefix=names[0].split('/')[0]+'/'
  for name in names:
   rel=name[len(prefix):]
   if rel=='SHA256SUMS.txt':
    assert z.read(name)==(published/'SHA256SUMS.txt').read_bytes();continue
   assert rel in manifest,rel
   with z.open(name) as f:h=hashlib.file_digest(f,'sha256').hexdigest()
   assert h==manifest[rel],rel
   actual[rel]=h
  assert set(actual)==set(manifest),(set(manifest)-set(actual),set(actual)-set(manifest))
  assert sum(n.endswith('.zip') and n.startswith(prefix+'packages/') for n in names)==41
 print('Entire collection validated:',len(actual),'file hashes and 41 stage ZIPs',flush=True)
 files=[p for p in published.iterdir() if p.is_file() and p.suffix in ['.docx','.pdf','.xlsx','.zip'] and p.name not in ['URP_Manuscript_CN.docx','URP_Manuscript_CN.pdf','URP_Manuscript_EN.docx','URP_Manuscript_EN.pdf','URP_midterm_report.docx','URP_midterm_report.pdf']]
 base='https://raw.githubusercontent.com/yuzhenwu920-afk/URP/'+info['Delivery_commit']+'/'+info['Delivery_path']+'/'
 def one(p):
  target=CACHE/'direct'/p.name;n=download(base+p.name,target);assert digest(target)==digest(p)
  if p.suffix in ['.docx','.xlsx','.zip']:
   with zipfile.ZipFile(target) as z:assert z.testzip() is None
  return dict(File=p.name,Bytes=n,SHA256=digest(target),HTTP_status=200)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(one,files))
 result=dict(Status='PASS',Verified_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),Delivery_commit=info['Delivery_commit'],Collection_commit=info['Collection_commit'],Collection_URL=info['All_stage_URL'],Collection_bytes=size,Collection_SHA256=digest(path),Collection_CRC='PASS',Payload_SHA256_matches=len(actual),Stage_ZIPs=41,Standalone_direct_downloads=rows,Elapsed_seconds=round(time.monotonic()-start,2),Main_unchanged=info['Main_unchanged'])
 (ROOT/'analysis/REMOTE_DOWNLOAD_VERIFICATION_20261023.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
