# 2022 新包核验与配对图更新（2026-10-18）

这是同日较早的缺件记录，8份缺件现已补齐。最新图表与六包见[四年图表同步版](../2026-10-18-four-year-refresh/)，原始审计数值保留其当时状态。

原2022模型源码已收到，并与阶段二检查点中的源哈希完全一致；12份data原件在新ZIP中全部缺席，其中4份已从旧附件按SHA256精确恢复，仍缺8份。本轮已重算配对指标并重绘2022及四年对比图，真实模型、Sobol和NSGA-III尚未重跑。

## 已完成

- 新包68项清单记录逐一核对通过；再次提交的DI_2022_Phase2.zip与10月17日原件相同。
- 2022阶段一4个检查点和阶段二检查点与冻结样本精确一致，保留行数分别215424和58784；MCMC未重跑。
- CC配对12条：R²=0.930617045146，RMSE=0.059574168180。
- 生物量配对10条：R²=0.996649936502，RMSE=0.556158882714 t/ha。
- 配对模拟值均与上传的148天生长序列对应日精确匹配。R²按1−SSE/SST计算，另存Pearson相关平方，二者不混用。
- 新环境18项既有工程检查通过，测试中的合成模型不是作物模型计算结果。

## 模型入口的实际阻塞

原模型已成功导入，调用原始load_inputs()后报MISSING_INPUT：ETO_FILE_DI_2022_ETo_Geometry_Daily.csv。源码明确用该B组ETo替换普通气象中的ETo，因此不能用已有普通ETo代填。

请从原DI_2022_OneClick工程中打包完整data文件夹。缺失清单为：

- `data/expected_initial.json`
- `data/origin.json`
- `data/start.json`
- `data/inputs/BIOMASS_FILE_biomass_observations.csv`
- `data/inputs/ETO_FILE_DI_2022_ETo_Geometry_Daily.csv`
- `data/inputs/HISTORICAL_MAP_FILE_historical_2022_grouped_MAP_point.csv`
- `data/inputs/INITIAL_POINT_FILE_mcmc_initial_point.csv`
- `data/inputs/READINESS_FILE_pre_mcmc_readiness.json`

恢复的4份原件是气象、Field CC、锁定初始水、遥感CC，分别与原manifest哈希一致，见model_input_inventory.csv。原manifest未改，缺失的READY、初始点和基准文件未人工造出。配对表不能自动等同于原似然输入文件。

本次新包只包含2022的原模型源码；其A18记录中“4个原模型已恢复”的表述属于原作者报告，不能据此认定本工作区已具备另外三个年度模型。

## 文件

- `URP_2022_Audit_and_Figures_20261018.zip`：核验结果、已恢复的2022源工程、配对数据、两幅PNG/PDF图、论文增补和复算脚本。
- `figures/F16_2022_paired_calibration.png`：2022生长时序及配对散点；`F17_four_year_calibration_updated.png`：四年对比，明确包含2022。
- `paper_addendum_20261018.md/.docx/.pdf`：可并入论文的新增校准证据及当前执行限制。
- `submitted/`：用户新包原件和原始清单/声称的审计门，仅作为来源档案。

这批文件记录当前已完成的复算和缺件，10月17日六包保留其既有版本；完成真实模型计算后再整体更新，避免把配对重绘当作新Sobol或优化结果。
