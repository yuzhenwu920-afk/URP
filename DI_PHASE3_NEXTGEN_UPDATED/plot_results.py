"""Plot only the revised workflow's actual responses; never reuse old proxy CSVs."""
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).parent/'.cache/matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

font=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
if font.exists():fm.fontManager.addfont(str(font));families=[fm.FontProperties(fname=str(font)).get_name(),'DejaVu Sans']
else:families=['Microsoft YaHei','SimHei','DejaVu Sans']
plt.rcParams.update({'font.family':families,'font.size':11,'axes.spines.top':False,
                     'axes.spines.right':False,'axes.unicode_minus':False,'pdf.fonttype':42,
                     'xtick.labelsize':11,'ytick.labelsize':11,'legend.fontsize':11})
COLORS=['#176B87','#A8762A','#805CA2','#3D8B75']
YEAR_COLORS={2019:'#0072B2',2020:'#D55E00',2021:'#009E73',2022:'#A85AA0'}


def save(fig,out,name):
    fig.tight_layout()
    for suffix in ['png','pdf']:fig.savefig(Path(out)/f'{name}.{suffix}',dpi=300,bbox_inches='tight')
    plt.close(fig)


def plot_sobol(df,out):
    for output,g in df.groupby('Output'):
        years=sorted(g.Year.unique());fig,axes=plt.subplots(len(years),1,figsize=(10,2.9*len(years)),squeeze=False)
        for a,year,col in zip(axes[:,0],years,COLORS):
            sub=g[g.Year==year];names=list(sub.Parameter.unique());x=np.arange(len(names))
            for i,seed in enumerate(sorted(sub.Seed.unique())):
                s=sub[sub.Seed==seed].set_index('Parameter').reindex(names);offset=(i-1)*.14
                a.errorbar(x+offset,s.ST,yerr=s.ST_conf,fmt='o',ms=4,c=col,alpha=.9,
                           capsize=2,label=f'ST seed {seed}')
                a.scatter(x+offset,s.S1,s=15,marker='x',c=col,alpha=.6)
            a.set(xticks=x,xticklabels=names,title=f'{year} · {output} · independent {sub.Track.iloc[0]} ranges',ylabel='S1 (×), ST (●)')
            a.tick_params(axis='x',labelrotation=20);a.grid(axis='y',alpha=.2);a.axhline(0,color='#AAB5BD',lw=.7)
            if year==years[0]:a.legend(ncol=3,fontsize=11)
        save(fig,out,f'sobol_{output}_annual_with_CI')
    # A heatmap of ordinal ranks preserves annual distinctions, not a mean ranking.
    sub=df[(df.Output=='Y_13pct')&(df.Status=='estimated')]
    if sub.empty:return
    st=sub.groupby(['Year','Parameter']).ST.mean().unstack('Year')
    ranks=st.rank(ascending=False,method='min')
    fig,a=plt.subplots(figsize=(7,5));im=a.imshow(ranks,cmap='viridis_r',vmin=1,vmax=len(ranks))
    a.set(xticks=range(len(ranks.columns)),xticklabels=ranks.columns,yticks=range(len(ranks)),yticklabels=ranks.index,
          title='Annual Y13 ST ranks (mean across scrambles; CIs separately)')
    for i in range(len(ranks)):
        for j in range(len(ranks.columns)):
            if np.isfinite(ranks.iloc[i,j]):a.text(j,i,str(int(ranks.iloc[i,j])),ha='center',va='center',color='white' if ranks.iloc[i,j]>4 else '#173246')
    fig.colorbar(im,ax=a,label='rank');save(fig,out,'sobol_cross_year_ranks')


def plot_optimization(fronts,history,candidates,base,observed,out):
    fig,axes=plt.subplots(1,2,figsize=(10.2,4.8))
    year=int(fronts.Year.iloc[0]);year_color=YEAR_COLORS[year]
    for j,(algorithm,g) in enumerate(fronts.groupby('Algorithm')):
        axes[0].scatter(g.Irrigation_mm,g.Y13,s=16,c=year_color if algorithm=='NSGA3' else '#7B8B94',alpha=.5,label=algorithm)
    axes[0].scatter([base['Irrigation_mm']],[base['Y_13pct']],marker='*',s=150,c='#B14C47',label='model baseline')
    if len(candidates):axes[0].scatter(candidates.Irrigation_mm,candidates.Y13,facecolor='none',edgecolor='black',s=90,label='epsilon candidates')
    axes[0].axhline(.95*observed,c='#B14C47',ls='--',lw=1,label='95% observed yield')
    axes[0].set(xlabel='灌水量（mm）',ylabel='Y13（t/ha）',title=f'{year} · 真实可行方案')
    axes[0].legend(fontsize=11)
    for algorithm,g in history.groupby('Algorithm'):
        values=g.pivot(index='Generation',columns='Seed',values='Hypervolume')
        color=year_color if algorithm=='NSGA3' else '#7B8B94'
        axes[1].plot(values.index,values.median(axis=1),lw=1.6,c=color,ls='-' if algorithm=='NSGA3' else '--',label=algorithm)
        axes[1].fill_between(values.index,values.min(axis=1),values.max(axis=1),color=color,alpha=.14,lw=0)
    axes[1].set(xlabel='代数',ylabel='归一化超体积 HV',title='五种子中位数及最小—最大范围')
    axes[1].legend(fontsize=11)
    for a in axes:a.grid(alpha=.2)
    save(fig,out,'optimization_front_and_convergence')


def plot_conditional(df,out):
    fig,axes=plt.subplots(1,2,figsize=(10.2,4.8));labels=[]
    year=int(df.Year.iloc[0]);color=YEAR_COLORS[year]
    for j,r in enumerate(df.itertuples()):
        group='阶段一' if r.Group.startswith('phase1') else '阶段二'
        label=f'{r.Candidate_ID.split("_")[-1]} · {group}';labels.append(label)
        p=r.Probability_above_absolute_gate
        axes[0].errorbar(p,j,xerr=[[max(0.,p-r.Wilson_low)],[max(0.,r.Wilson_high-p)]],fmt='o',c=color,capsize=3)
        axes[1].scatter(r.Mean_Y13,j,c=color,marker='o')
        axes[1].scatter(r.Q05_Y13,j,c=color,marker='v')
    for a in axes:a.set_yticks(range(len(labels)),labels);a.set_ylim(len(labels)-.5,-.5);a.grid(axis='x',alpha=.2)
    axes[0].set(xlabel='条件门槛达标比例',xlim=(-.04,1.04),title='观测产量95%门槛；重采样MC区间')
    axes[1].set(xlabel='Y13（t/ha）',title='条件均值（●）与5%分位数（▼）')
    save(fig,out,'conditional_candidate_checks')
