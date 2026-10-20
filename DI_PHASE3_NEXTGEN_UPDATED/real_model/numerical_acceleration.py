"""Exact-equation root-zone kernel; no approximation, surrogate, or fastmath."""
from collections import namedtuple
import importlib
import importlib.util
from pathlib import Path
import sys
import json
import functools

ProfileData=namedtuple('ProfileData','dzsum dz th_s th_fc th_wp th_dry')
_installed=False


def install():
    global _installed
    if _installed:return
    path=Path(__file__).with_name('root_zone_kernel.py')
    sys.path.insert(0,str(path.parent)) if str(path.parent) not in sys.path else None
    kernel=importlib.import_module('root_zone_kernel').root_zone_water
    def fast(prof,zroot,theta,ztop,zmin,aer):
        values=ProfileData(prof.dzsum,prof.dz,prof.th_s,prof.th_fc,prof.th_wp,prof.th_dry)
        return kernel(values,zroot,theta,ztop,zmin,aer)
    for name,module in list(sys.modules.items()):
        if name.startswith('aquacrop.') and hasattr(module,'root_zone_water'):
            module.root_zone_water=fast
    kernels=importlib.import_module('physical_kernels')
    metadata=json.loads(path.with_name('KERNEL_ARGUMENTS.json').read_text())
    for name,description in metadata.items():
        original=importlib.import_module('aquacrop.solution.'+name).__dict__[name]
        conversions={}
        for arg,attrs in description['attrs'].items():
            record=namedtuple(name+'_'+arg,attrs)
            globals()[record.__name__]=record
            conversions[description['args'].index(arg)]=(record,attrs)
        compiled=getattr(kernels,name)
        def wrap(original,compiled,conversions,name):
            @functools.wraps(original)
            def call(*args,**kwargs):
                if kwargs:raise TypeError('Numerical wrapper expects positional arguments')
                a=list(args)
                if name=='root_development' and a[14] is None:
                    if a[17]!=0:raise ValueError('Missing active groundwater depth')
                    a[14]=0.
                for index,(record,attrs) in conversions.items():
                    value=a[index];a[index]=record(*(getattr(value,k) for k in attrs))
                return compiled(*a)
            return call
        replacement=wrap(original,compiled,conversions,name) if conversions else compiled
        for module_name,module in list(sys.modules.items()):
            if module_name.startswith('aquacrop.') and getattr(module,name,None) is original:
                setattr(module,name,replacement)
    _installed=True
