# 按三份新增文件修订昨天的 Sobol 和 NSGA-III 工程

本版本直接替换昨天的`phaseB_sobol.py`、`phaseC_nsga3.py`和`DI_PHASE3_ONE_CLICK.py`。MCMC结果作为冻结输入读取，不重新采样，不改变MCMC的完成口径。

指导材料为《四年DI玉米MCMC确定性成果汇编》《后续Sobol与NSGAIII实施方法》以及`URP_Paper_Alignment_Resolution_2026-10-15.zip`。原件哈希见`GUIDANCE_SOURCES.json`；逐项落实情况见`按三份文件的改动说明.md`。

## 本次已落实的程序修改

| 模块 | 修改后的行为 |
| --- | --- |
| Sobol主分析 | 统一预声明的global physical范围、8参数独立均匀分布；N128×3 seeds，不算二阶，六个输出 |
| Sobol报告 | 分年S1/ST和bootstrap区间、均值、方差、单位、ST×输出方差、跨年排名与一致性检查 |
| 可选局部分析 | 真实样本的边际2.5%—97.5%范围，明确称local95邻域响应；不称posterior Sobol，不计算CAI |
| 优化主分析 | 固定新增CSV中的年度中心参数，min(-Y13,I)，不把参数波动放进第三目标 |
| 硬约束 | I≤年度DI基准；Y13≥0.95×文献观测产量；非负、灌期与完整水量账检查 |
| 管理变量 | 优先真实模块的SMT1—4（0—100%，需实际定义）；不支持时4—5阶段水量及明确日期窗口 |
| 算法 | 100参考方向/种群、100代、5种子NSGA-III；同预算5种子NSGA-II对照 |
| 过程保存 | 每代X/F/G/CV、可行数、统一尺度HV、每种子前沿、年度非支配并集 |
| 选解 | ε门槛内最低灌水量，加两个相邻备选；无可行解时明确无解，不取最高产量冒充达标 |
| 复核 | 候选真实回代；阶段一、阶段二分别≥128组整行条件扰动，报告概率、5%分位、水量和通量 |
| 图件 | 从新响应生成300dpi PNG与矢量PDF；不继承旧38%节水，不人为构造单调前沿 |

`frozen_inputs/combined_central_parameter_vectors.csv`逐字节采用新增ZIP的年度中心点表。`verified_phase_specific_draws.npz`沿用昨天从真实检查点重建的保留样本，哈希未变。只有这些样本用于可选local95与候选条件扰动；全局Sobol和确定性寻优不需要八维联合后验。

全局物理范围沿用昨天工程明示的公共范围：CCx [0.6,0.99]、CGC_CD [0.08,0.16]、CDC_CD [0.03,0.12]、SenescenceCD [115,145]、Kcb [1.05,1.6]、WP_early/WP_late [10,40]、HI0 [0.35,0.6]。这是依照指导文件预声明的下游实验空间，与各年MCMC先验密度或链支持范围不是同一概念。**上一轮我自行加入的“按年度链支持分别采样”不作为本版本默认方案。**

## 运行

在Python 3.12环境安装分析依赖，原作物模型的依赖按其冻结版本另行恢复：

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python DI_PHASE3_ONE_CLICK.py --phase all --auto-expand
```

默认按指导文件顺序运行：全局Sobol N128、必要时N512、年度确定性NSGA-III与NSGA-II对照、选解回代和条件扰动。若排名/区间仍不稳定，`all`会记录状态并暂停后续优化；不通过修改排名使流程通过。

```bash
python DI_PHASE3_ONE_CLICK.py --phase sobol --n 128 --years 2019 2020 2021 2022
python DI_PHASE3_ONE_CLICK.py --phase optimization --years 2019
```

单独执行`optimization`表示只请求该阶段，不宣称Sobol质量门已通过。`--track local95 --phase sobol --years 2019 2020 2021`是可选局部响应实验。2022局部分析缺真实阶段二样本时会明确报缺件，不生成正态替代样本。

默认输出到新的`output_revised/<UTC时间>/`。Sobol可用相同`--out`恢复已核对的成功点；日志或配置变化会拒绝续算。优化保留每代数值快照，但不承诺从中间一代原样恢复随机状态；中断后用新输出目录重启，原历史保留。

## 实际运行边界

**本轮完成的是上述工程代码的修改和软件验证，尚未完成真实模型的新数值运行。**三份指导材料描述了已恢复的Modified DI程序，但当前可读附件中没有交付其源码。`real_model/adapter.py`因此保留明确的接入口；不再自动调用昨天的`aquacrop_surrogate`。运行默认入口会返回非零退出码和`BLOCKED_OR_FAILED`，不会输出虚构的正式指数或前沿。

接入需保留actual CC蒸发、真实MulchPct、两阶段WP和年度HI0，返回`model_adapter.py`定义的完整输出和真实灌溉事件。SMT含义、触发方向及阶段窗口由实际灌溉模块给出；不能根据旧代理柱状图猜测。适配器的文件清单需哈希模型、气象、土壤、灌溉和观测文件。

前三年基准检查对齐已有原模型summary；2022按补充Word四舍五入表给出0.02容差并标为文档来源，不把表格当作已独立重演。新的四年中心点照指导文件作为冻结输入接受。2022真实阶段二样本未随材料交付，确定性寻优可使用中心点，候选阶段二扰动则标记缺组，不能把有限的阶段一核验称作完整不确定性核验。

当前15项测试包括Ishigami已知指数、设计响应恢复与防篡改、双目标/绝对约束、五种子算法对照、真实回代逻辑、无解处理和分组条件扰动。优化测试使用**合成函数、20种群、10代**，只检验软件；测试图和测试前沿均保存在临时目录并清理，没有打包为作物结果。

## 计算预算与输出

N128×4年×3种子=15360次Sobol调用；N512完整设计共61440次，重叠样本可审计复用但不能混用旧运行状态。主NSGA-III约200000次候选评估；默认同预算NSGA-II对照另约200000次。实际调用数因重复消除而变；还需基准回算、每候选每组128次扰动及配对基准。接入真实模型后应先测吞吐量，再决定是否完整执行。

Sobol输出为`space.json`、`design.npy/csv`、`responses.jsonl`、`response_matrix.npy/csv`、`indices.csv`、各年/种子运行状态、汇总表与图。置信区间为单设计bootstrap，不代表模型结构或田间误差；常量输出不产生伪零指数。

优化输出包括`decision_space.json`、`generation_*.npz`、`history.csv`、各种子前沿、`algorithm_comparison.csv`、`epsilon_candidates.csv`、真实回代表、条件响应矩阵及概率汇总与图。仅优化年度专用制度，未调用昨天的跨年通用方案选择模块；若要宣称未知年通用制度，需按文件要求另做留一年/嵌套验证。

`EXECUTION_STATUS.json`区分执行受阻、Sobol待扩样、无可行解、候选已完成但条件核验缺组以及请求阶段完成。`SOFTWARE_VALIDATION.json`和文件清单仅说明本次软件/交付核查，不等于真实Sobol、最终节水率或田间验证完成。
