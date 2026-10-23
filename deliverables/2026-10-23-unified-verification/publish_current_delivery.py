"""Publish the authorized current delivery and refresh the all-stage collection."""
from pathlib import Path
import hashlib,json,shutil,subprocess

ROOT=Path(__file__).resolve().parents[1]
REPO=Path('/workspace/URP')
PATH='deliverables/2026-10-23-unified-update'
BRANCH='delivery/urp-review-20261015'
COLLECTION='delivery/urp-all-stages-20261022'
MAIN='f040054a4a7fb789c1a10bf1835cd7a36d8cfcbb'

def git(*args,input=None):
 return subprocess.check_output(['git','-C',str(REPO),*args],input=input).decode().strip()

def run(*args):
 subprocess.run(['git','-C',str(REPO),*args],check=True)

def stage():
 assert git('branch','--show-current')==BRANCH
 assert not git('status','--porcelain')
 assert git('ls-remote','origin','refs/heads/main').split()[0]==MAIN
 assert json.loads((ROOT/'analysis/RELOCATABLE_REBUILD_QA.json').read_text())['Status']=='PASS'
 dst=REPO/PATH
 shutil.copytree(ROOT/'delivery',dst,dirs_exist_ok=True)
 shutil.copy2(ROOT/'analysis/RELOCATABLE_REBUILD_QA.json',dst/'RELOCATABLE_REBUILD_QA.json')
 hashes=[]
 for p in sorted(dst.rglob('*')):
  if p.is_file() and p.name!='SHA256SUMS.txt':
   h=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();hashes.append(f'{h}  {p.relative_to(dst)}')
 (dst/'SHA256SUMS.txt').write_text('\n'.join(hashes)+'\n')
 aliases={'URP_full_package.zip':'12_Current_CN_EN_manuscripts_and_reproduction.zip','URP_figures.zip':'11_Current_English_figures_tables.zip','URP_run_results.zip':'05_Current_five_stage/URP_FiveStage_MultiEvent_Results_20261022.zip'}
 for name,src in aliases.items():shutil.copy2(dst/'packages'/src,REPO/'deliverables'/name)
 text='''# URP · 当前统一交付（2026-10-23）

最新五生育期、每期最多3个可选事件的四年优化结果，已同步到中英文论文、中期报告、英文图表、逐次灌水日程和数据工作簿。计算版本为2026-10-22，文稿归档版本为2026-10-23。

**[一键下载全部阶段总包（约1.9 GB）](https://codeload.github.com/yuzhenwu920-afk/URP/zip/refs/heads/delivery/urp-all-stages-20261022)**

[全部文件与41个阶段包索引](deliverables/2026-10-23-unified-update/) · [论文、中期、图册与数据速取ZIP](deliverables/2026-10-23-unified-update/URP_Current_Papers_Midterm_and_Figures_20261023.zip)

|当前文件|下载|
|---|---|
|中文论文：20页、15组英文图、10张三线表|[Word](deliverables/2026-10-23-unified-update/URP_Manuscript_CN_Updated_20261023.docx) · [PDF](deliverables/2026-10-23-unified-update/URP_Manuscript_CN_Updated_20261023.pdf)|
|英文论文：20页，对应同一组数据图表|[Word](deliverables/2026-10-23-unified-update/URP_Manuscript_EN_Updated_20261023.docx) · [PDF](deliverables/2026-10-23-unified-update/URP_Manuscript_EN_Updated_20261023.pdf)|
|中期报告：11页，沿用学校模板|[Word](deliverables/2026-10-23-unified-update/URP_Midterm_Report_Updated_20261023.docx) · [PDF](deliverables/2026-10-23-unified-update/URP_Midterm_Report_Updated_20261023.pdf)|
|四年逐次日程、图表源数据|[Excel](deliverables/2026-10-23-unified-update/URP_All_Current_Data_20261023.xlsx)|
|当前15组英文图及中英文逐图解析|[矢量图册](deliverables/2026-10-23-unified-update/URP_All_Current_English_Figures_20261023.pdf) · [解析Word](deliverables/2026-10-23-unified-update/URP_All_Figure_Interpretations_Updated_20261023.docx)|

四年候选季节灌水量为209.83、306.50、264.50、257.47 mm。正文同步报告储水差、ET差、原链诊断与单次水量，保留各试验的物理设定和控制空间。原始数据、参考论文、四年MCMC两阶段代码与检查点、Sobol、原优化、全部补充试验及当前五期完整逐查询结果均在全阶段总包。

本次进行文稿和归档整合，无新增模型搜索。原有29个阶段包按原字节保留，旧稿和旧四窗口主结果单列history；当前正文采用新五期结果。实际报销、导师与专家审核签字留空。

旧版日期目录保存对应研究过程，当前入口见上方。[此前原链诊断](deliverables/2026-10-22-original-mcmc-diagnostic/) · [此前论文修订](deliverables/2026-10-22-manuscript-rewrite/) · [五期原始计算交付](deliverables/2026-10-22-five-stage-multi-event/)。

交付分支：delivery/urp-review-20261015；总包分支：delivery/urp-all-stages-20261022。main保持原提交。
'''
 (REPO/'README.md').write_text(text)
 (REPO/'deliverables/README.md').write_text(text.replace('deliverables/2026-','2026-'))
 (REPO/'deliverables/README.md').write_text((REPO/'deliverables/README.md').read_text()+'''
## 兼容旧入口

- [URP_full_package.zip](URP_full_package.zip)：当前中英文论文、图表数据和文稿再生成工程；完整原始链与逐查询运行记录见全部阶段总包。
- [URP_figures.zip](URP_figures.zip)：当前英文图件、源数据、解析与图册。
- [URP_run_results.zip](URP_run_results.zip)：当前五期优化结果、代码和汇总；四年完整逐查询记录在05_Current_five_stage下的四个年度运行包。

旧日期目录及历史压缩包保持其研究版本。
''')
 (REPO/'deliverables/2026-10-22-all-stages/README.md').write_text('''# URP 全部阶段总包：已更新至2026-10-23

**[点击下载最新全部阶段总包](https://codeload.github.com/yuzhenwu920-afk/URP/zip/refs/heads/delivery/urp-all-stages-20261022)**

当前总包包含41个阶段ZIP，以及已采用四年五期逐次优化结果的中英文论文、中期报告、英文图册与数据。原29包保留；旧四窗口结果和旧稿单列history。05_Current_five_stage含最新六个计算包，当前稿件见12包。

[最新文件与校验入口](../2026-10-23-unified-update/)

本目录原有COLLECTION_MANIFEST、SHA256及SINGLE_DOWNLOAD_VERIFICATION记录对应2026-10-22历史快照；最新清单以2026-10-23目录为准。主分支未修改。
''')
 run('add','-f','--',PATH,'README.md','deliverables/README.md','deliverables/2026-10-22-all-stages/README.md','deliverables/URP_full_package.zip','deliverables/URP_figures.zip','deliverables/URP_run_results.zip')
 run('-c','gc.auto=0','commit','-m','Update CN and EN manuscripts, midterm and all-stage archive with verified five-stage results')
 run('-c','pack.window=0','-c','gc.auto=0','push','origin','HEAD:refs/heads/'+BRANCH)
 head=git('rev-parse','HEAD')
 tree=git('rev-parse','HEAD:'+PATH)
 old=git('ls-remote','origin','refs/heads/'+COLLECTION).split()[0]
 git('cat-file','-e',old)
 commit=git('commit-tree',tree,'-p',old,'-m','Refresh all-stage collection with current five-stage papers, midterm and 41 research archives')
 git('update-ref','refs/heads/'+COLLECTION,commit)
 run('-c','pack.window=0','-c','gc.auto=0','push','origin',commit+':refs/heads/'+COLLECTION)
 assert git('ls-remote','origin','refs/heads/main').split()[0]==MAIN
 info={'Status':'PUBLISHED','Delivery_commit':head,'Delivery_path':PATH,'Collection_commit':commit,'Collection_parent':old,'Collection_tree':tree,'Main_unchanged':MAIN,'All_stage_URL':'https://codeload.github.com/yuzhenwu920-afk/URP/zip/'+commit,'Source_model_commit':'20f1616556f5aeb79329b7ead22faa28f9fcda6a'}
 (ROOT/'analysis/PUBLISHED_CURRENT.json').write_text(json.dumps(info,ensure_ascii=False,indent=2));print(json.dumps(info,indent=2),flush=True)

if __name__=='__main__':stage()
