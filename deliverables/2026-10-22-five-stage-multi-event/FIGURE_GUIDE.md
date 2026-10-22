# English figure guide

Each figure has a 450 dpi PNG, a vector PDF and an editable SVG. Four years are 2019, 2020, 2021 and 2022. Yield is grain yield at 13% moisture. The dashed joins connect evaluated solutions; they are not additional model evaluations.

1. **R03_Five_stage_multi_event_Pareto_4years_EN**: Four-year, 2×2 full-range NSGA-III yield–irrigation fronts. Blue dashed joins and red evaluated points follow the requested reference style. Label tuples give rounded stage totals in order: Seedling, Jointing, Heading, Grain filling, Maturity. Stars show original DI model baselines; orange open circles show formal selected 95%-observed-yield solutions. The selected point is obtained from formal searches, while the displayed full-range front comes from separate supplemental searches. `Full_range_Pareto_front.csv` and `Pareto_display_points.csv` provide full-precision controls. `Pareto_every_irrigation_event.csv.gz` supplies every individual date/depth for each full-range front solution. Four single-year R03 figures are also included.
2. **R04_Four_window_vs_multi_event_fronts_EN**: Historical four fixed-date window fronts compared with five phenological stages and optional multiple events. The revised experiment expands timing and event-allocation freedom under the same frozen physical model and weather. Original feasible schedules are explicit warm starts.
3. **R05_Five_stage_totals_and_counts_EN**: Original DI and selected optimized irrigation totals in all five stages. `n` counts exact positive-depth events after same-day merging, including trace depths. Zero-depth slots are not events. Source tables separately count depths ≥0.1 mm without changing the evaluated controls.
4. **R06_Optimized_event_calendar_EN**: Every selected positive-depth irrigation event, plotted at its optimized date and colored by stage. Background bands show eligible stage dates. Exact daily dates/depths are in `Optimized_every_irrigation_event.csv`.
5. **R07_Annual_irrigation_and_yield_EN**: Original DI, old four-window representative and selected five-stage seasonal depths; observed yield, model baseline, selected yield and deterministic 95% observed-yield gate. Percentage labels indicate irrigation reduction relative to original DI.
6. **R08_Daily_profile_storage_EN**: Original DI and selected daily soil water storage integrated over the unchanged 0–2.4 m simulated profile. Initial soil water and forcing are identical within each year. Interpret reduced irrigation alongside the ending storage difference.
7. **R09_Water_balance_decomposition_EN**: Signed baseline-minus-selected differences in ET, terminal storage and other losses. These sum to the irrigation reduction. Percentage labels show the terminal-storage difference divided by irrigation reduction; this is not the percentage reduction in ET.
8. **R10_Algorithm_convergence_EN**: Formal NSGA-III and NSGA-II population hypervolume across 100 generations. Lines show five-seed means and bands show min–max ranges. Population hypervolume can fluctuate; the seed-union metric is separately reported in `Algorithm_comparison.csv`.

## Figure-to-data mapping

| Figure | Main source tables |
|---|---|
| R03 | Full_range_Pareto_front; Pareto_display_points; Four_year_result_comparison |
| R04 | Old_four_window_Full_range_best_found_front; Full_range_Pareto_front |
| R05 | Five_stage_totals_and_event_counts |
| R06 | Optimized_every_irrigation_event; Five_stage_schedule_bounds |
| R07 | Four_year_result_comparison |
| R08 | YEAR_Original_DI_daily_water; YEAR_Selected_95pct_daily_water |
| R09 | Four_year_result_comparison; Baseline_and_selected_water_ledger |
| R10 | Generation_history; Search_run_summary |

Full-range curves and formal 95%-yield searches have distinct roles and are recorded separately. Every plotted line/point has evaluated source data; no agronomic field-validation values have been added.

Stage tuples use **actual** executed depths. In severe-deficit cases, planned irrigation after crop termination is cancelled; planned controls remain in the full-range table, and `S1_actual_total_mm` through `S5_actual_total_mm` reconcile with actual seasonal irrigation. Rounded display tuples can differ from the seasonal sum by rounding only.
