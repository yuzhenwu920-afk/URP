# URP论文15幅图、10张表：PyCharm复现包

本包逐一对应您上传的《URP_Manuscript_CN_Updated_修订版.docx》，不是把截图重新保存。图1—15均由Python绘制；15个独立图脚本和10个独立表脚本位于 `figure_scripts`、`table_scripts`，可以逐个在PyCharm右键运行。

## 先完成这四步

1. 把整个压缩包解压到普通文件夹，在PyCharm中打开 `URP_Paper_Figure_Reproduction` 根目录。不要只复制某一个 `.py`；代码需要相邻的 `data` 和 `assets` 文件夹。
2. 建立64位Python 3.12虚拟环境。当前验证环境为Python 3.12.14。
3. 在PyCharm底部Terminal执行：`python -m pip install -r requirements.txt`。
4. 右键运行根目录 `run_all.py`。它先验证来源并重算关键统计量，再输出15幅图和10张表。当前机器一次完整运行约半分钟，个人电脑速度会有所不同。

完成后运行：`python verify_reproduction.py --strict-pixels`。数值核对、328个论文表格单元格比较及25张PNG的像素核对写入 `outputs/validation`。

## 结果在哪里

- `outputs/figures`：15幅英文图，每图PNG 450 dpi、矢量PDF、路径化SVG以及数据/代码来源JSON。
- `outputs/tables`：10张英文三线表，每表CSV、Excel、PNG、PDF、SVG以及来源JSON。
- `outputs/URP_All_10_Tables.xlsx`：十张表的汇总工作簿。
- `outputs/derived`：从原链、原始Sobol响应、配对点、逐日水量账及优化解重算的绘图数据。
- `FIGURE_TABLE_INDEX.csv`：每幅图、每张表对应的独立脚本和数据文件。
- `reference`：原样保存的上传文稿、归档原图、原文表格和王尚今论文。

## 单张运行示例

```text
python figure_scripts/figure_04_cc_calibration.py
python figure_scripts/figure_11_five_stage_pareto_fronts.py
python table_scripts/table_05_calibration_performance.py
python run_all.py --figure 4 --figure 5
python run_all.py --table 7
```

独立脚本也会先进行完整数据核对。文件路径依据项目位置确定，不依赖PyCharm的Working directory；不需要更改您电脑的用户名或盘符。

## 固定版本与跨电脑一致性

图内字体统一使用随包附带的DejaVu Sans；使用Agg绘图后端、固定配色、字号、布局和英文月份。所有用于论文的散点和微量正水量事件都保留，不通过删点、人工平滑或修改排序让图片变好看。

输入文件的SHA256列于 `INPUT_SHA256.json`；源代码列于 `CODE_SHA256.json`；本次基准PNG像素列于 `REFERENCE_RENDER_HASHES.json`。同一固定环境下可以检查像素完全一致。不同操作系统的底层字体/抗锯齿库仍可能造成少量边缘像素差异；报告将像素差异和数值差异分开列出，不把它们混为一谈。

`verify_reproduction.py --strict-pixels` 对任何像素差异返回失败；不带该参数时保留差异清单供排查。输入被改动时，无论是否启用严格像素模式，都会停止数据核对。哈希和固定环境证明文件一致性、计算可追溯性；田间观测来源仍需以论文、原始记录及数字化说明为依据。

## 本次真正复核的内容

- 20份原始MCMC完整检查点，按各年度各阶段原预热截取，重新计算8参数的均值和经验区间；不混合时间顺序来改写ESS。
- 48个CC配对点、37个生物量配对点与原始输入逐点对应；重新计算R²cal、RMSE、籽粒产量相对偏差及汇总回归。
- 原始LAI按原公式换算CC；原始数字化生物量保留读图不确定性与“用于校准”的来源字段。
- 四年实际执行日期内的降水和经审计ETo-B，不把上传气象文件的另一列ETo替代进图3。
- 四年、三个N=512随机化序列，共61440条模型响应，按完整Saltelli响应块重算S1/ST及四年均值。
- 42条原精度正水量灌溉事件；原始微量水量不强制删掉，每期0—3次的限制和阶段合计逐一核对。
- 八份逐日水量账重新闭合，原DI与五期主候选的减灌差额重新分解。
- 正式最终种群解重新计算并集超体积及最低灌水量；40组最终代超体积与4000条逐代记录中的末代对照。
- 10张表共328个正文单元格与上传Word逐格比较；模型数值不因排版发生更改。

## 两点请在论文中保留准确口径

1. 表2原写 `Es,obs` 的76、79、78、81 mm，在归档代码中是近似重建的Es校准目标。本包把列名改为 `Es target`，数值原样保留，避免把它们描述为本次独立实测。
2. 图10原有bootstrap区间保留为有哈希的冻结统计量，因此默认重绘与论文一致。原历史bootstrap随机状态没有随源表完整留存。额外脚本 `recalculate_sobol_bootstrap.py` 提供新的固定seed完整响应块重采样，输出到独立文件夹，便于方法复核；它不覆盖原图区间，新抽样的区间宽度可能略变。

## 图2与最近卫星排版图的区别

这次严格对应上传Word中的图2：左为冻结GeoJSON绘制的研究区定位，右为400 m×200 m尺寸示意图，注明方向为示意。它不使用AI生成图，也不假定未知的田界。近期单独制作的AI辅助卫星排版图没有混入这个复现工程。如后续换成真实卫星截图，应把未经过生成式编辑的原始图片及其署名作为输入素材保留，并用Python直接拼接。

## 可选：重放四年原模型

普通复图不需要安装AquaCrop，也不会重新抽样或重新寻优。如果希望进一步核对前向模拟，执行：

```text
python -m pip install -r requirements_model_replay.txt
python replay_forward_models.py
```

该脚本在输出目录的临时模型副本中，重新执行四年原DI与主候选共8个情景，保留原AquaCrop-OSPy 3.1.0及过程修订。结果在 `outputs/model_replay`。物理设置与论文一致：四年主结果fMulch=0、Zmax=2.30 m；后续2021年1 m根深及0.50/0.75/0.85情景没有混入本次主图。重新运行随机MCMC或NSGA搜索与复绘既有论文图是不同操作，原搜索代码另存 `model_replay/code` 供查阅。

## 来源版本

- 用户上传Word：完整SHA256见 `reference/document_inventory.json`。
- 当前文稿、非优化图和表：Git提交 `c6649028a4cbb37c5f587921fb4887880c34ddd6`。
- 五期、每期最多3事件的原优化来源：`20f1616556f5aeb79329b7ead22faa28f9fcda6a`；未使用旧四窗口结果替代主图。
- 所有复制来源、原路径与逐文件SHA256：`SOURCE_COPY_LEDGER.json`。
- 观测资料：王尚今（2023）学位论文及项目归档的数字化/换算表；遥感辅助序列与DI校准数据分别保留。

Windows终端中文乱码时可先执行 `chcp 65001`；图内英文及数据文件均采用UTF-8，不依赖系统中文字体。
