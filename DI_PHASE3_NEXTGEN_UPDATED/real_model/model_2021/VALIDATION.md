# 交付验证记录

本包已完成实现核验，保留科学 REVIEW；正式作物模型长链未运行。

## 实际完成的检查

- 2019、2020主方案、2020备用日界、2021、2022全部技术预审通过，冻结输出复现。2019–2021保留REVIEW；2022通过既有过程门槛，仍不代表RS或零灌溉获得独立验证。
- 2022冻结起点及历史grouped MAP重新复现，包括湿基产量14.062076附近、Field CC R²约0.940、零灌溉产量约5.763与水量闭合。
- 四年实际AquaCrop两阶段短链执行：每阶段4个独立emcee ensemble，每组12 walkers、2步。仅执行测试，不形成可信后验。
- 四年相同配置再次执行成功，复用冻结的阶段1条件点；测试结果没有误标COMPLETE/收敛。
- 32 walkers配置的实际引擎停止测试：仅跑第一阶段2步，诊断为链长/收敛不足，未启动阶段2。
- 采样核：分段续跑与连续运行的样本、log posterior、接受标记逐位一致；修改检查点合同会被拒绝。
- 诊断：IID、AR(1)、已知正态目标检查通过；偏移、尺度不一致及常数序列没有被误判通过。匹配walker跨独立ensemble的诊断路径已执行。
- burn-in核验：严格ceil(5×max(tau))；无法估计tau时后验表为空，不使用固定值兜底。正式通过门槛另要求至少2000步。
- 四年缺生物量负向测试均在预审入口停止，不允许采样到第二阶段才发现缺数据，更不退回Yield-only。
- 四年全部评价表、绘图及参数预测导出路径用重复冻结点执行过。此测试不是后验预测检验或实际拟合收敛证据。
- 整包解压至新的临时路径，所有5个入口只用包内输入重新通过预审；验证源文件语法与manifest哈希。
- 四年DI/zero汇总CSV包含8条唯一记录，干湿基换算、ET=Tr+Es、减产比例及REVIEW标签已核对；原始观测未改写。

最后补充的缺生物量前置门槛和正式最少2000步门槛，分别经过负向测试与采样核回归；正常输入的整包预审再次执行。它们不改变模拟方程或采样提议。

## 证据

tests/kernel_tests.json、pipeline_tests.json、preflight_guard_tests.json、export_tests.json、relocation_tests.json。
交付包不含测试检查点，不能拿测试链续跑正式分析。此前试制的Metropolis实现不属于本交付版。

诊断方法参照[emcee自相关文档](https://emcee.readthedocs.io/en/stable/user/autocorr/)和[Stan诊断文档](https://mc-stan.org/docs/reference-manual/analysis.html)。自实现Rhat/ESS已做数值测试，但未声称与ArviZ逐位等价认证。
