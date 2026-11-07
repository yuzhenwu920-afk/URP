# URP当时使用的原始绘图代码与数据

这是原码收集包。`original/` 中的源文件及数据从既有URP归档逐字节复制，未改写绘图函数，未为本次打包重新计算或重新出图。来源提交、原路径与SHA256见 `ORIGINAL_FILE_MANIFEST.csv`。

## 在PyCharm运行

1. 解压后用PyCharm打开 `URP_Original_Plot_Sources` 文件夹，使用Python 3.12。
2. 在Terminal执行：`python -m pip install -r requirements.txt`。
3. 右键运行 `RUN_ORIGINAL_PLOTS.py`。结果在 `outputs/figures`，主图15组，每组PNG、PDF、SVG。原程序额外绘制的4张分年前沿放在子目录 `extra_original_year_panels`。
4. 表格运行 `RUN_ORIGINAL_TABLES.py`，输出原始CSV和十张可编辑Word三线表。

两个 `RUN_` 文件仅负责定位文件夹、调用原函数和对应论文文件名，不重写数据统计或绘图逻辑。它们不运行MCMC、不重新求Sobol，也不重新优化。`reference_images` 内就是当时已生成的15张原PNG，供你们自己重跑后对照。

## 对应的原程序

- 图1—10：`original/paper/code/nonoptimization_figures.py` 中的 `workflow`、`site`、`environment`、`cc`、`biomass`、`parameters`、`pooled`、`water`、`sobol`、`yield_ci`。
- 图11—15：`original/optimization/code/make_figures.py` 中的 `pareto`、`balance`、`event_calendar`、`stage_totals`、`convergence`。
- 表1—10：`original/paper/code/build_current_documents.py` 的 `data_tables` 及 `legacy_renderer.py` 的三线表函数。

原始 `nonoptimization_figures.py` 还含旧四窗口辅助函数，其原有 `main()` 会绘制部分历史图。推荐用根目录入口，它只按本次Word的15幅主图顺序调用相应原函数，并选择五生育期结果。

所有对应CSV及定位图GeoJSON均已附带。主模型仍按原记录fMulch=0、Zmax=2.30 m；后续2021年条件试验没有混入主图。图2按本次上传Word保留定位与尺寸示意，不混入近期AI辅助卫星排版图。

数据口径原样保留：原表2的“Es,obs”列实际对应归档代码中的近似重建Es校准目标，后续论文表述宜澄清；本原码包没有直接改动它。图10读取当时保存的bootstrap区间源表，绘图本身不重新抽样。

## 来源

- 原文稿/非优化绘图源码：`c6649028a4cbb37c5f587921fb4887880c34ddd6`。
- 五生育期逐次灌溉优化绘图源码：`20f1616556f5aeb79329b7ead22faa28f9fcda6a`。
- 本次上传Word原样附在 `reference/`。

原始完整科研环境依赖文件在各自原目录，根目录requirements只列复绘与表格导出所需依赖，普通复图无需安装AquaCrop。
