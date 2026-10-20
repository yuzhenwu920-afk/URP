# URP当前交付文件

[Figure 1与Figure 10第一部分修订包（2026-10-20）](2026-10-20-figures-part1/)：两种流程布局、四年环境图英文版及Word说明。

2026-10-20交付：2019、2020、2021、2022四年真实Sobol与NSGA-III实验全部完成，原MCMC冻结。此前“尚未完成”的说明属于历史记录。

Sobol最终N=512、3个独立随机种子，61,440行模型响应；NSGA-III与同预算NSGA-II各100个体×100代×5种子×4年，共400,000次评估和4,000代完整种群。全量数据一致性、水量平衡及六包逐文件哈希检查通过。

六包均含相同的32组四年PNG/PDF图件：18组校准背景（流程与气象已更新）及14组新增真实敏感性/优化结果。新增图字号至少11pt、PNG320dpi，固定蓝/橙/绿/紫年份色。完整、复核、执行及工程包配有44页Word/PDF论文正文与图解、15张结果表、10个可编辑公式和Excel工作簿。

## 六包直下载

- [完整资料包（论文、代码、数据和图件）](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/URP_full_package.zip) — 93.7 MiB
- [完整运行结果包（全部响应和每代种群）](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/URP_run_results.zip) — 88.7 MiB
- [四年高清图件包（PNG、PDF及源表）](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/URP_figures.zip) — 11.8 MiB
- [复核与论文更新包](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-16/URP_update_20261016.zip) — 30.8 MiB
- [模型复跑与执行包](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-16-execution-ready/URP_execution_ready_20261016.zip) — 53.6 MiB
- [Sobol与NSGA-III完整工程包](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-16-sobol-optimization/URP_Sobol_Optimization_Updated.zip) — 93.7 MiB

[单独下载Word、PDF、Excel及核验清单](2026-10-19-actual-results/)

Sobol使用声明的公共独立均匀范围；2022产量的第三、四名近似并列，保留数值排序不确定性。优化调整原灌水日期上的四个窗口水量；主候选未设季末储水约束，不能将灌水减少全部解释为耗水减少。论文与SCIENCE_REVIEW详细解释这一问题，并给出追加储水门槛后的事后筛查结果。原MCMC诊断限制和缺少独立田间验证的限制均保留。

文件名保留原日期以兼容旧链接；ZIP内部为本轮四年真实计算结果。历史文件请按原日期目录及提交记录识别。
