"""2022 conditional phase 2. Run in PyCharm; original phase 1 stays read-only.
Requires the original DI_2022_OneClick directory and its Python environment.
No claim of joint posterior or completed phase-1 convergence.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import sys
from types import SimpleNamespace
import numpy as np
from emcee.autocorr import integrated_time

PROJECT = Path(r'C:/Users/Lenovo/PycharmProjects/PythonProject/DI_2022_OneClick')
STEPS = 2000                 # Total, not additional steps; increase to resume.
WALKERS = 32                # ONE ensemble, not four ensembles.
SEED = 42
sys.dont_write_bytecode = True

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def canonical(x):
    return json.loads(json.dumps(x,sort_keys=True))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project',type=Path,default=PROJECT)
    ap.add_argument('--output',type=Path)
    ap.add_argument('--steps',type=int,default=STEPS)
    ap.add_argument('--preflight-only',action='store_true')
    ap.add_argument('--smoke',action='store_true',help='2 steps; separate test output, never inference')
    args=ap.parse_args()
    root=args.project.resolve();source=root/'DI_2022_MCMC_ONE_CLICK.py'
    src=root/'MCMC_Article_Results_2022/DI_2022/sampling'
    out=(args.output or Path(__file__).resolve().parent/('phase2_smoke' if args.smoke else 'phase2_conditional_results')).resolve()
    if out==src or src in out.parents:
        raise RuntimeError('Output must be outside original sampling directory')
    if args.steps<2: raise ValueError('steps must be >=2')
    out.mkdir(parents=True,exist_ok=True)
    lock=out/'.run.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
    write=None
    try:
        spec=importlib.util.spec_from_file_location('phase2_original',source)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        modules={k:mod._embedded_module(k) for k in ['sampler','diagnostics','audit_hooks','ensemble_pipeline']}
        runner=mod._embedded_module('runner');write=modules['sampler'].atomic_json
        m,data,start,folder=runner.load('2022',out)
        old_diag=json.loads((src/'canopy_transpiration_diagnostics.json').read_text())
        paths=[src/'checkpoints/canopy_transpiration'/f'ensemble_{i}.npz' for i in range(1,5)]
        hashes={str(p):digest(p) for p in paths}
        chains=[];contracts=[];logs=[]
        for p in paths:
            with np.load(p,allow_pickle=False) as z:
                chains.append(z['history']);logs.append(z['logs']);contracts.append(json.loads(str(z['contract'].item())))
        raw=np.stack(chains);lp=np.stack(logs)
        if raw.ndim!=4 or raw.shape[0]!=4 or raw.shape[2:]!=(32,5) or not np.isfinite(raw).all() or not np.isfinite(lp).all():
            raise RuntimeError('Invalid phase-1 checkpoint shape or nonfinite data')
        for e,c in enumerate(contracts):
            settings=SimpleNamespace(seed=c['seed'],walkers=c['walkers'],smoke=False)
            expected=runner.contract('2022',m,data,m.PHASE1_NAMES,start,'canopy_transpiration',settings)
            if canonical(dict(expected,ensemble=e))!=c:
                raise RuntimeError('Phase-1 scientific contract differs from current code/data/environment')
        tau=np.array([integrated_time(a,tol=0) for a in raw])
        if not np.isfinite(tau).all() or (tau<=0).any(): raise RuntimeError('Invalid phase-1 tau')
        burn=int(np.ceil(5*tau.max()))
        if raw.shape[1]-burn<100: raise RuntimeError('Insufficient retained phase-1 steps')
        if burn!=old_diag['Burn_in']: raise RuntimeError('Phase-1 burn-in reproduction failed')
        runner.compare_initial(m.simulate(data,start,'DI')[0],json.loads((folder/'expected_initial.json').read_text()))
        fixed=dict(start,**dict(zip(m.PHASE1_NAMES,map(float,raw[:,burn:].mean((0,1,2))))))
        initial=m.simulate(data,fixed,'DI')[0]
        runner.compare_initial(m.simulate(data,fixed,'DI')[0],initial)
        names=m.PHASE2_NAMES
        if not np.isfinite(m.logprob([fixed[k] for k in names],names,fixed,'biomass_yield',data)):
            raise RuntimeError('Nonfinite phase-2 initial posterior')
        cn=runner.contract('2022',m,data,names,fixed,'biomass_yield',SimpleNamespace(seed=SEED,walkers=WALKERS,smoke=args.smoke))
        cn.update(ensembles=1,phase1_checkpoint_sha256=hashes,phase1_burn=burn,
                  wrapper_sha256=digest(Path(__file__)),handoff='retained phase-1 arithmetic mean')
        handoff=dict(contract=cn,values=fixed,initial_metrics=initial,Phase1_converged=bool(old_diag['Converged']),
                     Original_phase1_diagnostics=old_diag,Joint_posterior=False,
                     Scope='Conditional on estimated phase-1 mean; phase-1 uncertainty not propagated; not independent validation')
        hp=out/'phase1_mean_handoff.json'
        if hp.exists() and json.loads(hp.read_text(encoding='utf-8'))!=canonical(handoff):
            raise RuntimeError('Frozen handoff changed; use a new output directory')
        write(hp,handoff)
        print('PREFLIGHT PASSED. Phase 1 converged:',old_diag['Converged'],flush=True)
        print('Conditional phase 2: ONE ensemble x 32 walkers x',2 if args.smoke else args.steps,'steps',flush=True)
        print('Output:',out,flush=True)
        if args.preflight_only:
            write(out/'run_status.json',dict(State='PREFLIGHT_ONLY',Sampling_started=False));return
        write(out/'run_status.json',dict(State='RUNNING_PHASE2',Phase1_converged=old_diag['Converged'],Joint_posterior=False))
        chain,logp,accept=modules['sampler'].run_ensemble(
            lambda v:m.logprob(v,names,fixed,'biomass_yield',data),
            [fixed[k] for k in names],[m.PRIOR_BOUNDS[k][0] for k in names],
            [m.PRIOR_BOUNDS[k][1] for k in names],2 if args.smoke else args.steps,WALKERS,
            SEED+2022*100+100000,out/'checkpoints/biomass_yield/ensemble_1.npz',cn,25)
        status=dict(State='SMOKE_COMPLETE' if args.smoke else 'SAMPLING_COMPLETE_REVIEW_REQUIRED',
                    Sampling_complete=True,Inference_validated=False,Phase1_converged=old_diag['Converged'],
                    Joint_posterior=False,Independent_validation=False,Zero_irrigation_validated=False,
                    Rhat=None,Rhat_note='Only one phase-2 ensemble; coupled walkers are not independent chains',
                    Acceptance_by_walker=accept.mean(0).tolist())
        if not args.smoke:
            t=integrated_time(chain,tol=0)
            valid=bool(np.isfinite(t).all() and (t>0).all())
            b=int(np.ceil(5*t.max())) if valid else len(chain)
            status.update(Tau=[float(v) if np.isfinite(v) else None for v in t],Burn_in=b,
                          Tau_trusted_50tau=bool(valid and len(chain)>=50*t.max()))
            if b<len(chain):
                post=chain[b:].reshape(-1,len(names)); means=post.mean(0)
                point=dict(fixed,**dict(zip(names,map(float,means))))
                summary={k:dict(Mean=float(means[j]),SD=float(post[:,j].std(ddof=1)),
                                  Quantiles_025_50_975=np.quantile(post[:,j],[.025,.5,.975]).tolist()) for j,k in enumerate(names)}
                di=m.simulate(data,point,'DI')[0];zero=m.simulate(data,point,'zero')[0]
                write(out/'conditional_parameter_summary.json',summary)
                write(out/'conditional_mean_model.json',dict(values=point,DI=di,Zero=zero,
                      Zero_loss_pct=100*(1-zero['Y_13pct']/di['Y_13pct']),
                      Note='Model at conditional sample mean, not posterior predictive mean; zero scenario unvalidated'))
                import matplotlib
                matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                fig,axes=plt.subplots(3,2,figsize=(11,8))
                for j,k in enumerate(names):
                    axes[j,0].plot(chain[:,:,j],alpha=.15);axes[j,0].axvline(b,color='k',ls='--');axes[j,0].set_ylabel(k)
                    axes[j,1].hist(post[:,j],bins=50,density=True)
                fig.suptitle('Conditional phase 2 - convergence not certified');fig.tight_layout()
                fig.savefig(out/'conditional_phase2_diagnostics.png',dpi=150);plt.close(fig)
            else: status['State']='NO_RETAINED_SAMPLES_EXTEND_REQUIRED'
        if any(digest(p)!=hashes[str(p)] for p in paths): raise RuntimeError('Phase-1 checkpoints changed during run')
        write(out/'run_status.json',status)
        print(status['State'],'; results are conditional, not a joint posterior.',flush=True)
    except BaseException as exc:
        if write: write(out/'run_status.json',dict(State='INTERRUPTED' if isinstance(exc,KeyboardInterrupt) else 'FAILED',Error=str(exc)))
        raise
    finally:
        lock.unlink(missing_ok=True)

if __name__=='__main__':
    main()
