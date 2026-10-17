# Sobol与NSGA-III修订工程（2026-10-17，2022第二阶段已补齐）

本版继续按照三份指导材料修订昨天的Sobol和优化，现已接入新补DI_2022_Phase2.zip的真实第二阶段。MCMC不重跑；原7个保留数组逐值不变，统一NPZ新增p2_2022（58784×3），2022中心点数值不变且现已由原链交叉核验。

## 本轮更新

- 正式链2000×32×3，burn=163，每walker保留1837步；2步smoke不进统计。
- 四年8个阶段组、32个中心值均有核验来源。2022阶段一均值与handoff逐值一致，4份源检查点哈希引用匹配既有核验记录。
- 2022的local95范围和阶段二128组整行条件扰动现可读取真样本。缺件保护仍保留，但不会再把正常2022数据误报为缺失。
- 2022基准改为新增JSON精确值：Y13=14.0777828181、Tr=529.9393430560、Es=66.8452930087、ET=596.7846360647；基准比对容差1e-5。
- 诊断、量账、来源和数组形状见frozen_inputs/PHASE2_2022_VALIDATION.json、FROZEN_INPUTS_MANIFEST.json和RUN_READINESS.json。

## 保持的正式分析设置

Sobol为8参数公共全局物理范围中的独立均匀响应实验，N128×3种子，必要时512；保存六输出、S1/ST及bootstrap区间、均值/方差/单位与输入响应矩阵。local95只称邻域响应，不称posterior Sobol，不计算CAI。正式公共范围不因2022链支持较窄而自动改成年度范围。

优化固定年度中心参数，min(-Y13,I)，硬约束I≤年度DI基准、Y13≥0.95×文献观测，另查非负量、灌期与完整量账。优先SMT1—4；不支持时4—5阶段水量。100方向/种群、100代、5种子，与同预算NSGA-II对照；每代保存X/F/G/CV和归一化HV。

推荐为ε门槛内最低灌水量及两个相邻可行备选，无可行解则无推荐。候选真实回代后，阶段一/固定阶段二中心、阶段二整行/固定阶段一中心分别至少128组扰动，报告概率、5%分位、MC误差与水量/通量。不是八维联合后验传播。年度专用制度不宣称未知年通用验证；旧2021约38%节水仍撤回。

## 执行

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python DI_PHASE3_ONE_CLICK.py --phase all --auto-expand
python DI_PHASE3_ONE_CLICK.py --phase sobol --track local95 --years 2022
```

原Modified DI模型的冻结依赖单独恢复。若仅检查已接入的2022范围，可执行：

```bash
python -c "from model_adapter import load_study; from phaseB_sobol import make_problem; print(make_problem(load_study(),2022,'local95'))"
```

## 尚未执行的真实计算

新增9KB脚本是衔接包装器，仍导入外部原项目DI_2022_MCMC_ONE_CLICK.py及data，不包含原模型实现。因此real_model/adapter.py仍需接入原Modified DI；本轮没有生成新的真实模型Sobol、Pareto前沿或节水率，程序不回退旧代理。完成源链核验也不等于已认证收敛或外部验证。

frozen_inputs/DI_2022_Phase2.zip原样保留上传文件，其中smoke仅为原件的一部分；当前程序只用显式正式路径与已核验统一NPZ。2022 R²仍缺配对表支持，原文档值不能称本轮配对重算。新模型JSON是条件均值参数点输出，不是后验预测均值。

测试记录见SOFTWARE_VALIDATION.json。测试使用Ishigami与合成模拟器，优化夹具为20种群、10代、5种子；测试图与前沿不作为作物结果交付。输出默认在output_revised/<UTC时间>；Sobol可按同配置/来源日志续算，优化保留每代快照但不承诺从中间代精确续跑。

包内包含完整修订代码、原始补件、冻结中心点与8个样本数组、源码差异、条件扰动/图表模块和核验清单。真实源码接入后再运行上述正式预算，不能用软件测试填入论文正式结果。

数值边界只允许64×机器epsilon×量级的舍入容差，用于将404.84000000000003视作404.84；不增加农艺约束松弛，0.0001mm等真实超限仍会被拒绝。
