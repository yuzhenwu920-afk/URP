# 四年真实Sobol与NSGA-III工程

2019、2020、2021、2022原年度源码和基础输入均已接入；四年Y13/Tr/Es/ET基准复现。20项工程检查通过，28个原方程/加速对照案例最大差约1.14e-13。原MCMC冻结，严格诊断限制未被下游计算消除。

正式实验已完成：Sobol N512×3种子，最终61,440行真实响应；NSGA-III与同预算NSGA-II各100个体×100代×5种子×4年，总400,000次评估、4,000代完整种群。23/24项Sobol筛查通过，2022产量WP early/Kcb第三、四名近似并列。当前全部八参数保留，未据该名次删参。

## 一键复跑

推荐Python3.12及根requirements。勿直接运行real_model/model_YYYY/中的原年度OneClick入口，它们默认启动MCMC。

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 python run_four_year_experiment.py --workers 4 --out /workspace/new_four_year_run
```

正式入口run_four_year_experiment.py显式分开Sobol数值审查和确定性优化，保留2022的微小排序不确定性。原DI_PHASE3_ONE_CLICK.py为兼容入口，其all模式仍保留严格Sobol筛查拦截；需要独立运行时可选择--phase sobol或--phase optimization。

Sobol为公共独立均匀范围，不是相关后验Sobol。提前成熟/死亡时保留实际收获产量，后续土壤水量核算至原日历截止日，维持覆膜并停止收获后灌水。记录实际收获日与取消量。所有响应检查逐日水量守恒，不删失败点、不填零。

优化变量是四个有序灌溉窗口总量，原日期和窗口内原比例固定，不是SMT或灌期优化。目标min(-Y13,I实际)，门槛为I≤原DI、Y13≥95%发表观测；初始化和修复同时限制计划总量预算。五种子同预算NSGA-II为对照，候选按ε门槛内最低I选择，不称几何膝点。

## 查看与复建图文

包内图表索引.html与figures含32组当前四年图；其中18组校准背景（流程/气象已更新）及14组新增真实结果。PNG、PDF、Word和Excel可独立使用。Word主文包含方法解释、实际数值表、原校准图与新增图及逐图说明。

完整/运行/工程ZIP的complete_runs包含全部设计、响应和各代X/F/G/CV的无损数据。运行python read_complete_results.py archive.npz --csv result.csv可导出完整响应；Python读取用load_columns，浮点精度未降低。原大矩阵的CSV文本仅是二进制的重复表达，未重复存放。

在包含完整运行记录的交付目录中可复建新图：

```bash
python publish_actual_results.py --run ../complete_runs --out ../recreated_publication
python -m pip install -r publication_tools/requirements_publication.txt
# Word可编辑公式转换需要Pandoc；当前环境已验证。
python publication_tools/build_actual_paper.py
python publication_tools/build_result_workbook.py
```

旧regenerate_four_year_figures.py仅用于历史18组校准背景重绘；当前新增Sobol/优化图请使用publish_actual_results.py。模型使用进程并行，避免线程共享原年度全局补丁。完整计算较长，先检查状态和现有进程，勿重复启动。已完成优化种子可校验后复用；中断种子应保留原件并在新目录重跑，不伪称精确续跑。

## 科学范围

条件扰动按阶段一/阶段二分别整行抽128组，固定另一组中心，不拼成联合后验。Wilson区间只覆盖给定经验样本池的重采样MC误差。主候选未约束季末土壤储水；新增同储水条件筛查只是在已评估点中选点并回代，不是带新约束重新优化。灌水节省不能全部写成耗水节省或多年可持续效益。细节见SCIENCE_REVIEW.md。

real_model各年度原manifest与data保持原件；frozen_inputs存放冻结数组、中心与原配对输出。其他旧日期说明为历史审查记录，不覆盖本轮当前结果。
