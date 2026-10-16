"""Separate conditional perturbations after deterministic candidate selection."""
from pathlib import Path
import math
import numpy as np
import pandas as pd
from model_adapter import NAMES,OUTPUTS,management,check_management_response,csv,write


def conditional_groups(study,year,k,seed):
    if k<128:raise ValueError('Guidance requires at least 128 perturbations per available parameter group')
    rng=np.random.default_rng(seed+year);groups={};missing=[]
    center=study['_centers'][year]
    with np.load(Path(study['_root'])/study['phase_samples'],allow_pickle=False) as z:
        for phase,names in [(1,NAMES[:5]),(2,NAMES[5:])]:
            key=f'p{phase}_{year}'
            if key not in z:
                missing.append(key);continue
            draws=z[key]
            if draws.ndim!=2 or draws.shape[1]!=len(names) or not np.isfinite(draws).all():raise ValueError('Invalid frozen phase samples')
            indices=rng.choice(len(draws),size=k,replace=True)
            rows=[]
            for i in indices:
                params=dict(center);params.update(dict(zip(names,map(float,draws[i]))));rows.append(params)
            groups[f'phase{phase}_conditional']={'params':rows,'source_indices':indices,
                  'fixed_group':'phase2 central' if phase==1 else 'phase1 central'}
    return groups,missing


def probability_summary(y,gate):
    y=np.asarray(y,float);n=len(y)
    if not n or not np.isfinite(y).all():raise ValueError('Invalid perturbation responses')
    p=float(np.mean(y>=gate));se=math.sqrt(p*(1-p)/n);z=1.95996398454
    center=(p+z*z/(2*n))/(1+z*z/n)
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return {'Mean_Y13':float(y.mean()),'SD_Y13':float(y.std(ddof=1)),
            'Q05_Y13':float(np.quantile(y,.05)),'Probability_above_absolute_gate':p,
            'MC_standard_error_conditional':se,'Wilson_low':center-half,'Wilson_high':center+half}


def validate_year(model,study,year,spec,candidates,out):
    out=Path(out);cfg=study['optimization'];k=cfg['conditional_draws']
    groups,missing=conditional_groups(study,year,k,cfg['validation_seed'])
    gate=study['yield_fraction']*study['observed_Y13'][str(year)]
    records=[];summaries=[]
    for group,description in groups.items():
        params=description['params'];base=[model.simulate(p,year) for p in params]
        for _,candidate in candidates.iterrows():
            x=np.array([candidate[n] for n in spec['names']]);request=management(spec,x)
            outputs=[check_management_response(model.simulate(p,year,request),spec,x) for p in params]
            y=np.array([r['Y_13pct'] for r in outputs]);yb=np.array([r['Y_13pct'] for r in base])
            stats=probability_summary(y,gate)
            summary=dict(Year=year,Candidate_ID=candidate.Candidate_ID,Group=group,N=k,
                         Fixed_group=description['fixed_group'],**stats,
                         Paired_probability_above_95pct_model_baseline=float(np.mean(y>=study['yield_fraction']*yb)),
                         Mean_Irrigation_mm=float(np.mean([r['Irrigation_mm'] for r in outputs])),
                         Mean_ET_mm=float(np.mean([r['ET_mm'] for r in outputs])),
                         Mean_Tr_mm=float(np.mean([r['Tr_mm'] for r in outputs])),
                         Mean_Es_mm=float(np.mean([r['Es_mm'] for r in outputs])),
                         Max_abs_water_residual_mm=float(np.max([abs(r['Water_balance_residual_mm']) for r in outputs])),
                         Probability_Irrigation_within_cap=float(np.mean([r['Irrigation_mm']<=study['baseline_irrigation_mm'][str(year)] for r in outputs])),
                         Interpretation='conditional group perturbation, not joint-posterior or field failure probability')
            summaries.append(summary)
            for j,(p,r,b) in enumerate(zip(params,outputs,base)):
                records.append(dict(Year=year,Candidate_ID=candidate.Candidate_ID,Group=group,Draw=j,
                       Source_index=int(description['source_indices'][j]),**p,
                       **{name:r[name] for name in OUTPUTS},Irrigation_mm=r['Irrigation_mm'],
                       Water_balance_residual_mm=r['Water_balance_residual_mm'],Paired_baseline_Y13=b['Y_13pct']))
    csv(out/'conditional_perturbation_responses.csv',records)
    summary=csv(out/'conditional_validation.csv',summaries)
    write(out/'conditional_validation_status.json',{'status':'COMPLETE' if not missing else 'PARTIAL_MISSING_RAW_GROUP',
          'groups_run':list(groups),'groups_missing':missing,'draws_per_available_group':k,
          'within_group_row_correlation_preserved':True,'eight_dimensional_joint_posterior_claim':False,
          'MC_note':'empirical conditional draws; intervals exclude field/model uncertainty',
          'not_an_extra_optimization_objective':True,'engine':model.identity})
    from plot_results import plot_conditional
    if len(summary):plot_conditional(summary,out)
    return summary,missing
