# URP 研究审查与论文图表交付

此独立分支用于交付文件，主分支未修改。

## 下载

打开 `URP_full_package.zip`，点击 GitHub 的 Download raw file（下载原始文件）按钮或 View raw。
如果仓库为私有，请使用拥有此仓库访问权限的 GitHub 账号登录。

压缩包约20MB，包含合理性审查报告、13页带图论文框架（Word/PDF）、14幅高清PNG和矢量PDF、结果工作簿及复现代码。

## 证据范围

四年第一阶段尚未达到原定收敛标准；2022第二阶段构造样本已从新增分析中排除。新增Sobol和NSGA-III运行为代理模型的方法诊断，不能视为原改进AquaCrop的真实复算或最终田间灌溉建议。

先阅读压缩包内的 `README_交付说明.md` 和 `artifacts/URP_合理性审查报告.pdf`。
文件SHA-256见 `SHA256SUMS.txt`。

## 本次实际跑出的完整结果（新增）

- [URP_run_results.zip](URP_run_results.zip)：完整运行产物，包含全部结果表、日志、后验保留样本、4096样本条件产量、Sobol多次试验、NSGA-III全部前沿和HV轨迹、图表及报告。此前未打包的17.7MB真实分阶段样本已补入。
- [URP_figures.zip](URP_figures.zip)：单独图件包，14张高清PNG及对应矢量PDF。

运行结果包内的 README_RESULTS.md、RUN_RESULTS_MANIFEST.json 与 NPZ_ARRAY_SHAPES.json 提供内容与校验清单。保留样本为从已有真实检查点重建，没有重跑MCMC；新增优化仍是代理探索。

## 2026-10-16 新版更新

[打开最新版交付目录](2026-10-16/)：新增材料复核、确定性主线论文Word/PDF、7张图与表格、9.5MB更新包。正式真实模型运行仍待原始源码与2022原链。
