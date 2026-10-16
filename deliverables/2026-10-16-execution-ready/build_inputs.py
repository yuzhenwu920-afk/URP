"""Rebuild audited settings from prior checkpoint contracts and review tables.

This script needs the original analysis workspace. The generated settings,
provenance and sampling inputs are portable and do not need this builder.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import real_model_pipeline as p

ROOT = Path(__file__).resolve().parent
DATA = Path('/workspace/urp_review/data')
OLD = Path('/workspace/urp_followup_20261016/revision')


def build():
    centers = pd.read_csv(OLD / 'tables/central_vectors_with_provenance.csv').set_index('Year')
    config = {'status': 'PREPARED_NOT_REAL_MODEL_EXECUTED', 'cases': {}}
    provenance = []
    domains = []
    gates = []
    for year in range(2019, 2023):
        r = DATA / f'②原始资料包_{year}'
        source = sorted(r.rglob('checkpoints/canopy_transpiration/ensemble_*.npz'))[0]
        with np.load(source, allow_pickle=False) as z:
            contract = json.loads(z['contract'].item())
        bounds = {name: contract['priors'][name] for name in p.NAMES}
        for other in sorted(r.rglob('checkpoints/*/ensemble_*.npz')):
            with np.load(other, allow_pickle=False) as z:
                c = json.loads(z['contract'].item())
            assert all(c['priors'][name] == bounds[name] for name in p.NAMES)
        info = {'year': year, 'checkpoint': str(source.relative_to(DATA)), 'sha256': p.sha(source),
                'contract_model_hashes': {k: v for k, v in contract['files'].items() if k.endswith('.py')},
                'original_normal_prior_names': contract['normal_priors'],
                'original_prior_centers': contract['center'], 'original_prior_sd': contract['prior_sd'],
                'support_bounds': bounds, 'source_code_present_in_readable_materials': False}
        provenance.append(info)
        expected = None
        observed = {2019: 16.55, 2020: 17.29, 2021: 15.86, 2022: 14.08}[year]
        irrigation = {2019: 445.27, 2020: 559.76, 2021: 633.47, 2022: 404.84}[year]
        if year < 2022:
            summary_path = next(r.rglob('summary.json'))
            summary = p.read(summary_path)
            d = summary['DI']
            expected = {key: float(d[key]) for key in p.REQUIRED if key in d}
            expected['B_t_ha'] = float(d['B_last'])
            info['matched_summary'] = str(summary_path.relative_to(DATA))
            info['matched_summary_sha256'] = p.sha(summary_path)
            assert summary['Yield']['yield_observed'] == observed
            assert d['Irrigation_mm'] == irrigation
            threshold = .95 * observed
            gates.append({'Year': year, 'Observed_Y13_t_ha': observed,
                          'Original_model_baseline_Y13_t_ha': d['Y_13pct'],
                          'Absolute_95pct_gate_t_ha': threshold,
                          'Remaining_loss_allowed_t_ha': d['Y_13pct'] - threshold,
                          'Remaining_loss_allowed_pct_of_model_baseline': 100 * (1 - threshold / d['Y_13pct']),
                          'Baseline_bias_pct_vs_observed': 100 * (d['Y_13pct'] / observed - 1),
                          'Baseline_Irrigation_mm': irrigation,
                          'Role': 'Existing original model output; no new crop simulation'})
        config['cases'][str(year)] = {
            'support_bounds': bounds, 'central_params': {n: float(centers.loc[year, n]) for n in p.NAMES},
            'center_evidence': 'phase1 verified; phase2 report only' if year == 2022 else 'both phases checkpoint verified',
            'central_params_are_not_joint_posterior_draws': True,
            'WP_switch_date': contract['switch'][:10], 'published_Y13_t_ha': observed,
            'absolute_95pct_yield_gate_t_ha': .95 * observed,
            'baseline_irrigation_mm': irrigation, 'baseline_expected': expected,
            'acceptance': {'water_balance_atol_mm': 1e-5, 'baseline_atol': 1e-5, 'baseline_rtol': 1e-5}}
        for name, (lo, hi) in bounds.items():
            domains.append({'Year': year, 'Parameter': name, 'Low': lo, 'High': hi,
                            'Distribution_for_new_design': 'independent uniform on annual support',
                            'Original_MCMC_prior_has_normal_component': name in contract['normal_priors'],
                            'Source_checkpoint_SHA256': p.sha(source)})
    p.write(ROOT / 'study_config.json', config)
    p.write(ROOT / 'source_provenance.json', provenance)
    (ROOT / 'tables').mkdir(exist_ok=True)
    pd.DataFrame(domains).to_csv(ROOT / 'tables/annual_sampling_domains.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(gates).to_csv(ROOT / 'tables/observed_yield_gate_headroom.csv', index=False, encoding='utf-8-sig')
    print('Annual checkpoint supports and three verified original-model baselines exported.')


if __name__ == '__main__':
    build()
