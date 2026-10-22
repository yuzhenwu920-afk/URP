# 四年五生育期多次灌溉优化交付（2026-10-22）

本次落实的用户设定是：**每个生育期最多3次灌水，允许零水量取消，实际次数由优化水量及日期确定**。四年分别计算，使用苗期、拔节期、抽穗期、灌浆期、成熟期五个年度生育期。每年15个可选事件，同时优化15个连续水量及15个整数日期。所有阶段均允许灌水；同日槽位合并计量。

## 先看哪些文件

- `documents/URP_Optimized_Every_Event_Schedule_20261022.docx`：逐年列出**每次日期、水量**及五期合计；有同名 PDF。
- `tables/URP_Five_Stage_Multi_Event_Results_20261022.xlsx`：年度指标、逐次日程、五期汇总、原始槽位、候选控制量、搜索过程及水量账本。
- `documents/URP_Five_Stage_Multi_Event_Optimization_20261022.docx`：方法、结果解析、英文图件和三线表；有同名 PDF。
- `figures/R03_Five_stage_multi_event_Pareto_4years_EN.*`：四年2×2前沿。其他图见 `FIGURE_GUIDE.md`。图件提供450 dpi PNG、矢量PDF及SVG。
- `tables/Optimized_every_irrigation_event.csv`：四年主候选全部正水量事件，按日期排列，保留未取整数值。
- `tables/Five_stage_totals_and_event_counts.csv`：每期总量、正水量次数、≥0.1 mm事件次数。
- `tables/All_selected_schedule_slots.csv`：基准、主候选、最高产候选的全部15个槽位，保留零量、取消和微量事件。
- `tables/Pareto_every_irrigation_event.csv.gz`：**全范围前沿每一个解**的逐次灌水日程，按 `Control_ID` 对应 `Full_range_Pareto_front.csv`。

CSV 为源数据；Word和图中文字有显示取整。主候选满足观测产量的95%门槛，取正式NSGA-III五种子最终种群可行非支配解并集中的最低实际灌水解。95%表示确定的产量水平门槛。

逐次日程中的 `Date` 是实际日历日期；内部日索引以播种日为0，源表的 `DAP` 沿用1起算模型日，因此播种日记录为1。报告据此标为“Model day (1-based)”，不与0起算的历时混用。

## 六个压缩包

1. `URP_FiveStage_MultiEvent_Results_20261022.zip`：报告、日程、表格、图件、全部本轮代码、冻结模型与输入、参考论文、校验记录。**不含全部查询与每代种群**，这些分年放在下列原始运行包中。
2. `URP_FiveStage_MultiEvent_Figures_20261022.zip`：全部英文图件、图注说明及主要配套数据。
3. `URP_FiveStage_MultiEvent_RawRuns_2019_20261022.zip`
4. `URP_FiveStage_MultiEvent_RawRuns_2020_20261022.zip`
5. `URP_FiveStage_MultiEvent_RawRuns_2021_20261022.zip`
6. `URP_FiveStage_MultiEvent_RawRuns_2022_20261022.zip`

后四包逐年保存13次搜索的所有查询、每代种群、收敛过程、运行身份与最终解。解压到同一父目录后，共用 `URP_Five_Stage_Multi_Event/` 根目录。包内同名元数据内容一致。SHA256SUMS和ZIP_MANIFEST提供下载校验。

## 固定条件与本轮变化

- 原四年已保留MCMC样本的八参数均值固定，未重新进行MCMC或Sobol。不是后续2021年1 m根深/地膜系数试验的混合结果。
- 使用相同年度逐日气象、初始水分和土壤剖面，`MulchPct=75%`、`fMulch=0`、`Zmin=0.30 m`、`Zmax=2.30 m`、模拟剖面2.4 m，WetSurf及AppEff均为100。
- `fMulch=0`是本轮沿用的历史模型结构设置；其含义是原生地膜减蒸项关闭。
- 生育期依据王尚今（2023）表2-3。可行日期为文献生育期与原模型实际执行日历的交集，见 `Five_stage_schedule_bounds.csv`。采用该年已知天气进行回顾性日期优化。
- 季节总量分别不超过445.27、559.76、633.47、404.84 mm。原日程和旧四窗口候选可在新空间精确表示，两算法均以这些日程作为公开初值。
- 旧模型按事件顺序分成四组；新模型增加了生育期内的日期和事件分配自由度。差异是控制空间扩展的共同结果。
- 目标是产量最大、实际季节灌水量最小，正式搜索设95%观测产量门槛；补充全范围搜索移除该门槛。按完整固定年度日历核算水分账本。
- 本轮没有额外设置单次硬件上限、最小间隔、季末储水下限或次数成本。管理器中的执行上限跟随候选日程，实际最大单次水量与最短间隔在结果表中报告。
- 连续优化可能产生微小正水量。源表保留全部正水量事件；≥0.1 mm计数仅是便于阅读的统计，没有替换或删除任何优化控制量。

## 搜索预算与原始记录

NSGA-III与NSGA-II各采用100个体×100代×5种子×4年，名义40万次目标查询；全范围NSGA-III采用80个体×60代×3种子×4年，57,600次。

实际总查询数为**457,596**。首个种子初始化的重复控制量经规范化去重后为99个，之后仍完成99代、每代100个；每年该种子为9,999次。最初的严格预算断言在保存第100代后报错，已从原始检查点恢复完成状态及前沿，没有重算、补行或替换模型结果。后续种子初始化补足100个不同控制量。原运行器、恢复脚本、错误与恢复记录均保存。后续采用修订运行器全新复算，名义预算会得到457,600次，因此不会逐字节复现首个种子的9,999次历史。

`Objective_queries` 是算法目标查询次数，包含精确缓存命中；`Actual_model_calls` 是搜索内缓存未命中的前向计算次数。两者分别报告。预检、前缀状态建立、回放和独立方程核对单独计数，没有混入搜索预算。状态缓存只复用同一年度、同一输入下的完全相同计算；未使用代理模型或拟合插值替代前向模型。

## 数据与图件核对

`verification/FINAL_DELIVERY_CHECK.json` 汇总所有查询的日期界限、每期次数、总水量、每日与季节水量闭合、冻结源文件哈希，以及最终报告版面核对。`FRESH_UNACCELERATED_CHECK.json` 在新的进程中以未加速原始日方程核对各年基准、主候选、最高产候选。主候选的逐次合计、五期合计与模型实际灌水量相互核对。

减灌量按同一水量平衡拆为ET差、季末储水差和其他损失差。季末储水差同时包含减少基准日程积水及消耗初始储水等成分，解释时结合每日储水曲线和起末储水量。精确数值见年度比较表与水量账本。

## 复算

建议Python 3.12；本次版本见 `requirements.txt`。LibreOffice用于把Word转为PDF，中文字体使用Noto Serif CJK SC。

在**新目录**解压结果包，保留 `source/` 与 `code/` 结构。复制源代码到新的空结果目录可避免覆盖本次原始运行。准备 `tables/`、`verification/`、`runs/`、`figures/`、`documents/` 后执行：

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
.venv/bin/python code/preflight.py
.venv/bin/python code/run_optimization.py
.venv/bin/python code/aggregate_results.py
.venv/bin/python code/verify_fresh_equations.py
.venv/bin/python code/make_figures.py
.venv/bin/python code/build_report.py
soffice --headless --convert-to pdf --outdir documents documents/*.docx
.venv/bin/python code/check_and_render_delivery.py
```

运行器对已存在的运行状态采取保护；它不会自动覆盖本次结果。首次预算恢复只用于本次原始历史的簿记，新的正常运行无需执行 `recover_initial_budget_accounting.py`。两份中断的早期控制空间试跑未混入本交付，范围调整保存在 `SCOPE_CHANGE.json`。

## 参考文献

王尚今. 不同灌溉方式下覆膜玉米田水热氮传输及作物生长的观测与模拟[D]. 北京：中国农业大学，2023.

Deb K, Pratap A, Agarwal S, Meyarivan T. A fast and elitist multiobjective genetic algorithm: NSGA-II. IEEE Transactions on Evolutionary Computation, 2002, 6(2):182–197. doi:10.1109/4235.996017.

Deb K, Jain H. An evolutionary many-objective optimization algorithm using reference-point-based nondominated sorting approach, Part I: Solving problems with box constraints. IEEE Transactions on Evolutionary Computation, 2014, 18(4):577–601. doi:10.1109/TEVC.2013.2281535.
