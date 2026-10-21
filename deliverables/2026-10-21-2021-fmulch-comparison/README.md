# 2021年fMulch三情景条件重校准与NSGA-III试验

- [全部文件压缩包](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-fmulch-comparison/URP_2021_fMulch_050_075_085_20261021.zip)
- [Word解析报告](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-fmulch-comparison/URP_2021_fMulch_Report.docx)
- [PDF解析报告](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-fmulch-comparison/URP_2021_fMulch_Report.pdf)
- [Excel核心数据](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-fmulch-comparison/URP_2021_fMulch_Data.xlsx)
- [产量—灌水量比较](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-fmulch-comparison/T01_Yield_irrigation_comparison.png)
- [NSGA-III前沿比较](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-fmulch-comparison/T03_all_NSGA3_front.png)

## 实际完成的计算

固定2021年原数据、最大根深1m、75%地膜覆盖，只改变fMulch结构为0.50/0.75/0.85，并分别重校准原有作物参数。每情景两阶段，每阶段4组独立ensemble×10walkers×500步，共120,000保存状态，不能当作独立有效样本。
每情景NSGA-III运行3种子×100个体×100代，共90,000次实际模型优化评价。双目标最大化Y13、最小化实际I，原7个日期和同窗口比例保留；4窗口总量可变。无400mm目标、无产量门槛、无虚构不确定性第三目标。
输出18组英文图，每组600dpi PNG/PDF/SVG。包含三个主题：完整0—633.47mm剂量响应；5灌水量的逐日水分胁迫与CC；NSGA-III最佳已找到前沿。另含拟合、参数边界/混合、土壤储水、400mm结构交叉、少灌量守恒分解、同总量不同分配对照及季末储水后筛选。

## 关键数值

| fMulch | CC RMSE | 原DI模型Y13 t/ha | Es mm | ET mm | 达95%实测产量的最少已找到I mm |
|---:|---:|---:|---:|---:|---:|
| 0.50 | 0.0349 | 15.170 | 57.35 | 618.90 | 319.11 |
| 0.75 | 0.0370 | 15.444 | 49.90 | 590.37 | 282.72 |
| 0.85 | 0.0360 | 15.487 | 45.71 | 600.10 | 287.53 |

文献2021年DI实测Y13=15.86t/ha、ET=626.81mm；95%产量=15.067t/ha。原Es=78mm为近似重建的目标，Tr=548.81为ET−Es，不是新增独立测量。原逐次灌水合计633.47mm，文献季总633.46mm的0.01mm差异保留。

**不能把“匹配自身模型产量”写成“达到文献完整实测产量”。**详见共同门槛表与NOT_FOUND标记。fMulch增大增强减蒸，固定参数时通常使缺水较轻；重校准后的平台移动还包含参数补偿，不能预设0.50一定较0.85合理，也未为符合400mm人为调曲线。
**500步短链未正式收敛**；WP_early/HI0等存在边界信号，所有短链分位数及固定选点前沿均为调试结果。没有传播完整参数后验不确定性。不得据此给出已验证田间灌水推荐。

## 固定条件和审计口径

Zmin=0.30m、Zmax=1.00m；原2.4m水力域及24×0.1m分层；MulchPct=75%、WetSurf=100%、AppEff=100%，天气/ETo、土壤质地与水力转换、原播前θ均不变。fMulch不代表地膜完好率。
当前云端历史模型实际fMulch=0；另一个工作位置所说0.85作为本次新对照结构重跑。历史f0结果保留，只作参照；用户提供2022年的剖面未作为本次2021年的实测。
季总计划≤633.47mm。原单次/季总量保护随候选最大事件/总量+0.10mm设置，不是已知设备能力；候选最大单次及是否超过原实测114.8mm均保存。提前结束后取消后续灌水，水量账延续到共同日历边界。
储水后筛选要求季末0—1m不低于本情景DI−0.01mm，仅是已评价点的子集，不是另一次约束优化；0.01mm为数值报告精度而非实测误差。深层水单列，无1m以下直接根系吸水。初始水仍为原近似重建，包含0.9—1.2m混合来源，不排除其不确定性。

## 包内目录

- figures：全部英文PNG/PDF/SVG；FIGURE_REGISTRY逐图数据源和中文解读。
- tables：全部拟合、响应、90,000次评价gzip CSV、前沿、跨结构候选复算、逐日θ/水量/胁迫原始轨迹；Excel含完整核心表与15组比例日程逐日数据，原始CSV另含9组优化及同总量轨迹，四窗口账本完整保存。
- calibration：24个500步10walkers原始NPZ检查点、随机状态、完整链CSV、保留段、诊断和选点。
- optimization：9次搜索，各100代X/F/G/CV、每次真实模型评价及配置；与tables合并表对应。
- sources/model_snapshots：历史f0参照、原输入和未经改写的2021年驱动及数值内核。
- verification：原方程与加速结果一致性、未加速最终复算、90,000条逐代种群映射、前沿非支配及水量闭合检查。
- Word/PDF报告、Excel数据、MANIFEST.json和SHA256SUMS.txt。

## 复现

使用Python3.12，安装requirements.txt，在解压后的URP_2021_fMulch目录运行：

```bash
export URP_PROJECT="$PWD/model_snapshots/DI_PHASE3_NEXTGEN_UPDATED"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1
export XDG_CACHE_HOME="$PWD/.cache" MPLCONFIGDIR="$PWD/.mplcache"
python code/preflight.py
python code/run_calibrations.py
python code/export_scenarios.py
python code/factorial_checks.py
python code/run_optimizations.py
python code/aggregate_comparison.py
python code/plot_comparison.py
python code/build_report.py
```

原MCMC检查点验证合同和随机状态，可恢复相同配置；已完成NSGA运行不重复追加。改变预算、种子或物理设置须用新实验目录并移走旧输出，不能混用。PDF使用LibreOffice生成。package_results.py含本工作区交付路径，为发布脚本，非科学复现所需步骤。

参考：王尚今（2023）DI原表、用户提供2021年MCMC原代码及AquaCrop-OSPy3.1.0；fMulch公式见随包源代码与https://aquacropos.github.io/aquacrop/entities/。原分支旧交付与main均不覆盖。
