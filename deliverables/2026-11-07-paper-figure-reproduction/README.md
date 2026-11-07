# URP修订稿图表：PyCharm完整复现包 · 2026-11-07

[完整源码、数据、图片及核对结果（约70.3 MiB）](URP_PyCharm_All_Figures_Tables_Reproduction.zip) · [仅图表及图册（约7.4 MiB）](URP_All_Figures_Tables_Images.zip)

[中文PyCharm说明Word](URP_PyCharm_Guide_CN.docx) · [快速说明](START_HERE_CN.md) · [15幅矢量图册](URP_All_15_Figures.pdf) · [10张三线表](URP_All_10_Tables.pdf) · [逐图逐表代码索引](FIGURE_TABLE_INDEX.csv) · [核对摘要](DELIVERY_QA.json)

对应本次上传的《URP_Manuscript_CN_Updated_修订版.docx》：15个独立绘图脚本、10个独立表脚本、统一入口run_all.py，图表均由Python重新绘制，不把参考PNG作为绘图输入。英文图输出450 dpi PNG、PDF和SVG；表格另有CSV、Excel及可编辑Word。包内附带固定字体、固定依赖版本、20份原始MCMC检查点、61440条Sobol响应、五期优化解和逐日水量账，以及原模型代码和参考论文。

已完成：832项数值核对、328个上传稿表格正文单元格比较、四年8个前向情景重放（核对输出最大差为0）、干净Python环境及含中文/空格路径下复跑。25张PNG与交付基准逐像素一致，输入改动检测通过。解压后安装requirements.txt，在PyCharm运行run_all.py，再运行verify_reproduction.py --strict-pixels。

数据口径：表2的Es列澄清为校准目标，原数字保留；图10历史bootstrap区间按冻结统计表复绘，额外提供新固定seed的完整响应块重采样脚本。两阶段条件参数、模型结构和旧四窗口初始化来源分别保留，五期主图不混入后续1 m根深/不同fMulch条件试验。

本包图2严格对应上传稿中的定位及尺寸示意图。近期单独制作的AI辅助卫星排版图未混入本工程。

完整ZIP的INPUT_SHA256、CODE_SHA256、REFERENCE_RENDER_HASHES及DELIVERY_FILE_MANIFEST用于源数据、代码与输出一致性检查。田间数据来源和数字化不确定性依照原论文及输入字段记录，不把复现检查等同于新增独立田间观测。
