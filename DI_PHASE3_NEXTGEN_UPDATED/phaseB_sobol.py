"""Revised phase B: independent global physical ranges; real Modified DI only.

Optional local95 is a marginal-neighborhood response experiment, not posterior
Sobol. MCMC is frozen input. No CAI, forced ranking or proxy result is imported.
"""
from __future__ import annotations
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from SALib.sample import sobol as sample_sobol
from SALib.analyze import sobol as analyze_sobol

from model_adapter import NAMES,OUTPUTS,HERE,RealModel,load_study,baseline,read,write,sha,csv


def make_problem(study,year,track='global'):
    if track=='global':bounds=study['global_physical_bounds']
    elif track=='local95':
        with np.load(Path(study['_root'])/study['phase_samples'],allow_pickle=False) as z:
            if f'p2_{year}' not in z:raise ValueError(f'{year}: real phase-2 samples unavailable for local95')
            a,b=z[f'p1_{year}'],z[f'p2_{year}']
            bounds={k:np.quantile(a[:,j],[.025,.975]).tolist() for j,k in enumerate(NAMES[:5])}
            bounds.update({k:np.quantile(b[:,j],[.025,.975]).tolist() for j,k in enumerate(NAMES[5:])})
    else:raise ValueError('Unknown input space')
    bd=np.array([bounds[k] for k in NAMES],float)
    if bd.shape!=(8,2) or not np.isfinite(bd).all() or np.any(bd[:,1]<=bd[:,0]):raise ValueError('Invalid Sobol space')
    return {'num_vars':8,'names':NAMES,'bounds':bd.tolist()}


def estimates(problem,y,seed,resamples=512):
    y=np.asarray(y,float);stride=len(problem['names'])+2
    if len(y)%stride or not np.isfinite(y).all():raise ValueError('Incomplete/nonfinite Sobol responses')
    ab=np.r_[y[::stride],y[stride-1::stride]]
    variance=float(np.var(ab,ddof=1));mean=float(np.mean(ab))
    if variance<=1e-14*max(float(np.mean(ab**2)),np.finfo(float).tiny):
        return [{'Parameter':k,'Status':'constant_output_indices_undefined','Mean':mean,'Variance':variance,
                 'S1':None,'ST':None,'S1_conf':None,'ST_conf':None,'ST_minus_S1':None,'Variance_times_ST':None} for k in problem['names']]
    si=analyze_sobol.analyze(problem,y,calc_second_order=False,num_resamples=resamples,
                           conf_level=.95,seed=seed,print_to_console=False)
    rows=[]
    for j,k in enumerate(problem['names']):
        d={q:float(si[q][j]) for q in ['S1','ST','S1_conf','ST_conf']}
        if not all(np.isfinite(list(d.values()))):raise ValueError('Invalid sensitivity estimate')
        rows.append(dict(Parameter=k,Status='estimated',Mean=mean,Variance=variance,
                         ST_minus_S1=d['ST']-d['S1'],Variance_times_ST=variance*d['ST'],**d))
    return rows


def run_track(model,study,year,n,seed,track,out):
    if n<2 or n&(n-1):raise ValueError('Use a power-of-two Sobol base sample count')
    out=Path(out);out.mkdir(parents=True,exist_ok=True);problem=make_problem(study,year,track)
    x=sample_sobol.sample(problem,n,calc_second_order=False,scramble=True,seed=seed)
    design=out/'design.npy';journal=out/'responses.jsonl'
    identity={'model':model.identity,'space':problem,'track':track,'N':n,'seed':seed,
              'calc_second_order':False,'expected_calls':10*n}
    if (out/'run.json').exists():
        previous=read(out/'run.json')
        if previous['identity']!=identity:raise ValueError('Cannot reuse another model/space run directory')
        if not design.exists() or not np.array_equal(np.load(design,allow_pickle=False),x):raise ValueError('Design changed')
        if previous['status']=='COMPLETE' and (not journal.exists() or sha(journal)!=previous['responses_sha256']):
            raise ValueError('Completed response checksum changed')
    else:
        if journal.exists():raise ValueError('Response journal has no provenance')
        np.save(design,x,allow_pickle=False)
        csv(out/'design.csv',pd.DataFrame(x,columns=NAMES).rename_axis('row_id').reset_index())
        write(out/'space.json',dict(problem,Distribution='independent_uniform',Meaning='physical_global' if track=='global' else 'local_marginal_95_neighborhood_not_posterior'))
    values={}
    if journal.exists():
        with journal.open(encoding='utf-8') as f:
            for line in f:
                r=json.loads(line);i=r['row_id']
                if type(i) is not int or not 0<=i<len(x) or i in values:raise ValueError('Duplicate or invalid response row')
                if not np.array_equal(r['params'],x[i]):raise ValueError('Response does not match the original design')
                from model_adapter import validate_output
                values[i]=validate_output(r['output'],study['water_balance_atol_mm'])
    write(out/'run.json',{'status':'RUNNING','identity':identity,'completed':len(values),'design_sha256':sha(design)})
    with journal.open('a',encoding='utf-8') as f:
        for i,row in enumerate(x):
            if i in values:continue
            t=time.perf_counter()
            try:r=model.simulate(dict(zip(NAMES,row)),year)
            except Exception as error:
                write(out/'failure.json',{'row_id':i,'params':row.tolist(),'error':str(error),'identity':identity})
                write(out/'run.json',{'status':'FAILED','identity':identity,'completed':len(values),'failed_row':i})
                raise
            f.write(json.dumps({'row_id':i,'params':row.tolist(),'output':r,'seconds':time.perf_counter()-t},allow_nan=False)+'\n');f.flush()
            values[i]=r
            if (i+1)%100==0:print(f'Sobol {year} {track} N={n} seed={seed}: {i+1}/{len(x)}',flush=True)
    if len(values)!=10*n:raise ValueError('Do not drop failed Saltelli rows')
    y=np.array([[values[i][name] for name in OUTPUTS] for i in range(len(x))])
    np.save(out/'response_matrix.npy',y,allow_pickle=False)
    csv(out/'response_matrix.csv',pd.DataFrame(y,columns=OUTPUTS).rename_axis('row_id').reset_index())
    rows=[]
    for j,name in enumerate(OUTPUTS):
        for r in estimates(problem,y[:,j],seed+8000,study['sobol']['bootstrap_resamples']):
            rows.append(dict(Year=year,Track=track,N=n,Seed=seed,Output=name,
                             Units='t/ha' if name in ['Y_13pct','B_t_ha'] else ('fraction' if name=='MaxCC' else 'mm'),**r))
    csv(out/'indices.csv',rows)
    write(out/'run.json',{'status':'COMPLETE','identity':identity,'completed':len(values),'failure_rate':0,
          'design_sha256':sha(design),'responses_sha256':sha(journal),'indices_sha256':sha(out/'indices.csv')})
    return pd.DataFrame(rows)


def rank_checks(df,study):
    rows=[];cfg=study['sobol']
    for (year,output),g in df.groupby(['Year','Output']):
        valid=g[g.Status=='estimated'].copy();sets=[]
        for _,s in valid.groupby('Seed'):sets.append(tuple(sorted(s.nlargest(cfg['key_parameter_count'],'ST').Parameter)))
        all_estimated=len(valid)==len(g)
        same_top=bool(sets and len(set(sets))==1 and set(g.Seed)==set(cfg['seeds']))
        narrow=bool(all_estimated and valid.ST_conf.max()<=cfg['ci_halfwidth_max'])
        rows.append(dict(Year=int(year),Output=output,Same_top_set_across_scrambles=same_top,
                         Max_ST_95ci_halfwidth=float(valid.ST_conf.max()) if len(valid) else None,
                         CI_halfwidth_limit=cfg['ci_halfwidth_max'],Stable_for_screening=all_estimated and same_top and narrow,
                         Next_action='retain screening' if all_estimated and same_top and narrow else ('constant output: no normalized ranking' if not len(valid) else 'increase N to 512 and compare')))
    return pd.DataFrame(rows)


def cross_year_key_flags(df,study):
    rows=[];years=set(study['years']);k=study['sobol']['key_parameter_count']
    for output,g in df.groupby('Output'):
        top={};valid=g[g.Status=='estimated']
        for (year,seed),s in valid.groupby(['Year','Seed']):top[year,seed]=set(s.nlargest(k,'ST').Parameter)
        for name in NAMES:
            sub=valid[valid.Parameter==name]
            full=set(sub.Year)==years and len(top)==len(years)*len(study['sobol']['seeds'])
            all_top=bool(full and all(name in names for names in top.values()))
            narrow=bool(len(sub) and sub.ST_conf.max()<=study['sobol']['ci_halfwidth_max'])
            rows.append(dict(Output=output,Parameter=name,Four_year_all_scrambles_top_k=all_top,
                             All_CI_halfwidths_small=narrow,Robust_key_under_declared_space=all_top and narrow,
                             Rule=f'top {k} in all annual scrambles, ST halfwidth <= {study["sobol"]["ci_halfwidth_max"]}'))
    return pd.DataFrame(rows)


def main(study=None,model=None,out=None,n=None,years=None,track='global'):
    study=study or load_study();model=model or RealModel(study);n=n or study['sobol']['N']
    years=years or study['years'];out=Path(out or HERE/'output_revised')/f'sobol_{track}_N{n}'
    out.mkdir(parents=True,exist_ok=True);frames=[]
    for year in years:
        baseline(model,study,year,out)
        for seed in study['sobol']['seeds']:
            frames.append(run_track(model,study,year,n,seed,track,out/f'{year}_seed{seed}'))
    df=pd.concat(frames,ignore_index=True);csv(out/'sobol_indices.csv',df)
    checks=rank_checks(df,study);csv(out/'scramble_checks.csv',checks)
    csv(out/'cross_year_key_flags.csv',cross_year_key_flags(df,study))
    write(out/'sobol_summary.json',{'status':'SCREENING_STABLE' if checks.Stable_for_screening.all() else 'REVIEW_OR_EXPAND_N',
          'engine':model.identity,'N':n,'second_order':False,'calls_per_year_per_seed':10*n,
          'years':years,'seeds':study['sobol']['seeds'],'track':track,'ranking':'ST primary; S1 and CI reported',
          'not_joint_posterior':True,'no_CAI_information_claim':True})
    from plot_results import plot_sobol
    plot_sobol(df,out)
    return out


if __name__=='__main__':main()
