# URP当前交付文件

[四年原始MCMC链诊断与未收敛原因（2026-10-22）](2026-10-22-original-mcmc-diagnostic/)：20份原始完整链、1,280,000行状态只读复核；11页Word/PDF、12组英文图与12页矢量图册、Excel/CSV和原因证据表，完整包44.7 MiB。第一阶段四年最差R̂=1.181/1.174/1.124/1.122，均未达到原严格标准；第二阶段各仅一独立ensemble，不能认证。归纳链长、后期信息、局部边界及条件参数补偿；未改支持域或物理设置、未新增采样，不作“参数无偏”证明。

[一键下载：全部阶段总包（一个ZIP，约1.34 GB，2026-10-22）](https://codeload.github.com/yuzhenwu920-afk/URP/zip/refs/heads/delivery/urp-all-stages-20261022)：29个阶段压缩包及全部独立Word/PDF/图册/工作簿，49个文件实际回下载SHA256核对通过。[说明与校验](2026-10-22-all-stages/)。

[收官归档：17个科研阶段、29个ZIP、中英文完整论文与中期报告（2026-10-21）](2026-10-21-final-research-archive/)：当前可取得的原始资料、参考论文、四年MCMC两阶段代码与20组正式检查点、真实Sobol和遗传优化及后续全部诊断。13,898个归档文件通过逐项SHA256核对；103组英文图及逐图解析，104页矢量图册和28页签数据工作簿。论文各14图、7张三线表，中文24页、英文22页；中期报告10页。目录内有约29 MB文稿速取包及全量按阶段下载链接。所有科学限制按现有证据披露，历史四年与后续2021条件试验分开，不把模型低灌水解直接称为田间定额。

[最新：单目标最小灌水与四种算法交叉验证（2026-10-21）](2026-10-21-single-objective-comparison/)：历史四年＋最新2021三种fMulch模型；253,440次目标查询、217,084次实际优化模型调用，508个不同控制完整复算。提供6组英文图、10页Word/PDF、Excel和全部查询数据。新单目标最低灌水与历史NSGA-III门槛解差−2.63至+1.33 mm；数值接近不代表田间定额已验证。

[此前：四年降水审计与224组固定参数补充试验（2026-10-21）](2026-10-21-rainfall-audit/)：8页Word/PDF、4组英文图、Excel与逐日数据。GEE与论文降水有差异，但不足以消除2021年350 mm平台；fMulch=0.85情景减灌283.47 mm主要对应季末整个剖面储水少279.23 mm，ET仅少4.12 mm。本次未重新校准或优化；原结果按条件性潜力解释。

[2021年fMulch=0.50/0.75/0.85条件校准与NSGA-III比较](2026-10-21-2021-fmulch-comparison/)：保留先前正式计算记录，500步pilot尚未证明后验收敛。

[此前：最大根深1m四年试验压缩包、主图与Word](2026-10-20-root1m-experiment/)：200,000次实际评价、2,000份逐代种群、6组英文图、13页Word/PDF、Excel与完整CSV。DI土壤及灌水表已逐项核对；本轮是冻结原MCMC参数的根深单因素试验，未声称1m模型已重新校准。最终8,460个前沿点在最浅1.1m水文域回放后产量、ET及实际灌水一致。

[最新优化机制诊断与完整压缩包（2026-10-20）](2026-10-20-optimization-diagnosis/)：15页Word/PDF、9组英文图、Excel、逐日逐层数据及38,400次实际模型约束搜索。固定原执行设置与季末不耗初始储水，并匹配原季节ET时，2020/2021年可行诊断点减灌约11.1%/26.8%，不是已验证田间节水率。原上限仅保障实测日程执行，不作为已知硬件能力；fMulch=0不等于地膜完好率0%。

[此前43组完整英文图与论文骨架](2026-10-20-English-paper/)；历史六包不覆盖，旧优化结论请结合上述机制诊断解读。

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
