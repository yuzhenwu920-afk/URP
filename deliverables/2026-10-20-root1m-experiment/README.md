# 最大根深1m · 四年DI玉米优化试验

本次将2019—2022年玉米Zmax统一由2.30改为1.00m，Zmin保留0.30m，重新运行NSGA-III。原MCMC中央参数、原DI灌水日期和窗口内比例、原天气/ETo、初始含水与地膜设置保留。**本轮没有在1m根深下重校准MCMC，是根深单因素条件试验。旧结果与旧六包不覆盖。**

- [完整压缩包](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-20-root1m-experiment/URP_Root1m_FourYear_Experiment_20261020.zip)
- [四年合并产量—灌水量图](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-20-root1m-experiment/R1_01_Four_year_yield_irrigation.png)
- [四年2×2帕累托前沿图](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-20-root1m-experiment/R1_02_Pareto_fronts_2x2.png)
- [可编辑Word报告](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-20-root1m-experiment/URP_Root1m_FourYear_Report.docx)

## 四年结果

| 年份 | 1m原DI模型产量t/ha | 最高找到产量t/ha | 零灌水产量t/ha | 匹配1m原DI产量的最少已找到灌水mm |
|---|---:|---:|---:|---:|
| 2019 | 16.543 | 16.571 | 5.186 | 322.11 |
| 2020 | 16.433 | 16.433 | 4.475 | 400.48 |
| 2021 | 14.962 | 14.983 | 1.255 | 309.44 |
| 2022 | 13.640 | 13.707 | 4.580 | 302.72 |

“最高/最少”均指本次有限搜索内已找到的结果，不证明全局最优；“匹配1m原DI模型产量”不等于匹配文献实测产量。95%观测及完整观测产量目标的找到/未找到状态见Target_feasibility.csv。

## 文献与输入

王尚今（2023）《不同灌溉方式下覆膜玉米田水热氮传输及作物生长的观测与模拟》，中国农业大学硕士学位论文。

- DI土壤：表2-1，PDF第19页/正文第9页，六层0—100cm砂粉黏组成。已逐层核对原模型，未混用BI。
- DI灌水：表2-3，PDF第21页/正文第11页；2019/2020各8次、2021年7次、2022年5次。逐次总量445.27、559.76、633.47、404.84mm。2021表4-1总量633.46mm与逐次合计差0.01mm，保留并注明。
- DI观测产量及ET：表4-1，PDF第63页/正文第53页。观测与模型结果分别保存。
- 表5-2（PDF第68页/正文第58页）WHCNS校准Rmax=100cm可作试验依据，但它不是直接测得的AquaCrop根深。

土壤水力参数保留原AquaCrop由DI质地转换的FC/WP等量，没有把WHCNS的van Genuchten参数未经说明混入AquaCrop。原重建初始含水及其来源局限保留，不冒充文献表格中新获得的播种日实测剖面。

## 计算设计与边界

4年×5种子（31/73/109/151/199）×100个体×100代，**200,000次实际优化评价、2,000份逐代X/F/G/CV**。只有两个目标：最大化Y13、最小化实际季节灌水。保留原季总水量预算；为得到全范围曲线，未新增产量门槛、季末储水底线或现场事件能力约束。原MaxIrr/MaxIrrSeason是执行日程的数值上限，不是设备能力。

主试验仅改变根深，保留原2.4m水文网格；逐层验证1m以下取水为0。另以1.1m最浅水文域（含AquaCrop要求的0.1m非根区缓冲）独立复核原DI、零灌水和全部最终前沿点，差异见verification/ALL_FRONT_SHALLOW_DOMAIN_CHECK.json。根域储水以0—1m单列，排水以1.1m边界单列，避免把根域外存水全部称为作物可用储水。

前沿由每年全部50,000条实际评价的非支配并集得到，不仅取最后一代。曲线点均有模型响应记录，未用平滑拟合补造交点。随机种子范围不是置信区间。末期产量/水量变动也可能包含储水、深渗和原参数在新根深下的拟合变化，不能直接当成田间推荐节水率。

## 文件位置

- Word/PDF：URP_Root1m_FourYear_Report，逐图中文解析及英文图注。
- Excel：URP_Root1m_FourYear_Data.xlsx，四年前沿主要列、目标可达性、原DI表、灌水方案与收敛数据；完整精度全部列另见CSV。
- figures：6组英文图，600dpi PNG、矢量PDF/SVG；R1_01与R1_02为用户要求的两组主图。
- tables：全部前沿、各种子前沿、相同比例1m/2.3m响应、逐日/逐层记录、选点日程及水量账。
- runs：20组真实搜索全部评价和2,000份逐代种群。
- sources：文献关键页截图、文本、来源哈希，原2.3m前沿仅作为初始控制向量，全部在1m下重新评价。
- verification：DI输入核对、未加速原引擎8组逐日对照、全部代记录核对、最浅域逐点检查、冻结输入哈希。

初始化预检发现重复零灌水锚点导致首代99个体，已停止并保留于正式结果以外；去重后正式20组均核对为100个体×100代。该预检未用于最终图表，作物方程未改。

## 复现

依赖原仓库DI_PHASE3_NEXTGEN_UPDATED，父提交ed25a3ebaec23d37f84bb91117fe0bfd8be804a9；Python依赖版本见verification/DEPENDENCY_VERSIONS.json。设置URP_PROJECT为该目录绝对路径，按以下顺序运行。新实验应使用新输出目录，已完成搜索不覆盖。

```bash
export URP_PROJECT=/absolute/path/to/URP/DI_PHASE3_NEXTGEN_UPDATED
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1
python code/prepare_thesis_inputs.py
python code/run_root1m_optimization.py
python code/reference_and_validation.py
python code/check_hydrological_boundary.py
python code/aggregate_root1m_results.py
python code/check_all_fronts_shallow_domain.py
python code/summarize_rootzone_water.py
python code/plot_root1m_figures.py
python code/build_root1m_report.py
python code/verify_root1m_results.py
```

若以后正式采用1m模型，应在该结构下重新校准MCMC阶段1/2并核查拟合与链诊断，再重做Sobol和优化；本试验不将旧后验冒充1m模型新后验。
