# 2022原模型与数据齐全核验（2026-10-18）

本次两包已补齐此前缺失的8份data原件。原目录共12个data文件，加上6个模型/说明文件，18项均与原manifest的SHA256完全一致；两包中的data逐文件一致。B组ETo、数字化生物量、READY、起点及初始参考等都已找到。

实际运行原模型的--preflight-only已通过：TECHNICAL_READY=true，Process_status=PASS，冻结初始点与历史分组MAP复现均通过。MCMC没有重新采样。

进一步使用已冻结的第二阶段样本均值点，分别重新执行DI与零灌溉模拟，所有已有数值汇总差异均小于1.5e-14；DI产量14.077782818070832 t/ha，ET596.7846360646791 mm，灌水404.84000000000003 mm，季节水量平衡残差约-1.3e-12 mm。既有校准与零灌溉反事实的解释限制继续适用。

model_2022/为完整的原模型及data。verified_preflight/与verified_phase2_mean_replay/是本工作区实际运行所得；UPLOADED_DATA_PREFLIGHT_VALIDATION.json是附件自带的核验声明，二者分开保存。DATA_COMPLETENESS_AND_REPLAY.json记录当前结论。

本次验证的是2022输入完整性、原模型可运行性和基准回放；完整Sobol与NSGA-III实验尚未完成。本包不新增MCMC采样，也不将历史敏感性或代理优化结果改称本次结果。

在model_2022目录中只做预审的命令为：

```bash
python DI_2022_MCMC_ONE_CLICK.py --preflight-only --output ../new_preflight
```

当前已验证运行环境采用AquaCrop3.1.0、Python3.12、NumPy2.3.5、pandas2.2.3；它与原采样合同中的环境版本不同，当前基准回放已逐项比对，原合同保留。本包原requirements文件也原样保留。正式Sobol/优化继续使用既有冻结MCMC输入。
