"""Supervised resumable Sobol batches and full-budget annual NSGA experiments.

Sobol journals resume exact designs. Completed optimization seeds are reused;
an interrupted optimization seed remains explicitly failed/incomplete.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import argparse
import json
import time
import traceback
import numpy as np
import pandas as pd
from model_adapter import load_study,RealModel,baseline,write,read,csv,sha,HERE
import phaseB_sobol as B
import phaseC_nsga3 as C


def run_job(job,root):
    study=load_study();model=RealModel(study);kind,year,value,seed=job
    if kind=='sobol':
        folder=Path(root)/f'sobol_global_N{value}'/f'{year}_seed{seed}'
        B.run_track(model,study,year,value,seed,'global',folder)
    else:
        folder=Path(root)/'optimization'/str(year)/f'{kind}_seed{seed}'
        if (folder/'run.json').exists() and read(folder/'run.json')['status'] in ['COMPLETE','NO_FEASIBLE_SOLUTION']:
            if read(folder/'run.json')['identity']['engine']!=model.identity:raise ValueError('Engine changed')
            return {'job':list(job),'status':'REUSED_COMPLETE'}
        problem=C.DeterministicIrrigationProblem(model,study,year,model.management_space(year))
        C.run_seed(problem,kind,seed,study['optimization']['generations'],study['optimization']['population'],folder)
    return {'job':list(job),'status':'COMPLETE'}


def parallel_jobs(jobs,root,workers,status):
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(run_job,job,str(root)):job for job in jobs}
        for future in as_completed(futures):
            job=futures[future]
            try:result=future.result()
            except Exception as e:
                result={'job':list(job),'status':'FAILED','error':str(e),'traceback':traceback.format_exc()}
                print(result['traceback'],flush=True)
            status['jobs'].append(result)
            status['last_update_UTC']=pd.Timestamp.now(tz='UTC').isoformat()
            write(root/'EXPERIMENT_STATUS.json',status)
            print('JOB RESULT',json.dumps(result,ensure_ascii=False),flush=True)


def collect_sobol(root,study,n):
    paths=sorted((root/f'sobol_global_N{n}').glob('*/indices.csv'))
    frames=[pd.read_csv(p) for p in paths]
    if not frames:return pd.DataFrame()
    df=pd.concat(frames,ignore_index=True);folder=root/f'sobol_global_N{n}'
    csv(folder/'sobol_indices.csv',df);csv(folder/'scramble_checks.csv',B.rank_checks(df,study))
    return df


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=HERE/'output_real_20261019')
    parser.add_argument('--workers',type=int,default=4);args=parser.parse_args()
    root=args.out.resolve();root.mkdir(parents=True,exist_ok=True)
    study=load_study();model=RealModel(study)
    status={'status':'RUNNING','engine':model.identity,'years':study['years'],'MCMC_frozen':True,
        'optimization':study['optimization'],'sobol':study['sobol'],'workers':args.workers,'jobs':[],
        'started_UTC':pd.Timestamp.now(tz='UTC').isoformat()}
    write(root/'EXPERIMENT_STATUS.json',status)
    write(root/'RUN_SOURCE_MANIFEST.json',{'engine':model.identity,'files':[
        {'file':p.relative_to(HERE).as_posix(),'sha256':sha(p)} for p in sorted(HERE.rglob('*.py'))
        if not any(part.startswith('output') for part in p.relative_to(HERE).parts)]})
    for year in study['years']:baseline(model,study,year,root/'baselines')
    first=[('sobol',year,128,seed) for year in study['years'] for seed in study['sobol']['seeds']]
    parallel_jobs(first,root,args.workers,status)
    initial=collect_sobol(root,study,128)
    checks=B.rank_checks(initial,study)
    expand=sorted(checks.loc[~checks.Stable_for_screening,'Year'].unique().astype(int).tolist())
    write(root/'SOBOL_EXPANSION_DECISION.json',{'expanded_years':expand,'rule':'any output fails declared top-three/CI screening stability','initial_checks':checks.to_dict('records')})
    seeds=study['optimization']['seeds']
    jobs=[('NSGA3',y,100,seeds[0]) for y in study['years']]
    jobs += [('sobol',y,512,seed) for y in expand for seed in study['sobol']['seeds']]
    jobs += [('NSGA3',y,100,seed) for seed in seeds[1:] for y in study['years']]
    jobs += [('NSGA2',y,100,seed) for seed in seeds for y in study['years']]
    parallel_jobs(jobs,root,args.workers,status)
    expanded=collect_sobol(root,study,512)
    final=pd.concat([initial[~initial.Year.isin(expand)],expanded],ignore_index=True)
    target=root/'sobol_final';target.mkdir(exist_ok=True)
    csv(target/'sobol_indices.csv',final);csv(target/'scramble_checks.csv',B.rank_checks(final,study))
    csv(target/'cross_year_key_flags.csv',B.cross_year_key_flags(final,study))
    for year in study['years']:
        folder=root/'optimization'/str(year)
        try:
            selected=C.run_year(model,study,year,folder,collect_existing=True)
            if len(selected):
                from validate_candidates import validate_year
                validate_year(model,study,year,model.management_space(year),selected,folder)
        except Exception as e:
            status['jobs'].append({'job':['collect_validate',year],'status':'FAILED','error':str(e),'traceback':traceback.format_exc()})
            print(traceback.format_exc(),flush=True)
    status['status']='COMPLETE' if all(j['status']!='FAILED' for j in status['jobs']) else 'INCOMPLETE_WITH_FAILURES'
    status['finished_UTC']=pd.Timestamp.now(tz='UTC').isoformat()
    status['frozen_input_hashes']=study['_frozen_hashes']
    write(root/'EXPERIMENT_STATUS.json',status)
    print('EXPERIMENT',status['status'],flush=True)


if __name__=='__main__':main()
