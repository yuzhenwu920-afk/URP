"""Download published archives/documents and compare their actual SHA256 bytes.

Run this script from a copy of the delivery directory; it reads PACKAGE_INDEX.csv
and SHA256SUMS.txt, uses four download workers, and writes verification JSON.
It does not execute any project model or send messages.
"""
from pathlib import Path
import argparse,csv,hashlib,json,time,urllib.request,urllib.parse,concurrent.futures
ROOT=Path(__file__).resolve().parent
P=argparse.ArgumentParser();P.add_argument('--ref',default='refs/heads/delivery/urp-review-20261015');P.add_argument('--output',default='REMOTE_DOWNLOAD_VERIFICATION.json');A=P.parse_args()
BASE='https://raw.githubusercontent.com/yuzhenwu920-afk/URP/'+A.ref+'/deliverables/2026-10-21-final-research-archive/'
EXPECTED={}
for line in (ROOT/'SHA256SUMS.txt').read_text().splitlines():
    h,n=line.split('  ',1);EXPECTED[n]=h
NAMES=[r['filename'] for r in csv.DictReader((ROOT/'PACKAGE_INDEX.csv').open(encoding='utf-8-sig'))]
NAMES += ['URP_Manuscript_CN.docx','URP_Manuscript_EN.docx','URP_Manuscript_CN.pdf','URP_Manuscript_EN.pdf','URP_midterm_report.docx','URP_midterm_report.pdf','URP_All_English_Figures_Final.pdf','URP_All_Figure_Interpretations.docx','URP_All_Figure_Interpretations.pdf','URP_Final_Paper_Data.xlsx','README.md','PACKAGE_INDEX.csv','ARCHIVE_VALIDATION.json','CONTENT_MANIFEST_VALIDATION.json']
def check(n):
    url=BASE+urllib.parse.quote(n)
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'URP-archive-download-check/1.0'})
            h=hashlib.sha256();size=0;t=time.monotonic()
            with urllib.request.urlopen(req,timeout=120) as r:
                status=r.status
                while block:=r.read(1024*1024):h.update(block);size+=len(block)
            value=h.hexdigest();ok=status==200 and value==EXPECTED[n]
            out=dict(file=n,url=url,HTTP_status=status,bytes=size,sha256=value,expected_sha256=EXPECTED[n],passed=ok,seconds=round(time.monotonic()-t,3))
            print(('PASS' if ok else 'FAIL'),n,size,flush=True);return out
        except Exception as e:
            error=str(e)
            if attempt<3:time.sleep(2*(attempt+1))
    print('ERROR',n,error,flush=True);return dict(file=n,url=url,passed=False,error=error)
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(check,NAMES))
    report=dict(status='PASS' if all(r['passed'] for r in results) else 'FAIL',ref=A.ref,checked_files=len(results),downloaded_bytes=sum(r.get('bytes',0) for r in results),checks=results)
    (ROOT/A.output).write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print('RESULT',report['status'],report['checked_files'],'files',report['downloaded_bytes'],'bytes',flush=True)
    if report['status']!='PASS':raise SystemExit(1)
