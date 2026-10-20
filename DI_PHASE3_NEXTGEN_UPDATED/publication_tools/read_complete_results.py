"""Decode lossless column archives into ordinary full-precision DataFrames."""
from pathlib import Path
import json
import numpy as np
import pandas as pd


def calculate(recipe,columns):
    op=recipe['op']
    if op=='copy':return np.asarray(columns[recipe['column']],dtype=np.float64)
    if op=='sum':return np.column_stack([columns[k] for k in recipe['columns']]).sum(axis=1)
    if op=='add':return columns[recipe['a']]+columns[recipe['b']]
    if op=='multiply':return columns[recipe['column']]*recipe['value']
    if op=='ratio':return recipe['scale']*columns[recipe['numerator']]/columns[recipe['denominator']]
    if op=='storage':
        return (columns['Profile_initial_mm']+columns['Irrigation_mm']+columns['Rain_mm']+columns['CR_mm']+columns['GwIn_mm']
            -columns['ET_mm']-columns['Runoff_mm']-columns['DeepPerc_mm']-columns['TileDrain_mm']
            -columns['Surface_final_mm']+columns['Surface_initial_mm'])
    if op=='scaled_difference':return (recipe['constant']-columns[recipe['column']])/recipe['divisor']
    raise ValueError('Unknown lossless arithmetic descriptor')


def load_columns(path):
    """Every floating-point bit is recovered; arithmetic is compression only."""
    with np.load(path,allow_pickle=False) as z:
        names=z['_column_names'].tolist()
        encoding=json.loads(str(z['_encoding_json'].item())) if '_encoding_json' in z else {}
        columns={k:z[k] for k in names if k in z}
        pending=dict(encoding)
        while pending:
            progress=False
            for k,recipe in list(pending.items()):
                try:predicted=np.ascontiguousarray(calculate(recipe,columns),dtype=np.float64)
                except KeyError:continue
                columns[k]=np.bitwise_xor(predicted.view(np.uint64),z['_xor_'+k]).view(np.float64)
                del pending[k];progress=True
            if not progress:raise ValueError('Cyclic or missing lossless descriptor')
    return pd.DataFrame({k:columns[k] for k in names})


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--csv',type=Path);a=p.parse_args()
    df=load_columns(a.archive)
    if a.csv:df.to_csv(a.csv,index=False,encoding='utf-8-sig')
    print(df.shape);print(df.head().to_string(index=False))
