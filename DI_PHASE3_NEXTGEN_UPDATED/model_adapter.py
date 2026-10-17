"""Shared real-model interface for the revised yesterday B/C workflow."""
from __future__ import annotations
import hashlib
import importlib.metadata
import importlib.util
import json
import math
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
NAMES = ['CCx','CGC_CD','CDC_CD','SenescenceCD','Kcb','WP_early','WP_late','HI0']
OUTPUTS = ['Y_13pct','B_t_ha','Tr_mm','Es_mm','ET_mm','MaxCC']
LEDGER = ['Irrigation_mm','Rain_mm','CR_mm','GwIn_mm','Runoff_mm','DeepPerc_mm',
          'TileDrain_mm','Profile_initial_mm','Profile_final_mm','Surface_initial_mm',
          'Surface_final_mm','Water_balance_residual_mm','Max_daily_balance_residual_mm']


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    temp.replace(path)


def csv(path,rows):
    df=rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(path,index=False,encoding='utf-8-sig');return df


def versions():
    return {p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','SALib','pymoo']}


def roundoff_tolerance(bound):
    """Machine-arithmetic allowance, not agronomic feasibility slack."""
    return 64*np.finfo(float).eps*max(1.,abs(float(bound)))


def load_study(path=HERE/'project_config.json'):
    path=Path(path).resolve();config=read(path)
    config['_root']=str(path.parent);config['_config_sha256']=sha(path)
    centers=path.parent/config['centers'];samples=path.parent/config['phase_samples']
    df=pd.read_csv(centers,float_precision='round_trip').set_index('Year')
    if df.index.duplicated().any():raise ValueError('Duplicate annual central parameter vectors')
    config['_centers']={int(y):{k:float(df.loc[y,k]) for k in NAMES} for y in config['years']}
    if not all(math.isfinite(v) for p in config['_centers'].values() for v in p.values()):
        raise ValueError('Invalid frozen central parameter')
    config['_frozen_hashes']={config['centers']:sha(centers),config['phase_samples']:sha(samples)}
    return config


def validate_output(raw,tolerance=1e-5):
    # The adapter must map real outputs explicitly; no guessed defaults for fluxes.
    r={k:float(raw[k]) for k in OUTPUTS+LEDGER+['Y_dry']}
    if not all(math.isfinite(v) for v in r.values()):raise ValueError('Nonfinite model output')
    if any(v < -1e-9 for k,v in r.items() if k!='Water_balance_residual_mm'):
        raise ValueError('Negative physical quantity')
    if r['MaxCC']>1.005+1e-9:raise ValueError('CC must be a fraction')
    if not math.isclose(r['Y_dry'],.87*r['Y_13pct'],rel_tol=1e-7,abs_tol=1e-7):
        raise ValueError('Y_dry must be 0.87*Y13')
    if not math.isclose(r['ET_mm'],r['Tr_mm']+r['Es_mm'],rel_tol=0,abs_tol=1e-6):
        raise ValueError('ET must equal Tr+Es')
    balance=(r['Irrigation_mm']+r['Rain_mm']+r['CR_mm']+r['GwIn_mm']-r['ET_mm']
             -r['Runoff_mm']-r['DeepPerc_mm']-r['TileDrain_mm']
             -r['Profile_final_mm']+r['Profile_initial_mm']-r['Surface_final_mm']+r['Surface_initial_mm'])
    if (abs(balance)>tolerance or abs(r['Water_balance_residual_mm'])>tolerance
            or abs(balance-r['Water_balance_residual_mm'])>tolerance
            or r['Max_daily_balance_residual_mm']>tolerance):
        raise ValueError(f'Water ledger failed: {balance:g} mm')
    r['IWP_kg_m3']=100*r['Y_13pct']/r['Irrigation_mm'] if r['Irrigation_mm']>0 else None
    r['ETWP_kg_m3']=100*r['Y_13pct']/r['ET_mm'] if r['ET_mm']>0 else None
    r['irrigation_events']=raw.get('irrigation_events')
    return r


class RealModel:
    def __init__(self,study,adapter=None):
        self.study=study
        path=Path(adapter).resolve() if adapter else Path(study['_root'])/study['adapter']
        if not path.is_file():raise FileNotFoundError(f'Modified DI adapter missing: {path}')
        spec=importlib.util.spec_from_file_location('urp_modified_di_adapter',path)
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
        self.provenance=self.module.provenance()
        if self.provenance.get('engine')!='Modified_DI_AquaCrop':
            raise ValueError('Formal workflow requires the original Modified DI model')
        if self.provenance.get('deterministic') is not True:raise ValueError('Deterministic engine required')
        roles={f['role'] for f in self.provenance['files']}
        if not {'model_source','weather','soil','irrigation','observations'}.issubset(roles):
            raise ValueError('Hash manifest must include model, weather, soil, irrigation and observations')
        for f in self.provenance['files']:
            fp=Path(f['path']);fp=fp if fp.is_absolute() else path.parent/fp
            if sha(fp)!=f['sha256']:raise ValueError(f'Frozen file hash mismatch: {fp.name}')
        identity={'adapter_sha256':sha(path),'provenance':self.provenance,
                  'config_sha256':study['_config_sha256'],'inputs':study['_frozen_hashes'],'versions':versions()}
        self.identity=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()

    def simulate(self,params,year,management=None):
        raw=self.module.simulate(params=dict(params),year=int(year),management=management)
        r=validate_output(raw,self.study['water_balance_atol_mm'])
        if management is None:
            if not math.isclose(r['Irrigation_mm'],self.study['baseline_irrigation_mm'][str(year)],abs_tol=1e-6,rel_tol=0):
                raise ValueError('Original annual baseline irrigation not reproduced')
        return r

    def management_space(self,year):
        return validate_space(self.module.management_space(int(year)))


def baseline(model,study,year,out):
    central=study['_centers'][year]
    a=model.simulate(central,year);b=model.simulate(central,year)
    for k in OUTPUTS+LEDGER+['Y_dry']:
        if not math.isclose(a[k],b[k],rel_tol=1e-10,abs_tol=1e-9):
            raise ValueError(f'Stateful simulation: repeated baseline changed {k}')
    ref=study['baseline_reference'][str(year)]
    for k in ['Y_13pct','Tr_mm','Es_mm','ET_mm']:
        if not math.isclose(a[k],ref[k],rel_tol=1e-6,abs_tol=ref['atol']):
            raise ValueError(f'Frozen baseline mismatch {year} {k}: {a[k]} vs {ref[k]}')
    write(Path(out)/f'baseline_{year}.json',{'year':year,'response':a,'engine':model.identity,
          'reference_evidence':ref['evidence'],'evaluation_role':'baseline reproduction, not external validation'})
    return a


def validate_space(spec):
    spec=dict(spec);kind=spec['kind'];n=len(spec['names'])
    if kind=='SMT':
        if n!=4 or spec['lower']!=[0]*4 or spec['upper']!=[100]*4:
            raise ValueError('SMT must use four stage thresholds in [0,100]')
        if not spec.get('definition'):raise ValueError('SMT percent meaning and trigger direction are required')
    elif kind=='stage_amounts':
        if n not in [4,5] or len(spec['dates'])!=n:
            raise ValueError('Fallback requires four or five stage amounts with explicit fixed dates')
    else:raise ValueError('Use SMT or stage_amounts; do not mix variable systems')
    lo,hi=np.array(spec['lower'],float),np.array(spec['upper'],float)
    if lo.shape!=(n,) or hi.shape!=(n,) or not np.isfinite([lo,hi]).all() or np.any(lo<0) or np.any(hi<=lo):
        raise ValueError('Invalid control bounds')
    if len(set(spec['names']))!=n:raise ValueError('Duplicate decision names')
    windows=spec['allowed_windows']
    if len(windows)!=n:raise ValueError('Each stage needs an allowed date window')
    for j,(a,b) in enumerate(windows):
        if date.fromisoformat(a)>date.fromisoformat(b):raise ValueError('Reversed stage window')
        if kind=='stage_amounts' and not a<=spec['dates'][j]<=b:
            raise ValueError('Fixed application date outside its declared window')
    return spec


def management(spec,x):
    x=np.asarray(x,float)
    if x.shape!=(len(spec['names']),) or not np.isfinite(x).all():raise ValueError('Invalid decision vector')
    if np.any(x<spec['lower']) or np.any(x>spec['upper']):raise ValueError('Decision outside control bounds')
    r={'kind':spec['kind'],'values':{k:float(v) for k,v in zip(spec['names'],x)}}
    if spec['kind']=='stage_amounts':r['events']=[{'date':d,'mm':float(v),'stage':j} for j,(d,v) in enumerate(zip(spec['dates'],x))]
    return r


def check_management_response(response,spec,x):
    events=response['irrigation_events']
    if not isinstance(events,list):raise ValueError('Actual irrigation events must be returned by the real model')
    total=0.
    for event in events:
        d=event['date'];date.fromisoformat(d);mm=float(event['mm']);stage=event['stage']
        if type(stage) is not int or not 0<=stage<len(spec['names']):raise ValueError('Invalid irrigation stage')
        a,b=spec['allowed_windows'][stage]
        if not a<=d<=b or not math.isfinite(mm) or mm<0:raise ValueError('Irrigation outside allowed window or negative')
        total+=mm
    if not math.isclose(total,response['Irrigation_mm'],rel_tol=0,abs_tol=1e-6):
        raise ValueError('Actual event ledger differs from total irrigation')
    if spec['kind']=='stage_amounts':
        if not math.isclose(total,float(np.sum(x)),rel_tol=0,abs_tol=1e-6):raise ValueError('Stage amounts were not applied')
        for j,(d,v) in enumerate(zip(spec['dates'],x)):
            actual=[e for e in events if e['stage']==j]
            if any(e['date']!=d for e in actual) or not math.isclose(sum(e['mm'] for e in actual),v,rel_tol=0,abs_tol=1e-6):
                raise ValueError('Applied stage amount/date differs from requested management')
    return response
