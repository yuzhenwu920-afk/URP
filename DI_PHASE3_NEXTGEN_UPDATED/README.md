# Sobol 与 NSGA-III 工程（2026-10-18，2022 原模型已接入）

MCMC保持冻结，8个年度/阶段样本数组不变。2022原源码及12份data原件已齐，全部哈希核验；实际预审、均值点回放及管理量修改检查通过。其他三年原始模型实现尚待接入，当前可运行年度为2022。

正式范围、目标与预算沿用既有指导：公共独立均匀范围Sobol，N128×3种子，必要时N512；优化固定中心点，min(-Y13,I)，I≤原DI、Y≥95%文献观测，100代×5种子，与同预算NSGA-II对照。2022使用原五个固定灌溉日的水量分配，不声称优化灌期或实现SMT。

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python DI_PHASE3_ONE_CLICK.py --years 2022 --phase sobol --n 128
python DI_PHASE3_ONE_CLICK.py --years 2022 --phase optimization
```

测试19项通过，含真实2022原模型基准重复运行与五次水量修改；合成/Ishigami测试结果不作为作物结果。完整Sobol和优化实验尚未完成。本版图表重绘及基准回放不能作为新敏感性排序、前沿或节水结论。

four_year_figures含完整18组四年PNG/PDF，与图件包逐文件一致，统一蓝/橙/绿/紫，最小字号10.5pt。图表索引.html可浏览。frozen_inputs/year_outputs含四年原始过程及配对表；2022是本次均值点回放，其余三年沿用原输出。源码/data与原manifest原样保留。

候选需真实回代，再对两个参数组分别做至少128行条件扰动，保留组内相关，不构造八维联合后验。严格采样诊断保留为补充。边界只允许机器舍入精度，未增加农艺约束松弛。正式试验结果不回退旧代理。

重绘全部18组四年图（不运行MCMC或作物模型）可执行：

```bash
python regenerate_four_year_figures.py --out ./recreated_figures
```

该脚本直接读取包内的原始逐日/配对输出、冻结样本和源表，输出独立目录；Linux中文字体已实测，另提供Windows常用中文字体选择。
