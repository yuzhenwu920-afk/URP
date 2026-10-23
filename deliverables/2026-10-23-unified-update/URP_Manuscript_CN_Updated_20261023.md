# 基于AquaCrop模型的膜下滴灌玉米参数校准与五生育期灌溉制度优化

为明确西北旱区膜下滴灌玉米灌水量、灌水时序与产量的响应关系，以甘肃武威2019—2022年滴灌玉米为研究对象，结合气象、土壤、冠层覆盖度、生物量及产量资料，采用分阶段马尔科夫链蒙特卡洛（MCMC）方法校准AquaCrop模型，运用Sobol方法识别主要敏感参数，并通过NSGA-III和NSGA-II分析五生育期灌水日程与产量的权衡关系。结果表明：（1）四年冠层覆盖度和地上生物量的校准决定系数分别为0.9306～0.9932和0.9685～0.9966，籽粒产量相对偏差为−4.18%～0.92%；（2）晚期水分生产率、参考收获指数、早期水分生产率和基础作物系数的产量总效应指数四年均值分别为0.396、0.206、0.164和0.145，年度平均敏感性排序一致；（3）每个生育期设置最多3个可选灌水事件，同时优化逐次日期和水量。在既定模型参数、初始水分和年度气象条件下，以观测产量的95%为门槛，四年代表方案的灌水量分别为209.83、306.50、264.50、257.47 mm，较原日程减少36.40～58.25%；（4）优化前后蒸散量下降1.89～5.98%，季末剖面储水差解释了81.09～96.72%的减灌水量。研究将多指标参数校准、五期逐次灌水与土壤储水核算相衔接，为同类条件下膜下滴灌玉米灌溉制度的分析与评价提供依据。

# 1 引言

西北旱区农业生产对灌溉供水具有较强依赖，合理安排灌水量及其生育期分配，是协调作物产量与农业用水的重要途径。膜下滴灌通过调节土壤水热环境、减少土面蒸发和改善根区供水促进玉米生长[1,16]。然而，作物耗水还受年度降水、初始土壤水分和生长过程共同影响，同一灌水总量在不同年份和分配方式下可产生不同产量。灌溉制度评价因而需要同时考察作物生长、实际蒸散和土壤储水变化，明确减灌水量的组成及其适用条件[13]。

作物模型与优化算法相结合，为分析灌水—产量关系提供了定量方法。AquaCrop以冠层覆盖、蒸腾、生物量和收获指数为核心，描述水分供应对作物生长与产量形成的影响[3,4]。Liu等[2]将多源数据、作物模型、MCMC参数校准、敏感性分析和多目标优化相结合，构建了棉田灌溉用水分析框架，体现了过程模型与数据约束协同应用的价值。在此基础上，根据研究区观测资料的类型设置分阶段校准目标，再对灌水总量及其时序分配进行优化，有助于将模型参数确定与灌溉决策衔接起来。

本研究以甘肃武威2019—2022年膜下滴灌玉米资料为基础，首先利用冠层覆盖度、蒸腾和土壤蒸发约束冠层及耗水参数，再利用生物量和产量约束水分生产率及收获指数；随后在四年共同参数范围内开展Sobol敏感性分析，比较主要参数作用的年度稳定性；最后采用NSGA-III和NSGA-II优化灌水分配，通过单目标求解器对照和水量平衡分析，解释较低灌水量下维持较高产量的形成原因。研究重点是将参数校准、生长过程、灌溉权衡及储水变化联系起来，形成适用于本试验条件的灌溉制度分析方法。

# 2 材料与方法

## 2.1 研究思路

研究技术路线如图1所示，主要包括资料整理、模型校准和分析评价三个部分。资料整理包括气候驱动、土壤及管理条件、作物生长指标；模型校准分为冠层与耗水参数校准、生物量与产量参数校准两个阶段；分析评价包括参数敏感性、灌溉多目标优化、单目标算法对照以及水量核算。各年度模型分别使用相应年份的观测资料和气象驱动。

![Figure 1](../figures/Fig01_Research_workflow_EN.png)

Figure 1. Research framework for staged calibration, sensitivity analysis and irrigation optimization. Three patterned columns summarize data preparation, crop-model calibration and decision analysis.

## 2.2 试验区与资料来源

试验区位于甘肃武威绿洲农业高效用水国家野外科学观测研究站，即中国农业大学石羊河实验站（37°52′N，102°52′E），海拔1581 m，属温带大陆性干旱气候，年平均降水量约164 mm，地下水埋深约40～50 m[1]。膜下滴灌玉米观测区面积为400 m×200 m，种植密度为79 365株·ha⁻¹。地膜宽度1.2 m，相邻地膜间距0.4 m，对应覆盖率75%。图2给出试验站位置和DI观测区尺度。

![Figure 2](../figures/Fig02_Study_site_EN.png)

Figure 2. Location of the study station and dimensions of the drip-irrigated maize field. Station coordinates and field dimensions follow Wang [1]. The field panel is a size schematic with illustrative orientation.

田间土壤资料采用王尚今[1]表2-1中的DI处理数据。0～100 cm土层由六层组成，砂粒含量为10.38%～30.81%，粉粒含量为58.67%～76.53%，黏粒含量为10.52%～16.20%，各层质地均为粉砂壤土，容重为1.29～1.69 g·cm⁻³（表1）。模型将这些分层资料与各年初始含水量配套输入，深于1 m的模拟剖面按归档土壤结构延伸至2.4 m。

Table 1. Soil properties of the DI field reported by Wang [1], Table 2-1.

| Depth (cm) | Sand (%) | Silt (%) | Clay (%) | Bulk density (g cm⁻³) | Texture |
| --- | --- | --- | --- | --- | --- |
| 0–10 | 29.70 | 59.66 | 10.64 | 1.65 | Silt loam |
| 10–20 | 30.81 | 58.67 | 10.52 | 1.65 | Silt loam |
| 20–40 | 19.43 | 68.25 | 12.32 | 1.69 | Silt loam |
| 40–60 | 13.22 | 70.58 | 16.20 | 1.29 | Silt loam |
| 60–80 | 10.38 | 74.87 | 14.75 | 1.48 | Silt loam |
| 80–100 | 11.81 | 76.53 | 11.66 | 1.45 | Silt loam |

Particle fractions refer to >0.05 mm, 0.002–0.05 mm and <0.002 mm, respectively.

四年DI灌水日程、生育期、叶面积指数、生物量、产量及水分消耗资料来自该试验研究[1]，年度汇总见表2。冠层覆盖度（CC）由田间叶面积指数（LAI）的数字化序列按式（1）换算，四年共48个配对点；地上干生物量由论文图件数字化获得，共37个配对点。籽粒产量统一按13%含水率表示。遥感CCquad序列用于辅助比较冠层变化，其处理标签和日期范围单列于附表S1。

CC = 1.005[1 − exp(−0.6LAI)]¹·² (1)

Table 2. Annual DI observations used for crop-model calibration.

| Year | Irrigation (mm) | Yobs (t ha⁻¹) | CC / B pairs | ETobs (mm) | Es,obs (mm) |
| --- | --- | --- | --- | --- | --- |
| 2019 | 445.27 | 16.55 | 12 / 9 | 661.45 | 76 |
| 2020 | 559.76 | 17.29 | 13 / 10 | 637.03 | 79 |
| 2021 | 633.47 | 15.86 | 11 / 8 | 626.81 | 78 |
| 2022 | 404.84 | 14.08 | 12 / 10 | 584.11 | 81 |

Yield is expressed at 13% moisture. The 2021 event sum is 633.47 mm; the published rounded seasonal total is 633.46 mm.

气象驱动包括逐日最低气温、最高气温、降水和参考蒸散量ETo[14]。新提供的四年气象文件与归档原始输入逐值一致，全年日期连续。模型采用经审计的ETo序列，并按实际执行日历统计水量。四年模型日历内降水量分别为177.87、113.46、143.32和151.38 mm，ETo分别为595.62、632.26、612.93和609.26 mm。图3展示逐日降水和ETo的季节分布，2019年生育期降水较多，2020年参考蒸散需求较高。

![Figure 3](../figures/Fig03_Environmental_drivers_EN.png)

Figure 3. Daily precipitation and reference evapotranspiration during the four model seasons. ETo uses the archived audited series; precipitation totals follow the executed model dates.

## 2.3 AquaCrop模型及固定条件

采用AquaCrop-OSPy 3.1.0及项目归档的过程修订实现[3,4]。模型以日为时间步长，根据土壤含水状态计算冠层扩展、气孔调节和衰老过程，利用归一化蒸腾量及有效水分生产率计算地上干生物量，再由调整收获指数计算干籽粒产量。早、晚期水分生产率切换日期分别为2019年7月10日、2020年7月14日、2021年7月13日和2022年7月5日。含水率换算关系为式（2）。

Y₁₃ = Ydry / (1 − 0.13) (2)

四年主分析沿用原校准模型的相同结构：MulchPct=75%，Zmin=0.30 m，Zmax=2.30 m，fMulch=0。该实现通过修订蒸发结构处理冠层对蒸发的影响，并将AquaCrop原生覆膜乘数固定为1，以保持校准与优化阶段一致。覆盖面积与蒸发调整因子的计算关系见式（3）。2021年fMulch为0.50、0.75和0.85、最大根深为1 m的条件重校准结果作为补充结构试验单列保存。

Es,mul = Es,pot[1 − fMulch × MulchPct/100] (3)

## 2.4 分阶段MCMC参数校准与评价

采用emcee集成采样方法[5]开展两阶段校准。第一阶段确定CCx、CGC_CD、CDC_CD、SenescenceCD和Kcb，分别表征最大冠层覆盖度、冠层增长速率、冠层衰退速率、衰老起始时间及基础作物系数；以CC、季节蒸腾量和土壤蒸发量构建高斯误差似然。第二阶段固定第一阶段保留样本均值，确定WP_early、WP_late和HI0，以地上干生物量和籽粒产量构建条件似然。参数含义及共同敏感性分析范围见表3，各年度校准先验见附表S2。

Table 3. Calibrated parameters and common independent Sobol input ranges.

| Parameter | Phase | Meaning | Unit | Sobol range |
| --- | --- | --- | --- | --- |
| CCx | 1 | Maximum canopy cover | fraction | 0.6–0.99 |
| CGC_CD | 1 | Canopy growth coefficient | d-1 | 0.08–0.16 |
| CDC_CD | 1 | Canopy decline coefficient | d-1 | 0.03–0.12 |
| SenescenceCD | 1 | Senescence onset | d | 115–145 |
| Kcb | 1 | Basal crop coefficient | dimensionless | 1.05–1.6 |
| WP_early | 2 | Early effective water productivity | g m-2 | 10–40 |
| WP_late | 2 | Late effective water productivity | g m-2 | 10–40 |
| HI0 | 2 | Reference harvest index | fraction | 0.35–0.6 |

Annual MCMC prior families and ranges are provided in Table S2. The ranges above define the independent Sobol experiment.

p(θ | D) ∝ L(D | θ)p(θ) (4)

第一阶段的CC误差尺度取0.05，土壤蒸发误差尺度取15 mm，蒸腾误差尺度取对应年度目标的10%；第二阶段采用各生物量数字化点的归档误差尺度，干籽粒产量误差尺度取0.5829 t·ha⁻¹。每组设置32个walkers、2000步，每年第一阶段运行4组独立ensemble，第二阶段运行1组ensemble。去除各阶段预热样本后，计算参数均值和2.5%～97.5%经验分位区间。

采样诊断采用秩归一化折叠分裂R̂、主体有效样本量（bulk ESS）、尾部有效样本量（tail ESS）和积分自相关时间τ，分别反映链间一致性、主体及尾部信息量和时间相关程度[15]。参考判据为R̂<1.01、bulk/tail ESS≥400，时间轴链长与τ之比采用50作为经验参考。第一阶段在4个独立ensemble的同编号walker间计算诊断，保持步数维度；同时比较不同预热截取和前后半段的参数中心。

模型拟合采用决定系数R²cal、均方根误差RMSE及产量相对偏差RE评价，计算公式见式（5）～（7）。生物量汇总回归以观测值为横轴、模拟值为纵轴，报告OLS回归R²和Pearson相关系数r。参数边界分析统计先验支持宽度上下各1%邻近带中的样本比例。

R²cal = 1 − Σ(Sᵢ − Oᵢ)² / Σ(Oᵢ − Ō)² (5)

RMSE = [Σ(Sᵢ − Oᵢ)²/n]¹ᐟ² (6)

RE = (Ysim − Yobs)/Yobs × 100% (7)

## 2.5 Sobol全局敏感性分析

采用Sobol方差分解法计算一阶效应S₁和总效应Sₜ[6,7]。八个参数按表3中的共同范围独立均匀抽样，四年使用相同输入分布，输出包括籽粒产量、生物量、蒸腾、土壤蒸发、蒸散量及最大冠层覆盖度。一阶效应反映参数单独作用，总效应包含该参数参与的交互作用，定义见式（8）。

S₁,ᵢ = Var[E(Y | Xᵢ)]/Var(Y)；Sₜ,ᵢ = E[Var(Y | X₋ᵢ)]/Var(Y) (8)

基础样本量由128、256增至512，最终使用三个独立随机化序列，每个年度、每个序列包含512×(8+2)=5120次模型计算，四年主分析共61 440次。每个序列进行512次完整响应块bootstrap重采样，估计三序列均值的近似95%数值区间。先计算各年度三序列均值，再对四年等权平均；通过年度参数排序相关及指数范围评价年度稳定性。

## 2.6 五生育期逐次灌水优化与算法对照

按照王尚今[1]表2-3，将每年玉米生育期划分为苗期、拔节期、抽穗期、灌浆期和成熟期。各期均设置3个可选灌水槽位，以15个连续灌水量和15个整数日期构成30维决策变量。日期取值范围为当年相应生育期与原模型执行日历的交集；零水量槽位不执行，同日槽位合并计量。各年全部五期均参与搜索，最终每期实际灌水次数为0～3次。具体年度日期界限见附表S4。

采用NSGA-III和NSGA-II求解产量最大、实际季节灌水量最小的双目标问题[8–10]，形式见式（9）。正式搜索要求Y₁₃≥0.95Yobs，计划总量及实际执行量均不超过原DI季节总量；95%表示确定的产量水平门槛。两算法均采用100个体、100代和5个种子（31、73、109、151、199），共同以原实测日程及前期四窗口可行日程作为公开初值，另加入日期扰动和随机控制量。每年NSGA-III首个种子的重复初值规范化后为99个，仍完整执行100代；四年两算法正式查询合计399 996次，其余种子按100个不同初值执行。

min F(x) = [Iactual(x), −Y₁₃(x)]；x = (w₁,…,w₁₅,d₁,…,d₁₅) (9)

主候选取正式NSGA-III五种子最终种群可行非支配解并集中的最低灌水解。另以3个种子、80个体、60代开展移除产量门槛的全范围搜索，四年共57 600次，以覆盖零灌水至高产平台；正式与补充搜索合计457 596次目标查询，对应455 505次搜索内实际前向模型调用。精确缓存命中与实际调用分别记录，全部逐代种群及逐次查询均保存。

本轮采用各年已知逐日天气开展回顾性日程优化，固定作物参数、土壤、初始含水量、覆膜及根系设置，联合调整每次灌水量和日期。灌溉管理器的单次与季节执行上限随候选日程设置，以完整执行计划；设备供水能力、最小事件水量、最小间隔和季末储水底线作为后续制度细化条件，未附加到本轮目标中。报告同时给出原始正水量事件数和≥0.1 mm事件数，微量正数保留在源表中。

前期还在固定日期四窗口空间内，将优化写为给定产量门槛q下的单目标最小灌水问题（式10），比较实数遗传算法、单目标NSGA-II、广义模拟退火和差分进化[8,10–12]。该组结果作为原控制空间下的算法与低水量机制诊断列于补充资料；本轮30维五期日程的算法比较使用上述NSGA-III与NSGA-II记录。

min Iactual(x)，s.t. Y₁₃(x) ≥ q，Iactual(x) ≤ IDI (10)

## 2.7 水量平衡与减灌来源分析

分别核算原DI日程和优化方案的降水P、灌水I、蒸腾Tr、土壤蒸发Es、径流R、深层排水D及初末储水S。ET=Tr+Es；其余入流包括毛管上升CR和地下水侧向入流GWin，其余出流包括排水TD。按整个2.4 m模拟剖面及地表储水建立水量平衡，计算式见式（11）。

ΔS = P + I + CR + GWin − ET − R − D − TD (11)

在气象、初始水分和外部入流相同的条件下，将原日程与代表方案的灌水差额分解为蒸散差、净损失差和季末储水差（式12）。采用该差额关系分析优化灌水量降低的来源，同时给出基准和代表方案相对于初值的储水变化，以区分减少基准增储和利用季初储水两种过程。

Ibase − Iopt = (ETbase − ETopt) + (Lbase − Lopt) + (Send,base − Send,opt) (12)

# 3 结果与分析

## 3.1 参数校准与作物生长模拟

四年分阶段校准参数均值见表4。CCx为0.9374～0.9773，CGC_CD为0.0956～0.1318 d⁻¹，CDC_CD为0.0603～0.0663 d⁻¹，衰老起始时间为播种后134.85～137.84 d，Kcb为1.3775～1.4866。早期WP为10.877～18.204 g·m⁻²，晚期WP为21.938～31.498 g·m⁻²，HI0为0.4013～0.5800。冠层增长参数和生物量形成参数随年度呈现不同组合，反映了各年度观测约束下的条件参数特征。

Table 4. Retained-sample parameter means used in deterministic simulations.

| Parameter | Unit | 2019 | 2020 | 2021 | 2022 |
| --- | --- | --- | --- | --- | --- |
| CCx | fraction | 0.9771 | 0.9773 | 0.9594 | 0.9374 |
| CGC_CD | d⁻¹ | 0.0988 | 0.0956 | 0.1154 | 0.1318 |
| CDC_CD | d⁻¹ | 0.0603 | 0.0607 | 0.0663 | 0.0642 |
| SenescenceCD | d | 137.38 | 137.84 | 134.85 | 134.95 |
| Kcb | – | 1.4866 | 1.4352 | 1.4161 | 1.3775 |
| WP_early | g m⁻² | 18.204 | 11.255 | 10.877 | 13.860 |
| WP_late | g m⁻² | 30.585 | 25.849 | 21.938 | 31.498 |
| HI0 | fraction | 0.4124 | 0.5738 | 0.5800 | 0.4013 |

Phase 2 is conditional on the corresponding retained mean from phase 1.

模型较好地再现了四年冠层形成、快速增长及高覆盖期的变化（图4）。2019—2022年CC的R²cal分别为0.9932、0.9794、0.9902和0.9306，RMSE分别为0.0316、0.0482、0.0370和0.0596。2022年的误差相对较高，主要表现为冠层时序与观测点之间的偏离。总体上，校准后的模型能够描述本试验玉米冠层覆盖度的主要季节变化。

![Figure 4](../figures/Fig04_CC_calibration_EN.png)

Figure 4. Canopy-cover calibration for drip-irrigated maize in 2019–2022. Lines show simulations at phase-specific retained means; circles show LAI-derived calibration observations.

四年地上干生物量模拟值与数字化观测值接近1∶1关系（图5），R²cal为0.9685～0.9966，RMSE为0.5562～1.2520 t·ha⁻¹。2022年生物量误差最小，2021年误差相对较大。年度籽粒产量模拟值依次为16.702、16.804、15.197和14.078 t·ha⁻¹，相对观测值偏差分别为0.92%、−2.81%、−4.18%和−0.02%（表5）。冠层、生物量和产量三类指标共同表明，校准参数能够较好表征各年作物生长与产量水平。

![Figure 5](../figures/Fig05_Biomass_calibration_EN.png)

Figure 5. Observed and simulated aboveground dry biomass in four years. Dashed lines indicate 1:1 agreement. R²cal and RMSE describe calibration fit.

Table 5. Calibration performance for canopy cover, biomass and grain yield.

| Year | CC R²cal | CC RMSE | B R²cal | B RMSE (t ha⁻¹) | Yobs (t ha⁻¹) | Ysim (t ha⁻¹) | Yield RE (%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2019 | 0.9932 | 0.0316 | 0.9926 | 1.0498 | 16.55 | 16.702 | +0.92 |
| 2020 | 0.9794 | 0.0482 | 0.9766 | 1.1393 | 17.29 | 16.804 | -2.81 |
| 2021 | 0.9902 | 0.0370 | 0.9685 | 1.2520 | 15.86 | 15.197 | -4.18 |
| 2022 | 0.9306 | 0.0596 | 0.9966 | 0.5562 | 14.08 | 14.078 | -0.02 |

R²cal = 1 − SSE/SST. Canopy cover is a fraction; biomass is aboveground dry matter.

参数经验区间及先验支持范围如图6所示。CGC_CD的年度区间较集中；CDC_CD和衰老时间的区间相对较宽。2019、2020年CCx在上界1%邻近带中的样本比例分别为22.14%和23.06%，2020、2021年WP_early在下界邻近带中的比例分别为11.43%和23.65%。这些结果说明，不同参数受观测资料约束的程度存在差异，边界邻近集中主要出现在最大冠层覆盖度和早期水分生产率。

![Figure 6](../figures/Fig06_Parameter_intervals_EN.png)

Figure 6. Annual parameter centers, retained-sample intervals and prior supports. Colored intervals show empirical 2.5–97.5% quantiles within each calibration phase. Gray intervals show annual prior supports.

参数中心对样本截取方式的变化较小：四年第一阶段在两种预热截取下的最大均值位移为0.040个样本标准差，保留段前后半段汇总均值的最大位移为0.094个标准差，独立ensemble均值的最大跨度为0.203个标准差。保留时间结构的诊断中，第一阶段最差R̂为1.122～1.181、对应各年最小组bulk ESS为17.79～25.34，与R̂<1.01、ESS≥400的参考目标仍有差距。后续分析采用表4的分阶段保留均值开展确定性模拟；独立ensemble数量、τ及全部诊断值列于附表S3。

为综合比较模型对生物量形成过程的描述，汇总四年37个生物量配对点进行线性回归（图7）。以观测生物量为x、模拟生物量为y，得到y=0.9979x+0.2412，OLS R²为0.9892，Pearson r为0.9946，汇总RMSE为1.0205 t·ha⁻¹。回归斜率接近1，表明四年主要生长阶段的生物量变化具有较好一致性。

![Figure 7](../figures/Fig07_Pooled_biomass_regression_EN.png)

Figure 7. Pooled four-year regression of simulated against observed biomass. The solid line is the OLS fit to 37 calibration pairs; the dashed line indicates 1:1 agreement.

## 3.2 原灌溉日程的年度水量分配

原日程年度入流、出流及储水变化见图8。四年入流量分别为623.14、673.22、776.79和556.22 mm，出流量分别为642.37、611.31、606.83和596.81 mm，剖面储水变化分别为−19.23、61.92、169.97和−40.58 mm。其中，2021年灌水量最大，但其ET为605.14 mm，与其他年份处于相近量级；该年全剖面储水由535.70增加至705.67 mm，表现出明显的季内增储。上述差异为解释后续减灌水结果提供了水量依据。

![Figure 8](../figures/Fig08_Annual_water_balance_EN.png)

Figure 8. Seasonal inflow, outflow and storage change under the original DI schedules. Inflow comprises precipitation and actual irrigation; outflow comprises ET and other losses. Storage change is final minus initial profile and surface water.

## 3.3 参数敏感性及年度稳定性

各输出的参数总效应指数见图9。籽粒产量主要受晚期WP、HI0、早期WP和Kcb影响；生物量主要受水分生产率与基础作物系数影响；季节ET以Kcb为主导；最大冠层覆盖度以CCx为主导。产量、生物量、ET及最大CC四个输出的年度平均参数排序在四年间一致，两两年度Spearman排序相关系数均为1.00，说明在本研究共同输入范围内，主要参数的作用层级具有年度稳定性。

![Figure 9](../figures/Fig09_Sobol_four_outputs_EN.png)

Figure 9. Total-effect Sobol indices for four crop-model outputs across years. Cells show means of three N=512 scrambles under the same independent input ranges; all panels use the same color scale.

产量一阶和总效应指数及其数值区间见图10。晚期WP的四年平均Sₜ为0.396，年度范围为0.353～0.426；HI0、早期WP和Kcb分别为0.206、0.164和0.145（表6）。前四个参数的总效应之和约0.911，反映出产量形成主要受生物量转换和水分消耗过程控制。年度排序的一致性支持采用等权四年均值概括主要敏感性层级，年度区间则保留了不同气象及生长条件造成的幅度变化。

![Figure 10](../figures/Fig10_Yield_Sobol_CI_EN.png)

Figure 10. First-order and total-effect yield sensitivity with four-year descriptive means. Error bars show approximate 95% numerical bootstrap intervals for three-scramble annual means. Diamonds indicate equal-weight means across the four years.

Table 6. Four-year descriptive yield sensitivity under common input ranges.

| Parameter | Mean S₁ | Mean Sₜ | Minimum Sₜ | Maximum Sₜ |
| --- | --- | --- | --- | --- |
| WP_late | 0.377 | 0.396 | 0.353 | 0.426 |
| HI0 | 0.193 | 0.206 | 0.203 | 0.208 |
| WP_early | 0.142 | 0.164 | 0.139 | 0.198 |
| Kcb | 0.130 | 0.145 | 0.139 | 0.148 |
| CCx | 0.049 | 0.057 | 0.052 | 0.060 |
| CGC_CD | 0.033 | 0.040 | 0.029 | 0.051 |
| SenescenceCD | 0.003 | 0.011 | 0.006 | 0.015 |
| CDC_CD | 0.003 | 0.006 | 0.003 | 0.009 |

Each annual estimate averages three scrambles; the four annual estimates receive equal weights.

## 3.4 五生育期灌水量与产量的帕累托关系

图11展示四年全范围五期NSGA-III非支配前沿。蓝色虚线连接已计算的非支配解，红点为标注解，括号内依次给出苗期、拔节期、抽穗期、灌浆期和成熟期的实际灌水合计；橙色空心点标示正式95%门槛主候选。各年前沿呈增加后逐渐趋于平台的关系。零灌水情景保留当年降水和初始土壤水，四年产量分别为9.071、6.184、6.140和5.850 t·ha⁻¹。

![Figure 11](../figures/Fig11_Five_stage_Pareto_fronts_EN.png)

Figure 11. Five-stage NSGA-III yield–irrigation fronts and individual-event schedules across four years. Red labels give rounded actual totals for Seedling, Jointing, Heading, Grain filling and Maturity. Stars show original DI model baselines; orange open circles show formal selected candidates. The displayed full-range fronts pool three 80-individual, 60-generation supplemental searches per year. Irrigation cancelled after crop termination is excluded from actual totals.

四年主候选灌水量分别为209.83、306.50、264.50、257.47 mm，较原DI日程分别减少52.88、45.24、58.25、36.40%，对应产量为15.725、16.427、15.068、13.390 t·ha⁻¹（表7）。2021年候选相对模型DI基准的产量差为-0.85%，相对田间观测值为-4.99%。因此，产量门槛、观测偏差及相对模型基准的变化分别列示。

Table 7. Selected five-stage NSGA-III schedules at 95% observed yield.

| Year | Recorded I (mm) | Selected I (mm) | Selected yield (t ha⁻¹) | I reduction (%) | Yield RE (%) | ET (mm) |
| --- | --- | --- | --- | --- | --- | --- |
| 2019 | 445.27 | 209.83 | 15.725 | 52.88 | -4.99 | 599.84 |
| 2020 | 559.76 | 306.50 | 16.427 | 45.24 | -4.99 | 592.92 |
| 2021 | 633.47 | 264.50 | 15.068 | 58.25 | -4.99 | 593.68 |
| 2022 | 404.84 | 257.47 | 13.390 | 36.40 | -4.90 | 568.93 |

The primary candidate minimizes actual irrigation within the feasible nondominated union of the five formal NSGA-III final populations. Yield RE uses the published annual observation.

与前期四窗口代表方案相比，本轮灌水量分别变化-8.53、-5.92、-2.80、-3.32 mm。新控制空间同时增加了灌水日期和事件分配自由度，且精确包含原日程与旧可行方案。相同物理设定下，低灌水高产区间在两种控制空间中均出现，水量来源需进一步结合蒸散与储水差额解释。

## 3.5 减灌水量的水量来源

原日程与五期主候选的水量差额见图12及表8。四年ET分别下降38.16、17.04、11.46、27.85 mm，占基准ET的5.98、2.79、1.89、4.67%；季末全剖面储水分别下降193.14、234.87、356.85、119.50 mm，解释了82.03、92.74、96.72、81.09%的灌水差额。实际蒸散变化较小，而季末水状态发生明显变化。

![Figure 12](../figures/Fig12_Irrigation_reduction_components_EN.png)

Figure 12. Water-balance components of irrigation reduction under the selected five-stage schedules. Percentages indicate the terminal-storage difference divided by the irrigation reduction. ET, storage and other-loss differences use identical annual forcing and initial soil water.

Table 8. Water-balance decomposition for the selected five-stage schedules.

| Year | I reduction (mm) | ET decrease (mm) | Lower final S (mm) | Other losses (mm) | Storage share (%) |
| --- | --- | --- | --- | --- | --- |
| 2019 | 235.44 | 38.16 | 193.14 | 4.14 | 82.03 |
| 2020 | 253.26 | 17.04 | 234.87 | 1.34 | 92.74 |
| 2021 | 368.97 | 11.46 | 356.85 | 0.66 | 96.72 |
| 2022 | 147.37 | 27.85 | 119.50 | 0.02 | 81.09 |

Differences are recorded schedule minus selected candidate. Storage integrates the unchanged 0–2.4 m simulated profile. Signed components sum to irrigation reduction.

2021年少灌368.97 mm，其中11.46 mm对应ET下降、0.66 mm对应其他损失下降，356.85 mm对应季末储水差。原日程由535.70增储至705.67 mm，五期候选则由相同初值降至348.82 mm，消耗初始储水186.89 mm。减少基准日程增储与增加初始储水利用共同支撑了该年的较低季节灌水量。逐日与季节水量核算及完整模型回放均通过核对，未加速原始方程回放的最大输出差约为1.14×10⁻¹³。

## 3.6 五期水量分配、逐次日程与算法对照

图13按实际日期绘制四年主候选的每次灌水量，完整日程见附表S5—S8。四年正水量事件数依次为12、13、9和8，其中≥0.1 mm事件分别为8、8、3和6；两种计数对应同一组未取整控制量。2021年≥0.1 mm的事件为6月15日92.959 mm、6月28日85.822 mm和7月29日85.634 mm，其余微量正数同时保留在源表中。

![Figure 13](../figures/Fig13_Optimized_event_calendar_EN.png)

Figure 13. Every optimized irrigation date and depth in the selected four-year schedules. Colors indicate five phenological stages, with up to three optional events in each stage. Positive-depth event counts include trace numerical amounts; counts for depths ≥0.1 mm are reported separately. All exact positive depths remain in the source table.

五期总量与次数见图14和表9。2021年水量主要分配在拔节期178.782 mm和灌浆期85.634 mm，其他阶段合计约0.084 mm。2019年则将较多水量分配在苗期与抽穗期。阶段合计、逐次实际执行量及模型季节灌水量相互核对，最大差小于10⁻⁷ mm。各期允许0～3次，并非要求每期都灌满3次。

![Figure 14](../figures/Fig14_Five_stage_totals_EN.png)

Figure 14. Five-stage irrigation totals and positive-depth event counts. Gray bars show recorded DI schedules and colored bars show selected schedules. Counts include merged exact positive depths. Stage sums reconcile with actually executed seasonal irrigation.

Table 9. Five-stage actual irrigation totals and event counts.

| Year | Seedling (mm) | Jointing (mm) | Heading (mm) | Grain filling (mm) | Maturity (mm) | Positive events | Events ≥0.1 mm |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2019 | 85.168 | 4.645 | 119.752 | 0.241 | 0.025 | 12 | 8 |
| 2020 | 108.288 | 94.704 | 2.255 | 88.711 | 12.541 | 13 | 8 |
| 2021 | 0.003 | 178.782 | 0.054 | 85.634 | 0.027 | 9 | 3 |
| 2022 | 0.035 | 181.420 | 2.935 | 73.030 | 0.044 | 8 | 6 |

All exact positive depths count as events after same-day merging; ≥0.1 mm counts are additional descriptive statistics. Stage totals use unrounded source controls.

两算法五种子的种群超体积变化见图15，最终种群并集指标见表10。NSGA-III与NSGA-II年度最低灌水量之差的绝对值为0.03～1.47 mm，得到相近但不完全相同的权衡关系。主日程按既定NSGA-III选择规则确定；NSGA-II的最低水量及各自最高产量另表给出。共同初值、相同目标和约束下的算法对照与逐日物理核算相互补充。

![Figure 15](../figures/Fig15_Algorithm_search_history_EN.png)

Figure 15. NSGA-III and NSGA-II population hypervolume across formal searches. Lines show five-seed means and shading shows seed ranges. Algorithms share disclosed recorded-schedule and four-window initialization anchors. Final feasible-population union metrics are tabulated separately.

Table 10. Final feasible-population union metrics from five seeds.

| Year | NSGA-III min I (mm) | NSGA-II min I (mm) | III minus II (mm) | NSGA-III HV | NSGA-II HV |
| --- | --- | --- | --- | --- | --- |
| 2019 | 209.832 | 209.866 | -0.035 | 0.541654 | 0.541554 |
| 2020 | 306.499 | 305.027 | +1.472 | 0.456772 | 0.459376 |
| 2021 | 264.500 | 264.546 | -0.046 | 0.571337 | 0.571307 |
| 2022 | 257.465 | 256.765 | +0.700 | 0.377835 | 0.379541 |

Each method shares the disclosed recorded and four-window initialization anchors, objectives and constraints. The primary calendar follows NSGA-III; hypervolume uses the stated annual normalization.

# 4 讨论

## 4.1 多指标分阶段校准对生长过程的约束

冠层覆盖度控制潜在蒸腾及冠层发育，水分生产率与收获指数控制生物量和籽粒形成[3]。本研究按照上述过程设置两个校准阶段，使冠层与耗水指标先确定作物生长及水分利用的基本轨迹，再以生物量和产量确定转换效率。CC、生物量及年产量的拟合结果体现了多指标约束的互补性。敏感性分析中晚期WP和HI0对产量的主导作用，与AquaCrop的产量形成机制相符，也说明第二阶段校准对于灌溉响应分析具有重要作用。

年度参数组合同时受气象条件、资料覆盖和误差假设影响。原校准中，衰老起始时间之后的CC观测仅有1～2个，CDC_CD和衰老时间的经验区间较宽；相较之下，快速冠层增长过程的观测较密集，对CGC_CD约束较强。第一阶段均值对预热截取和时间分段变化较小，而序列诊断仍体现较强时间相关。因此，本文用参数中心描述确定性模拟结果，用采样诊断报告参数分布的计算精度，两类结果分别评价[5,15]。

## 4.2 高产平台与土壤储水的调节作用

灌水总量与作物蒸散需求通过降水、初始储水及季末储水变化相联系。Qin等[16]从耗水分量讨论充分灌溉条件下覆膜滴灌的作用。本研究2021年减灌368.97 mm，而ET仅下降11.46 mm，季末储水差达到356.85 mm。该高产平台体现了既定初值、参数和单季边界下的灌溉—储水替代关系。

从水量组成看，基准方案的较大灌水量部分转化为季末增储；代表方案则以较低终值结束生育期。两者的灌水差具有明确的内部守恒关系。将“灌水减少率”与“ET下降率”分别报告，能够说明灌溉管理改变的是供水量、耗水量还是土壤水状态，并与灌溉效率研究强调的水量尺度相衔接[13]。在制度评价中，将季末允许储水范围与关键生育期供水水平配套考察，可进一步明确方案的跨季使用条件。

## 4.3 生育期日程、事件尺度与制度应用

五期划分与文献中的作物生育过程对应，逐次日期—水量联合优化进一步细化了灌溉决策。某些阶段的水量集中与当年作物过程及储水缓冲共同有关。各年优化日期是在已知年度天气、固定参数和初始墒情下求得的回顾性候选；实际轮灌安排可结合未来天气和当地供水条件作滚动调整。

单次水量与季节总量需同时评价。四年候选的最大单次水量分别为117.03、108.29、92.96、181.31 mm，具体完整数值见附表S9。2022年最大单次达到181.31 mm，而原日程最大单次为85.85 mm，反映了本轮未额外施加设备单次上限时的集中供水倾向。将管网能力、最低可执行水量、灌水间隔和允许季末储水配套纳入，可进一步形成实施尺度的制度。

前期四窗口空间中的四种单目标算法对照帮助识别了较低灌水区间的可重复性；本轮五期空间中的NSGA-II与NSGA-III对照进一步补充了时序自由度变化后的证据。两组试验的控制空间和初值方式分别记录。所有候选均与相应日期、季节水量账及模型设定联结，从而使算法结果与水分过程解释保持一致。

# 5 结论

（1）基于2019—2022年膜下滴灌玉米资料，建立了冠层与耗水、生物量与产量相衔接的两阶段参数校准方法。四年CC和生物量的R²cal分别为0.9306～0.9932和0.9685～0.9966，产量相对偏差为−4.18%～0.92%，模型较好再现了各年度主要生长过程和产量水平。

（2）在共同独立参数范围下，产量、生物量、ET及最大CC的年度平均敏感性排序一致。晚期WP、HI0、早期WP和Kcb的产量Sₜ四年均值分别为0.396、0.206、0.164和0.145，表明水分生产率、收获指数及耗水过程是本研究产量响应的主要控制环节。

（3）以五生育期、每期最多3个可选事件构建30维日期—水量控制空间。在95%观测产量门槛下，四年NSGA-III主候选为209.83、306.50、264.50、257.47 mm，较原日程减少36.40～58.25%。五期总量和逐次日程均已输出，两种遗传算法的年度最低灌水量差为0.03～1.47 mm。

（4）五期优化后ET下降1.89～5.98%，季末储水差解释了81.09～96.72%的减灌量。2021年储水差为356.85 mm，占该年减灌量的96.72%。将作物生长、逐次供水和储水变化统一分析，可明确单季灌溉优化的水量来源及跨季应用条件。

# 数据与代码

年度原始输入、分阶段MCMC检查点、敏感性响应、优化解集、日水量账和英文图表按研究阶段归档。本文图表源数据、统计脚本和逐项修订记录随稿提供。研究项目编号：X2026100190937。

[1] 王尚今. 不同灌溉方式下覆膜玉米田水热氮传输及作物生长的观测与模拟[D]. 北京: 中国农业大学, 2023.

[2] Liu, Y., Wang, Y., Šimůnek, J., & Liao, R. (2025). An integrated data assimilation, crop modeling, and multi-objective optimization framework for improving cotton irrigation water use efficiency. Agricultural Water Management, 319, 109774. DOI: 10.1016/j.agwat.2025.109774.

[3] Steduto, P., Hsiao, T. C., Raes, D., & Fereres, E. (2009). AquaCrop—The FAO crop model to simulate yield response to water: I. Concepts and underlying principles. Agronomy Journal, 101(3), 426–437. DOI: 10.2134/agronj2008.0139s.

[4] Kelly, T. D., & Foster, T. (2021). AquaCrop-OSPy: Bridging the gap between research and practice in crop-water modeling. Agricultural Water Management, 254, 106976. DOI: 10.1016/j.agwat.2021.106976.

[5] Foreman-Mackey, D., Hogg, D. W., Lang, D., & Goodman, J. (2013). emcee: The MCMC Hammer. Publications of the Astronomical Society of the Pacific, 125, 306–312. DOI: 10.1086/670067.

[6] Sobol’, I. M. (2001). Global sensitivity indices for nonlinear mathematical models and their Monte Carlo estimates. Mathematics and Computers in Simulation, 55(1–3), 271–280. DOI: 10.1016/S0378-4754(00)00270-6.

[7] Saltelli, A., Annoni, P., Azzini, I., Campolongo, F., Ratto, M., & Tarantola, S. (2010). Variance based sensitivity analysis of model output. Design and estimator for the total sensitivity index. Computer Physics Communications, 181(2), 259–270. DOI: 10.1016/j.cpc.2009.09.018.

[8] Deb, K., Pratap, A., Agarwal, S., & Meyarivan, T. (2002). A fast and elitist multiobjective genetic algorithm: NSGA-II. IEEE Transactions on Evolutionary Computation, 6(2), 182–197. DOI: 10.1109/4235.996017.

[9] Deb, K., & Jain, H. (2014). An evolutionary many-objective optimization algorithm using reference-point-based nondominated sorting approach, Part I: Solving problems with box constraints. IEEE Transactions on Evolutionary Computation, 18(4), 577–601. DOI: 10.1109/TEVC.2013.2281535.

[10] Blank, J., & Deb, K. (2020). pymoo: Multi-objective optimization in Python. IEEE Access, 8, 89497–89509. DOI: 10.1109/ACCESS.2020.2990567.

[11] Storn, R., & Price, K. (1997). Differential evolution—A simple and efficient heuristic for global optimization over continuous spaces. Journal of Global Optimization, 11, 341–359. DOI: 10.1023/A:1008202821328.

[12] Xiang, Y., Gubian, S., Suomela, B., & Hoeng, J. (2013). Generalized simulated annealing for global optimization: The GenSA package. The R Journal, 5(1), 13–28. DOI: 10.32614/RJ-2013-002.

[13] Grafton, R. Q., Williams, J., Perry, C. J., et al. (2018). The paradox of irrigation efficiency. Science, 361(6404), 748–750. DOI: 10.1126/science.aat9314.

[14] Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998). Crop evapotranspiration: Guidelines for computing crop water requirements. FAO Irrigation and Drainage Paper 56. FAO, Rome.

[15] Vehtari A, Gelman A, Simpson D, Carpenter B, Bürkner P C. Rank-normalization, folding, and localization: An improved R̂ for assessing convergence of MCMC[J]. Bayesian Analysis, 2021, 16(2): 667–718. DOI: 10.1214/20-BA1221.

[16] Qin S, Li S, Kang S, et al. Can the drip irrigation under film mulch reduce crop evapotranspiration and save water under the sufficient irrigation condition?[J]. Agricultural Water Management, 2016, 177: 128–137.
