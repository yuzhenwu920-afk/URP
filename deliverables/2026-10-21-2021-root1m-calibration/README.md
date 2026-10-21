# 2021年DI玉米：1m最大根深MCMC短链试跑

本轮**实际重新校准**，最大根深Zmax=1.00m、Zmin=0.30m；按用户指定每组**500步、10 walkers**，保留原代码4组独立ensemble与条件两阶段方法。两阶段共40,000个保存状态，非40,000个独立样本。旧四年结果和原MCMC文件未覆盖。

- [全部文件压缩包](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-root1m-calibration/URP_2021_Root1m_MCMC_Pilot_500x10_20261021.zip)
- [Word解析报告](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-root1m-calibration/URP_2021_Root1m_Pilot_Report.docx)
- [PDF报告](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-root1m-calibration/URP_2021_Root1m_Pilot_Report.pdf)
- [Excel数据表](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-root1m-calibration/URP_2021_Root1m_Pilot_Data.xlsx)
- [CC拟合图](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-root1m-calibration/P01_CC_fit_2021_root1m.png)
- [0至实际灌水量的产量响应图](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-root1m-calibration/P05_Yield_irrigation_0_to_actual.png)

## 主要结果

- CC：n=11，RMSE=0.03522，拟合R²=1−SSE/SST=0.99110，Pearson r=0.99656。
- 最终Y13=15.152156t/ha；实测15.86t/ha，差-0.707844t/ha（-4.463%）。内部似然靶值15.862沿用原代码，未混同文献显示精度。
- ET=639.465mm；文献626.81mm，差+12.655mm。
- 边界信号：WP_early所选值10.00839，贴近下限10；HI0=0.59798，贴近上限0.60。下1%范围内WP_early样本占37.05%，上1%范围内HI0样本占10.40%。详见完整边界表。
- 跨独立组匹配walker的保守Rhat范围=1.361—1.629，bulk ESS最小值=6.78。**正式收敛未通过**，不能宣称“无撞墙”。
- 曲线201点，实际灌水量严格从0到633.47mm；零灌水Y13=0.919271t/ha，终点Y13=15.152156t/ha，与新参数DI回放一致。

## 如何解释

这是用户要求“先看效果”的短链试验。原正式流程要求至少2000步，并同时满足Rhat<1.01、bulk/tail ESS≥400及自相关长度判据；本轮500步不足。后250步用于**明确标记的试跑摘要**，不是诊断确认的正式后验。所选点是这些状态中log posterior最高者，不是全局MAP。为完成短链测试，阶段二在第一阶段未正式收敛时仍继续，始终保留未收敛标记。

第一阶段拟合CC及原Tr/Es约束；第二阶段在阶段一所选点上条件拟合生物量和产量，不是8参数联合后验。CC和Yield都用于拟合，不是独立验证。生物量来自图件数字化，Sigma_assumed是假设而非实测SD；RS CC未进入似然。

阶段一交接点Y13=15.83564，阶段二兼顾生物量后Y13降为15.15216：生物量负log似然4.202→3.371、产量负log似然0.001→0.561，总损失降低。WP_late、HI及生物量约束存在取舍。在最终WP固定时把HI0设到0.60，Y13也仅15.20327；该上限复核点还比短链所选点的似然更高，进一步说明500步未充分探索。未为让结果好看而扩大HI上限或改写观测。

曲线是**原DI日期和各次比例不变、总水量从0到100%的固定比例剂量响应**，不是每个水量重新优化的NSGA-III帕累托前沿。横轴采用实际执行量；提前结束的低水点保留真实收获产量，收获后不再灌水，土壤水量账继续到共同日历末。零灌水仍保留143.32285mm季节降水和原初始水，不能人为设零产量。终点采用逐次DI合计633.47mm；论文表4-1为633.46mm，保留0.01mm差异。

地膜75%、fMulch=0、WetSurf=100%、AppEff=100%、天气/ETo、原初始水和土壤水力转换保留。fMulch=0仅关闭代码中额外地膜减蒸效应。保留2.4m水文网格以隔离根深变化；**根系动态上限确实为1m**，逐日记录已核验。深于1m的土壤属性和初始含水仍来自既有外推，不能冒充实测。

## 压缩包内容

- `figures/`：5组全英文图，每组600dpi PNG、PDF、SVG；Word逐图解析。
- `tables/`：CC配对、逐日生长、水量、201点响应及实际事件量、产量偏差、8参数边界与混合诊断、似然取舍与HI上限复核。
- `runs/`：8个独立ensemble检查点，500×10状态、log posterior、接受记录、原严格诊断、试跑后250步摘要和日志。
- `model_snapshots/`：原2021代码/输入和精确Numba物理内核；未改原代码中的根深，覆盖逻辑位于新试验代码，便于审计。
- `verification/`：根深/地膜核验、原/加速引擎输出一致性、终点与逐点水量守恒检查。
- `sources/`：文献相关DI表格页、来源哈希，非整本论文。
- Word、PDF、Excel、环境版本、MANIFEST.json及SHA256SUMS.txt。

## 复现

在Python 3.12独立虚拟环境安装`requirements.txt`。在解压后的`URP_2021_Root1m_Pilot`目录中运行：

```bash
export URP_PROJECT="$PWD/model_snapshots/DI_PHASE3_NEXTGEN_UPDATED"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1
export XDG_CACHE_HOME="$PWD/.cache" MPLCONFIGDIR="$PWD/.mplcache"
python code/run_pilot.py
python code/export_results.py
python code/plot_results.py
python code/build_report.py
python code/write_readme.py
```

原样检查点支持重复核验已完成的500步；若要新种子/新预算，复制到全新实验目录并修改参数，不能混用旧检查点合同。原程序的自适应5τ烧入/正式诊断同时保留，报告用的是另行标注的后250步试跑摘要。

`verify_and_package.py`为本次交付工作区打包器，含原工作区发布路径；科学复现不需要执行它。PDF由LibreOffice转换生成。软件和输入逐文件哈希、全部数字见包内记录。
