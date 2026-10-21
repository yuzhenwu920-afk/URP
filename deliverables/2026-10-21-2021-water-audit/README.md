# 2021年水分胁迫与储水量图，以及含水量审计

沿用2021年最大根深1m、500步/10walkers短链试跑选定参数；本轮没有重新MCMC，没有新做NSGA-III搜索。天气/ETo、地膜75%和fMulch=0、灌水日期及原比例均固定，比较0、316.735、400、475.1025和633.47mm五种实际季节灌水量。

- [完整压缩包](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-water-audit/URP_2021_Water_Stress_Storage_Audit_20261021.zip)
- [图一：水分胁迫及冠层](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-water-audit/W01_Water_stress_and_canopy.png)
- [图二：根域与根域以下储水](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-water-audit/W02_Root_domain_and_deep_storage.png)
- [Word审计与逐图解析](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-water-audit/URP_2021_Water_Audit_Report.docx)
- [PDF报告](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-water-audit/URP_2021_Water_Audit_Report.pdf)
- [Excel全部数据表](https://github.com/yuzhenwu920-afk/URP/raw/refs/heads/delivery/urp-review-20261015/deliverables/2026-10-21-2021-water-audit/URP_2021_Water_Audit_Data.xlsx)

## 两图怎样读

**图一**：四面板分别为冠层扩展、气孔和衰老缺水系数，以及冠层覆盖率。系数1表示对应缺水限制未触发，越小限制越强，不能直接当成百分比减产。系数来自原模型真实函数调用；气孔采用当前蒸腾模块实际使用的sto_lin。仅显示明确过程窗口；未计算或生长结束后的缺失值不补为1。DI的田间CC点只用于原DI比较。

**图二**：上图固定0—1m土层储水，下图单独显示1—2.4m相对初始储水变化。虚线FC/WP是原模型水力转换值，不是本轮实测。0—1m是统一比较域，根从0.3m动态增长；日末状态标在对应次日零时，并保留4月27日模拟前初值。

每图有600dpi PNG、PDF、SVG，以及可直接复图的W01_Figure_source_data.csv、W02_Figure_source_data.csv；Excel包含这两表及全部原始逐日/分层/函数调用记录。

## 审计发现

1. 400mm情景Y13=15.04499t/ha，ET=635.836mm；仅2个有效蒸腾日气孔Ks<0.95。75% DI和原DI的气孔Ks<0.95日数均为0。扩展系数在早期仍可下降，接近CCx时不一定产生同等比例冠层损失。
2. 0—1m初始储水324.9675mm；模型FC储水300.3mm、WP储水96.9mm。净高于FC24.6675mm；逐层正超额合计33.2mm，二者含义不同。
3. 原初始水不是原始表列播前观测：浅层来自图3-9/3-10近似重建，深层ERA5。0.9—1.2m单元已混合来源，再分为0.1m格点时沿用平均θ=0.224675，因此根内最后0.1m同样含混合来源。全剖面水量守恒不能替代空间来源核验。
4. 400mm比原DI少灌233.47mm，但ET只少约3.63mm，季末0—1m储水少约69.46mm、1—2.4m储水少约160.40mm。少灌不能直接写成同幅度节约耗水。
5. 截短水文计算域至1.1m（1m根区+0.1m无根缓冲层），五情景Y和ET完全一致。深层存水在浅域变为较多底排水；原2.4m域DeepPerc=0不表示没有水越过1m根底。
6. 根内初始θ减0.03m³/m³（少30mm）时，400mm情景产量15.04499→15.00556t/ha；逐层截至模型FC时为15.03325。平台不能仅归因于小幅初始水偏高。这些是假设敏感性情景，不是测量置信区间或已认可修正。

母版MCMC仍未正式收敛、WP_early与HI0仍有边界信号，亏缺水量下缺少独立观测验证。数值水量账闭合只说明模型记账一致；不能证明含水率来源、胁迫阈值和400mm灌水定额已获田间认可。

## 文件与复现

- `figures/`：两组图，各PNG/PDF/SVG。
- `tables/`：每图简表、740条逐日状态、17760条分层记录、逐次胁迫调用、源资料审计、1.1m域对照和20个初始水假设回放。
- `sources/`：上一轮参数与诊断，原文献关键页及来源哈希。
- `model_snapshots/`：原2021代码/输入及精确数值内核。
- `verification/`：观察器不改变输出、根深/地膜、分域水量账及未加速回放核验。
- Word、PDF、Excel及完整SHA256清单。

在Python3.12虚拟环境安装requirements.txt，解压后从URP_2021_Water_Audit目录执行：

```bash
export URP_PROJECT="$PWD/model_snapshots/DI_PHASE3_NEXTGEN_UPDATED"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1
export XDG_CACHE_HOME="$PWD/.cache" MPLCONFIGDIR="$PWD/.mplcache"
python code/run_water_audit.py
python code/plot_water_audit.py
python code/build_water_report.py
python code/write_readme.py
```

`package_water_audit.py`是本工作区交付打包器，含发布目录，不是科学复现所需步骤。PDF由LibreOffice生成。旧校准与六包不覆盖；本轮新加独立交付目录。
