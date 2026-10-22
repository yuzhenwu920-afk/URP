# 四年原始 MCMC 链诊断与未收敛原因（2026-10-22）

复核原始20组正式检查点、1,280,000行已存状态。本轮未新增采样、未改参数域、未改物理设置，不混入后来的2021根深/覆膜短链。

- [完整诊断包：Word、PDF、12组英文图、Excel/CSV、代码及20份原始完整链（44.7 MiB）](https://raw.githubusercontent.com/yuzhenwu920-afk/URP/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-22-original-mcmc-diagnostic/URP_Original_MCMC_Diagnostic_20261022.zip)
- [中文诊断 Word](URP_Original_MCMC_Diagnostic_CN.docx) / [PDF，11页](URP_Original_MCMC_Diagnostic_CN.pdf)
- [英文诊断图册，12页矢量PDF](Original_MCMC_English_Figure_Atlas.pdf)
- [全部诊断与原因证据表 Excel](Original_MCMC_diagnostics.xlsx)
- [快速结论](Diagnostic_summary_CN.md) / [逐图解析](Figure_interpretations.md)
- [文件与重算核验](FINAL_QA.json) / [ZIP校验](PACKAGE_VERIFICATION.json) / [SHA256](SHA256SUMS.txt)
- [GitHub实际回下载验证](DOWNLOAD_VERIFICATION.json)：ZIP、Word、PDF和Excel均返回HTTP 200，逐文件SHA256与本地一致，远端ZIP再次通过CRC检查。

| 年份 | 第一阶段最差 rank R̂ | 最小 matched-group bulk ESS | 2000步/最大τ |
|---|---:|---:|---:|
| 2019 | 1.181 | 17.8 | 25.4 |
| 2020 | 1.174 | 19.2 | 27.1 |
| 2021 | 1.124 | 24.9 | 28.8 |
| 2022 | 1.122 | 25.3 | 31.5 |

这些 ESS 是“同一walker编号跨四个独立ensemble”的诊断组数值，并非总ESS；32个相关组的ESS不相加。组中位R̂同样约为1.032–1.068。独立ensemble均值时间序列的辅助诊断也未全部通过。

主要证据支持：链长相对依赖时间不足、后期冠层观测约束薄弱、局部边界堆积，以及条件第二阶段的WP–HI补偿。四组参数均值位置跨度总体不大；未见所有walkers停止移动或样本超出记录支持域。不能把局部边界问题描述为所有参数都撞墙，也不能将参数均值相近写成“无偏证明”。

第二阶段各年只有一个独立ensemble，独立重复链R̂保留为空；2019/2022满足50τ长度参考仍不等于通过完整收敛认证。2022先验密度及条件阶段支持域与前三年不同。两阶段不拼成八参数联合后验。

原因按直接证据、机制推测和未完成验证分别陈述；本轮未重放前向模型或原似然。现有拟合、Sobol和优化按各自的条件性证据层级保留，不覆盖历史文件。
