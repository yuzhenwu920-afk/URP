"""昨天工程的修订入口：冻结MCMC，只执行Sobol、确定性优化与候选核验。"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
from pathlib import Path

from model_adapter import HERE,RealModel,load_study,read,write,versions


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=HERE/'project_config.json')
    parser.add_argument('--adapter',type=Path)
    parser.add_argument('--phase',choices=['all','sobol','optimization','validate'],default='all')
    parser.add_argument('--out',type=Path)
    parser.add_argument('--years',nargs='+',type=int)
    parser.add_argument('--n',type=int,choices=[128,512])
    parser.add_argument('--track',choices=['global','local95'],default='global')
    parser.add_argument('--auto-expand',action='store_true',help='If N128 is unstable, run N512 before optimization')
    args=parser.parse_args(argv)
    study=load_study(args.config)
    years=args.years or study['years']
    if not set(years).issubset(study['years']):parser.error('Year not present in frozen inputs')
    if args.phase=='all' and args.track!='global':parser.error('Main all-phase workflow must use global physical ranges')
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out=args.out or HERE/'output_revised'/run_id
    out.mkdir(parents=True,exist_ok=True)
    write(out/'execution_contract.json',{'scope':'Sobol and optimization; MCMC frozen and never rerun',
          'config_sha256':study['_config_sha256'],'frozen_input_hashes':study['_frozen_hashes'],
          'versions':versions(),'requested_phase':args.phase,'years':years,
          'global_bounds':study['global_physical_bounds'],'primary_track':'global',
          'optimization':'fixed central parameters, two objectives, hard observed-yield and irrigation gates'})
    try:
        model=RealModel(study,args.adapter)
        write(out/'real_model_provenance.json',dict(model.provenance,identity=model.identity))
        if args.phase in ['all','sobol']:
            import phaseB_sobol as B
            result=B.main(study,model,out,args.n,years,args.track)
            summary=read(result/'sobol_summary.json')
            if args.auto_expand and summary['status']!='SCREENING_STABLE' and summary['N']==128:
                result=B.main(study,model,out,512,years,args.track)
                summary=read(result/'sobol_summary.json')
            if args.phase=='all' and summary['status']!='SCREENING_STABLE':
                write(out/'EXECUTION_STATUS.json',{'status':'SOBOL_REVIEW_OR_N512_REQUIRED',
                      'real_Sobol_executed':True,'optimization_executed':False,'sobol_directory':str(result)})
                return 3
        if args.phase in ['all','optimization']:
            import phaseC_nsga3 as C
            C.main(study,model,out,years)
        if args.phase=='validate':
            import pandas as pd
            from validate_candidates import validate_year
            for year in years:
                folder=out/'optimization'/str(year)
                if read(folder/'optimization_summary.json')['engine']!=model.identity:
                    raise ValueError('Candidates belong to a different frozen model/configuration')
                validate_year(model,study,year,read(folder/'decision_space.json'),pd.read_csv(folder/'epsilon_candidates.csv'),folder)
        status='REQUESTED_PHASE_COMPLETED';details={}
        if args.phase in ['all','optimization','validate']:
            for year in years:
                folder=out/'optimization'/str(year)
                opt=read(folder/'optimization_summary.json')
                conditional=read(folder/'conditional_validation_status.json') if (folder/'conditional_validation_status.json').exists() else None
                details[str(year)]={'optimization':opt['status'],'conditional':conditional['status'] if conditional else 'NOT_RUN'}
            if any(v['optimization']=='NO_FEASIBLE_SOLUTION' for v in details.values()):status='NO_FEASIBLE_SOLUTION_IN_SOME_YEARS'
            elif any(v['conditional']!='COMPLETE' for v in details.values()):status='CANDIDATES_DONE_CONDITIONAL_CHECKS_PARTIAL'
        write(out/'EXECUTION_STATUS.json',{'status':status,'phase':args.phase,'engine':model.identity,'annual_status':details})
        print(f'输出目录: {out}')
        return 0 if status=='REQUESTED_PHASE_COMPLETED' else 4
    except Exception as error:
        write(out/'EXECUTION_STATUS.json',{'status':'BLOCKED_OR_FAILED','phase':args.phase,
              'error_type':type(error).__name__,'error':str(error),'no_proxy_fallback':True})
        print(f'未完成真实模型运行：{error}\n已记录状态：{out / "EXECUTION_STATUS.json"}')
        return 2


if __name__=='__main__':raise SystemExit(main())
