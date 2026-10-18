"""Software/analytic validation only. Synthetic simulator is never a crop result."""
import copy
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from SALib.sample import sobol
from SALib.test_functions import Ishigami

from model_adapter import (HERE,NAMES,load_study,validate_output,validate_space,management,
                           check_management_response,sha,read)
import phaseB_sobol as B
import phaseC_nsga3 as C
from validate_candidates import conditional_groups,validate_year


class SyntheticFixture:
    """Monotone analytic Y=8+0.03I plus declared parameter perturbations."""
    identity='SYNTHETIC_SOFTWARE_TEST_ONLY'
    def __init__(self,study):self.study=study;self.calls=0
    def management_space(self,year):
        return {'kind':'stage_amounts','names':['Stage1_mm','Stage2_mm','Stage3_mm','Stage4_mm'],
                'lower':[0]*4,'upper':[150]*4,'dates':[f'{year}-{m:02d}-01' for m in range(6,10)],
                'allowed_windows':[[f'{year}-{m:02d}-01',f'{year}-{m:02d}-28'] for m in range(6,10)]}
    def simulate(self,params,year,management=None):
        self.calls+=1;spec=self.management_space(year)
        if management is None:i=self.study['baseline_irrigation_mm'][str(year)];amounts=[i/4]*4
        else:amounts=list(management['values'].values());i=sum(amounts)
        center=self.study['_centers'][year]
        y=8+.03*i+.1*(params['WP_early']-center['WP_early'])+.02*(params['Kcb']-center['Kcb'])
        tr=200+.05*i+10*params['Kcb'];es=50+2*params['CDC_CD'];et=tr+es
        raw=dict(Y_13pct=y,Y_dry=.87*y,B_t_ha=.87*y/.45,Tr_mm=tr,Es_mm=es,ET_mm=et,MaxCC=params['CCx'],
                 Irrigation_mm=i,Rain_mm=150.,CR_mm=0.,GwIn_mm=0.,Runoff_mm=0.,DeepPerc_mm=0.,TileDrain_mm=0.,
                 Profile_initial_mm=500.,Profile_final_mm=500+i+150-et,Surface_initial_mm=0.,Surface_final_mm=0.,
                 Water_balance_residual_mm=0.,Max_daily_balance_residual_mm=0.,
                 irrigation_events=[{'date':d,'mm':float(mm),'stage':j} for j,(d,mm) in enumerate(zip(spec['dates'],amounts))])
        return validate_output(raw)


class RevisedWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.study=load_study();self.model=SyntheticFixture(self.study)
        self.original_samples_hash=sha(HERE/self.study['phase_samples'])
        for year in self.study['years']:
            b=self.model.simulate(self.study['_centers'][year],year)
            self.study['baseline_reference'][str(year)]={k:b[k] for k in ['Y_13pct','Tr_mm','Es_mm','ET_mm']}
            self.study['baseline_reference'][str(year)].update(atol=1e-8,evidence='SYNTHETIC_TEST_ONLY')
    def tearDown(self):
        self.assertEqual(self.original_samples_hash,sha(HERE/self.study['phase_samples']))
        self.temp.cleanup()

    def test_formal_defaults_follow_guidance(self):
        s=load_study()
        self.assertEqual(s['sobol']['N'],128);self.assertEqual(len(s['sobol']['seeds']),3)
        self.assertFalse(s['sobol']['calc_second_order'])
        self.assertEqual(s['optimization']['generations'],100)
        self.assertEqual(s['optimization']['population'],100)
        self.assertEqual(len(s['optimization']['seeds']),5)
        for year in s['years']:self.assertEqual(B.make_problem(s,year)['bounds'],B.make_problem(s,2019)['bounds'])

    def test_ishigami_known_sobol_indices(self):
        p={'num_vars':3,'names':['x1','x2','x3'],'bounds':[[-math.pi,math.pi]]*3}
        x=sobol.sample(p,4096,calc_second_order=False,seed=281)
        rows=B.estimates(p,Ishigami.evaluate(x),903)
        np.testing.assert_allclose([r['S1'] for r in rows],[.313905,.442411,0],atol=.03)
        np.testing.assert_allclose([r['ST'] for r in rows],[.557589,.442411,.243684],atol=.03)

    def test_design_response_resume_and_parameter_mismatch(self):
        folder=self.root/'sobol'
        result=B.run_track(self.model,self.study,2019,16,101,'global',folder)
        self.assertEqual(len(result),8*6)
        self.assertEqual(np.load(folder/'design.npy').shape,(160,8))
        self.assertEqual(np.load(folder/'response_matrix.npy').shape,(160,6))
        calls=self.model.calls;B.run_track(self.model,self.study,2019,16,101,'global',folder)
        self.assertEqual(self.model.calls,calls)
        journal=folder/'responses.jsonl';lines=journal.read_text().splitlines();first=json.loads(lines[0])
        first['params'][0]+=.001;lines[0]=json.dumps(first);journal.write_text('\n'.join(lines)+'\n')
        with self.assertRaisesRegex(ValueError,'checksum changed'):B.run_track(self.model,self.study,2019,16,101,'global',folder)

    def test_constant_and_incomplete_sobol_responses(self):
        p=B.make_problem(self.study,2019)
        rows=B.estimates(p,np.ones(80),101)
        self.assertTrue(all(r['ST'] is None for r in rows))
        self.assertTrue(all(r['Status']=='constant_output_indices_undefined' for r in rows))
        with self.assertRaises(ValueError):B.estimates(p,np.ones(79),101)
        with self.assertRaises(ValueError):B.estimates(p,np.r_[np.ones(79),np.nan],101)

    def test_failed_model_point_is_recorded_not_imputed(self):
        class FailingModel:
            identity='FAILURE_TEST_ONLY'
            def simulate(self,*args,**kwargs):raise RuntimeError('intentional model failure for software test')
        folder=self.root/'failed_sobol'
        with self.assertRaisesRegex(RuntimeError,'intentional model failure'):
            B.run_track(FailingModel(),self.study,2019,16,101,'global',folder)
        self.assertEqual(read(folder/'run.json')['status'],'FAILED')
        self.assertFalse((folder/'indices.csv').exists())
        self.assertFalse((folder/'response_matrix.npy').exists())

    def test_rank_gate_requires_all_scrambles_and_narrow_intervals(self):
        rows=[]
        for seed in self.study['sobol']['seeds']:
            for j,name in enumerate(NAMES):rows.append(dict(Year=2019,Output='Y_13pct',Seed=seed,
                      Parameter=name,Status='estimated',ST=(8-j)/10,ST_conf=.05))
        df=pd.DataFrame(rows)
        self.assertTrue(B.rank_checks(df,self.study).Stable_for_screening.all())
        self.assertFalse(B.rank_checks(df[df.Seed==101],self.study).Stable_for_screening.any())
        df.loc[0,'ST_conf']=.5
        self.assertFalse(B.rank_checks(df,self.study).Stable_for_screening.any())

    def test_physical_and_unit_failures_are_not_ignored(self):
        raw=self.model.simulate(self.study['_centers'][2019],2019)
        self.assertAlmostEqual(raw['IWP_kg_m3'],100*raw['Y_13pct']/raw['Irrigation_mm'])
        for key,value in [('Y_dry',raw['Y_13pct']),('Profile_final_mm',500),('ET_mm',999),('MaxCC',94),('Tr_mm',float('nan'))]:
            r=dict(raw);r[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_output(r)

    def test_smt_definition_and_stage_dates_required(self):
        spec={'kind':'SMT','names':['SMT1','SMT2','SMT3','SMT4'],'lower':[0]*4,'upper':[100]*4,
              'allowed_windows':[['2019-06-01','2019-09-01']]*4}
        with self.assertRaises(ValueError):validate_space(spec)
        spec['definition']='synthetic definition for a software test only';validate_space(spec)
        bad=self.model.management_space(2019);bad['dates'][0]='2019-05-01'
        with self.assertRaises(ValueError):validate_space(bad)

    def test_actual_event_sum_and_dates_are_checked(self):
        spec=self.model.management_space(2019);x=np.array([60.,70.,80.,90.])
        raw=self.model.simulate(self.study['_centers'][2019],2019,management(spec,x))
        check_management_response(raw,spec,x)
        bad=copy.deepcopy(raw);bad['irrigation_events'][0]['date']='2019-05-01'
        with self.assertRaises(ValueError):check_management_response(bad,spec,x)
        bad=copy.deepcopy(raw);bad['irrigation_events'][0]['mm']+=1
        with self.assertRaises(ValueError):check_management_response(bad,spec,x)

    def test_two_objectives_and_absolute_observed_gate(self):
        problem=C.DeterministicIrrigationProblem(self.model,self.study,2019,self.model.management_space(2019))
        out={};problem._evaluate(np.array([[100]*4,[0]*4,[150]*4]),out)
        self.assertEqual(out['F'].shape,(3,2));self.assertEqual(out['G'].shape,(3,2))
        self.assertTrue(np.all(out['G'][0]<=0));self.assertGreater(out['G'][1,1],0)
        self.assertGreater(out['G'][2,0],0)
        self.assertEqual(problem.gate,.95*16.55)

    def test_no_feasible_solution_has_no_high_yield_fallback(self):
        d=pd.DataFrame({'Y13':[14.,15.,20.],'Irrigation_mm':[100.,200.,700.]})
        self.assertTrue(C.epsilon_choices(d,16.55,445.27).empty)
        problem=C.DeterministicIrrigationProblem(self.model,self.study,2019,self.model.management_space(2019))
        problem.gate=1000.
        d,_=C.run_seed(problem,'NSGA3',31,3,12,self.root/'infeasible')
        self.assertTrue(d.empty)
        self.assertEqual(read(self.root/'infeasible/run.json')['status'],'NO_FEASIBLE_SOLUTION')

    def test_2022_cap_roundoff_is_not_a_physical_constraint_violation(self):
        cap=404.84;provided=404.84000000000003
        d=pd.DataFrame({'Y13':[14.07778281807083,14.07778281807083],
                        'Irrigation_mm':[provided,cap+.0001]})
        selected=C.epsilon_choices(d,14.08,cap)
        self.assertEqual(len(selected),1)
        self.assertEqual(selected.Irrigation_mm.iloc[0],provided)
        base_model=self.model
        class RoundoffFixture:
            identity='SYNTHETIC_ROUNDOFF_TEST_ONLY'
            def simulate(self,*args,**kwargs):
                r=base_model.simulate(*args,**kwargs)
                r['Irrigation_mm']=float(np.nextafter(cap,np.inf));return r
        problem=C.DeterministicIrrigationProblem(RoundoffFixture(),self.study,2022,self.model.management_space(2022))
        out={};problem._evaluate(np.array([[cap/4]*4]),out)
        self.assertEqual(out['G'][0,0],0.)

    def test_original_2022_baseline_and_management_are_reproduced(self):
        from model_adapter import RealModel, baseline
        study=load_study();model=RealModel(study)
        actual=baseline(model,study,2022,self.root/'real_2022')
        self.assertAlmostEqual(actual['Y_13pct'],14.07778281807083,places=10)
        spec=model.management_space(2022)
        self.assertEqual(spec['dates'],['2022-06-09','2022-06-22','2022-07-03','2022-07-24','2022-08-09'])
        x=np.array([84.36,77.12,80.73,76.78,85.85])*.8
        modified=check_management_response(model.simulate(study['_centers'][2022],2022,management(spec,x)),spec,x)
        self.assertAlmostEqual(modified['Irrigation_mm'],float(x.sum()),places=8)
        self.assertLess(abs(modified['Water_balance_residual_mm']),1e-8)
        with self.assertRaises(FileNotFoundError):model.simulate(study['_centers'][2019],2019)

    def test_epsilon_selects_lowest_feasible_and_two_neighbors(self):
        d=pd.DataFrame({'Y13':[14.,16.,16.5,17.,16.1],'Irrigation_mm':[100.,250.,300.,350.,310.]})
        selected=C.epsilon_choices(d,16.55,445.27)
        self.assertEqual(selected.Irrigation_mm.tolist(),[250.,300.,350.])
        self.assertEqual(selected.Selection.iloc[0],'epsilon_min_irrigation')

    def test_multiseed_optimization_replay_and_conditional_validation(self):
        selected=C.run_year(self.model,self.study,2019,self.root/'optimization',generations=10,
                            population=20,seeds=[31,73,109,151,199],compare=True)
        self.assertGreater(len(selected),0)
        self.assertTrue((selected.Y13>=.95*16.55).all());self.assertTrue((selected.Irrigation_mm<=445.27).all())
        analytic_min=(.95*16.55-8)/.03
        self.assertLess(selected.Irrigation_mm.iloc[0]-analytic_min,40)
        histories=pd.read_csv(self.root/'optimization/convergence_history.csv')
        self.assertEqual(len(histories),2*5*10)
        self.assertEqual(set(histories.Algorithm),{'NSGA3','NSGA2'})
        self.assertTrue(list((self.root/'optimization/NSGA3_seed31').glob('generation_*.npz')))
        summary,missing=validate_year(self.model,self.study,2019,self.model.management_space(2019),selected,self.root/'optimization')
        self.assertFalse(missing);self.assertEqual(set(summary.Group),{'phase1_conditional','phase2_conditional'})
        self.assertTrue((summary.N==128).all())

    def test_2022_groups_and_local95_use_new_real_samples(self):
        groups,missing=conditional_groups(self.study,2022,128,901)
        self.assertEqual(missing,[])
        self.assertEqual(set(groups),{'phase1_conditional','phase2_conditional'})
        problem=B.make_problem(self.study,2022,'local95')
        d=groups['phase2_conditional'];first=d['params'][0]
        with np.load(HERE/self.study['phase_samples'],allow_pickle=False) as z:
            np.testing.assert_array_equal([first[k] for k in NAMES[5:]],z['p2_2022'][d['source_indices'][0]])
            np.testing.assert_allclose(np.array(problem['bounds'])[5:],np.quantile(z['p2_2022'],[.025,.975],axis=0).T)
        self.assertEqual({k:first[k] for k in NAMES[:5]},{k:self.study['_centers'][2022][k] for k in NAMES[:5]})

    def test_missing_group_is_reported_without_synthetic_fallback(self):
        with np.load(HERE/self.study['phase_samples'],allow_pickle=False) as z:
            np.savez_compressed(self.root/'missing.npz',p1_2022=z['p1_2022'])
        altered=copy.deepcopy(self.study);altered['_root']=str(self.root);altered['phase_samples']='missing.npz'
        groups,missing=conditional_groups(altered,2022,128,901)
        self.assertEqual(missing,['p2_2022']);self.assertEqual(list(groups),['phase1_conditional'])
        with self.assertRaises(ValueError):B.make_problem(altered,2022,'local95')

    def test_new_2022_frozen_rows_equal_formal_chain_after_burn(self):
        source=HERE/self.study['phase2_2022_checkpoint']
        with np.load(source,allow_pickle=False) as raw,np.load(HERE/self.study['phase_samples'],allow_pickle=False) as combined:
            self.assertEqual(raw['history'].shape,(2000,32,3))
            np.testing.assert_array_equal(combined['p2_2022'],raw['history'][163:].reshape(-1,3))
            self.assertEqual(combined['p2_2022'].shape,(58784,3))
        production=load_study()
        self.assertEqual(production['baseline_reference']['2022']['atol'],1e-5)
        self.assertAlmostEqual(production['baseline_reference']['2022']['Y_13pct'],14.07778281807083)

    def test_entrypoint_stops_without_real_model_and_never_runs_mcmc(self):
        out=self.root/'blocked'
        result=subprocess.run([sys.executable,str(HERE/'DI_PHASE3_ONE_CLICK.py'),'--out',str(out)],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertEqual(read(out/'EXECUTION_STATUS.json')['status'],'BLOCKED_OR_FAILED')
        self.assertFalse(list(out.rglob('sobol_indices.csv')))
        self.assertFalse(list(out.rglob('pareto_front.csv')))
        self.assertFalse(list(out.rglob('history.npy')))


if __name__=='__main__':unittest.main(verbosity=2)
