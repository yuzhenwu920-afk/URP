# URP 创新训练项目中期报告书

填报整理日期：2026-10-19。正式项目名称：**基于马尔科夫链的不同灌溉方式灌溉制度优化**。项目编号：**X2026100190937**（据用户补充）。

## 先打开哪些文件

- `URP_midterm_report.docx`：建议使用的可编辑 Word 稿，保留原学校标识、封面字段及七项栏目，按内容重新分页。
- `URP_midterm_report.doc`：兼容原模板格式的旧版 Word 稿。
- `URP_midterm_report.pdf`：7页定版预览；含2页四年图件证明材料。
- `URP_midterm_report_text.md`：可复制的正文，便于填入其他表格或系统。
- `figures/`：专为报告印刷尺寸重排的两组四年图，每组提供300 dpi PNG和矢量PDF。
- `evidence/`：四年源表、复算指标、采样记录、2022模型接入与工程验证证明、六包同步记录。
- `template/`：用户提供的原中期模板、转换稿、基本信息表和立项申请书。

## 提交前仍须核定

1. **个人分工与贡献表述**：按用户明确要求，以组长吴雨臻、李承昊、段璞的贡献顺序拟定。组长侧重统筹、模型复核和核心研究方案；李侧重数据、指标和图表；段侧重文献、来源记录、归档和报告辅助。未编造贡献百分比，提交前请成员核对表述。
2. **已报销金额及凭证明细**：按用户要求全部留空。申请书5000元预算及原五个预算科目仍单列，预算不当作实际报销额。
3. **填表日期与后续日期**：暂按2026-10-19填表，对照立项书11—12月总结阶段安排后续工作，须按学校节点确认。
4. **导师及专家意见、签名**：留给相应审核人填写；未沿用立项申请书中的旧导师意见冒充中期意见。

## 立项信息与当前成果如何衔接

封面姓名、学号、院系班级、导师及联系方式来自此次补充的两份立项材料；正式执行时间采用申请书的2026年。项目编号与贡献顺序来自用户后续明确回复。项目来源为“吐哈盆地农业水资源节水潜力分析”。简介89个字符（含标点），满足模板100字以内要求。

申请书中的遥感动态同化、滴灌与喷灌对照、三链1000步方案、效率提升30%以上等属于原定方案或目标。当前证据主要支持四年DI资料、既有分阶段ensemble MCMC成果复核、2022原模型均值点回放和四年校准图。报告已说明方法调整、范围差距和后续任务，没有把目标写成实绩。

四年校准拟合不等同独立验证；2019—2021使用已核验原输出，2022使用本轮原模型冻结均值点回放。本轮没有重跑MCMC，完整新真实模型Sobol及NSGA-III实验尚未完成，未填写正式节水率或推荐灌溉制度。2022现有接口只支持原五个固定日期的灌水量分配。

表1的R²、RMSE、样本数均据源表复算；各年仅一对年产量，不计算单年产量R²。产量采用13%含水率，生物量为地上干生物量。图中模拟值逐点核对对应日期的逐日输出，包含全部四个年份。

## 对应的既有完整成果

报告和证明材料引用的18组四年图、论文框架及完整计算准备工程，仍在同一交付分支：

- [六包最新同步说明](https://github.com/yuzhenwu920-afk/URP/tree/delivery/urp-review-20261015/deliverables/2026-10-18-four-year-refresh)
- [完整报告包](https://github.com/yuzhenwu920-afk/URP/blob/delivery/urp-review-20261015/deliverables/URP_full_package.zip)
- [运行结果包](https://github.com/yuzhenwu920-afk/URP/blob/delivery/urp-review-20261015/deliverables/URP_run_results.zip)
- [18组四年图件包](https://github.com/yuzhenwu920-afk/URP/blob/delivery/urp-review-20261015/deliverables/URP_figures.zip)

本次中期报告单独交付，没有改写上述六包。

## 复现与检查

`build_midterm_report.py`从包内冻结表和转换模板生成报告及图件。环境依赖为Python、python-docx、numpy、pandas、matplotlib，中文字体为Noto CJK；`.doc`兼容导出和PDF由LibreOffice完成。Word正文为11 pt，主要标题12.5 pt；图中最小印刷字号约10 pt，固定年份色为蓝、橙、绿、紫。

`evidence/report_figure_checks.json`记录四年两类图的指标及原始字体；`evidence/report_content_checks.json`记录范围；`evidence/DOCUMENT_QA.json`记录最终Word/PDF与格式核查；`SHA256SUMS.txt`用于包内文件完整性核验。
