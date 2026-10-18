"""Read the original 2022 engine and inputs; no proxy fallback or MCMC rerun."""
from pathlib import Path
import copy
import importlib.util
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent / 'model_2022'
_STATE = None


def provenance():
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8-sig'))
    files = []
    for name, digest in manifest.items():
        if name.endswith('.py'): role = 'model_source'
        elif 'WEATHER_FILE' in name or 'ETO_FILE' in name: role = 'weather'
        elif 'INITIAL_WATER' in name: role = 'soil'
        elif any(k in name for k in ['FIELD_CC', 'BIOMASS', 'RS_CC']): role = 'observations'
        else: role = 'frozen_reference'
        files.append(dict(role=role, path='model_2022/' + name, sha256=digest))
    files.append(dict(role='irrigation', path='model_2022/DI_2022_MCMC_ONE_CLICK.py',
                      sha256=manifest['DI_2022_MCMC_ONE_CLICK.py']))
    # The preparation runner uses a generic input role for the same frozen file.
    weather='data/inputs/WEATHER_FILE_DI_Climate_2022_FINAL.csv'
    files.append(dict(role='input',path='model_2022/'+weather,sha256=manifest[weather]))
    return dict(engine='Modified_DI_AquaCrop', deterministic=True, available_years=[2022],
                files=files, input_role='original data; MCMC samples remain frozen',
                control='five irrigation amounts on the original five fixed dates')


def _load(year):
    global _STATE
    if year != 2022:
        raise FileNotFoundError(f'{year} original model implementation is not provided; only 2022 is connected. No proxy fallback.')
    if _STATE is None:
        source = ROOT / 'DI_2022_MCMC_ONE_CLICK.py'
        spec = importlib.util.spec_from_file_location('urp_original_2022', source)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        for name in ['sampler', 'diagnostics', 'audit_hooks', 'ensemble_pipeline']:
            module._embedded_module(name)
        module._embedded_module('runner')
        # Import-only; no MCMC entrypoint is called and no files are written.
        model = module._embedded_module('model', ROOT / 'data/model.py')
        data = model.load_inputs(); model.prepare_soil(data)
        _STATE = model, data
    return _STATE


def management_space(year):
    model, data = _load(year)
    dates = [d.strftime('%Y-%m-%d') for d in data['schedule'].Date]
    cap = float(data['schedule'].Depth.sum())
    return dict(kind='stage_amounts', names=[f'Stage{i+1}_mm' for i in range(len(dates))],
                lower=[0.] * len(dates), upper=[cap] * len(dates), dates=dates,
                allowed_windows=[[d, d] for d in dates],
                definition='Five amounts on original fixed irrigation dates; timing is not optimized',
                SMT_supported=False)


def simulate(*, params, year, management=None):
    model, original = _load(year); data = copy.copy(original)
    if management is not None:
        if management['kind'] != 'stage_amounts':
            raise ValueError('Original supplied engine exposes fixed-date schedule amounts, not SMT')
        spec = management_space(year); expected = spec['names']
        if set(management['values']) != set(expected): raise ValueError('Unknown irrigation decision names')
        events = management['events']
        if len(events) != len(expected): raise ValueError('Each original date needs one control')
        for j, event in enumerate(events):
            if event['stage'] != j or event['date'] != spec['dates'][j] or event['mm'] != management['values'][expected[j]]:
                raise ValueError('Request differs from original fixed-date controls')
        data['schedule'] = pd.DataFrame({'Date': pd.to_datetime(spec['dates']),
                                         'Depth': [management['values'][n] for n in expected]})
    summary, _, _, _ = model.simulate(data, dict(params), 'DI')
    # The original simulate checks actual daily IrrDay against this schedule.
    summary['irrigation_events'] = [dict(date=d.strftime('%Y-%m-%d'), mm=float(mm), stage=i)
                                    for i, (d, mm) in enumerate(zip(data['schedule'].Date, data['schedule'].Depth))]
    summary['B_t_ha'] = summary['B_last']
    return summary
