"""Revised phase C: fixed central parameters, two objectives and hard gates.

NSGA-III: 100 directions/population, 100 generations, five seeds. NSGA-II is
the default matched comparator. Conditional perturbations follow optimization.
"""
from __future__ import annotations
import math
from pathlib import Path

import numpy as np
import pandas as pd
from pymoo.core.problem import Problem
from pymoo.core.repair import Repair
from pymoo.core.sampling import Sampling
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.util.ref_dirs import get_reference_directions
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
from pymoo.indicators.hv import HV

from model_adapter import (HERE,RealModel,load_study,baseline,write,csv,OUTPUTS,LEDGER,
                           management,check_management_response,validate_space,roundoff_tolerance)


def hard_feasible(y,i,gate,cap):
    return (y>=gate-roundoff_tolerance(gate)) & (i<=cap+roundoff_tolerance(cap))


class WaterBudgetRepair(Repair):
    def _do(self,problem,X,**kwargs):
        X=np.maximum(X,0.)
        total=X.sum(axis=1)
        X*=np.minimum(1.,problem.base_i/np.maximum(total,np.finfo(float).tiny))[:,None]
        return X


class WaterBudgetSampling(Sampling):
    def _do(self,problem,n_samples,random_state=None,**kwargs):
        rng=random_state if random_state is not None else np.random.default_rng(0)
        X=rng.dirichlet(np.ones(problem.n_var),size=n_samples)*rng.uniform(.15,1.,n_samples)[:,None]*problem.base_i
        X=np.clip(X,problem.xl,problem.xu)
        X[0]=np.asarray(problem.spec['baseline_amounts'])
        return X


class DeterministicIrrigationProblem(Problem):
    def __init__(self,model,study,year,spec):
        self.model,self.study,self.year,self.spec=model,study,year,validate_space(spec)
        super().__init__(n_var=len(spec['names']),n_obj=2,n_ieq_constr=2,
                         xl=np.asarray(spec['lower'],float),xu=np.asarray(spec['upper'],float))
        self.params=study['_centers'][year]
        self.observed=float(study['observed_Y13'][str(year)])
        self.base_i=float(study['baseline_irrigation_mm'][str(year)])
        self.gate=study['yield_fraction']*self.observed

    def response(self,x):
        request=management(self.spec,x)
        r=self.model.simulate(self.params,self.year,request)
        return check_management_response(r,self.spec,x)

    def _evaluate(self,X,out,*args,**kwargs):
        f=[];g=[];records=[]
        for x in X:
            r=self.response(x);y,i=r['Y_13pct'],r['Irrigation_mm']
            f.append([-y,i])
            # Scale for the optimizer; the hard physical gates remain exact.
            gi=i-self.base_i;gy=self.gate-y
            if abs(gi)<=roundoff_tolerance(self.base_i):gi=0.
            if abs(gy)<=roundoff_tolerance(self.gate):gy=0.
            g.append([gi/self.base_i,gy/self.observed])
            if hasattr(self,'evaluation_file'):
                records.append(dict(**dict(zip(self.spec['names'],map(float,x))),
                    **{k:r[k] for k in OUTPUTS+LEDGER+['Y_dry','Growing_days','Harvest_date','Early_termination',
                        'Planned_irrigation_mm','Cancelled_irrigation_mm']},
                    G_irrigation=g[-1][0],G_yield=g[-1][1]))
        out['F']=np.asarray(f);out['G']=np.asarray(g)
        if records:
            pd.DataFrame(records).to_csv(self.evaluation_file,index=False,mode='a',
                header=not self.evaluation_file.exists(),compression='gzip')


def nondominated(df):
    if df.empty:return df.copy()
    d=df.copy();objectives=np.column_stack([-d.Y13,d.Irrigation_mm])
    keep=NonDominatedSorting().do(objectives,only_non_dominated_front=True)
    return d.iloc[keep].drop_duplicates(subset=['Y13','Irrigation_mm']).sort_values(['Irrigation_mm','Y13'],ascending=[True,False]).reset_index(drop=True)


def epsilon_choices(df,observed,base_i,fraction=.95):
    if df.empty:return df.copy()
    feasible=df[hard_feasible(df.Y13,df.Irrigation_mm,fraction*observed,base_i)].copy()
    front=nondominated(feasible)
    if front.empty:return front
    selected=front.head(3).copy()
    selected['Selection']=['epsilon_min_irrigation','adjacent_alternative_1','adjacent_alternative_2'][:len(selected)]
    return selected


def run_seed(problem,algorithm,seed,generations,population,folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    if (folder/'run.json').exists():
        raise FileExistsError('Use a new optimization run directory; do not overwrite a seeded search')
    if algorithm=='NSGA3':
        refs=get_reference_directions('das-dennis',2,n_partitions=population-1)
        algo=NSGA3(pop_size=population,ref_dirs=refs,eliminate_duplicates=True,sampling=WaterBudgetSampling(),repair=WaterBudgetRepair())
    elif algorithm=='NSGA2':algo=NSGA2(pop_size=population,eliminate_duplicates=True,sampling=WaterBudgetSampling(),repair=WaterBudgetRepair())
    else:raise ValueError('Unknown comparator')
    identity={'engine':problem.model.identity,'year':problem.year,'algorithm':algorithm,
              'seed':seed,'population':population,'generations':generations,'objectives':['-Y13','Irrigation_mm'],
              'constraints':['I<=annual_DI_baseline','Y13>=0.95*published_observed'],
              'yield_gate_t_ha':problem.gate,'space':problem.spec,
              'fixed_params':problem.params,'HV_normalization':['Y13/observed','I/baseline_I'],'HV_reference':[0,1.01]}
    write(folder/'run.json',{'status':'RUNNING','identity':identity})
    problem.evaluation_file=folder/'evaluations.csv.gz'
    history=[];indicator=HV(ref_point=np.array([0.,1.01]))
    def callback(a):
        x,f,g=a.pop.get('X'),a.pop.get('F'),a.pop.get('G')
        cv=a.pop.get('CV').ravel();feasible=f[cv<=0]
        nf=feasible/np.array([problem.observed,problem.base_i])
        hv=float(indicator(nf)) if len(nf) else 0.
        np.savez_compressed(folder/f'generation_{a.n_gen:04d}.npz',X=x,F=f,G=g,CV=cv)
        history.append(dict(Year=problem.year,Algorithm=algorithm,Seed=seed,Generation=a.n_gen,
                            Evaluations=a.evaluator.n_eval,Feasible=len(feasible),Hypervolume=hv))
        csv(folder/'history.csv',history)
        if a.n_gen%10==0:print(f'{problem.year} {algorithm} seed={seed} generation={a.n_gen}/{generations} feasible={len(feasible)}',flush=True)
    try:
        result=minimize(problem,algo,('n_gen',generations),seed=seed,callback=callback,verbose=False)
    except Exception as error:
        write(folder/'run.json',{'status':'FAILED','identity':identity,'error':str(error)})
        raise
    if result.F is None:
        write(folder/'run.json',{'status':'NO_FEASIBLE_SOLUTION','identity':identity,'evaluations':result.algorithm.evaluator.n_eval})
        return pd.DataFrame(),history
    rows=[]
    for x,f in zip(np.atleast_2d(result.X),np.atleast_2d(result.F)):
        y,i=-float(f[0]),float(f[1])
        if not hard_feasible(y,i,problem.gate,problem.base_i):continue
        rows.append(dict(Year=problem.year,Algorithm=algorithm,Seed=seed,Y13=y,Irrigation_mm=i,
                         **dict(zip(problem.spec['names'],map(float,x)))))
    df=nondominated(pd.DataFrame(rows));csv(folder/'pareto_front.csv',df)
    write(folder/'run.json',{'status':'COMPLETE' if len(df) else 'NO_FEASIBLE_SOLUTION',
          'identity':identity,'evaluations':result.algorithm.evaluator.n_eval,'feasible_front_size':len(df)})
    return df,history


def run_year(model,study,year,out,generations=None,population=None,seeds=None,compare=None,collect_existing=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    base=baseline(model,study,year,out);spec=model.management_space(year)
    write(out/'decision_space.json',spec)
    cfg=study['optimization'];generations=generations or cfg['generations'];population=population or cfg['population']
    seeds=seeds or cfg['seeds'];compare=cfg['compare_nsga2'] if compare is None else compare
    problem=DeterministicIrrigationProblem(model,study,year,spec)
    fronts=[];histories=[]
    algorithms=['NSGA3','NSGA2'] if compare else ['NSGA3']
    for algorithm in algorithms:
        for seed in seeds:
            folder=out/f'{algorithm}_seed{seed}'
            if collect_existing:
                from model_adapter import read
                status=read(folder/'run.json')
                if status['status'] not in ['COMPLETE','NO_FEASIBLE_SOLUTION'] or status['identity']['engine']!=model.identity:
                    raise ValueError('Cannot collect unfinished or different-engine optimization')
                f=pd.read_csv(folder/'pareto_front.csv') if status['status']=='COMPLETE' else pd.DataFrame()
                h=pd.read_csv(folder/'history.csv').to_dict('records')
            else:f,h=run_seed(problem,algorithm,seed,generations,population,folder)
            if not f.empty:fronts.append(f)
            histories+=h
            print(f'Optimization {year} {algorithm} seed={seed}: {len(f)} feasible front points',flush=True)
    all_fronts=pd.concat(fronts,ignore_index=True) if fronts else pd.DataFrame()
    csv(out/'all_seed_fronts.csv',all_fronts);csv(out/'convergence_history.csv',histories)
    observed=problem.observed
    if all_fronts.empty:
        write(out/'optimization_summary.json',{'status':'NO_FEASIBLE_SOLUTION','year':year,'engine':model.identity,
              'recommendation':None,'no_high_yield_fallback':True});return pd.DataFrame()
    # Recommend from the NSGA-III union; report NSGA-II separately for comparison.
    main_front=nondominated(all_fronts[all_fronts.Algorithm=='NSGA3'])
    csv(out/'pareto_front.csv',main_front)
    comparison=[]
    for algorithm,g in all_fronts.groupby('Algorithm'):
        union=nondominated(g);norm=np.column_stack([-union.Y13/observed,union.Irrigation_mm/problem.base_i])
        comparison.append(dict(Algorithm=algorithm,Union_front_size=len(union),
                               Normalized_union_HV=float(HV(ref_point=np.array([0.,1.01]))(norm))))
    csv(out/'algorithm_comparison.csv',comparison)
    choices=epsilon_choices(main_front,observed,problem.base_i,study['yield_fraction'])
    replays=[]
    for n,row in choices.iterrows():
        x=np.array([row[k] for k in spec['names']]);r=problem.response(x)
        if not math.isclose(r['Y_13pct'],row.Y13,rel_tol=1e-8,abs_tol=1e-8) or not math.isclose(r['Irrigation_mm'],row.Irrigation_mm,abs_tol=1e-6):
            raise ValueError('Candidate replay changed; reset simulator state')
        if not hard_feasible(r['Y_13pct'],r['Irrigation_mm'],problem.gate,problem.base_i):
            raise ValueError('Replayed candidate violates the absolute production/irrigation gate')
        candidate_id=f'{year}_C{n+1}'
        replays.append(dict(Candidate_ID=candidate_id,Selection=row.Selection,Y13=r['Y_13pct'],
                     Irrigation_mm=r['Irrigation_mm'],Observed_Y13=observed,Model_baseline_Y13=base['Y_13pct'],
                     Yield_change_vs_observed_pct=100*(r['Y_13pct']/observed-1),
                     Yield_change_vs_model_pct=100*(r['Y_13pct']/base['Y_13pct']-1),
                     Water_saving_pct=100*(1-r['Irrigation_mm']/problem.base_i),
                     IWP_kg_m3=r['IWP_kg_m3'],ET_mm=r['ET_mm'],Tr_mm=r['Tr_mm'],Es_mm=r['Es_mm'],
                     Water_balance_residual_mm=r['Water_balance_residual_mm'],
                     **{k:float(row[k]) for k in spec['names']}))
        write(out/f'{candidate_id}_real_replay.json',{'params':problem.params,'management':management(spec,x),'output':r,'engine':model.identity})
    selected=csv(out/'epsilon_candidates.csv',replays)
    write(out/'optimization_summary.json',{'status':'CANDIDATES_REPLAYED' if len(selected) else 'NO_FEASIBLE_SOLUTION',
          'year':year,'engine':model.identity,'objectives':2,'fixed_central_params':True,'algorithms':algorithms,
          'generations':generations,'population':population,'seeds':seeds,'candidate_count':len(selected),
          'requested_alternatives':2,'available_alternatives':max(0,len(selected)-1),
          'selection':'epsilon minimum irrigation, not geometric knee','conditional_validation':'separate next step'})
    from plot_results import plot_optimization
    plot_optimization(all_fronts,pd.DataFrame(histories),selected,base,observed,out)
    return selected


def main(study=None,model=None,out=None,years=None,generations=None,population=None,seeds=None,compare=None):
    study=study or load_study();model=model or RealModel(study)
    out=Path(out or HERE/'output_revised')/'optimization';out.mkdir(parents=True,exist_ok=True)
    for year in years or study['years']:
        target=out/str(year)
        selected=run_year(model,study,year,target,generations,population,seeds,compare)
        if not selected.empty:
            from validate_candidates import validate_year
            validate_year(model,study,year,model.management_space(year),selected,target)
    return out


if __name__=='__main__':main()
