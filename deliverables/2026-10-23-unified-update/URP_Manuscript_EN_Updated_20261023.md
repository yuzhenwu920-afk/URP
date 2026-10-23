# AquaCrop parameter calibration and five-stage irrigation scheduling for film-mulched drip-irrigated maize

Irrigation amount and timing jointly regulate maize production in arid northwestern China. Using four years (2019–2022) of film-mulched drip-irrigated maize observations from Wuwei, Gansu, we combined staged Markov chain Monte Carlo (MCMC) calibration of a project-specific AquaCrop implementation, Sobol sensitivity analysis, and NSGA-III/NSGA-II irrigation scheduling. Calibration used canopy cover, water use, biomass and grain yield. Canopy-cover and biomass calibration coefficients of determination ranged from 0.9306 to 0.9932 and from 0.9685 to 0.9966, respectively; grain-yield biases ranged from −4.18% to 0.92%. Mean total-effect yield indices were 0.396 for late water productivity, 0.206 for reference harvest index, 0.164 for early water productivity and 0.145 for the basal crop coefficient, with consistent annual-mean rankings. Up to three optional irrigation events were allocated to each of five phenological stages, and individual depths and dates were optimized jointly. At a yield gate of 95% of observed yield, selected seasonal depths were 209.83, 306.50, 264.50, 257.47 mm, reducing irrigation by 36.40–58.25% relative to recorded schedules under the same annual model settings. Evapotranspiration decreased by 1.89–5.98%, whereas lower terminal profile storage accounted for 81.09–96.72% of the irrigation differences. Linking staged calibration, individual-event scheduling and soil-water accounting clarifies the water sources supporting high-yield candidates under the specified seasonal conditions.

# 1 Introduction

Agricultural production in arid northwestern China depends strongly on irrigation. Allocating water across crop development is therefore central to coordinating yield and agricultural water use. Film-mulched drip irrigation modifies the soil hydrothermal environment, reduces soil evaporation and improves root-zone water supply [1,16]. Crop water use also depends on rainfall, initial soil water and growth dynamics, so equal seasonal irrigation can produce different yields across years and schedules. Assessing irrigation regimes requires joint consideration of crop growth, evapotranspiration and soil-water storage, including the components of reduced irrigation [13].

Combining crop models with optimization provides a quantitative basis for analyzing yield–irrigation relationships. AquaCrop links canopy cover, transpiration, biomass and harvest index to represent the effects of water supply on production [3,4]. Liu et al. [2] integrated multiple data sources, crop modeling, MCMC calibration, sensitivity analysis and multi-objective optimization in cotton irrigation research. Building on this methodological structure, staged calibration can reflect the available observations before seasonal water amounts and their timing are optimized.

This study uses film-mulched drip-irrigated maize data from Wuwei, Gansu, for 2019–2022. Canopy cover, transpiration and soil evaporation first constrain canopy and water-use parameters; biomass and yield then constrain water productivity and harvest index. Sobol analysis under common parameter ranges assesses annual sensitivity stability. NSGA-III and NSGA-II subsequently optimize irrigation schedules, while solver comparisons and water accounting examine the mechanisms supporting high yields with lower seasonal irrigation. The framework connects parameter calibration, crop processes, irrigation trade-offs and storage changes.

# 2 Materials and methods

## 2.1 Research framework

The workflow comprises data preparation, model calibration and decision analysis (Fig. 1). Inputs include climate forcing, soil and management conditions, and crop-growth observations. Calibration separates canopy and water-use parameters from biomass- and yield-formation parameters. Analysis covers parameter sensitivity, multi-objective scheduling, solver comparisons and water accounting. Each annual model uses its corresponding observations and weather.

![Figure 1](../figures/Fig01_Research_workflow_EN.png)

Figure 1. Research framework for staged calibration, sensitivity analysis and irrigation optimization. Three patterned columns summarize data preparation, crop-model calibration and decision analysis.

## 2.2 Study site and data sources

This study uses existing field observations of film-mulched drip-irrigated maize for 2019–2022 [1]. The observation site is at the Shiyanghe Experimental Station of China Agricultural University in Wuwei, Gansu (37°52′ N, 102°52′ E; 1581 m above sea level). The temperate continental arid climate has mean annual precipitation of approximately 164 mm, with groundwater at a depth of approximately 40–50 m. The DI observation field measured 400 m × 200 m and was planted at 79,365 plants ha⁻¹. Film strips were 1.2 m wide, separated by 0.4 m, giving 75% coverage (Fig. 2).

![Figure 2](../figures/Fig02_Study_site_EN.png)

Figure 2. Location of the study station and dimensions of the drip-irrigated maize field. Station coordinates and field dimensions are based on the reported field observations [1]. The field panel is a size schematic with illustrative orientation.

Soil inputs comprise measured physical properties of the 0–100 cm profile in the DI observation field [1]. Six measured layers cover 0–100 cm, with sand, silt and clay contents of 10.38–30.81%, 58.67–76.53% and 10.52–16.20%, respectively. All layers are classified as silt loam, with bulk density ranging from 1.29 to 1.69 g cm⁻³ (Table 1). These layers are combined with annual initial water profiles; the archived model extends the soil structure below 1 m to a simulated depth of 2.4 m.

Table 1. Measured soil properties of the drip-irrigated maize field [1].

| Depth (cm) | Sand (%) | Silt (%) | Clay (%) | Bulk density (g cm⁻³) | Texture |
| --- | --- | --- | --- | --- | --- |
| 0–10 | 29.70 | 59.66 | 10.64 | 1.65 | Silt loam |
| 10–20 | 30.81 | 58.67 | 10.52 | 1.65 | Silt loam |
| 20–40 | 19.43 | 68.25 | 12.32 | 1.69 | Silt loam |
| 40–60 | 13.22 | 70.58 | 16.20 | 1.29 | Silt loam |
| 60–80 | 10.38 | 74.87 | 14.75 | 1.48 | Silt loam |
| 80–100 | 11.81 | 76.53 | 11.66 | 1.45 | Silt loam |

Particle fractions refer to >0.05 mm, 0.002–0.05 mm and <0.002 mm, respectively.

The four-year DI observations include irrigation schedules, phenological periods, leaf area index, biomass, grain yield and water use [1] (Table 2). Canopy cover (CC) was calculated from digitized leaf area index (LAI) using Eq. (1), yielding 48 calibration pairs. Aboveground dry biomass was digitized from published figures, yielding 37 pairs. Grain yield is expressed at 13% moisture. Remote-sensing CCquad series provide auxiliary comparisons; treatment labels and date coverage are documented in Table S1.

CC = 1.005[1 − exp(−0.6LAI)]¹·² (1)

Table 2. Annual DI observations used for crop-model calibration.

| Year | Irrigation (mm) | Yobs (t ha⁻¹) | CC / B pairs | ETobs (mm) | Es,obs (mm) |
| --- | --- | --- | --- | --- | --- |
| 2019 | 445.27 | 16.55 | 12 / 9 | 661.45 | 76 |
| 2020 | 559.76 | 17.29 | 13 / 10 | 637.03 | 79 |
| 2021 | 633.47 | 15.86 | 11 / 8 | 626.81 | 78 |
| 2022 | 404.84 | 14.08 | 12 / 10 | 584.11 | 81 |

Yield is expressed at 13% moisture. The 2021 event sum is 633.47 mm; the published rounded seasonal total is 633.46 mm.

Daily forcing includes minimum and maximum air temperature, precipitation and reference evapotranspiration (ETo) [14]. The newly supplied four-year weather values match the archived raw inputs, with continuous full-year dates. The model uses the audited ETo series and actual executed calendar dates for water accounting. Seasonal precipitation totals are 177.87, 113.46, 143.32 and 151.38 mm, and ETo totals are 595.62, 632.26, 612.93 and 609.26 mm. Figure 3 shows daily distributions: 2019 has greater seasonal rainfall, whereas 2020 has higher reference evaporative demand.

![Figure 3](../figures/Fig03_Environmental_drivers_EN.png)

Figure 3. Daily precipitation and reference evapotranspiration during the four model seasons. ETo uses the archived audited series; precipitation totals follow the executed model dates.

## 2.3 AquaCrop implementation and fixed settings

The implementation uses AquaCrop-OSPy 3.1.0 with the archived project-specific process modifications [3,4]. At a daily time step, soil water status regulates canopy expansion, stomatal behavior and senescence. Normalized transpiration and effective water productivity determine aboveground dry biomass, and adjusted harvest index determines dry grain yield. Early/late water-productivity switching dates are 10 July 2019, 14 July 2020, 13 July 2021 and 5 July 2022. Moisture conversion follows Eq. (2).

Y₁₃ = Ydry / (1 − 0.13) (2)

The four-year main analysis retains the original calibrated structure: MulchPct=75%, Zmin=0.30 m, Zmax=2.30 m and fMulch=0. The implementation modifies the canopy treatment of evaporation and fixes the native AquaCrop mulch multiplier at one, maintaining consistency between calibration and optimization. Equation (3) distinguishes coverage from the evaporation-adjustment factor. Separate conditional recalibrations for 2021 use fMulch=0.50, 0.75 and 0.85 with a 1 m maximum root depth and are retained as supplemental structural experiments.

Es,mul = Es,pot[1 − fMulch × MulchPct/100] (3)

## 2.4 Staged MCMC calibration and assessment

The emcee ensemble sampler [5] is used in two calibration stages. Stage 1 estimates CCx, CGC_CD, CDC_CD, SenescenceCD and Kcb, representing maximum canopy cover, canopy growth and decline coefficients, senescence timing and basal crop coefficient. Gaussian-error likelihoods combine CC, seasonal transpiration and soil evaporation. Stage 2 fixes the retained stage-1 mean and estimates WP_early, WP_late and HI0 using biomass and grain yield. Parameter definitions and common sensitivity-analysis ranges appear in Table 3; annual calibration priors appear in Table S2.

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

Stage-1 error scales are 0.05 for CC, 15 mm for soil evaporation, and 10% of the annual transpiration target. Stage 2 uses archived error scales for digitized biomass observations and 0.5829 t ha⁻¹ for dry grain yield. Each ensemble has 32 walkers and 2000 steps. Every year has four independent stage-1 ensembles and one stage-2 ensemble. Parameter means and empirical 2.5–97.5% quantiles are calculated after the recorded burn-in removal.

Sampling diagnostics include rank-normalized folded split R̂, bulk and tail effective sample sizes (ESS), and integrated autocorrelation time τ [15]. Reference targets are R̂<1.01 and bulk/tail ESS≥400, with a chain-length-to-τ ratio of 50 as a heuristic. Stage-1 comparisons match walker indices across four independently initialized ensembles while preserving the time dimension. Parameter centers are additionally compared across burn-in choices and halves of the retained sequences.

Calibration fit is assessed by R²cal, RMSE and relative grain-yield bias (RE), defined in Eqs. (5)–(7). The pooled biomass regression uses observations on the horizontal axis and simulations on the vertical axis, with separate OLS R² and Pearson correlation r. Boundary diagnostics quantify sample fractions within the lower and upper 1% of each prior-support width.

R²cal = 1 − Σ(Sᵢ − Oᵢ)² / Σ(Oᵢ − Ō)² (5)

RMSE = [Σ(Sᵢ − Oᵢ)²/n]¹ᐟ² (6)

RE = (Ysim − Yobs)/Yobs × 100% (7)

## 2.5 Global Sobol sensitivity analysis

Sobol variance decomposition provides first-order effects S₁ and total effects Sₜ [6,7]. All eight parameters are sampled independently and uniformly within the common ranges in Table 3, using identical input distributions across years. Outputs include grain yield, biomass, transpiration, soil evaporation, evapotranspiration and maximum canopy cover. First-order effects represent individual contributions; total effects include interactions involving the parameter (Eq. 8).

S₁,ᵢ = Var[E(Y | Xᵢ)]/Var(Y)；Sₜ,ᵢ = E[Var(Y | X₋ᵢ)]/Var(Y) (8)

Base sample sizes increase from 128 and 256 to 512, with three independently randomized sequences. Each final annual sequence requires 512×(8+2)=5120 model evaluations, totaling 61,440 evaluations for the four-year main analysis. Complete response blocks are bootstrapped 512 times within each sequence to estimate approximate 95% numerical intervals for three-sequence means. Sequence means are averaged within years, followed by equal weighting of the four years. Annual rank correlations and index ranges assess stability.

## 2.6 Five-stage individual-event optimization and algorithm comparison

Five phenological stages are defined using the reported field observations [1]: Seedling, Jointing, Heading, Grain filling and Maturity. Each stage has three optional irrigation slots. Fifteen continuous depths and fifteen integer dates define a 30-dimensional decision vector. Dates are restricted to the intersection of the annual stage and executed model calendar. Zero-depth slots are inactive, and coincident slots are merged into one daily application. All five stages are eligible in every year, with zero to three executed events per stage (Table S4).

NSGA-III and NSGA-II maximize yield and minimize actually delivered seasonal irrigation [8–10] (Eq. 9). Formal searches enforce Y₁₃≥0.95Yobs, with both planned and delivered irrigation bounded by the recorded DI seasonal total. The 95% factor is a deterministic yield level. Both algorithms use 100 individuals, 100 generations and seeds 31, 73, 109, 151 and 199. Recorded schedules and earlier feasible four-window schedules are disclosed common initialization anchors, supplemented by timing perturbations and random controls. Canonical duplicate elimination leaves 99 initial individuals in each first NSGA-III seed, which nevertheless completes 100 generations. Actual formal queries total 399,996; subsequent seeds initialize 100 distinct controls.

min F(x) = [Iactual(x), −Y₁₃(x)]；x = (w₁,…,w₁₅,d₁,…,d₁₅) (9)

The primary candidate minimizes irrigation within the feasible nondominated union of final populations from the five formal NSGA-III seeds. Supplemental searches remove the yield gate and use three seeds, 80 individuals and 60 generations per year, totaling 57,600 queries across four years. Formal and supplemental searches together record 457,596 objective queries and 455,505 actual forward-model calls within the searches. Exact cache hits and forward calls are counted separately, with all queries and generation checkpoints retained.

Scheduling is retrospective under each year’s known daily weather. Crop parameters, soil, initial water, mulch and root settings remain fixed while individual amounts and dates vary jointly. Irrigation-manager event and seasonal execution caps follow each candidate plan to ensure full execution. Equipment capacity, minimum executable depth, minimum spacing and a terminal-storage floor are reserved for implementation-level refinement and are not added to this search. Exact positive-depth counts and counts of events ≥0.1 mm are both reported, with numerical trace depths preserved.

Earlier experiments expressed the fixed-date four-window problem as minimum irrigation at a prescribed yield threshold q (Eq. 10), comparing real-coded genetic optimization, one-objective NSGA-II, generalized simulated annealing and differential evolution [8,10–12]. Those results are retained as diagnostics of the earlier control space in the supplement. Algorithm comparisons for the current 30-dimensional five-stage schedules use the new NSGA-III and NSGA-II records.

min Iactual(x)，s.t. Y₁₃(x) ≥ q，Iactual(x) ≤ IDI (10)

## 2.7 Water balance and sources of irrigation reduction

Water accounting separately records precipitation P, actual irrigation I, transpiration Tr, soil evaporation Es, runoff R, deep drainage D, and initial and terminal storage S under recorded and optimized schedules. ET=Tr+Es; additional inflows are capillary rise CR and groundwater inflow GWin, and an additional outflow is tile drainage TD. Equation (11) integrates the full 2.4 m profile and surface storage.

ΔS = P + I + CR + GWin − ET − R − D − TD (11)

Under identical forcing, initial water and external inflows, the irrigation difference is decomposed into evapotranspiration, net-loss and terminal-storage differences (Eq. 12). Initial-to-final storage changes under each schedule are also reported, distinguishing reduced storage accumulation under the baseline from greater use of initial soil water under the selected schedule.

Ibase − Iopt = (ETbase − ETopt) + (Lbase − Lopt) + (Send,base − Send,opt) (12)

# 3 Results

## 3.1 Calibration and crop-growth simulation

Retained phase-specific means are listed in Table 4. CCx ranges from 0.9374 to 0.9773, CGC_CD from 0.0956 to 0.1318 d⁻¹, CDC_CD from 0.0603 to 0.0663 d⁻¹, senescence timing from 134.85 to 137.84 days, and Kcb from 1.3775 to 1.4866. Early and late WP range from 10.877 to 18.204 and from 21.938 to 31.498 g m⁻², respectively; HI0 ranges from 0.4013 to 0.5800. Annual combinations reflect the conditional parameter characteristics supported by the observations.

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

The model reproduces the principal canopy development and high-cover periods (Fig. 4). Annual CC R²cal values are 0.9932, 0.9794, 0.9902 and 0.9306, with RMSE values of 0.0316, 0.0482, 0.0370 and 0.0596. The larger 2022 error primarily reflects deviations in canopy timing from the observations. Overall, the calibrated model describes the main seasonal CC dynamics in these experiments.

![Figure 4](../figures/Fig04_CC_calibration_EN.png)

Figure 4. Canopy-cover calibration for drip-irrigated maize in 2019–2022. Lines show simulations at phase-specific retained means; circles show LAI-derived calibration observations.

Simulated and digitized observed biomass approach the 1:1 relationship (Fig. 5), with R²cal of 0.9685–0.9966 and RMSE of 0.5562–1.2520 t ha⁻¹. Biomass error is lowest in 2022 and highest in 2021. Simulated grain yields are 16.702, 16.804, 15.197 and 14.078 t ha⁻¹, corresponding to observed-yield biases of 0.92%, −2.81%, −4.18% and −0.02% (Table 5). These complementary indicators characterize annual growth and yield at the retained parameter centers.

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

Figure 6 shows empirical parameter intervals and prior supports. Annual CGC_CD intervals are relatively narrow, whereas CDC_CD and senescence intervals are wider. Upper-bound-neighborhood mass for CCx is 22.14% in 2019 and 23.06% in 2020; lower-bound-neighborhood mass for WP_early is 11.43% in 2020 and 23.65% in 2021. Observation constraints differ among parameters, with boundary-near concentration most evident for maximum canopy cover and early water productivity.

![Figure 6](../figures/Fig06_Parameter_intervals_EN.png)

Figure 6. Annual parameter centers, retained-sample intervals and prior supports. Colored intervals show empirical 2.5–97.5% quantiles within each calibration phase. Gray intervals show annual prior supports.

Parameter centers vary relatively little with retention choices. Maximum stage-1 mean shifts are 0.040 sample standard deviations between burn-in choices and 0.094 between halves of retained sequences; the maximum spread across independent-ensemble means is 0.203 standard deviations. Time-preserving diagnostics give worst R̂ values of 1.122–1.181 and annual minimum matched-group bulk ESS values of 17.79–25.34, below the reference targets for distributional precision. Subsequent deterministic simulations use the retained phase-specific means in Table 4. Ensemble counts, τ and full diagnostics appear in Table S3.

The pooled regression combines all 37 biomass calibration pairs across years (Fig. 7). With observed biomass as x and simulated biomass as y, the fitted relation is y=0.9979x+0.2412, with OLS R²=0.9892, Pearson r=0.9946 and pooled RMSE=1.0205 t ha⁻¹. The slope near one indicates close correspondence in biomass dynamics over the observed growth stages.

![Figure 7](../figures/Fig07_Pooled_biomass_regression_EN.png)

Figure 7. Pooled four-year regression of simulated against observed biomass. The solid line is the OLS fit to 37 calibration pairs; the dashed line indicates 1:1 agreement.

## 3.2 Annual water allocation under recorded schedules

Annual baseline inflows, outflows and storage changes are shown in Fig. 8. Inflows are 623.14, 673.22, 776.79 and 556.22 mm; outflows are 642.37, 611.31, 606.83 and 596.81 mm; and storage changes are −19.23, 61.92, 169.97 and −40.58 mm. Although 2021 receives the greatest irrigation, its ET of 605.14 mm is comparable with the other years. Profile storage increases from 535.70 to 705.67 mm, providing an important basis for interpreting subsequent irrigation reductions.

![Figure 8](../figures/Fig08_Annual_water_balance_EN.png)

Figure 8. Seasonal inflow, outflow and storage change under the original DI schedules. Inflow comprises precipitation and actual irrigation; outflow comprises ET and other losses. Storage change is final minus initial profile and surface water.

## 3.3 Parameter sensitivity and annual stability

Total-effect indices reveal output-specific parameter controls (Fig. 9). Grain yield is primarily sensitive to late WP, HI0, early WP and Kcb; biomass is controlled mainly by water productivity and Kcb; seasonal ET is dominated by Kcb; and maximum CC is dominated by CCx. Annual-mean parameter rankings for yield, biomass, ET and maximum CC agree across all four years, with pairwise Spearman correlations of 1.00 under the common input ranges.

![Figure 9](../figures/Fig09_Sobol_four_outputs_EN.png)

Figure 9. Total-effect Sobol indices for four crop-model outputs across years. Cells show means of three N=512 scrambles under the same independent input ranges; all panels use the same color scale.

First-order and total-effect yield indices and numerical intervals are shown in Fig. 10. Mean late-WP Sₜ is 0.396, with an annual range of 0.353–0.426; means for HI0, early WP and Kcb are 0.206, 0.164 and 0.145 (Table 6). Their total effects sum to approximately 0.911, emphasizing biomass conversion and water-use processes. Consistent annual-mean rankings support an equal-weight summary of the main sensitivity hierarchy, while annual ranges retain differences in magnitude.

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

## 3.4 Five-stage yield–irrigation Pareto relationships

Figure 11 presents full-range five-stage NSGA-III fronts. Blue dashed joins connect evaluated nondominated solutions; red-point tuples give rounded actual depths for Seedling, Jointing, Heading, Grain filling and Maturity. Orange open circles identify formal 95%-yield candidates. Yield generally increases and then approaches a plateau. Zero-irrigation simulations retain annual rainfall and initial soil water and yield 9.071, 6.184, 6.140 and 5.850 t ha⁻¹, respectively.

![Figure 11](../figures/Fig11_Five_stage_Pareto_fronts_EN.png)

Figure 11. Five-stage NSGA-III yield–irrigation fronts and individual-event schedules across four years. Red labels give rounded actual totals for Seedling, Jointing, Heading, Grain filling and Maturity. Stars show original DI model baselines; orange open circles show formal selected candidates. The displayed full-range fronts pool three 80-individual, 60-generation supplemental searches per year. Irrigation cancelled after crop termination is excluded from actual totals.

Selected irrigation depths are 209.83, 306.50, 264.50, 257.47 mm, reducing recorded DI irrigation by 52.88, 45.24, 58.25, 36.40% and yielding 15.725, 16.427, 15.068, 13.390 t ha⁻¹ (Table 7). In 2021, yield differs by -0.85% from the annual model baseline and by -4.99% from the field observation. The yield gate, observed-yield bias and change relative to the model baseline are therefore reported separately.

Table 7. Selected five-stage NSGA-III schedules at 95% observed yield.

| Year | Recorded I (mm) | Selected I (mm) | Selected yield (t ha⁻¹) | I reduction (%) | Yield RE (%) | ET (mm) |
| --- | --- | --- | --- | --- | --- | --- |
| 2019 | 445.27 | 209.83 | 15.725 | 52.88 | -4.99 | 599.84 |
| 2020 | 559.76 | 306.50 | 16.427 | 45.24 | -4.99 | 592.92 |
| 2021 | 633.47 | 264.50 | 15.068 | 58.25 | -4.99 | 593.68 |
| 2022 | 404.84 | 257.47 | 13.390 | 36.40 | -4.90 | 568.93 |

The primary candidate minimizes actual irrigation within the feasible nondominated union of the five formal NSGA-III final populations. Yield RE uses the published annual observation.

Irrigation changes relative to earlier four-window representatives are -8.53, -5.92, -2.80, -3.32 mm. The revised control space expands both timing and event allocation while exactly representing recorded and earlier feasible schedules. The lower-irrigation, high-yield region persists in both spaces under unchanged physical settings; evapotranspiration and storage differences explain the corresponding water sources.

## 3.5 Water sources supporting irrigation reduction

Water differences between recorded and selected five-stage schedules are shown in Fig. 12 and Table 8. ET decreases by 38.16, 17.04, 11.46, 27.85 mm, or 5.98, 2.79, 1.89, 4.67% of baseline ET. Terminal profile storage decreases by 193.14, 234.87, 356.85, 119.50 mm, accounting for 82.03, 92.74, 96.72, 81.09% of the irrigation differences. Consumptive-use changes are relatively small compared with the changes in terminal soil water.

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

In 2021, the irrigation reduction of 368.97 mm consists of 11.46 mm less ET, 0.66 mm less other losses and a 356.85 mm difference in terminal storage. The baseline accumulates water from 535.70 to 705.67 mm, whereas the selected schedule ends at 348.82 mm from the same initial state, drawing down 186.89 mm. Avoiding baseline accumulation and using initial water jointly support the lower seasonal irrigation. Daily and seasonal balances and full-model replays pass numerical checks; maximum discrepancy against fresh unaccelerated original equations is approximately 1.14×10⁻¹³.

## 3.6 Stage totals, individual schedules and algorithm comparison

Figure 13 plots every positive-depth irrigation event at its optimized date; complete schedules appear in Tables S5–S8. Exact positive-depth counts are 12, 13, 9 and 8, whereas counts of events ≥0.1 mm are 8, 8, 3 and 6. Both counts describe the same unrounded controls. The 2021 events ≥0.1 mm are 92.959 mm on 15 June, 85.822 mm on 28 June and 85.634 mm on 29 July. Remaining trace positive depths are preserved in the source tables.

![Figure 13](../figures/Fig13_Optimized_event_calendar_EN.png)

Figure 13. Every optimized irrigation date and depth in the selected four-year schedules. Colors indicate five phenological stages, with up to three optional events in each stage. Positive-depth event counts include trace numerical amounts; counts for depths ≥0.1 mm are reported separately. All exact positive depths remain in the source table.

Stage totals and counts appear in Fig. 14 and Table 9. The 2021 schedule mainly allocates 178.782 mm to Jointing and 85.634 mm to Grain filling, with approximately 0.084 mm across the other stages. The 2019 schedule instead concentrates more water in Seedling and Heading. Stage sums, individual executed depths and modeled seasonal irrigation reconcile within 10⁻⁷ mm. Zero to three events are permitted per stage rather than requiring three applications in every stage.

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

Figure 15 shows population hypervolume over five seeds for each algorithm; final-population union metrics appear in Table 10. Absolute annual differences between the lowest irrigation values found by NSGA-III and NSGA-II range from 0.03 to 1.47 mm, indicating similar but nonidentical trade-offs. The primary calendar follows the stated NSGA-III selection rule; NSGA-II minima and each algorithm’s maximum yields are listed separately. Comparisons under common anchors, objectives and constraints complement the daily water-process accounting.

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

# 4 Discussion

## 4.1 Process constraints from staged multi-output calibration

Canopy cover regulates potential transpiration and canopy development, while water productivity and harvest index govern biomass and grain formation [3]. Staged calibration follows these processes: canopy and water-use observations first determine growth and water-use trajectories, after which biomass and yield constrain conversion efficiency. The complementary fit indicators and sensitivity of yield to late WP and HI0 support the role of stage-2 calibration in irrigation-response analysis.

Annual parameter combinations reflect weather, observation coverage and error assumptions. Only one or two CC observations occur after senescence begins, contributing to wider intervals for CDC_CD and senescence timing. Denser observations during rapid canopy growth constrain CGC_CD more closely. Stage-1 means are relatively stable across retention choices, whereas time-series diagnostics still show substantial autocorrelation. Parameter centers therefore describe deterministic process results, and sampling diagnostics separately quantify distributional computational precision [5,15].

## 4.2 High-yield plateaus and soil-water buffering

Irrigation and crop evapotranspiration are linked through rainfall, initial soil water and terminal storage. Qin et al. [16] examine film-mulched drip irrigation using water-use components under sufficient irrigation. Here the 2021 irrigation reduction of 368.97 mm accompanies only 11.46 mm less ET and a 356.85 mm terminal-storage difference. The high-yield plateau thus reflects an irrigation–storage substitution under the specified initial state, parameters and seasonal boundary.

Part of the larger baseline irrigation becomes terminal storage, whereas selected schedules end with lower storage. These differences satisfy the same internal water balance. Reporting irrigation reduction separately from ET reduction distinguishes changes in supplied water, consumptive use and soil-water state, consistent with the water-accounting perspective on irrigation efficiency [13]. Joint evaluation of allowable terminal storage and stage-specific water supply helps define conditions for use across seasons.

## 4.3 Phenological scheduling, event scale and management application

The five stages correspond to the published crop-development periods, and joint date–depth optimization resolves decisions at individual-event scale. Concentration of water in particular stages reflects both annual crop processes and soil-water buffering. Dates are retrospective candidates under known annual weather, fixed parameter centers and initial soil water; practical rotations can be adjusted using future weather and local supply conditions.

Individual depths should be evaluated alongside seasonal totals. The selected annual maximum events are 117.03, 108.29, 92.96, 181.31 mm (Table S9). In 2022, the largest event is 181.31 mm compared with 85.85 mm in the recorded schedule, reflecting the concentration possible without an additional equipment event cap. Incorporating pipe-network capacity, minimum executable depth, event spacing and acceptable terminal storage provides a route to implementation-level scheduling.

Four scalar solvers previously reproduced the lower-irrigation region within the four-window space. The current NSGA-II/NSGA-III comparisons add evidence after timing and event-allocation freedom are expanded. Control spaces and initialization procedures are recorded separately for the two experiments. Linking every candidate to its calendar, seasonal water account and model settings keeps algorithmic results consistent with the process interpretation.

# 5 Conclusions

The four-year data support a staged calibration framework linking canopy and water use to biomass and yield. CC and biomass R²cal range from 0.9306 to 0.9932 and from 0.9685 to 0.9966, respectively, and grain-yield bias ranges from −4.18% to 0.92%. The retained parameter centers reproduce the principal annual growth processes and yield levels.

Under common independent input ranges, annual-mean parameter rankings agree across years for yield, biomass, ET and maximum CC. Mean yield Sₜ values are 0.396 for late WP, 0.206 for HI0, 0.164 for early WP and 0.145 for Kcb, identifying water productivity, harvest index and water-use processes as the main controls of the simulated yield response.

A 30-dimensional date–depth control space represents five phenological stages with up to three optional events per stage. At 95% of observed yield, selected NSGA-III depths are 209.83, 306.50, 264.50, 257.47 mm, reducing recorded irrigation by 36.40–58.25%. Stage totals and individual calendars are provided, and annual NSGA-II/NSGA-III minimum-irrigation differences are 0.03–1.47 mm.

Five-stage optimization reduces ET by 1.89–5.98%, while terminal-storage differences explain 81.09–96.72% of irrigation reductions. The 2021 storage difference is 356.85 mm, accounting for 96.72% of that year’s irrigation reduction. Joint analysis of crop growth, individual supply and storage identifies seasonal water sources and conditions for use across seasons.

# Data and code

Annual inputs, staged MCMC checkpoints, sensitivity responses, optimization solutions, daily water accounts and English figures are archived by research stage. Figure/table source data, processing code and revision records accompany the manuscripts. Project number: X2026100190937. The optimization source version is recorded at Git commit 20f1616556f5aeb79329b7ead22faa28f9fcda6a in the URP repository.

[1] Wang, S. (2023). Observation and simulation of water, heat, and nitrogen transport and crop growth in maize fields under different irrigation methods. Master’s thesis, China Agricultural University, Beijing. [In Chinese.]

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
