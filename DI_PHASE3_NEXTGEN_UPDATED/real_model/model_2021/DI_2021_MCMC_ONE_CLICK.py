# -*- coding: utf-8 -*-
"""2021 DI FULL MCMC: all model, sampler, audit and report code included.
No runner.py or other project Python files are required. Keep data/ beside this file.
ONE CLICK: preflight, then formal sampling (2000 steps per ensemble per phase).
Four independent ensembles, 32 walkers each, conditional two-stage inference.
"""
from pathlib import Path
import types,sys,linecache

# ================= USER INPUT / OUTPUT PATHS =================
PACKAGE_DIR=Path(__file__).resolve().parent
DATA_DIR=PACKAGE_DIR/'data'  # Frozen input snapshot. Keep this folder intact.
OUTPUT_DIR=PACKAGE_DIR/'MCMC_Article_Results_2021'/'DI_2021'
# PyCharm: click Run directly. Leave Script parameters EMPTY.
# ============================================================

# Source sections use isolated namespaces to preserve the audited model globals.
# Plain source is embedded below, not downloaded, extracted, or executed externally.
_SOURCES={}

# ================= FULL SOURCE: sampler =================
_SOURCES['sampler']=r'''
"""emcee ensembles with atomic, exact-RNG NumPy checkpoints (no pickle/HDF)."""
import json,os
from pathlib import Path
import numpy as np
import emcee

def atomic_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    os.replace(temp,path)

def encode_rng(state):
    return json.dumps([state[0],state[1].tolist(),int(state[2]),int(state[3]),float(state[4])])

def decode_rng(value):
    x=json.loads(value)
    return (x[0],np.array(x[1],dtype=np.uint32),x[2],x[3],x[4])

def run_ensemble(logp,start,lower,upper,steps,walkers,seed,path,contract,checkpoint_every=25):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    lower=np.asarray(lower,float);upper=np.asarray(upper,float);dim=len(lower)
    if walkers<2*dim: raise ValueError('emcee needs at least 2*dimension walkers')
    encoded=json.dumps(contract,sort_keys=True,allow_nan=False)
    if path.exists():
        with np.load(path,allow_pickle=False) as f:
            if str(f['contract'].item())!=encoded: raise RuntimeError('Checkpoint contract mismatch; use a new output directory')
            x=f['position'];lp=f['logp'];rng=decode_rng(str(f['rng_state'].item()))
            hist=list(f['history']);logs=list(f['logs']);accepted=list(f['accepted'])
        actual=np.array([logp(v) for v in x])
        if not np.isfinite(actual).all() or not np.allclose(actual,lp,atol=1e-8,rtol=0):
            raise RuntimeError('Checkpoint log posterior cannot be reproduced')
    else:
        random=np.random.RandomState(seed);coords=[];probs=[]
        for _ in range(100000):
            v=np.asarray(start)+random.normal(0,.06,dim)*(upper-lower)
            if np.any(v<lower) or np.any(v>upper): continue
            p=logp(v)
            if np.isfinite(p): coords.append(v);probs.append(p)
            if len(coords)==walkers: break
        else: raise RuntimeError('Cannot initialize finite walkers')
        x=np.array(coords);lp=np.array(probs);rng=random.get_state();hist=[];logs=[];accepted=[]
    def save():
        temp=path.with_suffix('.npz.tmp')
        with open(temp,'wb') as f:
            np.savez_compressed(f,position=x,logp=lp,history=np.array(hist).reshape(-1,walkers,dim),
                logs=np.array(logs).reshape(-1,walkers),accepted=np.array(accepted,bool).reshape(-1,walkers),
                contract=encoded,rng_state=encode_rng(rng))
            f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    if len(hist)>steps: raise RuntimeError('Requested steps are shorter than checkpoint')
    if not path.exists(): save()
    if len(hist)==steps: return np.array(hist),np.array(logs),np.array(accepted)
    sampler=emcee.EnsembleSampler(walkers,dim,logp)
    state=emcee.State(x,log_prob=lp,random_state=rng)
    for state in sampler.sample(state,iterations=steps-len(hist),store=False):
        accepted.append(np.any(state.coords!=x,axis=1))
        x=state.coords.copy();lp=state.log_prob.copy();rng=state.random_state
        hist.append(x.copy());logs.append(lp.copy())
        if len(hist)%checkpoint_every==0:
            save();print(path.name,'step',len(hist),'/',steps,flush=True)
    save()
    return np.array(hist),np.array(logs),np.array(accepted)

'''

# ================= FULL SOURCE: diagnostics =================
_SOURCES['diagnostics']=r'''
"""Rank-normalized folded split Rhat and split bulk/tail ESS.
Definitions: https://mc-stan.org/docs/reference-manual/analysis.html
ESS uses Geyer positive, monotone paired autocorrelations; conservatively capped
at actual draws (no antithetic ESS bonus). Chains here are INDEPENDENT chains.
"""
import numpy as np
from scipy.stats import rankdata,norm

def split(x):
    half=x.shape[1]//2
    return np.concatenate([x[:,:half],x[:,-half:]],axis=0)

def ranks(x):
    r=rankdata(x.ravel(),method='average')
    return norm.ppf((r-.375)/(len(r)+.25)).reshape(x.shape)

def basic_rhat(x):
    n=x.shape[1];W=np.mean(np.var(x,axis=1,ddof=1))
    if W<=0: return float('inf')
    varplus=(n-1)/n*W+np.var(x.mean(axis=1),ddof=1)
    return float(np.sqrt(varplus/W))

def ess(x):
    m,n=x.shape
    W=np.mean(np.var(x,axis=1,ddof=1))
    vp=(n-1)/n*W+np.var(x.mean(axis=1),ddof=1)
    if not np.isfinite(vp) or vp<=0: return 0.
    centered=x-x.mean(axis=1,keepdims=True)
    size=1<<(2*n-1).bit_length()
    f=np.fft.rfft(centered,n=size,axis=1)
    acov=np.fft.irfft(f*np.conjugate(f),n=size,axis=1)[:,:n]/n
    rho=1-(W-acov.mean(axis=0))/vp;rho[0]=1.
    pairs=[]
    for lag in range(0,n-1,2):
        pair=float(rho[lag]+rho[lag+1])
        if pair<0: break
        pairs.append(min(pair,pairs[-1]) if pairs else pair)
    tau=max(1.,-1+2*sum(pairs))
    return float(m*n/tau)

def diagnose(chains,names):
    # chains shape: independent chain, retained draw, parameter
    reports=[]
    for j,name in enumerate(names):
        x=np.asarray(chains[:,:,j],float)
        valid=x.shape[0]>=4 and x.shape[1]>=8 and np.isfinite(x).all()
        if valid:
            s=split(x);z=ranks(s)
            r=max(basic_rhat(z),basic_rhat(ranks(np.abs(s-np.median(s)))))
            bulk=ess(z);ql,qh=np.quantile(s,[.05,.95]);tail=min(ess((s<=ql).astype(float)),ess((s<=qh).astype(float)))
        else: r=float('inf');bulk=tail=0.
        passed=bool(x.shape[1]>=100 and np.isfinite(r) and r<1.01 and bulk>=400 and tail>=400)
        reports.append(dict(Parameter=name,Rhat=float(r) if np.isfinite(r) else None,ESS_bulk=bulk,ESS_tail=tail,Passed=passed))
    return reports

'''

# ================= FULL SOURCE: audit_hooks =================
_SOURCES['audit_hooks']=r'''
import inspect
import numpy as np
AuditError = RuntimeError

def harvest_index_observer(original, context, records):
    """Audit HI0 preservation and the explicit HImult cap in harvest_index."""
    signature = inspect.signature(original)

    def wrapper(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        v = bound.arguments
        required = ['Crop', 'InitCond', 'growing_season']
        if any((k not in v for k in required)):
            raise AuditError(f'harvest_index接口变化，实际签名={signature}')
        crop = v['Crop']
        cond = v['InitCond']
        hi0_before = float(crop.HI0)
        result = original(*args, **kwargs)
        f_pre = float(getattr(result, 'f_pre', np.nan))
        f_post = float(getattr(result, 'f_post', np.nan))
        hmult_raw = f_pre * f_post
        hmult_cap = 1 + float(crop.dHI0) / 100
        hit = int(getattr(result, 'dap', 0)) - int(getattr(result, 'delayed_cds', 0)) - int(crop.HIstartCD) - 1
        cap_branch_applicable = bool(v['growing_season'] and getattr(result, 'yield_form', False) and (hit >= 0) and (int(crop.CropType) in (2, 3)))
        values = np.asarray([hi0_before, float(crop.HI0), float(getattr(result, 'harvest_index', np.nan)), float(getattr(result, 'harvest_index_adj', np.nan)), f_pre, f_post], float)
        records.append(dict(Case=context['case'], Date=context['date'], HI0_before=hi0_before, HI0_after=float(crop.HI0), HI_ref=float(getattr(result, 'hi_ref', np.nan)), HI_after=float(getattr(result, 'harvest_index', np.nan)), HI_adj_after=float(getattr(result, 'harvest_index_adj', np.nan)), f_pre=f_pre, f_post=f_post, f_pol=float(getattr(result, 'f_pol', np.nan)), HImult_raw=hmult_raw, HImult_cap=hmult_cap, HImult_cap_branch_applicable=cap_branch_applicable, HImult_cap_triggered=bool(cap_branch_applicable and hmult_raw > hmult_cap + 1e-12), Nonfinite_state=bool(not np.isfinite(values).all()), HI_out_of_physical_range=bool(np.any(values[:4] < -1e-12) or np.any(values[:4] > 1 + 1e-12))))
        return result
    return wrapper

def pollination_observer(original, context, records):
    """Reconstruct the uncapped f_pol update and report the exact >1 cap."""
    signature = inspect.signature(original)

    def wrapper(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        v = bound.arguments
        required = ['NewCond_CC', 'NewCond_Fpol', 'Crop_FloweringCD', 'Crop_CCmin', 'Crop_exc', 'Ksw', 'Kst', 'HIt']
        if any((k not in v for k in required)):
            raise AuditError(f'HIadj_pollination接口变化，实际签名={signature}')
        hit = float(v['HIt'])
        flower = float(v['Crop_FloweringCD'])
        if hit <= 0:
            frac = 0.0
        else:

            def flowering_fraction(t):
                if t <= 0:
                    return 0.0
                pct = min(100.0, 100 * t / flower)
                value = 0.00558 * np.exp(0.63 * np.log(pct)) - 0.000969 * pct - 0.00383
                return max(0.0, float(value))
            f1 = flowering_fraction(hit - 1)
            f2 = flowering_fraction(hit)
            frac = 0.0 if abs(f1 - f2) < 1e-07 else 100 * ((f1 + f2) / 2) / flower
        if float(v['NewCond_CC']) < float(v['Crop_CCmin']):
            increment = 0.0
        else:
            ksw = v['Ksw']
            kst = v['Kst']
            increment = min(float(ksw.pol), float(kst.PolC), float(kst.PolH)) * frac * (1 + float(v['Crop_exc']) / 100)
        raw = float(v['NewCond_Fpol']) + increment
        result = original(*args, **kwargs)
        records.append(dict(Case=context['case'], Date=context['date'], HIt=hit, f_pol_before=float(v['NewCond_Fpol']), increment_raw=increment, f_pol_uncapped=raw, f_pol_after=float(result), Pollination_cap_triggered=bool(raw > 1 + 1e-12)))
        return result
    return wrapper

'''

# ================= FULL SOURCE: ensemble_pipeline =================
_SOURCES['ensemble_pipeline']=r'''
"""Four independent emcee ensembles; coupled walkers are NOT independent chains."""
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from emcee.autocorr import integrated_time
from _di_2021_sampler import atomic_json,run_ensemble
from _di_2021_diagnostics import diagnose

def analyze(phase,names,raw,logs,accept,lower,upper,out,smoke):
    ensembles,n,walkers,dim=raw.shape
    tables=[]
    for e in range(ensembles):
        t=pd.DataFrame(raw[e].reshape(-1,dim),columns=names)
        t.insert(0,'Walker',np.tile(np.arange(walkers),n));t.insert(0,'Step',np.repeat(np.arange(n),walkers));t.insert(0,'Ensemble',e)
        t['Log_posterior']=logs[e].ravel();t['Accepted']=accept[e].ravel();tables.append(t)
    full=pd.concat(tables,ignore_index=True)
    # Raw draws and final walkers are persisted BEFORE autocorrelation/plotting.
    full.to_csv(out/f'mcmc_full_chain_{phase}.csv',index=False)
    full[full.Step==n-1].to_csv(out/f'last_walker_positions_{phase}.csv',index=False)
    taus=[]
    for e in range(ensembles):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            try: tau=integrated_time(raw[e],tol=0)
            except (ValueError,IndexError): tau=np.full(dim,np.nan)
        taus.append(tau)
    taus=np.array(taus);valid=bool(np.isfinite(taus).all() and (taus>0).all())
    burn=int(np.ceil(5*taus.max())) if valid else None
    usable=burn is not None and burn<n
    post=full[full.Step>=burn].copy() if usable else full.iloc[:0].copy()
    post.to_csv(out/f'mcmc_posterior_after_burnin_{phase}.csv',index=False)
    retained=raw[:,burn:,:,:] if usable else raw[:,:0,:,:]
    # Compare each fixed walker index ACROSS independent ensembles. Never pool
    # walkers from the same ensemble as independent chains for Rhat or ESS.
    groups=[diagnose(retained[:,:,w,:],names) for w in range(walkers)] if usable else []
    rows=[]
    for j,k in enumerate(names):
        values=[g[j] for g in groups]
        rh=[v['Rhat'] for v in values]
        r=max(rh) if rh and all(v is not None for v in rh) else None
        bulk=min(v['ESS_bulk'] for v in values) if values else 0.
        tail=min(v['ESS_tail'] for v in values) if values else 0.
        passed=bool(values and all(v['Passed'] for v in values))
        rows.append(dict(Parameter=k,Rhat_max_across_walker_groups=r,ESS_bulk_min=bulk,ESS_tail_min=tail,Passed=passed))
    tau_trusted=bool(valid and n>=50*taus.max())
    passed=bool(not smoke and n>=2000 and usable and tau_trusted and all(r['Passed'] for r in rows))
    atomic_json(out/f'{phase}_diagnostics.json',dict(Converged=passed,Smoke_test=smoke,
        Burn_in=burn,Rule='ceil(5 * maximum tau across parameters and independent ensembles); NO fixed fallback',
        Tau_by_ensemble=[[float(v) if np.isfinite(v) else None for v in row] for row in taus],
        Tau_estimate_trusted_50tau=tau_trusted,Parameters=rows,
        Acceptance_by_ensemble_walker=accept.mean(axis=1).tolist(),
        Status='CONVERGED' if passed else 'SMOKE_NOT_INFERENCE' if smoke else 'CHAIN_LENGTH_OR_CONVERGENCE_INSUFFICIENT',
        Rhat_scope='Conservative maximum over matched-walker groups across 4 independent ensembles; not 128 independent chains',
        Criteria='>=2000 total steps; Rhat<1.01, bulk/tail ESS>=400 in each group; >=100 retained steps; chain>=50*max(tau)',
        References=['https://emcee.readthedocs.io/en/stable/user/autocorr/','https://mc-stan.org/docs/reference-manual/analysis.html']))
    # Test-only point permits exercising phase 2; never called a posterior MAP.
    eligible=post if len(post) else full if smoke else None
    best={}
    if eligible is not None:
        row=eligible.loc[eligible.Log_posterior.idxmax()];best={k:float(row[k]) for k in names}
    summaries=[]
    if len(post):
        for j,k in enumerate(names):
            v=post[k].to_numpy();q=np.quantile(v,[.025,.25,.5,.75,.975]);edge=.01*(upper[j]-lower[j])
            summaries.append(dict(Phase=phase,Mean=v.mean(),SD=v.std(ddof=1),Median=q[2],
                P2_5=q[0],P25=q[1],P75=q[3],P97_5=q[4],MAP=best[k],Tau=float(taus[:,j].max()),
                Burn_in=burn,ESS=rows[j]['ESS_bulk_min'],Prior_low=lower[j],Prior_high=upper[j],
                MAP_near_boundary_1pct=bool(min(best[k]-lower[j],upper[j]-best[k])<=edge),
                Mass_lower_1pct=float(np.mean(v<=lower[j]+edge)),Mass_upper_1pct=float(np.mean(v>=upper[j]-edge)),**rows[j]))
    summary=pd.DataFrame(summaries)
    summary.to_csv(out/f'{phase}_summary.csv',index=False)
    combined=raw.transpose(1,0,2,3).reshape(n,ensembles*walkers,dim)
    return dict(phase=phase,names=names,best=best,converged=passed,summary=summary,
        chain=combined,post=post,burn=burn,acceptance=accept.mean(axis=1).ravel(),
        retained=retained.reshape(ensembles,-1,dim),smoke=smoke)

def run_phase(m,data,fixed,names,phase,args,out,cn,cached=False):
    lower=np.array([m.PRIOR_BOUNDS[k][0] for k in names]);upper=np.array([m.PRIOR_BOUNDS[k][1] for k in names])
    start=np.array([fixed[k] for k in names]);allx=[];allp=[];alla=[]
    for e in range(4):
        path=out/'checkpoints'/phase/f'ensemble_{e+1}.npz'
        if cached:
            with np.load(path,allow_pickle=False) as f: x=f['history'];p=f['logs'];a=f['accepted']
        else:
            x,p,a=run_ensemble(lambda v:m.logprob(v,names,fixed,phase,data),start,lower,upper,
                args.steps,args.walkers,args.seed+m.YEAR*100+e+(100000 if phase=='biomass_yield' else 0),
                path,dict(cn,ensemble=e),args.checkpoint_every)
        allx.append(x);allp.append(p);alla.append(a)
    result=analyze(phase,names,np.array(allx),np.array(allp),np.array(alla),lower,upper,out,args.smoke)
    result['values']=dict(fixed,**result['best'])
    atomic_json(out/f'{phase}_sampled_MAP.json',dict(values=result['values'] if result['best'] else None,
        Converged=result['converged'],Smoke_test=args.smoke,
        Meaning='Test-only point, NOT posterior MAP' if args.smoke else 'Maximum retained sampled log posterior; not globally optimized MAP'))
    return result

'''

# ================= FULL SOURCE: runner =================
_SOURCES['runner']=r'''
"""Audited conditional grouped MCMC. Default: preflight only; no sampling."""
from pathlib import Path
import argparse,importlib.util,importlib.metadata,importlib,inspect,json,hashlib,os
import numpy as np
import pandas as pd
from _di_2021_sampler import atomic_json
from _di_2021_ensemble_pipeline import run_phase
from _di_2021_diagnostics import diagnose
from _di_2021_audit_hooks import harvest_index_observer,pollination_observer

ROOT=Path(__file__).resolve().parent
KEYS=['Y_dry','Tr_mm','Es_mm','B_last','CC_RMSE']
LIMITATIONS=[
    'Grouped conditional inference: phase 2 conditions on phase-1 sampled MAP; not an 8-parameter joint posterior.',
    '2019-2021 effective WP Uniform(10,40) is a declared working prior, NOT a literature-validated physiological prior.',
    '2019-2021 HI0 stays within [0.35,0.60]; boundary posterior mass must be reported, not silently eliminated.',
    'Digitized biomass has assumed sigma, not measured SD, and is not independent validation.',
    'Zero irrigation is an unvalidated counterfactual under locked initial water and fixed-calendar WP switch; no target loss percentage.',
    '2019 Es bias and phase-1 parameter boundaries remain model limitations.',
    '2020 primary: 152 simulated days through Sep18; 151-day alternative is separately provided.',
    'SenescenceCD remains continuous in the prior and is rounded to integer days by the engine, as in the audited baseline.'
]

def compare_initial(actual,reference):
    if any(not np.isfinite(actual[k]) or abs(actual[k]-reference[k])>1e-8 for k in KEYS):
        raise RuntimeError('MCMC initial-point reproduction failed')

def load(case,out):
    folder=ROOT/'data'
    m=_embedded_module('model',folder/'model.py')
    m.OUTPUT_DIR=out/'input_audit';m.OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
    data=m.load_inputs();m.prepare_soil(data)
    point=json.loads((folder/'start.json').read_text())
    if case!='2022':
        m.PRIOR_BOUNDS.update(WP_early=(10.,40.),WP_late=(10.,40.),HI0=(.35,.60))
        m.NORMAL_PRIORS={'CDC_CD','SenescenceCD'}
        data['center'].update(WP_early=25.,WP_late=25.) # irrelevant to these uniform priors
    assert m.PHASE2_NAMES==['WP_early','WP_late','HI0']
    assert len(m.DATES)==(152 if case=='2020' else 151 if case in ['2019','2020_151d'] else 148)
    return m,data,point,folder

def internal_audit(m,data,point,mode,out):
    step=importlib.import_module('aquacrop.timestep.run_single_timestep')
    hi=importlib.import_module('aquacrop.solution.harvest_index')
    original=step.harvest_index;opol=hi.HIadj_pollination
    signature=inspect.signature(original);records=[];poll=[];context={'case':mode,'date':None}
    observed=harvest_index_observer(original,context,records)
    def call(*args,**kwargs):
        v=signature.bind(*args,**kwargs).arguments
        context['date']=str((m.PLANT+pd.Timedelta(days=int(v['InitCond'].dap)-1)).date())
        result=observed(*args,**kwargs)
        c=v['Crop'];records[-1]['Effective_WP']=float(c.WP*c.fCO2)
        records[-1]['PlantPop']=float(c.PlantPop)
        return result
    try:
        step.harvest_index=call;hi.HIadj_pollination=pollination_observer(opol,context,poll)
        result=m.simulate(data,point,mode)
    finally:
        step.harvest_index=original;hi.HIadj_pollination=opol
    h=pd.DataFrame(records);p=pd.DataFrame(poll)
    m.require(len(h)==len(m.DATES) and len(p)>0,'HI audit calls incomplete')
    m.require(pd.DatetimeIndex(pd.to_datetime(h.Date)).equals(m.DATES),'HI audit date mismatch')
    m.require(np.isfinite(h.select_dtypes(include=[np.number]).to_numpy()).all(),'Nonfinite HI internal state')
    m.require(np.isfinite(p.select_dtypes(include=[np.number]).to_numpy()).all(),'Nonfinite pollination state')
    clipped=not (np.allclose(h.HI0_before,point['HI0'],atol=1e-12,rtol=0) and np.allclose(h.HI0_after,point['HI0'],atol=1e-12,rtol=0))
    m.require(not clipped and not h.HI_out_of_physical_range.any(),'HI clipping or nonphysical state')
    expected=np.where(pd.to_datetime(h.Date)<m.SWITCH,point['WP_early'],point['WP_late'])
    m.require(np.allclose(h.Effective_WP,expected,atol=1e-9,rtol=0),'Effective WP daily mismatch')
    m.require(np.allclose(h.PlantPop,79365.),'Density mismatch')
    m.require(result[0]['Max_daily_balance_residual_mm']<1e-8,'Water balance failed')
    out.mkdir(parents=True,exist_ok=True);h.to_csv(out/(mode+'_HI_daily.csv'),index=False);p.to_csv(out/(mode+'_pollination.csv'),index=False)
    return result,dict(Calls=len(h),Pollination_calls=len(p),Input_clipped=clipped,
        HI_out_of_range=bool(h.HI_out_of_physical_range.any()),HImult_cap_days=int(h.HImult_cap_triggered.sum()),
        Pollination_cap_days=int(p.Pollination_cap_triggered.sum()),Effective_WP_daily_verified=bool(np.allclose(h.Effective_WP,expected,atol=1e-9,rtol=0)))

def preflight(m,data,point,folder,out):
    m.require(not data.get('bio_error') and not data['bio'].empty,
        data.get('bio_error') or 'MISSING_BIOMASS_CALIBRATION_DATA')
    data['start']=point
    data['start_boundary_flags']=[k+' starts within 1% of a prior bound' for k in m.ALL_NAMES
        if min(point[k]-m.PRIOR_BOUNDS[k][0],m.PRIOR_BOUNDS[k][1]-point[k])<=.01*(m.PRIOR_BOUNDS[k][1]-m.PRIOR_BOUNDS[k][0])]
    process_status,flags=m.pre_run(data)
    m.require(process_status!='FAIL','Pre-run scientific/physical hard failure: '+str(flags))
    m.frozen_regression(data)
    expected=json.loads((folder/'expected_initial.json').read_text())
    di,hi=internal_audit(m,data,point,'DI',out/'preflight')
    zero,zh=internal_audit(m,data,point,'zero',out/'preflight')
    if abs(di[0]['Es_mm']/m.ES_TARGET-1)>.15:
        flags.append('Es differs from digitized target by more than 15%; retained model limitation')
        process_status='REVIEW'
    if abs(di[0]['Y_13pct']/m.Y13_PUBLISHED-1)>.015:
        flags.append('Yield error exceeds 1.5%; retained discrepancy, not a hard sampling target')
        process_status='REVIEW'
    compare_initial(di[0],expected)
    compare_initial(m.simulate(data,point,'DI')[0],expected)
    bad=dict(expected,Y_dry=expected['Y_dry']+.01);negative=False
    try: compare_initial(di[0],bad)
    except RuntimeError: negative=True
    m.require(negative,'Fail-fast negative test failed')
    # Fixed-WP HI endpoints must leave the water/canopy/biomass unchanged.
    for value in m.PRIOR_BOUNDS['HI0']:
        s=m.simulate(data,dict(point,HI0=value),'DI')[0]
        for key in ['B_last','CC_RMSE','Tr_mm','Es_mm','ET_mm']:
            m.require(abs(s[key]-di[0][key])<1e-8,'HI profile invariance failed: '+key)
    prior={k:dict(low=m.PRIOR_BOUNDS[k][0],high=m.PRIOR_BOUNDS[k][1],
                 distribution='truncated_normal' if k in m.NORMAL_PRIORS else 'uniform',
                 center=data['center'][k] if k in m.NORMAL_PRIORS else None,
                 sd=m.PRIOR_SD[k] if k in m.NORMAL_PRIORS else None) for k in m.ALL_NAMES}
    report=dict(TECHNICAL_READY=True,Process_status=process_status,Process_flags=flags,Scientific_status='CONDITIONAL_MODEL_WITH_DECLARED_LIMITATIONS',
        Scientific_limitations=LIMITATIONS,Default_sampling=False,Negative_test_rejected=negative,
        Initial_DI=di[0],Initial_zero=zero[0],HI_audit=hi,Zero_HI_audit=zh,Switch=str(m.SWITCH.date()),
        Dates=[str(m.DATES[0].date()),str(m.DATES[-1].date())],Days=len(m.DATES),Priors=prior,
        Source_precision_note='Legacy internal yield targets retained, not claimed as newly observed precision')
    atomic_json(out/'preflight.json',report)
    return report

def contract(case,m,data,names,fixed,phase,args):
    files={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
           for p in (ROOT/'data').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    files[Path(__file__).name]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return dict(case=case,phase=phase,names=names,fixed=fixed,priors=m.PRIOR_BOUNDS,
        normal_priors=sorted(m.NORMAL_PRIORS),prior_sd=m.PRIOR_SD,center=data['center'],
        sigmas=[m.SIGMA_CC,m.SIGMA_TR,m.SIGMA_ES,m.SIGMA_Y],targets=[m.TR_TARGET,m.ES_TARGET,m.YDRY_TARGET],
        seed=args.seed,ensembles=4,walkers=args.walkers,mode='SMOKE_NOT_INFERENCE' if args.smoke else 'sampling',
        switch=str(m.SWITCH),files=files,versions={k:importlib.metadata.version(k) for k in ['aquacrop','numpy','pandas','scipy','emcee']})

def predictive(m,data,p1,p2,c1,c2,args,out):
    rng=np.random.default_rng(args.seed+700)
    predictions=[];biomass=[];canopies=[]
    for i in range(args.ppc):
        # Phase 2 is conditional on the stage-1 MAP; do not invent a joint posterior.
        c=rng.integers(4);t=rng.integers(c2.shape[1]);v=dict(p2,**dict(zip(m.PHASE2_NAMES,c2[c,t])))
        s,g,_,_=m.simulate(data,v,'DI');z=m.simulate(data,v,'zero')[0];biomass.append(g.Biomass_t_ha.to_numpy())
        c=rng.integers(4);t=rng.integers(c1.shape[1]);v1=dict(p1,**dict(zip(m.PHASE1_NAMES,c1[c,t])))
        w,cg,_,_=m.simulate(data,v1,'DI');canopies.append(cg.canopy_cover.to_numpy())
        predictions.append(dict(draw=i,Conditional_Y13=s['Y_13pct'],Conditional_zero_Y13=z['Y_13pct'],
            Conditional_loss_pct=100*(1-z['Y_13pct']/s['Y_13pct']),Phase1_Tr=w['Tr_mm'],Phase1_Es=w['Es_mm'],Phase1_ET=w['ET_mm']))
    pd.DataFrame(predictions).to_csv(out/'conditional_predictive_draws.csv',index=False)
    for name,array in [('conditional_biomass',biomass),('phase1_canopy',canopies)]:
        q=np.quantile(array,[.025,.5,.975],axis=0)
        pd.DataFrame(dict(Date=m.DATES,Q025=q[0],Median=q[1],Q975=q[2])).to_csv(out/(name+'_bands.csv'),index=False)
    atomic_json(out/'predictive_scope.json',dict(Description='Parameter-induced model prediction intervals; no observation noise added. Not independent validation.',
        Phase1='CC/Tr/Es vary with phase-1 posterior',Phase2='B/yield/zero loss conditional on phase-1 sampled MAP',
        No_first_stage_uncertainty_propagation=True,Zero_irrigation_validated=False))

def main(case,default_output=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sample',action='store_true');p.add_argument('--accept-limitations',action='store_true')
    p.add_argument('--smoke',action='store_true',help='Two-step execution test only, never posterior inference')
    p.add_argument('--steps',type=int,default=2000,help='Total steps per independent emcee ensemble per phase; increase to resume')
    p.add_argument('--seed',type=int,default=42);p.add_argument('--checkpoint-every',type=int,default=25)
    p.add_argument('--ppc',type=int,default=100);p.add_argument('--output',type=Path)
    args=p.parse_args();args.walkers=32
    if args.smoke: args.steps=2;args.walkers=12;args.ppc=0
    if args.steps<2 or args.checkpoint_every<1 or args.ppc<0: p.error('Invalid settings')
    sampling=args.sample or args.smoke
    if sampling and not args.accept_limitations: p.error('Sampling requires --accept-limitations; see ACCOUNT_LEDGER.md')
    base=Path(default_output) if default_output else ROOT/f'MCMC_Article_Results_{case[:4]}'/f'DI_{case}'
    out=(args.output or base/('smoke' if args.smoke else 'sampling' if args.sample else 'preflight')).resolve()
    out.mkdir(parents=True,exist_ok=True);lock=out/'.run.lock'
    try: fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError: raise SystemExit('Output locked: confirm no active process before removing a stale .run.lock')
    os.write(fd,str(os.getpid()).encode());os.close(fd)
    try:
        atomic_json(out/'run_status.json',dict(State='PREFLIGHT_RUNNING',Complete=False,Smoke=args.smoke))
        m,data,point,folder=load(case,out);status=preflight(m,data,point,folder,out)
        print(case,'TECHNICAL PREFLIGHT PASSED; scientific limitations retained',flush=True)
        if not sampling:
            atomic_json(out/'run_status.json',dict(State='PREFLIGHT_COMPLETE',Complete=False,Technical_ready=True,Sampling_started=False));return
        atomic_json(out/'run_status.json',dict(State='RUNNING',Complete=False,Smoke=args.smoke,Limitations=LIMITATIONS))
        def phase(fixed,names,label,cached=False):
            actual=m.simulate(data,fixed,'DI')[0]
            reference=json.loads((folder/'expected_initial.json').read_text()) if label=='canopy_transpiration' else json.loads((out/'phase1_handoff.json').read_text())['initial_metrics']
            compare_initial(actual,reference)
            atomic_json(out/(label+'_initial_point.json'),dict(values=fixed,metrics=actual))
            cn=contract(case,m,data,names,fixed,label,args)
            return run_phase(m,data,fixed,names,label,args,out,cn,cached)
        handoff=out/'phase1_handoff.json'
        if handoff.exists():
            saved=json.loads(handoff.read_text())
            current=contract(case,m,data,m.PHASE1_NAMES,point,'canopy_transpiration',args)
            if saved['contract']!=json.loads(json.dumps(current)): raise RuntimeError('Frozen phase-1 contract mismatch')
            for rel,h in saved['hashes'].items():
                if hashlib.sha256((out/rel).read_bytes()).hexdigest()!=h: raise RuntimeError('Frozen phase-1 evidence changed')
            p1=phase(point,m.PHASE1_NAMES,'canopy_transpiration',cached=True)
            if p1['values']!=saved['values']: raise RuntimeError('Frozen phase-1 MAP changed')
            print('Reusing frozen phase 1; extension only advances phase 2.',flush=True)
        else:
            p1=phase(point,m.PHASE1_NAMES,'canopy_transpiration')
        if not p1['converged'] and not args.smoke:
            atomic_json(out/'run_status.json',dict(State='EXTEND_PHASE1',Complete=False,Phase1_converged=False))
            print('Chain length/convergence insufficient. Increase --steps with identical output/seed. Phase 2 NOT started.');return
        if not handoff.exists():
            evidence=sorted((out/'checkpoints/canopy_transpiration').glob('ensemble_*.npz'))
            atomic_json(handoff,dict(values=p1['values'],converged=p1['converged'],
                initial_metrics=m.simulate(data,p1['values'],'DI')[0],
                contract=contract(case,m,data,m.PHASE1_NAMES,point,'canopy_transpiration',args),
                hashes={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in evidence}))
        if not args.smoke: pd.DataFrame([p1['values']]).to_csv(out/'phase1_MAP_point.csv',index=False)
        p2=phase(p1['values'],m.PHASE2_NAMES,'biomass_yield')
        if p2['converged']:
            pd.DataFrame([p2['values']]).to_csv(out/'grouped_MAP_point.csv',index=False)
            m.OUTPUT_DIR=out;m.NWALKERS=4*args.walkers
            m.postprocess(data,p1,p2)
            # Correct legacy presentation metadata; numerical model is unchanged.
            metadata=pd.read_csv(out/'run_metadata.csv').set_index('Setting')['Value'].to_dict()
            metadata.update(WP_structure='two-stage effective WP for ALL years; experimental structural modification',
                checkpoint_policy='Atomic NPZ including full chain, log posterior, MT19937 state, contract',
                walkers_per_ensemble=args.walkers,independent_ensembles=4,
                inference='Sequential grouped conditional MCMC; not joint 8D posterior',
                Zero_irrigation_validated=False,Limitations=json.dumps(LIMITATIONS))
            pd.DataFrame(metadata.items(),columns=['Setting','Value']).to_csv(out/'run_metadata.csv',index=False)
            if (out/'MAP_biomass_calibration.png').exists():
                (out/'MAP_biomass_validation.png').write_bytes((out/'MAP_biomass_calibration.png').read_bytes())
            if args.ppc: predictive(m,data,p1['values'],p2['values'],p1['retained'],p2['retained'],args,out)
        atomic_json(out/'run_status.json',dict(State='SMOKE_COMPLETE' if args.smoke else 'COMPLETE' if p2['converged'] else 'EXTEND_PHASE2',
            Complete=bool(p1['converged'] and p2['converged']),Smoke=args.smoke,
            Phase1_converged=p1['converged'],Phase2_converged=p2['converged'],
            Joint_8D_posterior=False,Zero_irrigation_validated=False,Scientific_limitations=LIMITATIONS))
        print(case,'SMOKE_COMPLETE' if args.smoke else 'CONVERGED' if p2['converged'] else 'EXTEND_PHASE2',flush=True)
    except BaseException as exc:
        atomic_json(out/'run_status.json',dict(State='INTERRUPTED' if isinstance(exc,KeyboardInterrupt) else 'FAILED',
            Complete=False,Error=str(exc),Checkpoint_note='Last atomically committed checkpoint preserved'))
        raise
    finally: lock.unlink(missing_ok=True)

if __name__=='__main__': raise SystemExit('Use annual DI_YYYY_MCMC_Article_Final_v2.py')

'''

# ================= FULL SOURCE: model =================
_SOURCES['model']=r'''
# -*- coding: utf-8 -*-
# ============================================================================
# >>>>>>>>>>>>>>>>>>>>>>> USER INPUT / OUTPUT PATHS <<<<<<<<<<<<<<<<<<<<<<<<<<<
# ============================================================================
from pathlib import Path
# 【需要你接入的文件 1】研究数据根目录（已有文件，仅读取）
ROOT = Path('C:\\Users\\Lenovo\\Desktop\\竞赛科研\\科研\\URP')
# 【需要你接入的文件 2】本年度气象；禁止缺日插值或替代
WEATHER_FILE = Path(__file__).resolve().parent / 'inputs' / 'WEATHER_FILE_DI_Climate_2021_FINAL.csv'
# 【需要你接入的文件 3】正式 Field LAI-derived CC
FIELD_CC_FILE = Path(__file__).resolve().parent / 'inputs' / 'FIELD_CC_FILE_DI_2019_2022_FIELD_LAI_CC_LOCKED.csv'
# 【需要你接入的文件 4】锁定初始水（含层顶、层底）
INITIAL_WATER_FILE = Path(__file__).resolve().parent / 'inputs' / 'INITIAL_WATER_FILE_DI_2019_2022_AquaCrop_InitialWater_FIELD_LOCKED.csv'
# 【需要你接入的文件 5】RS 辅助检查，绝不进入 likelihood
RS_CC_FILE = Path(__file__).resolve().parent / 'inputs' / 'RS_CC_FILE_Maize-2021-main.csv'
# 【近似校准数据】图4-8数字化DI地上干生物量；Sigma_assumed不是实测SD
BIOMASS_FILE = Path(__file__).resolve().parent / 'inputs' / 'BIOMASS_FILE_DI_2021_biomass_digitized.csv'
# 【需要你接入的文件 7】2022 冻结初始点，随包提供；其他年份不用
INITIAL_POINT_FILE = Path(__file__).resolve().parent / 'inputs' / 'INITIAL_POINT_FILE_mcmc_initial_point.csv'
# 【需要你接入的文件 8】2021 年逐小时标量风速纠偏 ETo，缺失即停止
ETO_FILE = Path(__file__).resolve().parent / 'inputs' / 'ETO_FILE_DI_2021_ETo_B_Audited_Daily.csv'
# 【需要你接入的文件 11】同次 GEE 导出的 2022 control，用于验证同一纠偏算法
ETO_CONTROL_FILE = Path(__file__).resolve().parent / 'inputs' / 'ETO_CONTROL_FILE_DI_2022_ETo_B_Audited_Daily.csv'
# 【随包冻结参照】不可用新 control 覆盖它
FROZEN_2022_ETO_FILE = Path(__file__).resolve().parent / 'inputs' / 'FROZEN_2022_ETO_FILE_DI_2022_ETo_Geometry_Daily.csv'
# 【需要你接入的文件 9】2022 READY 证据
READINESS_FILE = Path(__file__).resolve().parent / 'inputs' / 'READINESS_FILE_pre_mcmc_readiness.json'
# 【需要你接入的文件 10】2022 历史 MAP，仅结构复现，不能作为 prior center
HISTORICAL_MAP_FILE = Path(__file__).resolve().parent / 'inputs' / 'HISTORICAL_MAP_FILE_historical_2022_grouped_MAP_point.csv'
# 【需要你接入的文件 12】本次确定性第一阶段起点；仅用于初始化，绝不是 posterior/prior center
PHASE1_START_POINT_FILE = Path(__file__).resolve().parent / 'inputs' / 'PHASE1_START_POINT_FILE_phase1_deterministic_start_2021.csv'
# 【结果路径】与旧科研结果分开，默认脚本同目录；--output 可覆盖
OUTPUT_DIR = Path(__file__).resolve().parent / 'MCMC_Article_Results_2021' / 'DI_2021'
# 灌溉逐次表、播收边界与物候来自原项目 YEAR_CONFIG；在下方明列，不另猜路径。
# 默认只做 PRE-RUN；正式采样需要 --formal，REVIEW 默认中止。
# ============================================================================
YEAR = 2021
CFG = {'plant': '2021-04-27', 'harvest': '2021-09-22', 'maturity_cd': 148, 'histart_cd': 77, 'yield_t_ha': 15.862, 'late_cc': '2021-08-21', 'irrigation': [('2021-06-13', 93.11), ('2021-06-30', 86.91), ('2021-07-09', 84.57), ('2021-07-20', 76.6), ('2021-07-30', 114.8), ('2021-08-11', 89.54), ('2021-08-23', 87.94)]}
ET_OBS = 626.81
ES_TARGET = 78.0
Y13_PUBLISHED = 15.86
Y13_TARGET = 15.862
IRR_PUBLISHED = 633.46

"""Shared build source. Each delivered annual script includes a full copy."""
import argparse
import copy
import hashlib
import importlib
import importlib.metadata
import inspect
import json
import os
import sys
import time
import numpy as np
import pandas as pd
from aquacrop import AquaCropModel, Soil, Crop, InitialWaterContent, IrrigationManagement, FieldMngt

NWALKERS = 32
NSTEPS = 2000
STOP_BEFORE_FORMAL_MCMC_ON_REVIEW = True
RANDOM_SEED = 42
ETO_AUDIT_REVIEW = []
SIGMA_CC, SIGMA_ES, SIGMA_Y = .05, 15., .67*.87
PHASE1_NAMES = ['CCx','CGC_CD','CDC_CD','SenescenceCD','Kcb']
PHASE2_NAMES = ['WP_early','WP_late','HI0']
ALL_NAMES = PHASE1_NAMES + PHASE2_NAMES
PRIOR_BOUNDS = dict(CCx=(.60,.99), CGC_CD=(.08,.16), CDC_CD=(.03,.12),
                    SenescenceCD=(115.,145.), Kcb=(1.05,1.60), WP=(28.,40.),
                    WP_early=(10.,22.), WP_late=(20.,38.), HI0=(.35,.50 if YEAR==2022 else .60))
PRIOR_SD = dict(CCx=.05, CGC_CD=.015, CDC_CD=.025, SenescenceCD=10., Kcb=.10,
                WP=4., WP_early=3., WP_late=4., HI0=.03)
# 2019–2021: Kcb uses a uniform prior on unchanged [1.05,1.60] bounds.
# Default Kcb=1.05 is not an observation and no longer supplies a Gaussian penalty.
NORMAL_PRIORS = set(ALL_NAMES) if YEAR==2022 else {'CDC_CD','SenescenceCD'}
PLANT = pd.Timestamp(CFG['plant'])
HARVEST = pd.Timestamp(CFG['harvest'])
DATES = pd.date_range(PLANT, HARVEST-pd.Timedelta(days=1))
SWITCH = PLANT + pd.Timedelta(days=CFG['histart_cd'])
TR_TARGET = 503. if YEAR==2022 else ET_OBS-ES_TARGET
SIGMA_TR = .1*TR_TARGET
YDRY_TARGET = Y13_TARGET*.87
ROLES = dict(inference='sequential grouped Bayesian calibration; Phase 2 conditional on Phase 1 MAP',
             field='calibration evidence; not independent validation',
             biomass='digitized approximate calibration evidence; not independent validation',
             yield_role='calibration/model-data agreement',
             rs='auxiliary remote-sensing temporal reference with source/treatment-label uncertainty',
             zero='zero-irrigation counterfactual under the locked/observed initial soil-water condition')

class AuditError(RuntimeError):
    pass

class CandidateInvalid(ValueError):
    """Only expected candidate failures become -inf; input/API errors propagate."""

def require(ok, message):
    if not ok:
        raise AuditError(message)

def read_csv(path, columns):
    require(path.is_file(), f'MISSING_INPUT: {path}')
    d=pd.read_csv(path, encoding='utf-8-sig')
    require(set(columns)<=set(d.columns), f'{path}: missing columns {set(columns)-set(d.columns)}')
    return d

def finite(a, label):
    require(np.isfinite(np.asarray(a, dtype=float)).all(), f'NaN/Inf: {label}')

def unique_dates(d, column='Date'):
    d[column]=pd.to_datetime(d[column], errors='raise').dt.normalize()
    require(not d[column].isna().any() and not d[column].duplicated().any(), f'Missing/duplicate {column}')
    return d.sort_values(column).reset_index(drop=True)

def save_csv(d, path):
    """Atomic replacement: completed evidence survives interrupted postprocessing."""
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    d.to_csv(tmp,index=False,encoding='utf-8-sig')
    os.replace(tmp,path)

def save_json(d,path):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2,default=str,allow_nan=False),encoding='utf-8')
    os.replace(tmp,path)

def load_inputs():
    raw=read_csv(WEATHER_FILE,[])
    date='Date' if 'Date' in raw else 'date'
    mapping=dict(Tmin_C='MinTemp',Tmax_C='MaxTemp',Precip_mm='Precipitation',ETo_mm='ReferenceET')
    w=raw.rename(columns={**mapping,date:'Date'})
    require(set(['Date','MinTemp','MaxTemp','Precipitation','ReferenceET'])<=set(w), 'Weather schema')
    # AquaCrop 3.1.0 converts weather to a positional NumPy array: Date must be last.
    w=unique_dates(w[['MinTemp','MaxTemp','Precipitation','ReferenceET','Date']].copy())
    for c in ['MinTemp','MaxTemp','Precipitation','ReferenceET']: w[c]=pd.to_numeric(w[c],errors='raise')
    if YEAR==2022:
        e=unique_dates(read_csv(ETO_FILE,['Date','ETo_B_mm']))
        w['ReferenceET']=w.Date.map(e.set_index('Date').ETo_B_mm)
    else:
        w=read_audited_eto_b(w)
    finite(w[['MinTemp','MaxTemp','Precipitation','ReferenceET']], 'weather')
    require((w.MinTemp<=w.MaxTemp).all() and (w.Precipitation>=0).all() and (w.ReferenceET>=0).all(), 'Weather physical QC')
    expected=pd.date_range(f'{YEAR}-01-01', f'{YEAR}-12-31')
    require(pd.DatetimeIndex(w.Date).equals(expected), 'Weather dates incomplete or extraneous; no interpolation')
    f=read_csv(FIELD_CC_FILE,['Year','Date','LAI','Field_CC','Irrigation'])
    f=f[pd.to_numeric(f.Year,errors='raise')==YEAR].copy()
    require(len(f)>=5 and f.Irrigation.eq('DI').all(),'Field CC year/treatment mismatch')
    f=unique_dates(f)
    finite(f[['LAI','Field_CC']], 'Field CC')
    require(np.allclose(f.Field_CC,1.005*(1-np.exp(-.6*f.LAI))**1.2,atol=1e-10),'Field CC/LAI formula mismatch')
    require(f.Date.isin(DATES).all() and f.Field_CC.between(0,1).all(),'Field CC dates/range')
    f=f[['Date','Field_CC']].rename(columns={'Field_CC':'Observed_CC'})
    f['Weight']=np.where(f.Date>=pd.Timestamp(CFG['late_cc']),.5,1.)
    p=read_csv(INITIAL_WATER_FILE,['Year','Treatment','Planting_Date','Depth_top_m','Depth_bottom_m','Depth_mid_m','Initial_theta_m3m3'])
    p=p[(pd.to_numeric(p.Year,errors='raise')==YEAR)&p.Treatment.eq('DI')].copy().sort_values('Depth_top_m')
    require(len(p)>0 and pd.to_datetime(p.Planting_Date).eq(PLANT).all(),'Initial water year/planting mismatch')
    finite(p[['Depth_top_m','Depth_bottom_m','Depth_mid_m','Initial_theta_m3m3']], 'initial water')
    a=p.Depth_top_m.to_numpy(float); b=p.Depth_bottom_m.to_numpy(float)
    require(np.all(b>a) and np.isclose(a[0],0) and np.isclose(b[-1],2.4) and np.allclose(a[1:],b[:-1]),'Initial profile has gaps/overlap; needs exact 0–2.4m coverage')
    require(np.allclose(p.Depth_mid_m,(a+b)/2),'Initial profile midpoints mismatch')
    rs=read_csv(RS_CC_FILE,['CCquad'])
    rc='Date' if 'Date' in rs else 'date'
    rs=unique_dates(rs.rename(columns={rc:'Date'}))
    rs['RS_CC']=pd.to_numeric(rs.CCquad,errors='raise')/100
    finite(rs.RS_CC,'RS CC'); require(rs.RS_CC.between(0,1).all(),'RS CC range')
    rsmeta={k:'|'.join(map(str,rs[k].dropna().unique())) for k in ['Year','CropType','IrriMetho'] if k in rs}
    bio=pd.DataFrame(columns=['Date','Observed_B_t_ha','Sigma_assumed'])
    bio_error=''
    if BIOMASS_FILE.is_file():
        b=read_csv(BIOMASS_FILE,['Date','Observed_B_t_ha','Sigma_assumed'])
        if len(b):
            b=unique_dates(b)
            if YEAR!=2022:
                require({'Year','Treatment','Source'}<=set(b),'Biomass requires Year,Treatment,Source')
                require(b.Year.eq(YEAR).all() and b.Treatment.eq('DI').all() and b.Source.fillna('').str.strip().ne('').all(),'Biomass provenance/year/treatment')
            finite(b[['Observed_B_t_ha','Sigma_assumed']],'biomass')
            require(b.Date.isin(DATES).all() and (b.Observed_B_t_ha>=0).all() and (b.Sigma_assumed>0).all(),'Biomass dates/units/uncertainty')
            anchor=PLANT+pd.Timedelta(days=CFG['histart_cd'])
            require(len(b)>=3 and (b.Date<anchor).any() and (b.Date>=anchor).any(),'INSUFFICIENT_BIOMASS_CALIBRATION_DATA: >=3 dates spanning HIstart required')
            bio=b
    if bio.empty:
        bio_error=f'MISSING_BIOMASS_CALIBRATION_DATA: {YEAR}; {BIOMASS_FILE}; missing season-specific dates and aboveground dry biomass t/ha; thesis Fig 4-8'
    schedule=unique_dates(pd.DataFrame(CFG['irrigation'],columns=['Date','Depth']))
    finite(schedule.Depth,'irrigation')
    require(schedule.Date.isin(DATES).all() and (schedule.Depth>0).all(),'Irrigation date/depth')
    delta=float(schedule.Depth.sum()-IRR_PUBLISHED)
    require(abs(delta-(.01 if YEAR==2021 else 0))<1e-8,'Irrigation schedule differs from published annual contract')
    if YEAR==2022:
        t=read_csv(INITIAL_POINT_FILE,['Parameter','Value'])
        require(not t.Parameter.duplicated().any() and set(ALL_NAMES)<=set(t.Parameter),'Frozen center schema')
        center={k:float(t.set_index('Parameter').Value[k]) for k in ALL_NAMES}
        r=json.loads(READINESS_FILE.read_text(encoding='utf-8-sig'))
        require(r.get('READY') is True,'Frozen readiness is not READY=true')
    else:
        center=dict(CCx=.90,CGC_CD=.120,CDC_CD=.070,SenescenceCD=132.,WP=33.7,HI0=.45,Kcb=1.05)
        require(np.isclose(Crop('Maize',planting_date=PLANT.strftime('%m/%d')).Kcb,1.05),'Installed Maize Kcb default changed')
    finite(list(center.values()),'parameter center')
    require(all(PRIOR_BOUNDS[k][0]<=v<=PRIOR_BOUNDS[k][1] for k,v in center.items()),'Center outside prior')
    return dict(weather=w,field=f,profile=p,rs=rs,rsmeta=rsmeta,bio=bio,bio_error=bio_error,schedule=schedule,center=center)

SOIL_LAYERS=[(.10,29.70,10.64),(.10,30.81,10.52),(.20,19.43,12.32),(.20,13.22,16.20),(.20,10.38,14.75),(.20,11.81,11.66)]

def base_soil():
    s=Soil('custom',dz=[.1]*10)
    for thickness,sand,clay in SOIL_LAYERS:
        s.add_layer_from_texture(thickness=thickness,Sand=sand,Clay=clay,OrgMat=2.,penetrability=100)
    s.fill_nan()
    return s

def crop_for(v):
    c=Crop('Maize',planting_date=PLANT.strftime('%m/%d'),harvest_date=HARVEST.strftime('%m/%d'))
    for k in ['CCx','CGC_CD','CDC_CD','Kcb','HI0']: setattr(c,k,float(v[k]))
    c.SenescenceCD=int(round(v['SenescenceCD']))
    c.MaturityCD=CFG['maturity_cd']; c.HIstartCD=CFG['histart_cd']
    for k in ['CGC','CDC','Senescence','Maturity','HIstart']:
        if hasattr(c,k): setattr(c,k,getattr(c,k+'_CD' if k in ['CGC','CDC'] else k+'CD'))
    c.WP=20.
    c.PlantPop=79365.; c.CC0=c.SeedSize*c.PlantPop*1e-8
    return c

def field_management():
    return FieldMngt(mulches=True,mulch_pct=75.,f_mulch=0.,bunds=False,curve_number_adj=False,sr_inhb=False)

def irrigation(data,mode):
    if mode=='zero': return IrrigationManagement(irrigation_method=0)
    require(mode=='DI','Unknown irrigation mode')
    s=data['schedule']
    return IrrigationManagement(irrigation_method=3,Schedule=s.copy(),MaxIrr=float(s.Depth.max()+.1),MaxIrrSeason=float(s.Depth.sum()+.1),WetSurf=100.,AppEff=100.)

def make_model(data,v,soil,iw,mode):
    return AquaCropModel(sim_start_time=PLANT.strftime('%Y/%m/%d'),sim_end_time=f'{YEAR}/12/31',
        weather_df=data['weather'].copy(),soil=soil,crop=crop_for(v),initial_water_content=iw,
        irrigation_management=irrigation(data,mode),field_management=field_management())

def prepare_soil(data):
    template=base_soil(); src=template.profile.copy(deep=True)
    p=data['profile']
    if YEAR==2022:
        # Exact frozen legacy initialization; the engine's existing interpolation is
        # retained ONLY for 2022 structural reproduction, not to fill missing data.
        iw=InitialWaterContent(wc_type='Num',method='Depth',depth_layer=p.Depth_mid_m.tolist(),value=p.Initial_theta_m3m3.tolist())
        legacy=make_model(data,data['center'],template,iw,'DI'); legacy._initialize()
        old=legacy._param_struct.Soil.profile
        widths=old.dz.to_numpy(float); bottom=np.cumsum(widths); top=bottom-widths
        theta=np.asarray(legacy._init_cond.th,float)
    else:
        top=p.Depth_top_m.to_numpy(float); bottom=p.Depth_bottom_m.to_numpy(float)
        theta=p.Initial_theta_m3m3.to_numpy(float); widths=bottom-top
    newbot=np.round(np.arange(1,25)*.1,10); newtop=newbot-.1; mid=(newbot+newtop)/2
    overlap=np.maximum(0,np.minimum(newbot[:,None],bottom)-np.maximum(newtop[:,None],top))
    require(np.allclose(overlap.sum(axis=1),.1,atol=1e-10),'Initial water coverage incomplete')
    mapped=overlap@theta/.1
    require(np.isclose(np.sum(mapped*.1),np.sum(theta*widths),atol=1e-10,rtol=0),'Nonconservative water mapping')
    idx=np.minimum(np.searchsorted(np.cumsum(src.dz.to_numpy(float)),mid),len(src)-1)
    s=base_soil(); frame=src.iloc[idx].copy().reset_index(drop=True)
    for k,val in dict(Comp=np.arange(24),dz=np.full(24,.1),dzsum=newbot,zBot=newbot,z_top=newtop,zMid=mid).items(): frame[k]=val
    s.profile=frame; s.nComp=24; s.nLayer=int(frame.Layer.max()); s.zSoil=2.4; s.fill_nan()
    require(((mapped>=frame.th_dry.to_numpy()-1e-10)&(mapped<=frame.th_s.to_numpy()+1e-10)).all(),'Initial theta outside dry/saturation; no clipping')
    data['soil']=s; data['theta']=mapped; data['mid']=mid

def evap_wrapper(original):
    sig=inspect.signature(original)
    def call(*args,**kwargs):
        b=sig.bind(*args,**kwargs)
        require({'NewCond_CCadj','NewCond_CC'}<=set(b.arguments),'soil_evaporation API changed')
        b.arguments['NewCond_CCadj']=float(b.arguments['NewCond_CC'])
        return original(*b.args,**b.kwargs)
    return call

def effective_wp(full,target):
    lo,hi=0.,60.
    for _ in range(80):
        m=(lo+hi)/2; f=1+np.clip((40-m)/20,0,1)*(full-1)
        if m*f<target: lo=m
        else: hi=m
    wp=(lo+hi)/2; f=float(1+np.clip((40-wp)/20,0,1)*(full-1))
    require(np.isclose(wp*f,target,atol=1e-9),'WP inversion failed')
    return wp,f

def simulate(data,v,mode='DI'):
    theta=data['theta']; soil=copy.deepcopy(data['soil'])
    iw=InitialWaterContent(wc_type='Num',method='Depth',depth_layer=data['mid'].tolist(),value=theta.tolist())
    m=make_model(data,v,soil,iw,mode)
    mod=importlib.import_module('aquacrop.timestep.run_single_timestep')
    original=mod.soil_evaporation; mod.soil_evaporation=evap_wrapper(original)
    storage=[]; surface=[]
    try:
        m._initialize()
        require(len(m._init_cond.th)==24 and np.allclose(m._param_struct.Soil.Profile.dz,.1,atol=1e-12),'Corrected grid changed')
        require(np.allclose(m._init_cond.th,theta,atol=1e-10,rtol=0),'soil initialization mismatch')
        require(np.isclose(m._param_struct.Soil.zSoil,2.4),'Soil depth changed')
        sc=m._param_struct.Seasonal_Crop_List[0]; full=float(sc.fCO2)
        require(np.isclose(sc.PlantPop,79365.) and np.isclose(sc.CC0,sc.SeedSize*79365.*1e-8),'Field density/CC0 lost at runtime')
        if True: require(np.isclose(sc.WP,20.) and np.isclose(sc.WPy,100.),'Frozen WP state changed')
        storage.append(float(np.sum(m._init_cond.th)*100)); surface.append(float(m._init_cond.surface_storage))
        dry=soil.profile.th_dry.to_numpy(float); sat=soil.profile.th_s.to_numpy(float)
        n=0
        while not m._clock_struct.model_is_finished:
            date=pd.Timestamp(m._clock_struct.step_start_time)
            if n>=len(DATES) or date!=DATES[n]: raise CandidateInvalid('season dates incomplete: premature/late termination')
            if True:
                sc=m._param_struct.Seasonal_Crop_List[0]
                target=v['WP_early'] if date<SWITCH else v['WP_late']
                sc.WP,sc.fCO2=effective_wp(full,target)
            m.run_model(num_steps=1,initialize_model=False,process_outputs=False)
            th=np.asarray(m._init_cond.th,float); finite(th,'daily theta')
            require(np.all(th>=dry-1e-8) and np.all(th<=sat+1e-8),'soil water outside dry/saturation limits')
            storage.append(float(np.sum(th)*100)); surface.append(float(m._init_cond.surface_storage))
            if True:
                sc=m._param_struct.Seasonal_Crop_List[0]
                require(np.isclose(sc.WP*sc.fCO2,target,atol=1e-9),'Effective WP lost after daily step')
            n+=1
        if n!=len(DATES): raise CandidateInvalid(f'season dates incomplete: {n}/{len(DATES)}')
    finally:
        mod.soil_evaporation=original
    f=m._outputs.water_flux.iloc[:n].copy()
    required=['time_step_counter','Tr','Es','IrrDay','DeepPerc','Runoff','CR','GwIn']
    require(set(required)<=set(f),'Flux API changed; missing required components')
    finite(f[required],'daily flux')
    require(np.array_equal(f.time_step_counter.to_numpy(),np.arange(n)),'Flux date counter mismatch')
    f['Date']=DATES; f['ET']=f.Tr+f.Es
    # TileDrain absent in AquaCrop 3.1.0 with disabled tile drainage is a structural zero.
    if 'TileDrain' not in f: f['TileDrain']=0.
    finite(f.TileDrain,'TileDrain')
    rain=data['weather'].set_index('Date').loc[DATES,'Precipitation'].to_numpy(float)
    wb=rain+f.IrrDay.to_numpy()+f.CR.to_numpy()+f.GwIn.to_numpy()-f.Tr.to_numpy()-f.Es.to_numpy()-f.DeepPerc.to_numpy()-f.Runoff.to_numpy()-f.TileDrain.to_numpy()-np.diff(storage)-np.diff(surface)
    finite(wb,'daily water balance')
    require(np.max(np.abs(wb))<=1e-4 and abs(wb.sum())<=1e-4,'water balance residual >1e-4 mm')
    stats=m._outputs.final_stats
    require(len(stats)==1 and pd.Timestamp(stats.iloc[0]['Harvest Date (YYYY/MM/DD)'])==HARVEST,'Harvest boundary mismatch')
    y=float(stats.iloc[0]['Dry yield (tonne/ha)']); irr=float(stats.iloc[0]['Seasonal irrigation (mm)'])
    targetirr=float(data['schedule'].Depth.sum()) if mode=='DI' else 0.
    require(abs(irr-targetirr)<1e-7 and abs(f.IrrDay.sum()-targetirr)<1e-7,'DI/zero irrigation mismatch')
    expectedirr=data['schedule'].set_index('Date').Depth.reindex(DATES,fill_value=0).to_numpy() if mode=='DI' else np.zeros(n)
    require(np.allclose(f.IrrDay,expectedirr,atol=1e-7,rtol=0),'Daily irrigation differs from schedule')
    g=m._outputs.crop_growth.iloc[:n].copy()
    finite(g[['dap','canopy_cover','biomass','harvest_index_adj','DryYield']],'growth')
    require(np.array_equal(g.dap.to_numpy(),np.arange(1,n+1)),'Growth dates incomplete')
    g['Date']=DATES; g['Biomass_t_ha']=g.biomass/100
    cc=data['field'].merge(g[['Date','canopy_cover']],on='Date',how='left',validate='one_to_one')
    bio=data['bio'].merge(g[['Date','Biomass_t_ha']],on='Date',how='left',validate='one_to_one')
    finite(cc.canopy_cover,'CC match')
    if len(bio): finite(bio.Biomass_t_ha,'Biomass match')
    active=g[g.DryYield>0]; last=active.iloc[-1] if len(active) else g.iloc[-1]
    s=dict(Y_dry=y,Y_13pct=y/.87,Irrigation_mm=irr,Rain_mm=float(rain.sum()),
           Tr_mm=float(f.Tr.sum()),Es_mm=float(f.Es.sum()),ET_mm=float(f.ET.sum()),
           DeepPerc_mm=float(f.DeepPerc.sum()),Runoff_mm=float(f.Runoff.sum()),
           CR_mm=float(f.CR.sum()),GwIn_mm=float(f.GwIn.sum()),TileDrain_mm=float(f.TileDrain.sum()),
           Profile_initial_mm=storage[0],Profile_final_mm=storage[-1],Profile_depletion_mm=storage[0]-storage[-1],
           Surface_initial_mm=surface[0],Surface_final_mm=surface[-1],
           Water_balance_residual_mm=float(wb.sum()),Max_daily_balance_residual_mm=float(np.max(np.abs(wb))),
           MaxCC=float(g.canopy_cover.max()),HI_last=float(last.harvest_index_adj),B_last=float(last.Biomass_t_ha),
           CC_RMSE=float(np.sqrt(np.mean((cc.canopy_cover-cc.Observed_CC)**2))))
    finite(list(s.values()),'model summary')
    require(y>=0 and (f[['Tr','Es','ET']].to_numpy()>=-1e-10).all(),'Negative yield/flux')
    if len(bio):
        s['B_RMSE']=float(np.sqrt(np.mean((bio.Biomass_t_ha-bio.Observed_B_t_ha)**2)))
    return s,g,cc,bio

def compare_scenarios(di,zero):
    require(zero['Y_13pct']<=di['Y_13pct']+1e-8,'zero-irrigation yield > DI yield')
    loss=100*(di['Y_13pct']-zero['Y_13pct'])/di['Y_13pct'] if di['Y_13pct']>0 else 0.
    flags=list(ETO_AUDIT_REVIEW)
    if abs(100*(di['ET_mm']/ET_OBS-1))>15: flags.append('DI ET relative error >15%')
    if loss<25: flags.append('zero-irrigation yield loss <25%')
    if loss>90: flags.append('zero-irrigation yield loss >90%')
    budget=zero['Rain_mm']+zero['Profile_depletion_mm']+zero['Surface_initial_mm']-zero['Surface_final_mm']
    if zero['ET_mm']>budget+1e-4: flags.append('zero ET exceeds rainfall + soil/surface depletion; inspect other inflows')
    for mode,s in [('DI',di),('zero',zero)]:
        if not .4<=s['MaxCC']<=1: flags.append(f'{mode} MaxCC outside declared red-flag range [0.4,1]')
        if not .2<=s['HI_last']<=.65: flags.append(f'{mode} HI outside declared red-flag range [0.2,0.65]')
    return ('REVIEW' if flags else 'PASS'),flags,loss

def pre_run(data):
    print(f'\nPRE-RUN STRUCTURAL CHECK — {YEAR}',flush=True)
    results={}; errors=[]
    for mode in ['DI','zero']:
        try:
            s,*_=simulate(data,data.get('start',data['center']),mode); results[mode]=s
            print('\n'+('DI:' if mode=='DI' else 'ZERO IRRIGATION:'),flush=True)
            for k,v in s.items(): print(f'    {k}: {v:.10g}')
        except (AuditError,CandidateInvalid) as e:
            errors.append(f'{mode}: {e}'); print(f'{mode}: FAIL: {e}',flush=True)
    print(f'    Published yield: {Y13_PUBLISHED}; internal yield target: {Y13_TARGET}')
    print(f'    Published irrigation: {IRR_PUBLISHED}; schedule: {data["schedule"].Depth.sum():.2f}')
    print(f'    Tr target: {TR_TARGET}; Es target: {ES_TARGET}; Observed ET: {ET_OBS}')
    status='FAIL'; flags=errors; loss=None
    if not errors:
        try: status,flags,loss=compare_scenarios(results['DI'],results['zero'])
        except AuditError as e: flags=[str(e)]
    if 'DI' in results:
        print(f'    Yield relative error vs published: {100*(results["DI"]["Y_13pct"]/Y13_PUBLISHED-1):+.5f}%')
        print(f'    ET relative error: {100*(results["DI"]["ET_mm"]/ET_OBS-1):+.5f}%')
    if loss is not None:
        print(f'    Yield loss vs DI: {results["DI"]["Y_13pct"]-results["zero"]["Y_13pct"]:.6f} t/ha; {loss:.4f}%')
    if status!='FAIL' and data.get('start_boundary_flags'):
        flags += data['start_boundary_flags']; status='REVIEW'
    print('PRE_RUN_STATUS =',status,'; '.join(flags),flush=True)
    rows=[]
    for mode in ['DI','zero']:
        rows.append(dict(Year=YEAR,Scenario=mode,PRE_RUN_STATUS=status,Flags='; '.join(flags),
                         Phase2_data_status=data['bio_error'] or 'AVAILABLE',Yield_loss_pct=loss,
                         Published_yield=Y13_PUBLISHED,Internal_yield_target=Y13_TARGET,Published_ET=ET_OBS,
                         Tr_target=TR_TARGET,Es_target=ES_TARGET,Published_irrigation=IRR_PUBLISHED,
                         Schedule_irrigation=float(data['schedule'].Depth.sum()),**results.get(mode,{})))
    save_csv(pd.DataFrame(rows),OUTPUT_DIR/'pre_run_summary.csv')
    return status,flags

def frozen_regression(data):
    if YEAR!=2022: return
    s=simulate(data,data['center'],'DI')[0]
    expected=dict(Y_dry=(12.25617778072742,.002),Tr_mm=(525.4468722329179,.002),
                  Es_mm=(73.16250053907443,.002),B_last=(30.5249401326545,.002),CC_RMSE=(.0869466373051667,.0001))
    rows=[]
    for k,(v,tol) in expected.items():
        rows.append(dict(Check='frozen_center_'+k,Actual=s[k],Expected=v,Tolerance=tol,Passed=abs(s[k]-v)<=tol))
    t=read_csv(HISTORICAL_MAP_FILE,ALL_NAMES)
    require(len(t)==1,'Historical MAP must contain one parameter row')
    v={k:float(t.iloc[0][k]) for k in ALL_NAMES}
    di,g,cc,_=simulate(data,v,'DI'); zero=simulate(data,v,'zero')[0]
    r2=metrics(cc.Observed_CC,cc.canopy_cover)['R2']
    loss=100*(1-zero['Y_13pct']/di['Y_13pct'])
    for k,actual,target,tol in [('MAP_Y13',di['Y_13pct'],14.062076,.002),('MAP_Field_R2',r2,.940,.002),
                              ('MAP_Zero_Y13',zero['Y_13pct'],5.763,.005),('MAP_Zero_loss_pct',loss,59.,.1),
                              ('MAP_Zero_water_balance',zero['Water_balance_residual_mm'],0.,1e-4)]:
        rows.append(dict(Check=k,Actual=actual,Expected=target,Tolerance=tol,Passed=abs(actual-target)<=tol))
    tab=pd.DataFrame(rows); save_csv(tab,OUTPUT_DIR/'frozen_2022_reproduction.csv')
    print('\n2022 FROZEN CENTER + HISTORICAL GROUPED-MAP REPRODUCTION\n',tab.to_string(index=False),flush=True)
    require(tab.Passed.all(),'2022 frozen initial-point / historical grouped-MAP reproduction failed')

def logprob(vector,names,fixed,phase,data):
    v=dict(fixed); v.update(zip(names,map(float,vector)))
    prior=0.
    for k in names:
        x=v[k]; lo,hi=PRIOR_BOUNDS[k]
        if not np.isfinite(x) or not lo<=x<=hi: return -np.inf
        if k in NORMAL_PRIORS: prior-=.5*((x-data['center'][k])/PRIOR_SD[k])**2
    try: s,g,cc,bio=simulate(data,v,'DI')
    except CandidateInvalid: return -np.inf
    if phase=='canopy_transpiration':
        ll=-.5*np.sum(cc.Weight*((cc.canopy_cover-cc.Observed_CC)/SIGMA_CC)**2)
        ll-=.5*((s['Tr_mm']-TR_TARGET)/SIGMA_TR)**2+.5*((s['Es_mm']-ES_TARGET)/SIGMA_ES)**2
    else:
        require(len(bio)>0,data['bio_error'] or 'MISSING_BIOMASS_CALIBRATION_DATA')
        ll=-.5*np.sum(((bio.Biomass_t_ha-bio.Observed_B_t_ha)/bio.Sigma_assumed)**2)-.5*((s['Y_dry']-YDRY_TARGET)/SIGMA_Y)**2
    return float(ll+prior)

def signature(data,names,fixed,phase):
    files=[PHASE1_START_POINT_FILE,WEATHER_FILE,FIELD_CC_FILE,INITIAL_WATER_FILE,RS_CC_FILE,BIOMASS_FILE,ETO_FILE,ETO_CONTROL_FILE,FROZEN_2022_ETO_FILE]
    if YEAR==2022: files += [ETO_FILE,INITIAL_POINT_FILE,READINESS_FILE,HISTORICAL_MAP_FILE]
    return dict(Year=YEAR,phase=phase,names=names,fixed=fixed,center=data['center'],CFG=CFG,
                priors=PRIOR_BOUNDS,normal_priors=sorted(NORMAL_PRIORS),prior_sd=PRIOR_SD,
                sigmas=[SIGMA_CC,SIGMA_TR,SIGMA_ES,SIGMA_Y],targets=[TR_TARGET,ES_TARGET,YDRY_TARGET],
                files={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                source=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                versions={k:importlib.metadata.version(k) for k in ['aquacrop','emcee','h5py','numpy','pandas']})

def run_phase(data,phase,names,fixed,total_steps):
    import emcee
    import h5py
    path=OUTPUT_DIR/f'_resume_{phase}.h5'
    contract=signature(data,names,fixed,phase)
    encoded=json.dumps(contract,sort_keys=True,default=str)
    backend=emcee.backends.HDFBackend(str(path))
    if path.exists():
        with h5py.File(path,'r') as h:
            require(h.attrs.get('scientific_contract','')==encoded,'Checkpoint scientific contract changed; use a new output directory. Never reuse mismatched chain.')
        require(backend.shape==(NWALKERS,len(names)),'Backend shape mismatch')
    else:
        backend.reset(NWALKERS,len(names))
        with h5py.File(path,'a') as h: h.attrs['scientific_contract']=encoded
    def lp(x): return logprob(x,names,fixed,phase,data)
    start=None
    if backend.iteration==0:
        rng=np.random.default_rng(RANDOM_SEED+YEAR+(100003 if phase=='biomass_yield' else 0))
        start=[]
        for walker in range(NWALKERS):
            for attempt in range(3000):
                pos=np.array([fixed[k] for k in names])+rng.normal(size=len(names))*.25*np.array([PRIOR_SD[k] for k in names])
                if np.isfinite(lp(pos)): start.append(pos); break
            else: raise AuditError(f'Cannot initialize walker {walker}')
        start=np.asarray(start)
    sampler=emcee.EnsembleSampler(NWALKERS,len(names),lp,backend=backend)
    if backend.iteration==0:
        sampler.random_state=np.random.RandomState(RANDOM_SEED+YEAR+(100003 if phase=='biomass_yield' else 0)).get_state()
    else:
        # Explicitly restore the HDF stored RNG and positions, including after an interrupted run.
        start=backend.get_last_sample()
    remaining=max(0,total_steps-backend.iteration)
    if remaining: sampler.run_mcmc(start,remaining,progress=True)
    return export_phase(backend,phase,names,fixed)

def export_phase(backend,phase,names,fixed):
    """Separated so evidence preservation/failure paths can be tested without sampling."""
    chain=backend.get_chain(); logp=backend.get_log_prob()
    n,nw,nd=chain.shape
    full=pd.DataFrame(chain.reshape(-1,nd),columns=names)
    full.insert(0,'walker',np.tile(np.arange(nw),n)); full.insert(0,'step',np.repeat(np.arange(n),nw))
    full['log_probability']=logp.reshape(-1)
    save_csv(full,OUTPUT_DIR/f'mcmc_full_chain_{phase}.csv')
    last=pd.DataFrame(chain[-1],columns=names); last.insert(0,'walker',np.arange(nw)); last['log_probability']=logp[-1]
    save_csv(last,OUTPUT_DIR/f'last_walker_positions_{phase}.csv')
    # Raw chain + last positions are safe before tau, summary, MAP or figures.
    acceptance=backend.accepted/float(n)
    try:
        tau=np.asarray(backend.get_autocorr_time(tol=0),float)
    except Exception as e:
        save_csv(full.iloc[:0],OUTPUT_DIR/f'mcmc_posterior_after_burnin_{phase}.csv')
        raise AuditError(f'chain length insufficient under paper specification: tau unavailable in {phase}; {e}. Full chain and HDF retained; extend original backend.') from e
    valid=np.isfinite(tau).all() and (tau>0).all()
    burn=int(np.ceil(5*tau.max())) if valid else n
    save_csv(pd.DataFrame(dict(Parameter=names,Tau=tau,Phase=phase,Steps=n,Burn_in=burn)),OUTPUT_DIR/f'_diagnostic_{phase}.csv')
    if not valid or burn>=n:
        # There is no scientifically defined retained posterior under this rule.
        save_csv(full.iloc[:0],OUTPUT_DIR/f'mcmc_posterior_after_burnin_{phase}.csv')
        raise AuditError(f'chain length insufficient under paper specification: {phase}; steps={n}, tau={tau}, burn-in={burn}. HDF retained; extend with --steps N --formal.')
    post=full[full.step>=burn].copy()
    save_csv(post,OUTPUT_DIR/f'mcmc_posterior_after_burnin_{phase}.csv')
    best=post.loc[post.log_probability.idxmax(),names]
    values=dict(fixed); values.update({k:float(best[k]) for k in names})
    summary=[]
    for j,k in enumerate(names):
        a=post[k].to_numpy(); lo,hi=PRIOR_BOUNDS[k]; edge=.01*(hi-lo)
        q=np.percentile(a,[2.5,25,50,75,97.5])
        summary.append(dict(Phase=phase,Parameter=k,Mean=a.mean(),Median=q[2],SD=a.std(ddof=1),
            P2_5=q[0],P25=q[1],P75=q[3],P97_5=q[4],MAP=values[k],Tau=tau[j],Burn_in=burn,
            ESS=(n-burn)*nw/tau[j],Prior_low=lo,Prior_high=hi,
            MAP_near_boundary_1pct=min(values[k]-lo,hi-values[k])<=edge,
            P2_5_near_lower_1pct=q[0]<=lo+edge,P97_5_near_upper_1pct=q[4]>=hi-edge,
            Mass_lower_1pct=float(np.mean(a<=lo+edge)),Mass_upper_1pct=float(np.mean(a>=hi-edge))))
    return dict(phase=phase,names=names,chain=chain,post=post,values=values,summary=pd.DataFrame(summary),burn=burn,acceptance=acceptance)

def metrics(obs,sim):
    from scipy.stats import pearsonr,spearmanr
    a=np.asarray(obs,float); b=np.asarray(sim,float); finite(a,'metric obs'); finite(b,'metric sim')
    require(len(a)>=3 and np.std(a)>0,'Insufficient/constant metric observations')
    return dict(N=len(a),RMSE=float(np.sqrt(np.mean((a-b)**2))),R2=float(1-np.sum((a-b)**2)/np.sum((a-a.mean())**2)),
                Pearson_r=float(pearsonr(a,b).statistic) if np.std(b)>0 else np.nan,
                Spearman_rho=float(spearmanr(a,b).statistic) if np.std(b)>0 else np.nan)

def postprocess(data,p1,p2):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    best=p2['values']; s,g,cc,bio=simulate(data,best,'DI'); z=simulate(data,best,'zero')[0]
    status,flags,loss=compare_scenarios(s,z)
    fm=metrics(cc.Observed_CC,cc.canopy_cover)
    rs=data['rs']; rs=rs[(rs.Date>=PLANT)&(rs.Date<HARVEST)].merge(g[['Date','canopy_cover']],on='Date',how='left',validate='one_to_one')
    finite(rs.canopy_cover,'RS exact-date match')
    rm=metrics(rs.RS_CC,rs.canopy_cover)
    lag=int((rs.loc[rs.canopy_cover.idxmax(),'Date']-rs.loc[rs.RS_CC.idxmax(),'Date']).days)
    rm.update(Peak_lag_days=lag,Timing_consistent_within_16days=abs(lag)<=16,Role=ROLES['rs'],Source_metadata=json.dumps(data['rsmeta']))
    save_csv(cc,OUTPUT_DIR/'MAP_CC_comparison.csv'); save_csv(bio,OUTPUT_DIR/'MAP_biomass_comparison.csv')
    save_csv(pd.DataFrame([{**fm,'Role':ROLES['field']}]),OUTPUT_DIR/'CC_Field_performance_metrics.csv')
    save_csv(pd.DataFrame([rm]),OUTPUT_DIR/'CC_RS_temporal_metrics.csv')
    save_csv(pd.DataFrame([{**z,'Yield_loss_pct':loss,'Role':ROLES['zero']}]),OUTPUT_DIR/'zero_irrigation_summary.csv')
    save_csv(pd.DataFrame([{**s,'Published_yield':Y13_PUBLISHED,'Internal_target':Y13_TARGET,
        'Yield_error_pct':100*(s['Y_13pct']/Y13_PUBLISHED-1),'ET_observed':ET_OBS,
        'ET_error_pct':100*(s['ET_mm']/ET_OBS-1),'Tr_target':TR_TARGET,'Es_target':ES_TARGET,
        'Published_irrigation':IRR_PUBLISHED,'Schedule_minus_published_mm':float(data['schedule'].Depth.sum()-IRR_PUBLISHED),
        'Field_R2':fm['R2'],'Zero_Y13':z['Y_13pct'],'Zero_loss_pct':loss,'Process_status':status,
        'Process_flags':'; '.join(flags),'Inference':ROLES['inference']}]),OUTPUT_DIR/'MAP_validation_summary.csv')
    summary=pd.concat([p1['summary'],p2['summary']],ignore_index=True)
    save_csv(summary,OUTPUT_DIR/'posterior_parameter_summary.csv'); save_csv(summary,OUTPUT_DIR/'parameter_estimates.csv')
    save_csv(summary[['Phase','Parameter','Tau','Burn_in','ESS']],OUTPUT_DIR/'autocorrelation_time_summary.csv')
    save_csv(pd.concat([pd.DataFrame(dict(Phase=p['phase'],Walker=np.arange(NWALKERS),Acceptance_fraction=p['acceptance'])) for p in [p1,p2]]),OUTPUT_DIR/'acceptance_diagnostic.csv')
    def figsave(name):
        plt.tight_layout(); plt.savefig(OUTPUT_DIR/name,dpi=250,bbox_inches='tight'); plt.close()
    for field in [True,False]:
        plt.figure(figsize=(9,5)); plt.plot(g.Date,g.canopy_cover,label='AquaCrop MAP')
        if field: plt.scatter(cc.Date,cc.Observed_CC,label='Field CC (calibration)')
        plt.scatter(rs.Date,rs.RS_CC,marker='x',label='RS auxiliary'); plt.xlim(PLANT,HARVEST); plt.ylim(0,1)
        plt.ylabel('Canopy cover'); plt.legend()
        label=f"RS temporal r={rm['Pearson_r']:.3f}, rho={rm['Spearman_rho']:.3f}"
        if field: label=f"Field R2={fm['R2']:.3f}, RMSE={fm['RMSE']:.3f}, r={fm['Pearson_r']:.3f}\n"+label
        plt.title(label); figsave('MAP_CC_validation.png' if field else 'MAP_CC_RS_temporal_validation.png')
    plt.figure(figsize=(8,5)); plt.plot(g.Date,g.Biomass_t_ha,label='MAP')
    plt.errorbar(bio.Date,bio.Observed_B_t_ha,yerr=bio.Sigma_assumed,fmt='o',label='Digitized approximate biomass calibration')
    plt.ylabel('Aboveground dry biomass (t/ha)'); plt.legend(); figsave('MAP_biomass_calibration.png')
    for name,labels,vals in [('MAP_yield_observed_vs_simulated.png',['Published','Internal target','Grouped MAP'],[Y13_PUBLISHED,Y13_TARGET,s['Y_13pct']]),
                             ('Yield_DI_vs_ZeroIrrigation.png',['DI','Zero irrigation'],[s['Y_13pct'],z['Y_13pct']])]:
        plt.figure(figsize=(7,5)); plt.bar(labels,vals); plt.ylabel('Yield at 13% moisture (t/ha)'); figsave(name)
    for p in [p1,p2]:
        for j,k in enumerate(p['names']):
            plt.figure(figsize=(9,4)); plt.plot(p['chain'][:,:,j],alpha=.25); plt.axvline(p['burn'],color='k',ls='--'); plt.ylabel(k); plt.xlabel('Step'); figsave(f'trace_{k}.png')
            plt.figure(figsize=(6,4)); plt.hist(p['post'][k],bins=40); plt.xlabel(k); figsave(f'posterior_{k}.png')
        corr=p['post'][p['names']].corr()
        save_csv(corr.rename_axis('Parameter').reset_index(),OUTPUT_DIR/f'posterior_correlation_{p["phase"]}.csv')
    metadata={**ROLES,'YEAR':YEAR,'walkers':NWALKERS,'phase1_steps':len(p1['chain']),'phase2_steps':len(p2['chain']),
        'biomass_source':str(BIOMASS_FILE),'initial_water_source':str(INITIAL_WATER_FILE),'RS_metadata':json.dumps(data['rsmeta']),
        'soil_grid':'24 x 0.1m','mulch_pct':75,'f_mulch':0,'WP_structure':'two-stage effective' if YEAR==2022 else 'single annual WP',
        'phenology_caveat':'HIstartCD provisional anchor','Es_sigma_assumed_mm':SIGMA_ES,'Tr_sigma_assumed_mm':SIGMA_TR,
        'initial_water_caveat':'0–1m approximate figure reconstruction; deep ERA5-Land retained',
        'post_MAP_process_status':status,'post_MAP_process_flags':'; '.join(flags),'checkpoint_policy':'HDF retained for extension and reproducibility'}
    save_csv(pd.DataFrame(metadata.items(),columns=['Setting','Value']),OUTPUT_DIR/'run_metadata.csv')
    for p in [p1,p2]:
        diagnostic=OUTPUT_DIR/f'_diagnostic_{p["phase"]}.csv'
        if diagnostic.exists(): diagnostic.unlink()  # Superseded by combined successful diagnostics.
    # HDF deliberately retained even on success; all requested outputs already safe.
    print(f'Completed {YEAR}; MAP process status={status}; {flags}',flush=True)

def main(argv=None):
    parser=argparse.ArgumentParser(description=ROLES['inference'])
    parser.add_argument('--formal',action='store_true',help='Explicit opt-in; default only PRE-RUN')
    parser.add_argument('--steps',type=int,default=NSTEPS,help='Total steps per phase, including existing HDF iterations')
    parser.add_argument('--output',type=Path,default=None,help='Override result directory without editing scientific configuration')
    args=parser.parse_args(argv)
    global OUTPUT_DIR
    if args.output is not None: OUTPUT_DIR=args.output.resolve()
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
    require(args.steps>=NSTEPS,'Formal specification requires >=2000 steps per phase')
    data=load_inputs(); load_phase1_start(data); prepare_soil(data)
    print(f'DATA AVAILABILITY AUDIT {YEAR}: Field={len(data["field"])}, biomass={len(data["bio"])}, Phase2={data["bio_error"] or "AVAILABLE"}',flush=True)
    status,flags=pre_run(data)
    if status=='FAIL': raise AuditError('PRE_RUN_STATUS = FAIL; '+ '; '.join(flags))
    frozen_regression(data)
    if data['bio_error']:
        print(data['bio_error'],flush=True)
        if args.formal: raise AuditError(data['bio_error'])
    if not args.formal:
        print('PRE-RUN only completed. No MCMC performed.',flush=True); return
    require(not data['bio_error'],data['bio_error'])
    raise AuditError('APPROXIMATE_BIOMASS_REVIEW_REQUIRED: inspect phase2 diagnostic, bounds and uncertainty sensitivity before formal MCMC')
    if status=='REVIEW' and STOP_BEFORE_FORMAL_MCMC_ON_REVIEW:
        raise AuditError('STOP_BEFORE_FORMAL_MCMC_ON_REVIEW=True; manual review required before changing this switch')
    try: import emcee, h5py
    except ImportError as e: raise AuditError('Formal sampling requires emcee and h5py; no checkpoint fallback allowed') from e
    p1=run_phase(data,'canopy_transpiration',PHASE1_NAMES,dict(data.get('start',data['center'])),args.steps)
    save_csv(pd.DataFrame([p1['values']]),OUTPUT_DIR/'phase1_MAP_point.csv')
    simulate(data,p1['values'],'DI')  # Fresh full MAP run before phase 2
    p2=run_phase(data,'biomass_yield',PHASE2_NAMES,p1['values'],args.steps)
    save_csv(pd.DataFrame([p2['values']]),OUTPUT_DIR/'grouped_MAP_point.csv')
    postprocess(data,p1,p2)

def read_audited_eto_b(weather):
    """Read annual ERA5-Land B export; independently recompute ETo, never fit a scale."""
    required=['Date','Tmin_C','Tmax_C','Tmean_C','Tdew_C','Pressure_kPa','Precip_mm',
              'Rn_ERA5_MJ','Wind2m_A_ms','Wind2m_B_ms','ETo_A_raw','ETo_B_raw','ETo_A_mm','ETo_B_mm',
              'Hourly_image_count','Hourly_valid_count','Hourly_vs_daily_vector_ms','Day_basis',
              'Wind_method','Latitude','Longitude','Daily_source','Hourly_source']
    require(ETO_FILE.is_file(),f'MISSING_AUDITED_ETO_B: {YEAR}; {ETO_FILE}. Run Export_DI_2019_2022_ETo_B_GEE.js; do not scale old ETo or copy 2022 weather.')
    e=unique_dates(read_csv(ETO_FILE,required))
    require(pd.DatetimeIndex(e.Date).equals(pd.DatetimeIndex(weather.Date)),'Audited ETo year/date coverage mismatch')
    numeric=[c for c in required if c not in ['Date','Day_basis','Wind_method','Daily_source','Hourly_source']]
    for c in numeric: e[c]=pd.to_numeric(e[c],errors='raise')
    finite(e[numeric],'audited ETo source')
    require(e.Day_basis.eq('UTC').all() and e.Wind_method.eq('ERA5LAND_UTC_SCALAR_WIND_B_v1').all(),'ETo day basis/method mismatch')
    require(e.Daily_source.eq('ECMWF/ERA5_LAND/DAILY_AGGR').all() and e.Hourly_source.eq('ECMWF/ERA5_LAND/HOURLY').all(),'ETo source dataset mismatch')
    require(e.Hourly_image_count.eq(24).all() and e.Hourly_valid_count.eq(24).all(),'Hourly wind incomplete; no daily interpolation allowed')
    require(np.allclose(e.Longitude,102.87597633340303,atol=1e-9,rtol=0) and np.allclose(e.Latitude,37.82250517046916,atol=1e-9,rtol=0),'ETo geometry differs from frozen 2022 extraction')
    require((e.Wind2m_A_ms>=0).all() and (e.Wind2m_B_ms>=e.Wind2m_A_ms-1e-7).all(),'Wind scalar/vector consistency failed')
    require(e.Hourly_vs_daily_vector_ms.abs().max()<1e-6,'Hourly/daily wind-vector mismatch')
    require((e.Pressure_kPa>0).all() and (e.Tmin_C<=e.Tmax_C).all(),'ETo pressure/temperature QC')
    for ec,wc in [('Tmin_C','MinTemp'),('Tmax_C','MaxTemp'),('Precip_mm','Precipitation')]:
        require(np.allclose(e[ec],weather[wc],atol=1e-6,rtol=0),f'Original weather vs audited ETo source mismatch: {ec}; stop instead of overwriting temperatures/rainfall')
    def esat(t): return .6108*np.exp(17.27*t/(t+237.3))
    delta=4098*esat(e.Tmean_C)/(e.Tmean_C+237.3)**2
    gamma=.000665*e.Pressure_kPa
    vpd=np.maximum(0,(esat(e.Tmax_C)+esat(e.Tmin_C))/2-esat(e.Tdew_C))
    for tag in ['A','B']:
        wind=e[f'Wind2m_{tag}_ms']
        reconstructed=(.408*delta*e.Rn_ERA5_MJ+gamma*900/(e.Tmean_C+273)*wind*vpd)/(delta+gamma*(1+.34*wind))
        require(np.allclose(reconstructed,e[f'ETo_{tag}_raw'],atol=1e-7,rtol=0),f'ETo {tag} equation reconstruction failed')
        require(np.allclose(np.maximum(reconstructed,0),e[f'ETo_{tag}_mm'],atol=1e-7,rtol=0),f'ETo {tag} clipping convention mismatch')
    # Rebuild 2022 with the SAME export script; this isolates source/geometry drift.
    require(ETO_CONTROL_FILE.is_file(),f'MISSING_2022_ETO_CONTROL: {ETO_CONTROL_FILE}; export the 2022 control too')
    ctrl=unique_dates(read_csv(ETO_CONTROL_FILE,['Date','ETo_B_mm','Tmin_C','Tmax_C','Precip_mm','Hourly_valid_count','Hourly_image_count']))
    frozen=unique_dates(read_csv(FROZEN_2022_ETO_FILE,['Date','ETo_B_mm','Tmin_C','Tmax_C','Precip_mm']))
    require(pd.DatetimeIndex(ctrl.Date).equals(pd.DatetimeIndex(frozen.Date)),'2022 ETo control date mismatch')
    finite(ctrl[['ETo_B_mm','Tmin_C','Tmax_C','Precip_mm','Hourly_valid_count','Hourly_image_count']],'2022 control')
    require(ctrl.Hourly_valid_count.eq(24).all() and ctrl.Hourly_image_count.eq(24).all(),'2022 control hourly coverage')
    for c in ['ETo_B_mm','Tmin_C','Tmax_C','Precip_mm']:
        require(np.allclose(ctrl[c],frozen[c],atol=1e-6,rtol=0),f'2022 ETo control cannot reproduce frozen {c}; inspect source/geometry, do not relax tolerance silently')
    season=weather.Date.isin(DATES)
    old=float(weather.loc[season,'ReferenceET'].sum()); a=float(e.loc[season,'ETo_A_mm'].sum()); b=float(e.loc[season,'ETo_B_mm'].sum())
    source_delta=100*(a/old-1) if old>0 else float('inf')
    global ETO_AUDIT_REVIEW
    ETO_AUDIT_REVIEW=[]
    # Declared attribution check, not a calibrated correction factor.
    if abs(source_delta)>2:
        ETO_AUDIT_REVIEW.append('ETo A differs from legacy seasonal ETo by >2%; source attribution needs review')
    audit=dict(Year=YEAR,Old_ETo_mm=old,A_ETo_mm=a,B_ETo_mm=b,A_vs_old_pct=source_delta,
               B_minus_A_mm=b-a,Method='hourly scalar-wind correction only',Control2022='PASS',
               Source_review='; '.join(ETO_AUDIT_REVIEW))
    save_csv(pd.DataFrame([audit]),OUTPUT_DIR/'ETo_source_audit.csv')
    print('ETO SOURCE AUDIT:',audit,flush=True)
    result=weather.copy(); result['ReferenceET']=e.ETo_B_mm.to_numpy(float)
    return result



def load_phase1_start(data):
    tab=read_csv(PHASE1_START_POINT_FILE,PHASE1_NAMES)
    require(len(tab)==1,'Phase-1 deterministic start must have one row')
    values=dict(data['center'])
    for k in PHASE1_NAMES:
        v=float(tab.iloc[0][k]); lo,hi=PRIOR_BOUNDS[k]
        require(np.isfinite(v) and lo<=v<=hi,'Phase-1 start outside bounds: '+k)
        values[k]=v
    data['start']=values
    data['start_boundary_flags']=[k+' deterministic start within 1% of prior boundary'
        for k in PHASE1_NAMES if min(values[k]-PRIOR_BOUNDS[k][0],PRIOR_BOUNDS[k][1]-values[k])
        <=.01*(PRIOR_BOUNDS[k][1]-PRIOR_BOUNDS[k][0])]
    print('Using deterministic Phase-1 starting point, NOT a posterior/prior center:',values,flush=True)

if __name__=='__main__':
    raise SystemExit('Use DI_YYYY_MCMC.py in the package root; this is a model engine, not a sampling entry point.')

'''

def _embedded_module(name,filename=None):
    module_name='_di_2021_'+name
    module=types.ModuleType(module_name)
    module.__file__=str(filename or Path(__file__).resolve())
    module.__dict__['_embedded_module']=_embedded_module
    sys.modules[module_name]=module
    source=_SOURCES[name]
    virtual_name=str(filename or (PACKAGE_DIR/('_embedded_'+name+'.py')))
    linecache.cache[virtual_name]=(len(source),None,source.splitlines(keepends=True),virtual_name)
    exec(compile(source,virtual_name,'exec'),module.__dict__)
    return module

def main():
    if not DATA_DIR.is_dir():
        raise SystemExit('Missing data/ folder. Extract the complete annual ZIP first.')
    for name in ['sampler','diagnostics','audit_hooks','ensemble_pipeline']:
        _embedded_module(name)
    _embedded_module('runner').main('2021',default_output=OUTPUT_DIR)


# ================= ONE-CLICK START =================
DEFAULT_STEPS = 2000

def one_click_arguments(arguments):
    """No arguments => preflight + formal sampling. Hard checks stay enabled."""
    args=list(arguments)
    if '--preflight-only' in args:
        args.remove('--preflight-only')
        if '--sample' in args or '--smoke' in args:
            raise SystemExit('--preflight-only cannot be combined with sampling modes')
        return args
    if '--help' in args or '-h' in args:
        return args
    if '--smoke' not in args and '--sample' not in args:
        args.append('--sample')
    if '--accept-limitations' not in args:
        args.append('--accept-limitations')
    if not any(x=='--steps' or x.startswith('--steps=') for x in args):
        args.extend(['--steps',str(DEFAULT_STEPS)])
    return args

def run_one_click():
    incoming=sys.argv[1:]
    effective=one_click_arguments(incoming)
    if '--sample' in effective:
        print('一键模式：先预审，通过硬检查后自动开始正式 MCMC。',flush=True)
        print('已接受账本中声明的 REVIEW 限制；缺数据、复现失败等硬错误仍会停止。',flush=True)
        print('每阶段4组独立 ensemble，每组32 walkers，默认每组2000步。',flush=True)
        print('初始化期间可能暂时没有步数输出，请不要重复启动。',flush=True)
        print('阶段1诊断不通过时，会保存检查点并停止，不会强行进入阶段2。',flush=True)
    sys.argv=[sys.argv[0],*effective]
    main()

if __name__=='__main__':
    run_one_click()
