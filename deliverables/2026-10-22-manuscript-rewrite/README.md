# URP论文重写交付（2026-10-22）

依据本次23页批注稿及王尚今2023年学位论文，重写中文正文，逐条落实段落旁修改意见。正文18页，13张全英文图、8张英文三线表、16条参考文献，另有5页补充资料和2页逐项修改说明。

## 文件

- documents/URP_Manuscript_CN_Rewritten_20261022.docx：可编辑中文论文。
- documents/URP_Manuscript_CN_Rewritten_20261022.pdf：排版预览。
- documents/URP_Supplementary_Methods_and_Diagnostics_20261022.docx/pdf：先验、采样诊断、四窗口日期和补充结构试验。
- documents/URP_Revision_Response_20261022.docx/pdf：20项修改意见落实记录。
- figures/：13组450 dpi PNG、矢量PDF及SVG，全部英文。
- tables/URP_Manuscript_Data_and_Revision_20261022.xlsx：图表源数据与修改记录汇总；同目录保留逐表CSV。
- source/uploads/：本次全部11份上传文件原样保存，清单附SHA256；两份2021遥感文件字节相同。
- source/method_records/：关键模型和四窗口控制代码的原样快照。
- code/：本轮数据比对、图表重绘、文档生成、排版检查和打包脚本。
- analysis/：批注文字、数据和版面检查记录。

## 结果口径

四年主模型固定fMulch=0、MulchPct=75%、Zmax=2.30 m；2021年根深1 m、fMulch=0.50/0.75/0.85条件试验在补充资料单列。优化源码实际使用4个有序灌水管理窗口，与5个生育期的田间描述分别解释。正文以保留样本均值作确定性模拟，原链R̂、ESS和均值稳定性采用真实时间序列诊断记录；原修订稿中的R̂≤1.0048、ESS≥3200不替代原时间序列诊断。

本轮没有新增MCMC采样、没有重新求解优化模型；进行了新上传资料接入比较、既有数据统计、13组图重绘及论文重写。四年气象原值与冻结输入一致，模型ETo采用原审计序列，降水汇总按实际执行日期计算。

## 再生成

在含有本包tables及source的目录运行：

    python code/make_figures.py
    python code/build_documents.py

依赖numpy、pandas、scipy、matplotlib、Pillow、python-docx、openpyxl。PDF由LibreOffice转换；review_layout_and_data.py另需PyMuPDF。prepare_evidence.py记录原工作区来源路径，用于本轮证据接入，不是MCMC运行器。引用书目与依据位于source/REFERENCE_EVIDENCE_revised.json。

## 直接下载

- [URP_Manuscript_Rewrite_20261022.zip](https://raw.githubusercontent.com/yuzhenwu920-afk/URP/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-22-manuscript-rewrite/URP_Manuscript_Rewrite_20261022.zip)
- [URP_Manuscript_CN_Rewritten_20261022.docx](https://raw.githubusercontent.com/yuzhenwu920-afk/URP/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-22-manuscript-rewrite/URP_Manuscript_CN_Rewritten_20261022.docx)
- [URP_Revision_Response_20261022.docx](https://raw.githubusercontent.com/yuzhenwu920-afk/URP/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-22-manuscript-rewrite/URP_Revision_Response_20261022.docx)
- [URP_Supplementary_Methods_and_Diagnostics_20261022.docx](https://raw.githubusercontent.com/yuzhenwu920-afk/URP/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-22-manuscript-rewrite/URP_Supplementary_Methods_and_Diagnostics_20261022.docx)
- [URP_Manuscript_CN_Rewritten_20261022.pdf](https://raw.githubusercontent.com/yuzhenwu920-afk/URP/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-22-manuscript-rewrite/URP_Manuscript_CN_Rewritten_20261022.pdf)
- [URP_Revision_Response_20261022.pdf](https://raw.githubusercontent.com/yuzhenwu920-afk/URP/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-22-manuscript-rewrite/URP_Revision_Response_20261022.pdf)
- [URP_Supplementary_Methods_and_Diagnostics_20261022.pdf](https://raw.githubusercontent.com/yuzhenwu920-afk/URP/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-22-manuscript-rewrite/URP_Supplementary_Methods_and_Diagnostics_20261022.pdf)
- [URP_Manuscript_Data_and_Revision_20261022.xlsx](https://raw.githubusercontent.com/yuzhenwu920-afk/URP/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-22-manuscript-rewrite/URP_Manuscript_Data_and_Revision_20261022.xlsx)
