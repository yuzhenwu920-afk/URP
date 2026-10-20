"""Original annual DI engines with an explicit common-calendar harvest adapter.

Crop equations and input snapshots are untouched. Early crop termination is
retained as a physical outcome: yield is saved at harvest, subsequent crop
transpiration/irrigation cease, and the soil balance continues to the original
calendar boundary. The declared film management remains on the field.
"""
from pathlib import Path
from functools import lru_cache
import copy
import hashlib
import importlib
import importlib.util
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
STATES = {}
NAMES = ['CCx','CGC_CD','CDC_CD','SenescenceCD','Kcb','WP_early','WP_late','HI0']


def provenance():
    files=[]
    for year in range(2019,2023):
        folder=ROOT/f'model_{year}'
        manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8-sig'))
        for name,digest in manifest.items():
            if name.endswith('.py'): role='model_source'
            elif 'WEATHER_FILE' in name or 'ETO_FILE' in name: role='weather'
            elif 'INITIAL_WATER' in name: role='soil'
            elif any(s in name for s in ('FIELD_CC','BIOMASS','RS_CC')): role='observations'
            else: role='frozen_reference'
            files.append(dict(role=role,path=f'model_{year}/'+name,sha256=digest))
        script=f'DI_{year}_MCMC_ONE_CLICK.py'
        files.append(dict(role='irrigation',path=f'model_{year}/'+script,sha256=manifest[script]))
    for name in ['numerical_acceleration.py','root_zone_kernel.py','physical_kernels.py','KERNEL_ARGUMENTS.json']:
        p=ROOT/name
        if p.exists(): files.append(dict(role='implementation',path=name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    return dict(engine='Modified_DI_AquaCrop',deterministic=True,available_years=list(range(2019,2023)),
        files=files,input_role='original annual supplied input snapshots; no MCMC resampling',
        control='amounts on every original irrigation date; timing unchanged',
        extension='common-calendar balance; original crop-harvest yield; no irrigation after crop termination',
        post_harvest_management='same declared mulch as during growing season')


def _load(year):
    if year not in STATES:
        folder=ROOT/f'model_{year}';source=folder/f'DI_{year}_MCMC_ONE_CLICK.py'
        spec=importlib.util.spec_from_file_location(f'urp_original_{year}',source)
        driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
        model=driver._embedded_module('model',folder/'data/model.py')
        model.OUTPUT_DIR=ROOT.parent/'output_real/input_audit'/str(year)
        model.OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
        data=model.load_inputs();model.prepare_soil(data)
        model.effective_wp=lru_cache(maxsize=64)(model.effective_wp)
        STATES[year]=(model,data)
    return STATES[year]


def management_space(year):
    model,data=_load(year)
    dates=data['schedule'].Date.dt.strftime('%Y-%m-%d').tolist()
    cap=float(data['schedule'].Depth.sum())
    groups=np.array_split(np.arange(len(dates)),4)
    amounts=data['schedule'].Depth.to_numpy(float)
    stages=[int(next(j for j,g in enumerate(groups) if i in g)) for i in range(len(dates))]
    totals=[float(amounts[g].sum()) for g in groups]
    weights=[float(amounts[i]/totals[stages[i]]) for i in range(len(dates))]
    return dict(kind='stage_amounts',names=[f'Window{i+1}_mm' for i in range(4)],
        lower=[0.]*4,upper=[cap]*4,dates=[dates[g[0]] for g in groups],
        event_dates=dates,event_stages=stages,event_weights=weights,baseline_amounts=totals,
        allowed_windows=[[dates[g[0]],dates[g[-1]]] for g in groups],
        definition='Four ordered irrigation-window totals; retain original event dates and within-window baseline proportions; not SMT or optimized timing',
        actual_irrigation_policy='cancel events after actual harvest; preserve planned and actual amounts',
        SMT_supported=False)


@lru_cache(maxsize=12)
def _template(year,values):
    model,data=_load(year)
    v=dict(zip(NAMES,values))
    soil=copy.deepcopy(data['soil'])
    iw=model.InitialWaterContent(wc_type='Num',method='Depth',depth_layer=data['mid'].tolist(),value=data['theta'].tolist())
    m=model.make_model(data,v,soil,iw,'DI')
    m.off_season=True
    m.fallow_field_management=model.field_management()
    m._initialize()
    if not np.allclose(m._init_cond.th,data['theta'],atol=1e-10,rtol=0):
        raise RuntimeError('Original initial water not reproduced')
    # All management alternatives share the exact trajectory before the first
    # possible irrigation date. Cache that numerical state, never a response
    # approximation. A new parameter vector always computes its own prefix.
    sc=m._param_struct.Seasonal_Crop_List[0]
    m._urp_full_fco2=float(sc.fCO2)
    prefix_storage=[float(np.sum(m._init_cond.th)*100)]
    prefix_surface=[float(m._init_cond.surface_storage)]
    prefix_states=[]
    step=importlib.import_module('aquacrop.timestep.run_single_timestep');core=importlib.import_module('aquacrop.core')
    original_evap,original_stop=step.soil_evaporation,core.check_model_is_finished
    step.soil_evaporation=_evap_wrapper(original_evap)
    core.check_model_is_finished=lambda current_time,*args: bool(current_time>=model.HARVEST)
    try:
        first=data['schedule'].Date.min()
        while m._clock_struct.step_start_time<first:
            date=m._clock_struct.step_start_time
            sc.WP,sc.fCO2=model.effective_wp(m._urp_full_fco2,v['WP_early'] if date<model.SWITCH else v['WP_late'])
            m._clock_struct,m._init_cond,m._param_struct,m._outputs=m._perform_timestep()
            prefix_storage.append(float(np.sum(m._init_cond.th)*100))
            prefix_surface.append(float(m._init_cond.surface_storage))
            prefix_states.append(np.array(m._init_cond.th,copy=True))
    finally:
        step.soil_evaporation=original_evap;core.check_model_is_finished=original_stop
    m._urp_prefix=(prefix_storage,prefix_surface,prefix_states)
    return m


def _evap_wrapper(original):
    import inspect
    names=list(inspect.signature(original).parameters)
    adj,cc=names.index('NewCond_CCadj'),names.index('NewCond_CC')
    def call(*args,**kwargs):
        if kwargs:
            return _load(2022)[0].evap_wrapper(original)(*args,**kwargs)
        a=list(args);a[adj]=float(a[cc]);return original(*a)
    return call


def simulate(*,params,year,management=None,details=False,accelerate=True):
    model,data=_load(year)
    if accelerate:
        import sys
        if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
        module=importlib.import_module('numerical_acceleration')
        module.install()
    m=copy.deepcopy(_template(year,tuple(float(params[k]) for k in NAMES)))
    schedule=data['schedule'].copy()
    if management is not None:
        space=management_space(year)
        if management['kind']!='stage_amounts' or set(management['values'])!=set(space['names']):
            raise ValueError('Unexpected management controls')
        schedule['Depth']=[management['values'][space['names'][j]]*w for j,w in zip(space['event_stages'],space['event_weights'])]
    # Initialized management's daily schedule is exactly the original calendar.
    daily=np.zeros(len(m._clock_struct.time_span))
    indexes=m._clock_struct.time_span.get_indexer(schedule.Date)
    if np.any(indexes<0): raise ValueError('Irrigation event outside model calendar')
    daily[indexes]=schedule.Depth.to_numpy(float)
    im=m._param_struct.IrrMngt
    im.Schedule=daily;im.MaxIrr=float(schedule.Depth.max()+.1);im.MaxIrrSeason=float(schedule.Depth.sum()+.1)
    sc=m._param_struct.Seasonal_Crop_List[0]
    full=m._urp_full_fco2
    wp=[model.effective_wp(full,params[k]) for k in ('WP_early','WP_late')]
    step=importlib.import_module('aquacrop.timestep.run_single_timestep')
    core=importlib.import_module('aquacrop.core')
    original_evap,original_stop=step.soil_evaporation,core.check_model_is_finished
    step.soil_evaporation=_evap_wrapper(original_evap)
    core.check_model_is_finished=lambda current_time,*args: bool(current_time>=model.HARVEST)
    storage,surface,states=m._urp_prefix
    offset=len(storage)-1
    try:
        for date in model.DATES[offset:]:
            if m._clock_struct.model_is_finished or date!=m._clock_struct.step_start_time:
                raise RuntimeError('Fixed-calendar simulation clock changed')
            sc.WP,sc.fCO2=wp[int(date>=model.SWITCH)]
            m._clock_struct,m._init_cond,m._param_struct,m._outputs=m._perform_timestep()
            th=m._init_cond.th
            if not np.isfinite(th).all(): raise RuntimeError('Nonfinite soil water')
            storage.append(float(np.sum(th)*100));surface.append(float(m._init_cond.surface_storage))
            states.append(np.array(th,copy=True))
    finally:
        step.soil_evaporation=original_evap;core.check_model_is_finished=original_stop
    if not m._clock_struct.model_is_finished: raise RuntimeError('Fixed-calendar boundary not reached')
    n=len(model.DATES)
    f=m._outputs.water_flux.iloc[:n].copy();g=m._outputs.crop_growth.iloc[:n].copy()
    f['Date']=model.DATES;g['Date']=model.DATES
    required=['Tr','Es','IrrDay','DeepPerc','Runoff','CR','GwIn','TileDrain']
    if not np.isfinite(f[required].to_numpy()).all():raise RuntimeError('Nonfinite flux')
    states=np.array(states);profile=data['soil'].profile
    if (states<profile.th_dry.to_numpy()-1e-8).any() or (states>profile.th_s.to_numpy()+1e-8).any():
        raise RuntimeError('Soil water outside original dry/saturation bounds')
    rain=data['weather'].set_index('Date').loc[model.DATES,'Precipitation'].to_numpy(float)
    wb=rain+f.IrrDay.to_numpy()+f.CR.to_numpy()+f.GwIn.to_numpy()-f.Tr.to_numpy()-f.Es.to_numpy()-f.DeepPerc.to_numpy()-f.Runoff.to_numpy()-f.TileDrain.to_numpy()-np.diff(storage)-np.diff(surface)
    if abs(wb.sum())>1e-5 or np.max(abs(wb))>1e-5:raise RuntimeError('Daily/season water ledger failed')
    stats=m._outputs.final_stats
    if len(stats)!=1: raise RuntimeError('Expected one actual crop harvest')
    last=stats.iloc[0];harvest=pd.Timestamp(last['Harvest Date (YYYY/MM/DD)'])
    growing_days=int(last['Harvest Date (Step)'])+1 if 'Harvest Date (Step)' in last else int((harvest-model.PLANT).days)
    harvest_row=g.iloc[growing_days-1]
    actual=f.IrrDay.to_numpy(float)
    expected=schedule.set_index('Date').Depth.reindex(model.DATES,fill_value=0).to_numpy()
    if not np.allclose(actual[:growing_days],expected[:growing_days],atol=1e-7,rtol=0) or np.any(actual[growing_days:]>1e-8):
        raise RuntimeError('Actual irrigation differs from schedule-before-harvest policy')
    y=float(last['Dry yield (tonne/ha)'])
    s=dict(Y_dry=y,Y_13pct=y/.87,B_t_ha=float(harvest_row.biomass/100),B_last=float(harvest_row.biomass/100),
        Irrigation_mm=float(f.IrrDay.sum()),Planned_irrigation_mm=float(schedule.Depth.sum()),
        Cancelled_irrigation_mm=float(schedule.Depth.sum()-f.IrrDay.sum()),Rain_mm=float(rain.sum()),
        Tr_mm=float(f.Tr.sum()),Es_mm=float(f.Es.sum()),ET_mm=float((f.Tr+f.Es).sum()),
        Tr_until_harvest_mm=float(f.Tr.iloc[:growing_days].sum()),Es_until_harvest_mm=float(f.Es.iloc[:growing_days].sum()),
        DeepPerc_mm=float(f.DeepPerc.sum()),Runoff_mm=float(f.Runoff.sum()),CR_mm=float(f.CR.sum()),
        GwIn_mm=float(f.GwIn.sum()),TileDrain_mm=float(f.TileDrain.sum()),Profile_initial_mm=storage[0],Profile_final_mm=storage[-1],
        Surface_initial_mm=surface[0],Surface_final_mm=surface[-1],Water_balance_residual_mm=float(wb.sum()),
        Max_daily_balance_residual_mm=float(abs(wb).max()),MaxCC=float(g.canopy_cover.max()),
        Harvest_date=harvest.strftime('%Y-%m-%d'),Growing_days=growing_days,Calendar_days=n,
        Early_termination=bool(growing_days<n),Crop_dead=bool(m._init_cond.crop_dead),
        irrigation_events=[dict(date=d.strftime('%Y-%m-%d'),mm=float(actual[model.DATES.get_loc(d)]),stage=management_space(year)['event_stages'][j])
            for j,d in enumerate(schedule.Date)])
    return (s,f,g) if details else s
