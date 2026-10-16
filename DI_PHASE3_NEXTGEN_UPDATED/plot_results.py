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
plt.rcParams.update({'font.family':families,'font.size':10,'axes.spines.top':False,
                     'axes.spines.right':False,'axes.unicode_minus':False,'pdf.fonttype':42})
COLORS=['#176B87','#A8762A','#805CA2','#3D8B75']


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
            if year==years[0]:a.legend(ncol=3,fontsize=8)
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
    fig,axes=plt.subplots(1,2,figsize=(12,4.6))
    for j,(algorithm,g) in enumerate(fronts.groupby('Algorithm')):
        axes[0].scatter(g.Irrigation_mm,g.Y13,s=20,c=COLORS[j],alpha=.65,label=algorithm)
    axes[0].scatter([base['Irrigation_mm']],[base['Y_13pct']],marker='*',s=150,c='#B14C47',label='model baseline')
    if len(candidates):axes[0].scatter(candidates.Irrigation_mm,candidates.Y13,facecolor='none',edgecolor='black',s=90,label='epsilon candidates')
    axes[0].axhline(.95*observed,c='#B14C47',ls='--',lw=1,label='95% observed yield')
    axes[0].set(xlabel='Irrigation / mm',ylabel='Y13 / (t/ha)',title='Actual feasible points; no constructed monotone envelope')
    axes[0].legend(fontsize=8)
    for (algorithm,seed),g in history.groupby(['Algorithm','Seed']):
        axes[1].plot(g.Generation,g.Hypervolume,lw=1,alpha=.7,label=f'{algorithm} {seed}')
    axes[1].set(xlabel='Generation',ylabel='Normalized hypervolume',title='Fixed within-year reference [0, 1.01]')
    axes[1].legend(fontsize=7,ncol=2)
    for a in axes:a.grid(alpha=.2)
    save(fig,out,'optimization_front_and_convergence')


def plot_conditional(df,out):
    fig,axes=plt.subplots(1,2,figsize=(12,4.6));labels=[]
    for j,r in enumerate(df.itertuples()):
        label=f'{r.Candidate_ID}\n{r.Group}';labels.append(label)
        axes[0].errorbar(j,r.Probability_above_absolute_gate,
                         yerr=[[r.Probability_above_absolute_gate-r.Wilson_low],[r.Wilson_high-r.Probability_above_absolute_gate]],
                         fmt='o',c=COLORS[j%4],capsize=3)
        axes[1].scatter(j,r.Mean_Y13,c=COLORS[j%4],marker='o')
        axes[1].scatter(j,r.Q05_Y13,c=COLORS[j%4],marker='v')
    for a in axes:a.set_xticks(range(len(labels)),labels,rotation=35,ha='right');a.grid(axis='y',alpha=.2)
    axes[0].set(ylabel='Conditional probability',ylim=(-.05,1.05),title='Absolute observed-yield gate; Wilson intervals')
    axes[1].set(ylabel='Y13 / (t/ha)',title='Conditional mean (●) and 5th percentile (▼)')
    save(fig,out,'conditional_candidate_checks')
