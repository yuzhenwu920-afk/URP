# 2021年NSGA-III帕累托前沿：1m根深校准试跑参数

基于上一轮2021年最大根深1m、500步/10walkers条件两阶段MCMC试跑选定参数和含水量审计，本轮实际运行NSGA-III。3个随机种子各100个体、100代，共**30,000次实际模型优化评价**。三代遗传指NSGA-III算法，不是只运行3代。

- [完整压缩包](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-nsga3/URP_2021_NSGA3_Pareto_20261021.zip)
- [主帕累托前沿图](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-nsga3/N21_01_Pareto_front.png)
- [季末储水资格对照图](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-nsga3/N21_02_Storage_qualification.png)
- [Word解析报告](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-nsga3/URP_2021_NSGA3_Report.docx)
- [PDF报告](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-nsga3/URP_2021_NSGA3_Report.pdf)
- [Excel全部数据](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-nsga3/URP_2021_NSGA3_Data.xlsx)

## 结果

- 主前沿：全部30,000评价的非支配并集，共1,437点；最高找到Y13=15.209652t/ha。
- 原DI：633.47mm，模型Y13=15.152156t/ha；文献实测15.86t/ha。本次未找到达到实测15.86的候选，不能改称“达到实际产量”。
- 匹配原DI**模型产量**的最少已找到灌水为342.946mm，Y13=15.154031t/ha；比原DI多耗0—1m根层储水126.653mm。大的少灌比例不等于同等耗水节约。
- 从已评价候选中筛出季末0—1m储水近似不低于原DI的子集后，匹配DI模型产量的最少已找到灌水为475.103mm，Y13=15.178829t/ha。**这是后筛选子集前沿，不是另一次带储水约束的充分优化。**
- 子集储水基准为原DI模型季末276.493445mm，比较允许0.01mm报告精度容差（不是实测误差界限）。共有150个已评价候选合格、子集前沿17点；该子域搜索覆盖有限。

## 设计及边界

**两个目标**：最大化13%含水率籽粒产量，最小化实际季节灌水量。NSGA-III可用于双目标，未人为增加无依据的不确定性第三目标。未加95%产量门槛，保留零水和低水区；未在主搜索新增季末储水约束。

**四个控制**：按原7次DI事件分为2/2/2/1次的四窗口总量，日期及同窗口原比例不变。窗口不是重新识别的四个生育期。计划总量≤633.47mm；实际灌水用于目标，提前收获后取消后续灌水，土壤水量账继续到原日历末。

Zmin=0.30m、Zmax=1.00m，MulchPct=75%、fMulch=0、WetSurf=100%、AppEff=100%，原天气/ETo、初始水及水力转换固定。原MaxIrr/MaxIrrSeason随候选最大事件/季总量加0.10mm，确保日程执行，不是已知设备能力；本轮未新增硬件单次上限，最大事件量已保存。

种子31/73/109；100条二维Das–Dennis方向；SBX概率0.9/η15；PM个体概率1、变量概率0.25/η20。初始锚点（零水、原DI、部分同比例响应等）均按当前参数实际重算。主前沿使用所有种子、所有代的实际评价，不只取最终种群。

主图前沿颜色为季末0—1m储水，不是第三目标；灰虚线是固定比例减灌响应。原DI可能被支配，前沿不强行延长到633.47mm；模型基准与实测参照分开标记。几何示意点只取前沿端点归一化后的形状特征，可能产量很低，**不是农业推荐点**。

母版MCMC仍未正式收敛，WP_early和HI0仍有边界信号；初始含水有图件近似重建与0.9—1.2m混合来源。前沿是固定试跑参数下有限搜索的最佳已找到结果，未传播全部参数/输入不确定性，也未获亏缺灌水田间独立验证。

## 文件

- `figures/`：主前沿、储水后筛选对照、三种子稳定性共3组图，每组600dpi PNG、PDF、SVG。
- `tables/`：主前沿、储水合格子集前沿、目标可达性与选点、实际逐次灌水、选点逐日结果、完整30,000行评价；Excel亦包含全部评价。
- `runs/seed*/`：每次评价、100代X/F/G/CV、进度、历史、种子前沿与配置。
- `sources/`：上一轮参数/诊断、固定比例响应和含水审计基准。
- `model_snapshots/`：原2021代码/输入及精确内核；`verification/`包含逐代种群与实际评价匹配、前沿非支配性及未加速回放检查。
- Word/PDF解析、环境版本、MANIFEST和SHA256完整清单。

## 复现

在Python3.12虚拟环境安装requirements.txt，于解压后的URP_2021_NSGA3目录执行：

```bash
export URP_PROJECT="$PWD/model_snapshots/DI_PHASE3_NEXTGEN_UPDATED"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1
export XDG_CACHE_HOME="$PWD/.cache" MPLCONFIGDIR="$PWD/.mplcache"
python code/run_nsga3.py
python code/aggregate_nsga3.py
python code/plot_nsga3.py
python code/build_nsga3_report.py
python code/write_readme.py
```

已完成run.json避免重复追加；更改搜索预算或种子应使用新目录。package_nsga3.py为本工作区发布打包器，含固定交付路径，不是科学复现所需步骤；PDF由LibreOffice生成。旧校准、含水审计及原六包未覆盖。

文献观测来自王尚今（2023）表4-1。逐次DI灌水633.47mm与该表633.46mm相差0.01mm，保留原逐次表精度。
