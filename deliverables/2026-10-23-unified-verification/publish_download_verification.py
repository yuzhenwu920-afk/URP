"""Publish download checks separately from the immutable verified payload."""
from pathlib import Path
import hashlib,json,shutil,subprocess

ROOT=Path(__file__).resolve().parents[1];REPO=Path('/workspace/URP')

def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args]).decode().strip()

def main():
 q=json.loads((ROOT/'analysis/REMOTE_DOWNLOAD_VERIFICATION_20261023.json').read_text());assert q['Status']=='PASS'
 p=REPO/'deliverables/2026-10-23-unified-verification';p.mkdir(exist_ok=True)
 for name in ['REMOTE_DOWNLOAD_VERIFICATION_20261023.json','PUBLISHED_CURRENT.json','DOCUMENT_AND_DATA_QA.json','RELOCATABLE_REBUILD_QA.json','CITATION_REVISION_QA.json']:shutil.copy2(ROOT/'analysis'/name,p/name)
 for name in ['publish_current_delivery.py','verify_remote_delivery.py','publish_download_verification.py']:shutil.copy2(ROOT/'code'/name,p/name)
 size=q['Collection_bytes']/1e9
 text=f'''# URP 最新交付回下载验收（2026-10-23）

状态：PASS。实际下载全部阶段总包（{size:.3f} GB），外层ZIP CRC通过；{q['Payload_SHA256_matches']}个交付文件SHA256逐项匹配，含41个阶段ZIP。另对{len(q['Standalone_direct_downloads'])}个Word、PDF、Excel及文稿速取包独立下载核对，全部HTTP 200且哈希一致。

[一键下载已验收总包]({q['Collection_URL']}) · [当前交付目录](../2026-10-23-unified-update/) · [完整验收记录](REMOTE_DOWNLOAD_VERIFICATION_20261023.json)

论文正文采用四年五生育期、每期最多3个可选事件的新计算结果；旧29个来源ZIP按原字节保留。原始完整模型结果版本20f1616556f5aeb79329b7ead22faa28f9fcda6a。

交付内容固定于 `{q['Delivery_commit']}`；总包内容固定于 `{q['Collection_commit']}`。验收记录另存此目录，避免更改已核对的交付文件。main仍为 `{q['Main_unchanged']}`。

外层总包SHA256：`{q['Collection_SHA256']}`。
'''
 (p/'README.md').write_text(text)
 checks=[]
 for f in sorted(p.iterdir()):
  if f.is_file() and f.name!='SHA256SUMS.txt':
   with f.open('rb') as stream:h=hashlib.file_digest(stream,'sha256').hexdigest()
   checks.append(f'{h}  {f.name}')
 (p/'SHA256SUMS.txt').write_text('\n'.join(checks)+'\n')
 for path,link in [(REPO/'README.md','deliverables/2026-10-23-unified-verification/'),(REPO/'deliverables/README.md','2026-10-23-unified-verification/')]:
  body=path.read_text();body=body.replace('约1.9 GB',f'{size:.2f} GB');body+=f'\n[实际回下载验收通过：{q["Payload_SHA256_matches"]}项哈希、41个阶段ZIP及独立文稿链接]({link})。\n';path.write_text(body)
 subprocess.run(['git','-C',str(REPO),'add','-f','--','README.md','deliverables/README.md','deliverables/2026-10-23-unified-verification'],check=True)
 subprocess.run(['git','-C',str(REPO),'-c','gc.auto=0','commit','-m','Verify citation-revised manuscripts and complete collection downloads'],check=True)
 subprocess.run(['git','-C',str(REPO),'-c','pack.window=0','-c','gc.auto=0','push','origin','HEAD:refs/heads/delivery/urp-review-20261015'],check=True)
 assert git('ls-remote','origin','refs/heads/main').split()[0]==q['Main_unchanged']
 print(json.dumps({'Status':'PASS','Verification_commit':git('rev-parse','HEAD'),'Verified_collection_commit':q['Collection_commit'],'Collection_GB':size,'Stage_ZIPs':41},indent=2),flush=True)

if __name__=='__main__':main()
