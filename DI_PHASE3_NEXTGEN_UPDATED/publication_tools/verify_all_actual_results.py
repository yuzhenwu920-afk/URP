"""Verify complete archived numeric evidence; does not rerun crop simulations."""
from pathlib import Path
import argparse
import json
import sys
import numpy as np
import pandas as pd
from read_complete_results import load_columns

YEARS=[2019,2020,2021,2022]
OBS={2019:16.55,2020:17.29,2021:15.86,2022:14.08}
CAP={2019:445.27,2020:559.76,2021:633.47,2022:404.84}
OUTPUTS=['Y_13pct','B_t_ha','Tr_mm','Es_mm','ET_mm','MaxCC']


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def tolerance(v):return 64*np.finfo(float).eps*max(1.,abs(v))


def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--out',type=Path);args=p.parse_args()
    root=args.root;status=read(root/'EXPERIMENT_STATUS.json')
    if status['status']!='COMPLETE':raise RuntimeError('Experiment status is not COMPLETE')
    engine=status['engine'];checks=[];evaluations=0;generations=0;population_rows=0;sobol_rows=0
    max_residual=0.
    for year in YEARS:
        for seed in [101,202,303]:
            folder=root/'sobol_global_N512'/f'{year}_seed{seed}'
            meta=read(folder/'run.json')
            assert meta['status']=='COMPLETE' and meta['identity']['model']==engine
            df=load_columns(folder/'all_response_columns.npz')
            assert len(df)==5120 and df.row_id.tolist()==list(range(5120))
            x=np.load(folder/'design.npy',allow_pickle=False);y=np.load(folder/'response_matrix.npy',allow_pickle=False)
            assert x.shape==(5120,8) and y.shape==(5120,6)
            np.testing.assert_array_equal(df[OUTPUTS].to_numpy(),y,strict=True)
            old=root/'sobol_global_N128'/f'{year}_seed{seed}'
            np.testing.assert_array_equal(np.load(old/'design.npy',allow_pickle=False),x[:1280],strict=True)
            np.testing.assert_array_equal(np.load(old/'response_matrix.npy',allow_pickle=False),y[:1280],strict=True)
            assert abs(df.Water_balance_residual_mm).max()<1e-5
            assert df.Max_daily_balance_residual_mm.max()<1e-5
            max_residual=max(max_residual,float(abs(df.Water_balance_residual_mm).max()))
            sobol_rows+=len(df)
            checks.append({'unit':f'Sobol {year} seed{seed}','rows':len(df),'status':'PASS'})
        for algorithm in ['NSGA3','NSGA2']:
            for seed in [31,73,109,151,199]:
                folder=root/'optimization'/str(year)/f'{algorithm}_seed{seed}'
                meta=read(folder/'run.json')
                assert meta['status']=='COMPLETE' and meta['identity']['engine']==engine
                df=load_columns(folder/'all_evaluations_columns.npz')
                assert len(df)==meta['evaluations']==10000
                names=meta['identity']['space']['names'];controls=df[names].to_numpy()
                assert np.all(controls>=0) and np.all(controls.sum(axis=1)<=CAP[year]+tolerance(CAP[year]))
                assert np.all(df.Irrigation_mm>=0) and np.all(df.Y_13pct>=0)
                assert np.max(abs(df.Y_dry-.87*df.Y_13pct))<1e-10
                assert np.max(abs(df.ET_mm-df.Tr_mm-df.Es_mm))<1e-10
                balance=(df.Irrigation_mm+df.Rain_mm+df.CR_mm+df.GwIn_mm-df.ET_mm-df.Runoff_mm-df.DeepPerc_mm-df.TileDrain_mm
                    -df.Profile_final_mm+df.Profile_initial_mm-df.Surface_final_mm+df.Surface_initial_mm)
                assert max(abs(balance).max(),abs(df.Water_balance_residual_mm).max(),df.Max_daily_balance_residual_mm.max())<1e-5
                max_residual=max(max_residual,float(abs(df.Water_balance_residual_mm).max()))
                table={x.tobytes():i for i,x in enumerate(controls)}
                h=pd.read_csv(folder/'history.csv',float_precision='round_trip')
                assert h.Generation.tolist()==list(range(1,101))
                with np.load(folder/'all_generations.npz',allow_pickle=False) as z:
                    assert z['X'].shape==(100,100,4) and z['F'].shape==(100,100,2)
                    assert z['G'].shape==(100,100,2) and z['CV'].shape==(100,100)
                    assert z['Generation'].tolist()==list(range(1,101))
                    for generation in range(100):
                        x,f,g,cv=(z[k][generation] for k in ['X','F','G','CV'])
                        indexes=[table[v.tobytes()] for v in x]
                        source=df.iloc[indexes]
                        expected_f=np.column_stack([-source.Y_13pct,source.Irrigation_mm])
                        expected_g=source[['G_irrigation','G_yield']].to_numpy()
                        np.testing.assert_array_equal(f,expected_f,strict=True)
                        np.testing.assert_array_equal(g,expected_g,strict=True)
                        np.testing.assert_allclose(cv,np.maximum(g,0).sum(axis=1),rtol=0,atol=1e-14)
                    population_rows+=10000
                front=pd.read_csv(folder/'pareto_front.csv',float_precision='round_trip')
                assert len(front)>0
                assert np.all(front.Y13>=.95*OBS[year]-tolerance(.95*OBS[year]))
                assert np.all(front.Irrigation_mm<=CAP[year]+tolerance(CAP[year]))
                evaluations+=len(df);generations+=len(h)
                checks.append({'unit':f'{algorithm} {year} seed{seed}','rows':len(df),'generations':len(h),'status':'PASS'})
        raw=pd.read_csv(root/'optimization'/str(year)/'conditional_perturbation_responses.csv',float_precision='round_trip')
        summary=pd.read_csv(root/'optimization'/str(year)/'conditional_validation.csv',float_precision='round_trip')
        assert len(raw)==3*2*128 and len(summary)==6
        for r in summary.itertuples():
            group=raw[(raw.Candidate_ID==r.Candidate_ID)&(raw.Group==r.Group)]
            assert len(group)==128
            assert abs(group.Y_13pct.mean()-r.Mean_Y13)<1e-10
            assert abs(group.Y_13pct.quantile(.05)-r.Q05_Y13)<1e-10
            assert abs((group.Y_13pct>=.95*OBS[year]).mean()-r.Probability_above_absolute_gate)<1e-12
        checks.append({'unit':f'Conditional validation {year}','rows':len(raw),'status':'PASS'})
    assert evaluations==400000 and sobol_rows==61440 and generations==4000 and population_rows==400000
    report={'status':'PASS','engine':engine,'actual_crop_simulations_rerun_by_this_audit':False,
        'sobol_final_design_rows':sobol_rows,'optimization_new_evaluations':evaluations,'generations':generations,
        'all_stored_population_individuals_checked_against_actual_evaluations':population_rows,
        'conditional_response_rows':4*3*2*128,'max_abs_season_water_residual_mm':max_residual,
        'numeric_lossless_repack':'float64 bits and all original generation arrays verified during packing',
        'MCMC_strict_convergence_limitations_retained':True,'checks':checks}
    path=args.out or root/'ALL_RESULTS_VERIFICATION.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
