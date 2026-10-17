# 2026-10-17更新：2022真实第二阶段已接入

正式2000×32×3链已核验，统一burn=163后保留58784行。四年32个中心点全部可追溯；原7个数组逐值不变，新增p2_2022。2步smoke排除。

本包的论文、图表、表格、来源与状态已更新；2022参数区间、相关结构、水量账和精确基准已补齐。当前正式方法仍为公共全局独立范围Sobol、固定中心点双目标优化和候选分组条件扰动。

新增包仅含依赖原项目的衔接脚本，不包含其导入的DI_2022_MCMC_ONE_CLICK.py及原data。因此真实模型的新Sobol/NSGA-III尚未运行；历史代理图和旧节水结果不升级为正式结果。2022逐日CC/生物量配对表仍未交付，R²标为文档来源。

文件名中的20261016保留用于原下载链接兼容，正文及核验版本均为2026-10-17。请先读当前README和PHASE2_2022_VALIDATION.json。

## 计算准备包内容与复建
包含精确2022基准、统一8组保留样本、正式链副本与源JSON、15360行公共全局设计、响应检查程序、当前论文/图表与核验。设计只有输入X，尚无真实模型响应Y。

`python build_inputs.py --out new_designs --n 128`从已交付配置检查2022基准并生成新设计；`python build_documents.py`用当前Markdown和图重建Word/PDF（另需reportlab、python-docx、Pillow和Pandoc）。`python verify_delivery.py`检查设计、来源、原链与文档。

real_model_pipeline.py的prepare/benchmark/run/analyze仍可用；真实适配器缺件时明确失败。2022基准已更新为精确JSON，不再因阶段二缺失而阻止验收。`study_config.json`主空间改为公共全局物理范围，`tables/annual_sampling_domains.csv`仅描述链支持，两者不是同一对象。
