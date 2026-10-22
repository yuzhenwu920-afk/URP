# 原始 MCMC 图件逐图解析
所有图采用英文标签；经验分布均保留相关样本和未认证收敛的限制。

## D01_Independent_ensemble_convergence_EN
Phase-1 diagnostics after the original tau-based burn-in. Each group contains one matched walker index from each of four independent ensembles; walkers in an ensemble are not independent chains. Cells show the maximum rank-normalized folded split R-hat and minimum bulk ESS over 32 dependent groups. ESS values are not summed. Reference criteria are R-hat<1.01 and bulk/tail ESS>=400 within each group. The displayed ESS is not the pooled effective sample size.

四年第一阶段均未达到严格阈值。这里的 ESS 是“每个固定 walker 编号跨四个独立 ensemble”的诊断组数值，并非四年样本的总 ESS；不能把 32 组 ESS 相加。各参数组中位 R̂ 也约为 1.032–1.068，问题并非只发生在一个极端 walker。

## D02_Autocorrelation_length_and_acceptance_EN
Original chain length divided by maximum emcee IAT, alongside acceptance fractions. Phase 1 has four ensembles per year; phase 2 has one. Error bars span the observed walker acceptance range. All walkers make accepted post-burn moves. A satisfactory acceptance fraction does not establish convergence. IAT estimates from short chains can themselves be unstable; 50*tau is an inherited length reference.

第一阶段的时间长度不足；第二阶段 2020/2021 也未达到 50τ 长度参考，而 2019/2022 达到这一参考仍不代表独立链验证通过。接受率不低，只说明提议经常被接受，不能保证链已充分探索分布。

## D03_Phase1_four_year_trace_blocks_EN
Phase-1 independent-ensemble trajectories for all five parameters and four years. Each point averages a non-overlapping 50-step block across the 32 coupled walkers. Smoothing is for readability and does not demonstrate convergence. Gray regions mark the original burn-in. Raw time-ordered checkpoints and unsmoothed diagnostic statistics are provided.

四组 ensemble 的均值轨迹有共同覆盖区，未见均值完全分离为几个相距很远的群。轨迹中仍有长时间起伏；平滑均值图不足以取代 R̂、ESS 和尾部诊断。阴影为原规则丢弃部分，未重新挑选窗口。

## D04_Phase2_conditional_traces_EN
Phase-2 trajectories conditional on the retained phase-1 arithmetic-mean handoff. Faint lines show six fixed walker indices at a plotting stride of five; bold lines average all walkers in 50-step time blocks. These walkers are coupled and must not be used as independent convergence chains. All statistics use full, unthinned checkpoints.

三参数条件链总体仍有移动，但每年只有一个 ensemble，不能把淡色 walker 轨迹当成独立链。第二阶段承接第一阶段保留样本的算术均值，未传播第一阶段全部不确定性。

## D05_Boundary_mass_four_years_EN
Empirical retained-sample mass in the lower and upper 1% bands of each recorded support. Phase 1 and conditional phase 2 are separated by the white divider. CCx upper-band masses are 22.14% and 23.06% in 2019 and 2020; WP_early lower-band masses are 11.43% and 23.65% in 2020 and 2021. This is neighborhood accumulation, not evidence that values were numerically clipped to an endpoint. A uniform prior assigns 1% mass to such a band; Gaussian-prior band masses are recorded separately.

撞墙必须按年份、参数讨论：2019/2020 的 CCx 上界附近堆积突出，2020/2021 的 WP_early 下界附近堆积突出，HI0 在 2020/2021 上界附近也有堆积。原值都在支持域内；邻界堆积不是代码把样本强制截成边界值的证据。

## D06_Prior_to_sample_contraction_EN
Retained-sample SD relative to the analytical SD of the actual recorded prior (including truncation for normal priors). CDC_CD retains 91.7–96.8% of prior SD, consistent with limited late-season information. This is a descriptive contraction diagnostic, not a calibrated measure of identifiability or parameter bias. The 2022 priors have different density families and phase-2 supports.

CDC_CD 的经验分布宽度接近真实先验宽度，显示现有证据对它提供的信息有限。CCx、CGC_CD 收缩较强，但收缩本身不证明后验正确，也不消除其混合问题。

## D07_Late_season_prior_overlap_EN
Phase-1 CDC_CD and SenescenceCD distributions overlaid on their actual truncated-normal priors. There are only 2, 2, 1 and 2 CC observations on or after the rounded senescence handoff in 2019–2022. The forward model rounds SenescenceCD to integer days, giving a piecewise response. Prior-like CDC_CD marginals support weak information but do not alone establish the cause of all mixing failures.

CDC_CD 保留了约 92%–97% 的先验标准差。每年衰老时间点之后仅有 1–2 个 CC 数据点，且 SenescenceCD 在模型中被四舍五入为整数日，后期参数的连续细调缺少充分观测分辨率。

## D08_Phase_specific_correlation_matrices_EN
Within-phase Pearson correlations from all retained time-ordered sample rows after flattening only for descriptive correlation. Separate panels preserve the 5-D phase-1 and 3-D conditional phase-2 dependence structures. The strongest pair is 2019 WP_late–HI0 (r=-0.871); corresponding correlations are -0.595, -0.463 and -0.645 in 2020–2022. These correlations show compensation, not causally identified parameter errors or an eight-dimensional joint posterior.

相关性按阶段分别计算，没有伪造八参数联合后验。第一阶段相关矩阵条件数仅约 2.48–3.50，不能把四年第一阶段未收敛都归咎于极端强的线性参数相关。

## D09_WP_HI_compensation_EN
Conditional phase-2 WP_late–HI0 joint sample distributions. Because final yield depends on both biomass formation and harvest index, multiple pairs can give similar yields. Approximate biomass observations reduce but do not remove this trade-off. Correlations are descriptive for the existing samples; there is no independent-ensemble convergence certification for phase 2.

WP_late 增大与 HI0 减小可以部分抵消，使产量仍接近目标。2019 年此关系最明显。2021 年相关约 −0.463，属于可见补偿，不能夸大为完全不可辨识。

## D10_Ensemble_location_and_time_drift_EN
Phase-1 differences normalized by pooled retained-sample SD. The span of four ensemble means is at most 0.204 SD; each ensemble's difference between equal early and late retained halves is at most 0.187 SD. This supports modest observed location drift rather than gross between-ensemble separation, but it does not override failed rank R-hat/ESS diagnostics or exclude unsampled modes.

四组第一阶段均值最大跨度约为 0.204 个保留样本标准差；各组前后半段均值最大变化约为 0.187 个标准差。分布位置没有表现为巨大分离，但有限混合、尾部与 Monte Carlo 误差仍未满足严格条件。

## D11_Autocorrelation_four_years_EN
Mean within-walker autocorrelation for all sampled parameters. Each retained walker time series is centered and normalized separately; ACFs are then averaged within ensemble and, for phase 1, over the four ensembles. This display is not a pooled ESS estimate. Acceptance can be frequent while samples remain strongly time dependent.

短间隔状态高度相关，因此保存了几十万行不等于有几十万个独立后验样本。增加 walkers、稀疏抽取或平滑轨迹都不能替代足够长的时间探索。

## D12_Burnin_and_ensemble_functional_checks_EN
Sensitivity checks using the same unchanged checkpoints. Discarding the first 1000 steps raises the worst matched-walker R-hat to 1.347, 1.281, 1.264 and 1.176 across 2019–2022; shorter retained length is one reason. Four independent ensemble-mean time series also fail for some parameters (annual worst R-hat 1.110, 1.182, 1.100 and 1.169), so the finding is not solely a single extreme walker comparison. Neither check licenses post hoc selection of a passing segment.

简单丢掉前 1000 步反而提高了最差 R̂，表明不能用增加 burn-in 掩盖不足。四个独立 ensemble 的均值与 CDF 等时间序列也存在混合问题，原结论不是仅由“最差 walker”这个保守标准造成的。