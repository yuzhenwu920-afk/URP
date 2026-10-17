"""Check the delivered exact 2022 baseline and generate a fresh global design."""
import argparse
from pathlib import Path
import numpy as np
import real_model_pipeline as pipeline
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--n',type=int,default=128)
    args=parser.parse_args()
    case=pipeline.read(ROOT/'study_config.json')['cases']['2022']
    model=pipeline.read(ROOT/'source_data/conditional_mean_model.json')
    for name,value in case['central_params'].items():
        assert np.isclose(value,model['values'][name],atol=1e-9,rtol=0)
    for name,value in case['baseline_expected'].items():
        key='B_last' if name=='B_t_ha' else name
        assert np.isclose(value,model['DI'][key],atol=1e-9,rtol=0)
    result=pipeline.prepare(ROOT/'study_config.json',args.out,n=args.n)
    print(result['status'],result['total_model_calls_required'])
