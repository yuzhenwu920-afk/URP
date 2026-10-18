"""Audit the supplied 2022 model package without substituting missing inputs.

Recomputes metrics and plots from supplied paired outputs, not a new crop run.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import shutil
import traceback
import zipfile

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, dates as mdates


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def metrics(observed, simulated):
    observed, simulated = np.asarray(observed, float), np.asarray(simulated, float)
    assert len(observed) >= 3 and np.isfinite([observed, simulated]).all()
    residual = simulated - observed
    return dict(N=len(observed), R2=float(1 - np.sum(residual**2)/np.sum((observed-observed.mean())**2)),
                Pearson_r2=float(np.corrcoef(observed, simulated)[0, 1]**2),
                RMSE=float(np.sqrt(np.mean(residual**2))), MAE=float(np.mean(abs(residual))),
                Bias=float(residual.mean()))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--package', type=Path, required=True)
    ap.add_argument('--known-inputs', type=Path, required=True)
    ap.add_argument('--frozen-samples', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    package, out = args.package.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = package/'01_frozen_model'
    restored = out/'restored_model_2022'
    shutil.copytree(source, restored, dirs_exist_ok=True)
    manifest = json.loads((source/'manifest.json').read_text())
    # This preserves the provided manifest; missing originals are not manufactured.
    known = {}
    for p in args.known_inputs.rglob('*'):
        if p.is_file():
            known.setdefault(sha(p), p)
    inventory = []
    for name, expected in manifest.items():
        original, dest = source/name, restored/name
        status = 'provided' if original.is_file() else 'missing'
        recovery = ''
        if not dest.is_file() and expected in known:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(known[expected], dest)
            status, recovery = 'recovered_exact_sha256', known[expected].name
        elif not original.is_file() and dest.is_file():
            status = 'recovered_exact_sha256'
            recovery = known[expected].name if expected in known else 'previous exact restoration'
        actual = sha(dest) if dest.is_file() else None
        if actual is not None:
            assert actual == expected, name
        inventory.append(dict(file=name, status=status, expected_sha256=expected,
                              actual_sha256=actual, recovered_from=recovery))
    pd.DataFrame(inventory).to_csv(out/'model_input_inventory.csv', index=False, encoding='utf-8-sig')
    missing = [r['file'] for r in inventory if r['status']=='missing']
    recovered = sum(r['status']=='recovered_exact_sha256' for r in inventory)
    assert recovered == 4 and len(missing) == 8
    package_manifest = json.loads((package/'08_provenance/MANIFEST_SHA256.json').read_text(encoding='utf-8-sig'))
    for record in package_manifest:
        p = package/record['relative_path']
        assert p.is_file() and p.stat().st_size == record['bytes'] and sha(p) == record['sha256']
    # Both stages are compared with the already frozen retained samples.
    p2 = package/'03_phase2_complete/DI_2022_Phase2/phase2_conditional_results/checkpoints/biomass_yield/ensemble_1.npz'
    with np.load(p2, allow_pickle=False) as z:
        contract = json.loads(str(z['contract'].item()))
        p2rows = z['history'][163:].reshape(-1, 3).copy()
    assert sha(source/'DI_2022_MCMC_ONE_CLICK.py') == contract['files']['DI_2022_MCMC_ONE_CLICK.py']
    with zipfile.ZipFile(package/'02_phase1_results/MCMC_Article_Results_2022.zip') as z:
        rows = []
        for i in range(1, 5):
            name=f'MCMC_Article_Results_2022/DI_2022/sampling/checkpoints/canopy_transpiration/ensemble_{i}.npz'
            data=z.read(name)
            expected = next(v for k,v in contract['phase1_checkpoint_sha256'].items() if k.endswith(f'ensemble_{i}.npz'))
            assert hashlib.sha256(data).hexdigest()==expected
            with np.load(io.BytesIO(data), allow_pickle=False) as checkpoint:
                rows.append(checkpoint['history'][317:].reshape(-1,5).copy())
        p1rows=np.concatenate(rows)
    with np.load(args.frozen_samples, allow_pickle=False) as frozen:
        np.testing.assert_array_equal(frozen['p1_2022'], p1rows)
        np.testing.assert_array_equal(frozen['p2_2022'], p2rows)
    # Existing paired model outputs can be audited even while runtime inputs are absent.
    supplied=package/'04_phase2_review/final_results_20261010'
    pairs=out/'supplied_pairs';pairs.mkdir(exist_ok=True)
    for name in ['CC_pairs.csv','Biomass_pairs.csv','Daily_growth.csv','Flux_comparison.csv','Yield_comparison.csv','summary.json']:
        shutil.copyfile(supplied/name,pairs/name)
    cc=pd.read_csv(pairs/'CC_pairs.csv',parse_dates=['Date'],float_precision='round_trip')
    bio=pd.read_csv(pairs/'Biomass_pairs.csv',parse_dates=['Date'],float_precision='round_trip')
    growth=pd.read_csv(pairs/'Daily_growth.csv',parse_dates=['Date'],float_precision='round_trip')
    assert len(growth)==148 and growth.Date.min()==pd.Timestamp('2022-04-17') and growth.Date.max()==pd.Timestamp('2022-09-11')
    assert growth.Date.is_unique and np.array_equal(growth.dap,np.arange(1,149))
    result=dict(CC=metrics(cc.CC_observed,cc.CC_simulated),Biomass=metrics(bio.B_observed_t_ha,bio.B_simulated_t_ha))
    old=json.loads((pairs/'summary.json').read_text(encoding='utf-8-sig'))
    for kind in ['CC','Biomass']:
        assert np.isclose(result[kind]['R2'],old[kind]['R_Square'],rtol=0,atol=1e-12)
        assert np.isclose(result[kind]['RMSE'],old[kind]['RMSE'],rtol=0,atol=1e-12)
    np.testing.assert_allclose(cc.CC_simulated,growth.set_index('Date').loc[cc.Date,'canopy_cover'],rtol=0,atol=1e-12)
    np.testing.assert_allclose(bio.B_simulated_t_ha,growth.set_index('Date').loc[bio.Date,'Biomass_t_ha'],rtol=0,atol=1e-12)
    result.update(Year=2022,scope='Recomputed from supplied paired outputs; no new crop simulation',
                  annual_yield_pairs=1,annual_yield_R2=None)
    write(out/'paired_metrics_2022.json',result)
    pd.DataFrame([dict(Variable=k,**result[k]) for k in ['CC','Biomass']]).to_csv(out/'paired_metrics_2022.csv',index=False,encoding='utf-8-sig')
    font=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    if font.is_file():
        font_manager.fontManager.addfont(str(font));plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
    plt.rcParams.update({'axes.spines.top':False,'axes.spines.right':False,'axes.unicode_minus':False,
                        'axes.labelsize':11,'font.size':10,'pdf.fonttype':42})
    figures=out/'figures';figures.mkdir(exist_ok=True)
    fig,axes=plt.subplots(2,2,figsize=(11.6,7.5))
    for j,(kind,frame,obs,sim,gcol,label,color) in enumerate([
        ('CC',cc,'CC_observed','CC_simulated','canopy_cover','冠层覆盖度', '#207a94'),
        ('Biomass',bio,'B_observed_t_ha','B_simulated_t_ha','Biomass_t_ha','地上干生物量（t/ha）','#bf713b')]):
        ax=axes[0,j];ax.plot(growth.Date,growth[gcol],color=color,lw=2.2,label='已提供模型日序列')
        ax.scatter(frame.Date,frame[obs],color=color,s=37,edgecolor='white',lw=.7,zorder=4,label='校准观测')
        ax.set(ylabel=label,title=f'{"ab"[j]}  2022 年生长过程');ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.grid(alpha=.18);ax.legend(frameon=False,fontsize=9)
        ax=axes[1,j];lo=min(frame[obs].min(),frame[sim].min());hi=max(frame[obs].max(),frame[sim].max());gap=(hi-lo)*.08
        ax.plot([lo-gap,hi+gap],[lo-gap,hi+gap],color='#828b96',ls='--',lw=1.2,label='1:1')
        ax.scatter(frame[obs],frame[sim],s=45,color=color,edgecolor='white',lw=.8)
        ax.set(xlim=(lo-gap,hi+gap),ylim=(lo-gap,hi+gap),xlabel='校准观测',ylabel='已提供模型输出',title=f'{"cd"[j]}  配对一致性')
        m=result[kind];ax.text(.04,.94,f"n = {m['N']}\nR² = {m['R2']:.4f}\nRMSE = {m['RMSE']:.4f}",transform=ax.transAxes,va='top',bbox=dict(boxstyle='round,pad=.45',fc='#f3f6f8',ec='none'))
        ax.grid(alpha=.18)
    fig.suptitle('2022 年冠层与生物量：新增配对表复核',fontsize=16,y=.995)
    fig.text(.5,.005,'根据上传的既有模型输出重算；样本内校准评价，非本次模型重跑或独立验证。',ha='center',color='#5e6876',fontsize=10)
    fig.tight_layout(rect=(0,.04,1,.96))
    for ext in ['png','pdf']:fig.savefig(figures/f'F16_2022_paired_calibration.{ext}',dpi=300,bbox_inches='tight')
    plt.close(fig)
    # Import the actual embedded model, then exercise its input loader.
    state={'status':'NOT_RUN','models_simulated':0,'MCMC_rerun':False}
    try:
        spec=importlib.util.spec_from_file_location('urp_2022_restored',restored/'DI_2022_MCMC_ONE_CLICK.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        model=module._embedded_module('model',restored/'data/model.py')
        state['model_source_imported']=True
        model.load_inputs()
        state['status']='INPUTS_LOADED_ONLY'
    except Exception as exc:
        state.update(status='BLOCKED_MISSING_ORIGINAL_INPUTS' if 'MISSING_INPUT' in str(exc) else 'UNEXPECTED_ERROR',
                     error_type=type(exc).__name__,error=str(exc))
        (out/'model_input_loader.log').write_text(traceback.format_exc(),encoding='utf-8')
    assert state['status']=='BLOCKED_MISSING_ORIGINAL_INPUTS',state
    write(out/'MODEL_EXECUTION_STATUS.json',state)
    report=dict(date='2026-10-18',package_manifest_entries_verified=len(package_manifest),
                original_2022_model_source_present=True,source_matches_phase2_contract=True,
                missing_original_data_files=missing,exact_input_files_recovered=recovered,
                phase1_rows_equal_frozen=215424,phase2_rows_equal_frozen=58784,
                CC_pairs=12,Biomass_pairs=10,supplied_daily_rows=148,
                runtime=state,new_real_model_Sobol_executed=False,new_real_model_NSGAIII_executed=False,
                other_annual_original_models_in_this_upload=False,
                package_ready_flag_is_not_runtime_validation=True)
    write(out/'SOURCE_PACKAGE_AUDIT.json',report)
    versions={name:importlib.metadata.version(name) for name in ['aquacrop','numpy','pandas','scipy','matplotlib','emcee','SALib','pymoo']}
    write(out/'ANALYSIS_ENVIRONMENT.json',versions)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
