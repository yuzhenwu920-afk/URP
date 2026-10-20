# URP灌溉优化机制诊断 · 2026-10-20

本包补充原2019—2022年结果，重点追溯2020、2021年过大的表观减灌比例。原MCMC、原模型方程、原正式结果与主分支未覆盖。

先读 `URP_Optimization_Mechanism_Report.docx`（可编辑）或同名PDF，再看 `URP_Optimization_Mechanism_Data.xlsx`。9组英文图在 `figures/`，每组有600 dpi PNG、矢量PDF和SVG；中文解析见Word与 `FIGURE_INTERPRETATIONS.json`。

## 已证实的模型内原因

- 原C1的季末储水低于原DI，2020/2021年储水差分别解释减灌量的93.3%/97.4%。这不是全部来自初始深层水，而是避免原DI补蓄与额外动用储水的合成。
- 冠层峰值与模型开花期授粉胁迫几乎不变。2021年直接将每次原灌水减半，无需遗传算法，模型产量也仅比原DI低0.42%。
- 默认2.3m根域及深层土壤/初始含水假设影响亏缺灌溉外推。根深变化只作为独立假设诊断，不能当成新校准。
- 八个MCMC参数不包括根深及主要水分胁迫阈值/形状；原DI未触发气孔水分胁迫，原制度拟合不能独立验证亏缺灌溉响应。
- 2020年C1把灌水高度前置，最大事件约180mm。用户确认原84.88mm上限只是实测日程执行数值设置，不能当成设备能力；固定原上限只是受控诊断，不能凭此断言原接口错误。

## 已完成的对照

| 条件 | 2020减灌比例 | 2021减灌比例 |
|---|---:|---:|
| 原C1 | 44.19% | 57.80% |
| 保留原单次执行设置 | 42.88% | 57.75% |
| 再加季末不低于初始储水 | 12.38% | 27.38% |
| 同上，且季节实际ET匹配原DI的可行诊断点 | 11.06% | 26.82% |

前三组采用95%文献观测产量门槛，不是观测产量完全相同。最后一组是求根可行对照，不是最低灌水证明。储水底线是诊断比较条件，最终阈值应有农艺依据。保持原DI期末储水也不能自动当成唯一推荐约束。

## 不变条件与用户确认

四年MulchPct=75%、fMulch=0（关闭额外代码减蒸效应，不表示田间膜完好率0%）、Zmin/Zmax=0.30/2.30m；原上限仅保证实测日程完整执行，不是MCMC校准参数或实测硬件限制。原天气、ETo、初始含水、年别中央参数和原作物方程均保留。根深变体单独标注。实际ET是输出；等ET组只匹配季节总量，不强制每日ET相同。

详见 `tables/User_confirmed_common_settings.csv`、`verification/User_clarification_20261020.md`。0–1m初始水来自原论文图近似读取、深层来自ERA5-Land的来源边界也完整保留，未冒充实测表。

## 记录与复现

- `tables/All_daily_traces.csv.gz`、`All_layer_traces.csv.gz`：28个原条件回放场景的逐日/逐层记录。
- `Period_water_canopy_stress.csv`：五个模型日历时期的雨、灌、Tr、Es、储水、冠层与胁迫；不是四个优化决策窗口。
- `Period_soil_water_by_layer.csv`：四年DI/C1共960个时期×土层记录。
- `Root_depth_hypothesis_test.csv`：16行根深对照；原2.3m参考行复用原回放，另实际运行12个缩根情景，未重新校准。
- `constrained_runs/`：2020/2021×3种储水策略×2种子=12组，每组64个体×50代；38,400条实际模型评价，600份逐代X/F/G/CV文件。全部种群成员已与评价记录核对。
- `Constrained_replay_summary.csv`、`Constrained_daily_traces.csv.gz`及`Constrained_layer_traces.csv.gz`：6个已找到的最少灌水候选独立回放。
- `Equal_ET_fixed_management_diagnostics.csv`：6个季节实际ET匹配原DI的点；2020/2021在“同原DI期末储水”条件下采用原DI作已知可行对照。
- 原探索性的`ET_matching_diagnostic.csv`和`Scenario_summary.csv`中的`ET_matched_diagnostic`另有保留：2020年该探索点超出原单次数值上限，不用于本包最终受控结论；请以`Equal_ET_fixed_management_diagnostics.csv`和D09为准。
- `verification/`：原输出复现、未加速引擎对照、冻结文件哈希、完整评价检查和依赖版本。单个初始化日志竞争已独立重试，12组搜索完整；未修改作物方程。

代码依赖原仓库 `yuzhenwu920-afk/URP` 的 `DI_PHASE3_NEXTGEN_UPDATED`，基于父提交 `06f568294eaf86240f49140ef8e820b259c4f764`。原年别驱动与数据无需改动。设置 `URP_PROJECT` 为该目录绝对路径。Python依赖版本见 `verification/DEPENDENCY_VERSIONS.json`。

```bash
export URP_PROJECT=/absolute/path/to/URP/DI_PHASE3_NEXTGEN_UPDATED
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1
python code/run_mechanism_traces.py
python code/constrained_demonstration.py
python code/aggregate_and_replay_constraints.py
python code/match_ET_under_fixed_limits.py
python code/build_diagnostic_figures.py
python code/build_report_and_workbook.py
python code/verify_diagnostic_delivery.py
```

已有完整搜索会读取完成记录，不重复评价；要做新的科学实验请复制到新输出目录，保留本次记录。仅重生成图表、Word与Excel可从最后三步开始。新诊断为有限预算下找到的可行结果，不替代原正式100×100×5种子实验，也不证明全局最优或田间可实现性。

建议后续：核实根域与含水剖面、现场施灌能力、净/毛灌水及湿润体口径；按后茬和全年补蓄确定储水目标。若改动物理假设，要在所有方案中一致修改，再重校准MCMC并重做Sobol/优化，不能仅改优化曲线。
