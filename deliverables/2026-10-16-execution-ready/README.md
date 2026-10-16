# URP 正式计算准备与论文增补（2026-10-16）

本包包含真正生成的采样输入、可运行的调用与检查程序、2张新图及更新后的9页论文框架。**没有新增真实Modified DI模型的Sobol或NSGA-III结果**。缺少原模型源码，2022阶段二原链及配套输出亦未交付，不能用代理代替。

GitHub下载：[完整准备与论文更新包](URP_execution_ready_20261016.zip)；[论文Word](paper_framework_execution_ready.docx)；[论文PDF](paper_framework_execution_ready.pdf)。ZIP网页不能预览时，点击下载箭头或View raw。

## 先看这些文件

- `paper_framework_execution_ready.docx` / `.pdf`：完整论文框架，9张配图（7张沿用、2张新绘）。新增年度参数范围和绝对保产余量；保留正式结果占位。
- `figures/E01_annual_supports.*`：2022的WP_early、WP_late、HI0支持范围与前三年不同，取自原始检查点。
- `figures/E02_yield_gate_headroom.*`：按已有原模型输出，2019—2021相对模型基准可减产余量为5.86%、2.25%、0.86%，**不是节水率**。
- `execution_evidence.xlsx`、`tables/`：图的数值和来源表。
- `designs_N128/`：四年×3种子，12组设计，每组1280行，共15360行。NPY保留精确数值，CSV带固定行号和A/AB/B角色。**只有输入X，没有作物模型响应Y**。
- `study_config.json`、`source_provenance.json`：原始检查点的范围、源码哈希记录、年度中心点、原模型匹配基准与验收误差。
- `real_model_pipeline.py`：生成设计、基准复现、调用、断点续算和Sobol分析。
- `adapter_template.py`：真实模型接口约定，尚未实现，运行将报缺件错误。
- `test_pipeline.py`、`SOFTWARE_VALIDATION.json`：解析函数和合成软件夹具测试；不代表真实玉米模型已验证。
- `DELIVERY_VALIDATION.json`、`SHA256SUMS.txt`：交付完整性检查与文件哈希。

## 本次科学解释修正

2022的WP_early=[10,22]、WP_late=[20,38]、HI0=[0.35,0.50]；前三年分别为[10,40]、[10,40]、[0.35,0.60]。设计在各年的历史支持范围内独立均匀采样，不能叫MCMC原先验密度或后验传播。原MCMC部分参数含正态先验。跨年比较同时受范围、年度设置、气象影响；气候归因需另外统一输入空间，当前未执行。

保产约束为Y≥0.95×文献观测产量。2021模型基准15.1971、文献观测15.86 t/ha，绝对门槛15.0670，只剩0.1301 t/ha余量。不能改成0.95×模型基准。这不说明一定没有可行节水空间，仍需真实模型搜索。

## 接入后的执行顺序

已在Python 3.12、numpy 2.5.4、scipy 1.18.1、SALib 1.5.2环境验证程序。`requirements-run.txt`只包含调用程序的依赖；原Modified DI模型的依赖应按原项目版本恢复，不能为运行方便改动其结构。

```bash
python -m pip install -r requirements-run.txt
python -m unittest -v test_pipeline
```

1. 找回`DI_2019_MCMC_ONE_CLICK.py`等年度原始实现及完整data目录。按实际API实现适配器；冻结全部实际使用的源码、输入及版本哈希。模板没有降级到代理的分支。
2. 核对逐日纠偏ETo、初始分层水、两阶段WP切换、冠层蒸发修改与基准灌溉日程。`management=None`必须使用原模型的年度基准，不能拿旧代理手填日程代替。
3. 先完成基准复现和重复调用检查，再按实测速度决定工作预算。下面的`my_real_adapter.py`必须是接入后的实际适配器。

```bash
python -c "from pathlib import Path; Path('results').mkdir(exist_ok=True)"
python real_model_pipeline.py benchmark --year 2019 --adapter my_real_adapter.py --out results/baseline_2019.json
python real_model_pipeline.py run --year 2019 --seed 101 --adapter my_real_adapter.py --designs designs_N128 --baseline-receipt results/baseline_2019.json --journal results/responses_2019_101.jsonl --limit 10
```

`--limit 10`只执行首批10个成功点供试跑计时，不做敏感性结论。去掉`--limit`即可按同一日志续算至1280行；如输入、适配器、源文件或验收凭据改变，必须使用新日志。

```bash
python real_model_pipeline.py run --year 2019 --seed 101 --adapter my_real_adapter.py --designs designs_N128 --baseline-receipt results/baseline_2019.json --journal results/responses_2019_101.jsonl
python real_model_pipeline.py analyze --year 2019 --seed 101 --designs designs_N128 --journal results/responses_2019_101.jsonl --out results/sobol_2019_101.json
```

分别对种子101、202、303及各年度执行。2022目前没有匹配的原始阶段二输出，基准验收会明确阻止该年继续；拿到真实文件后核验并更新配置，随后重新生成全部绑定该配置哈希的设计。

如指数跨scramble/样本量不稳定，用`prepare --out designs_N512 --n 512`生成扩展设计。本版本SALib中相同种子的N128是N512的前缀，测试已核验；软件版本变更后须再核验。新设计响应日志仍必须有独立完整溯源，不能直接复用旧manifest或给新设计伪造已完成状态。

## 检查程序的含义

适配器返回字段见`real_model_pipeline.REQUIRED`。产量为t/ha、13%含水率；水量为mm；CC为小数。程序检查Y_dry=0.87Y13、ET=Tr+Es、完整剖面与地表储水账、实际灌水量、有限值，并计算IWP=100Y/I和ETWP=100Y/ET（kg/m³）。CR与GwIn应是互不重复的独立入流；新增过程须同步扩展并说明水量账。

分析前校验设计哈希、行号和参数。失败点单独记录并停止，不填零、不删行；日志截断也不会被静默忽略。断点恢复只复用已核对的成功点。常量输出的归一化Sobol指数不定义，不强行排排名；指数不裁剪，不预设Kcb必须第一。区间为单个设计内bootstrap半宽，须同时看跨种子/样本量差异和输出方差。

基准复现、守恒和哈希是必要的软件与数值检查，不能证明模型生物学正确，也不能替代独立田间验证。适配器的引擎声明是自述，仍需审阅源码。2022阶段一原链虽已提供，不等于其阶段二也已核验。

## 优化仍待实际灌溉接口

本包没有虚构SMT与水量的转换，也没有生成新的NSGA-III前沿。原模型接口恢复后，先核对SMT定义与方向；若改用阶段水量，则明确日期约束。固定年度中心点，min(-Y13,I)，保留绝对产量门槛与灌水上限，多种子记录收敛；候选再用同一真实模型复算。取门槛内最低水量称ε约束选解，不自动称几何膝点。条件参数扰动单列。

## 重新构建与历史版本

`build_inputs.py`、`build_documents.py`依赖此前本云环境的原始资料目录和已核验交付；用于审计追溯，路径在源码内明示。生成的设计、配置及执行程序可以独立复制；实际运行仍需原模型及其data目录。文档重建另需pandas、matplotlib、python-docx、reportlab、pandoc等原审查环境工具。

旧版ZIP、原始文件和交付分支历史均保留。当前新增内容上传到同一个`delivery/urp-review-20261015`分支，主分支不变。
