# URP论文写作框架与正文示例

根据本次提供的Liu等（2025）论文，以及2019—2022年DI玉米已核验成果编写。版本：2026-10-19。

## 下载后先看

- **URP_paper_writing_framework.docx**：可编辑Word主稿，38页，包含论文框架、摘要至结论的正文示例、模型与统计解释、11张方法/数据表、图表导航及全部18组现有四年图的逐图解读。
- **URP_paper_writing_framework.pdf**：对应预览，便于核对公式、字体与横竖页面。
- **URP_paper_writing_framework.md**：可复制的正文及图表索引。

图版共20页：18组图中的参数区间和年度中心各拆为上下两页，保持印刷字号。每页都有“图注—正文示例—写作说明”。Word含25处可编辑数学对象；数学对象包含行内变量及显示公式，并非25个独立编号公式。

## 内容安排

1. 参考论文的结构、方法与URP研究的映射，题目、研究问题及贡献建议。
2. 摘要与引言四段式正文示例。
3. 资料角色、改进AquaCrop过程、两段有效WP、分阶段MCMC及似然、拟合指标、水量平衡、Sobol、NSGA-III和候选条件扰动的写法。
4. 已有四年校准、参数补偿与水量结果的数值和解读。
5. 正式敏感性、真实前沿和代表方案的待补位置及填写模板。
6. 讨论、结论、参考文献，以及现有全部18组四年图的图注和写作解读。

这是一份带指导说明的扩展写作稿。投稿时删除“写作说明”，按目标期刊篇幅精简，确认试验来源、署名和实际实验状态。论文题目不能因URP立项名称包含“不同灌溉方式”就宣称已完成滴/喷等方式对照。

## 资料与方法口径

参考论文为：Liu, Y., Wang, Y., Šimůnek, J., & Liao, R. 2025. An integrated data assimilation, crop modeling, and multi-objective optimization framework for improving cotton irrigation water use efficiency. Agricultural Water Management 319, 109774. DOI: 10.1016/j.agwat.2025.109774。所给PDF共11页。

现有MCMC保持冻结，本任务没有新增采样。2019—2021沿用已核验的原输出；2022引用本轮原模型均值点回放。校准拟合、内部水量账及数值复现均不替代独立田间验证。

正式的新增真实模型Sobol和NSGA-III实验尚未完成，Word保留了明确结果位置，没有把历史代理图、旧节水率或参考棉花论文的效果填为玉米结果。2022现有管理接口为五个固定日期的灌水量，不是四阶段SMT触发控制。

2022正式阶段二检查点记载的交接是“保留阶段一样本的算术均值”，以该实际合同为准，不依据旧源代码默认MAP流程推断。原先验与后续独立Sobol范围分开说明。源表parameter_intervals_verified中的旧Prior_low/Prior_high字段不用于重建2022原采样先验；正式合同信息见REFERENCE_AND_DATA_SOURCES.json。

## 包内材料

- figures_original/：18组当前原图，每组PNG与矢量PDF，原件保持不变。
- figures_word/：适合Word印刷尺寸的科学图重排版，数值来源不变；源字号经页面缩放后仍不小于约10 pt。
- tables/：用于论文表格、图件和数值解读的已核验CSV。
- FIGURE_WRITING_INDEX.json：每张图的文件、四年覆盖、图注、解读、写作说明与实际印刷字号。
- REFERENCE_AND_DATA_SOURCES.json：参考论文元数据、原模型哈希及2022正式阶段二合同的相关字段。
- DOCUMENT_QA.json：38页版式、20张嵌入图、12张Word表（含1张导航表）、可编辑数学对象和边界检查记录。
- SHA256SUMS.txt：文件完整性校验。

rebuild_word.py可从包内writing_template.md、tables/与图件重建Word；需要Python依赖（requirements_document.txt）、系统Pandoc及Noto CJK字体。PDF可使用LibreOffice导出。重建脚本只重新组织文稿与插图，不调用MCMC或灌溉模型。

本次单独交付论文写作稿，原六个科研交付包及中期报告保持不变。
