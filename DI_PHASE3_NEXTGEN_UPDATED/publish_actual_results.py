"""Publication figures and readable result tables from actual four-year runs.

Never reads any historical proxy sensitivity or optimization table.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
from model_adapter import HERE,NAMES,OUTPUTS,LEDGER,load_study,RealModel,management,csv,write,read

YEARS=[2019,2020,2021,2022]
COLORS={2019:'#0072B2',2020:'#D55E00',2021:'#009E73',2022:'#A85AA0'}
LABELS={'Y_13pct':'籽粒产量 Y13','B_t_ha':'地上干生物量 B','Tr_mm':'蒸腾 Tr',
        'Es_mm':'土壤蒸发 Es','ET_mm':'总耗水 ET','MaxCC':'最大冠层覆盖度'}
PLABELS=['CCx','CGC','CDC','Senescence','Kcb','WP early','WP late','HI0']
font=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
if font.exists():fm.fontManager.addfont(str(font));FAMILY=fm.FontProperties(fname=str(font)).get_name()
else:FAMILY='DejaVu Sans'
plt.rcParams.update({'font.family':[FAMILY,'DejaVu Sans'],'font.size':12,'axes.titlesize':13,
    'axes.labelsize':12,'xtick.labelsize':11,'ytick.labelsize':11,'legend.fontsize':11,
    'axes.spines.top':False,'axes.spines.right':False,'axes.unicode_minus':False,
    'pdf.fonttype':42,'savefig.facecolor':'white'})
REGISTRY=[]


def context_figures(model,folder):
    from matplotlib.patches import FancyBboxPatch
    from matplotlib.dates import MonthLocator,DateFormatter
    fig,ax=plt.subplots(figsize=(6.2,6.1),layout='constrained');ax.set_axis_off()
    texts=[
        '2019—2022 年原始输入与年度源码\n四年中心点基准复现',
        '冻结分阶段 MCMC\n条件推断；保留严格诊断限制',
        'Sobol：八参数公共独立范围\nN=512 × 3 scrambles；六输出与区间',
        'NSGA-III 与同预算 NSGA-II\n100个体 × 100代 × 5种子；双目标',
        '候选回代与分阶段条件扰动\n解释产量、灌水、耗水和季末储水']
    colors=['#E7EFF3','#EDF0F2','#E0F0E9','#EDE5F2','#F8EDDE']
    for j,(text,color) in enumerate(zip(texts,colors)):
        y=.87-j*.185
        ax.add_patch(FancyBboxPatch((.03,y-.055),.94,.13,boxstyle='round,pad=.014,rounding_size=.015',
            transform=ax.transAxes,facecolor=color,edgecolor='#A0B0BA',lw=.8))
        ax.text(.5,y+.01,text,transform=ax.transAxes,ha='center',va='center',fontsize=12,color='#273F4C',linespacing=1.5)
        if j<4:ax.annotate('',xy=(.5,y-.103),xytext=(.5,y-.073),xycoords='axes fraction',arrowprops={'arrowstyle':'->','color':'#80939E','lw':1.3})
    save(fig,folder,'F01_workflow','四年校准成果到真实敏感性与决策的衔接',
        '全部下游计算均使用四年原年度模型；MCMC冻结，严格采样诊断限制保留。候选核验是分组条件扰动，不代表八维联合稳健优化。','portrait')
    fig,axes=plt.subplots(2,2,figsize=(10.2,5.8),sharey=True,layout='constrained')
    for ax,year in zip(axes.flat,YEARS):
        source,data=model.module._load(year)
        w=data['weather'].set_index('Date').loc[source.DATES]
        twin=ax.twinx();twin.bar(w.index,w.Precipitation,width=1.,color='#C6D1D8',alpha=.7)
        twin.set_ylim(0,60);twin.set_ylabel('降水（mm）',color='#7F8E97',fontsize=11)
        twin.tick_params(axis='y',labelsize=11,colors='#7F8E97');twin.spines['top'].set_visible(False)
        ax.set_zorder(twin.get_zorder()+1);ax.patch.set_visible(False)
        ax.plot(w.index,w.ReferenceET,c=COLORS[year],lw=1.15)
        ax.set(title=str(year),ylabel='参考蒸散 ETo（mm/d）',ylim=(0,11))
        ax.xaxis.set_major_locator(MonthLocator(interval=1));ax.xaxis.set_major_formatter(DateFormatter('%m-%d'))
        ax.grid(axis='y',alpha=.16)
    save(fig,folder,'F10_climate','四年实际使用的气象驱动',
        '彩线为本轮原年度模型实际使用的B组审计ETo，灰柱为原降水。四年均读取补齐包内的逐日驱动，没有用年度比例替代原ETo。显示各年原计算日历窗口。')


def save(fig,folder,name,title,caption,orientation='landscape'):
    folder.mkdir(parents=True,exist_ok=True)
    for suffix in ['png','pdf']:
        path=folder/f'{name}.{suffix}';fig.savefig(path,dpi=320,bbox_inches='tight',pad_inches=.12)
    REGISTRY.append(dict(name=name,title=title,caption=caption,years=YEARS,orientation=orientation,
        source='actual original annual Modified DI AquaCrop runs',font_minimum_pt=11,
        png_dpi=320,files=[f'{name}.png',f'{name}.pdf']))
    plt.close(fig)


def sobol_figures(df,folder,checks):
    for output in OUTPUTS:
        mean=df[df.Output==output].groupby(['Parameter','Year']).ST.mean().unstack('Year').reindex(index=NAMES,columns=YEARS)
        fig,ax=plt.subplots(figsize=(6.2,5.0),layout='constrained')
        vmax=max(1.,float(mean.max().max()))
        im=ax.imshow(mean,cmap='YlGnBu',vmin=0,vmax=vmax,aspect='auto')
        ax.set(xticks=np.arange(4),xticklabels=YEARS,yticks=np.arange(8),yticklabels=PLABELS,
            title=LABELS[output]+'：总效应指数 ST')
        for i in range(8):
            for j in range(4):
                value=mean.iloc[i,j]
                ax.text(j,i,f'{value:.3f}',ha='center',va='center',fontsize=11,
                    color='white' if value>.55*vmax else '#1B3343')
        fig.colorbar(im,ax=ax,shrink=.82,label='ST（三个独立 scramble 的均值）')
        ax.set_xlabel('年份；公共独立均匀范围')
        name='R01_Sobol_ST_'+output
        save(fig,folder,name,LABELS[output]+'的四年参数贡献',
             '总效应指数为各年三个独立scramble的均值。原始S1、ST、95%bootstrap半宽及三个种子分别保存在表中；均值热图不替代区间与稳定性检查。输入是公共独立均匀范围，未使用相关后验样本构造Sobol输入。','portrait')
    fig,axes=plt.subplots(2,2,figsize=(10.2,5.8),sharex=True,sharey=True,layout='constrained')
    d=df[df.Output=='Y_13pct'];maxx=max(1.,float((d.ST+d.ST_conf).max())+.025)
    for ax,year in zip(axes.flat,YEARS):
        sub=d[d.Year==year];seeds=sorted(sub.Seed.unique());yp=np.arange(8)
        for i,seed in enumerate(seeds):
            rows=sub[sub.Seed==seed].set_index('Parameter').reindex(NAMES)
            ax.errorbar(rows.ST,yp+(i-1)*.19,xerr=rows.ST_conf,fmt=['o','s','^'][i],
                color=COLORS[year],ms=4.2,lw=.9,capsize=2,alpha=.85)
        s1=sub.groupby('Parameter').S1.mean().reindex(NAMES)
        ax.scatter(s1,yp,s=29,facecolors='none',edgecolors='#303C42',marker='D',zorder=4)
        c=checks[(checks.Year==year)&(checks.Output=='Y_13pct')].iloc[0]
        status='稳定性门槛通过' if c.Stable_for_screening else '仍需保留数值不确定性'
        ax.set(title=f'{year}  ·  N={int(sub.N.iloc[0])}',yticks=yp,yticklabels=PLABELS,
            xlim=(-.025,maxx),ylim=(7.6,-.65),xlabel='Sobol 指数')
        ax.grid(axis='x',alpha=.18);ax.axvline(0,color='#939EA5',lw=.6)
        ax.text(.98,.045,status,transform=ax.transAxes,ha='right',fontsize=11,color='#5C6870')
    fig.legend(handles=[Line2D([],[],marker='o',c='#536D7B',ls='-',label='ST及95%区间（3种子）'),
        Line2D([],[],marker='D',mfc='white',mec='#303C42',c='none',label='S1种子均值')],
        loc='outside upper center',ncol=2,frameon=False)
    save(fig,folder,'R02_Sobol_Yield_CI','四年产量敏感性及数值区间',
        '圆、方、三角分别为三个scramble的ST，水平线为512次bootstrap得到的95%区间半宽；空心菱形为S1种子均值。保留负S1等有限样本估计，不截为零，也不把ST−S1估计差直接解释为校准吸收的信息。')


def optimize_figures(fronts,history,chosen,baselines,schedules,conditional,folder):
    fig,axes=plt.subplots(2,2,figsize=(10.2,5.8),layout='constrained')
    for ax,year in zip(axes.flat,YEARS):
        d=fronts[fronts.Year==year];main=d[d.Algorithm=='NSGA3'];control=d[d.Algorithm=='NSGA2']
        ax.scatter(main.Irrigation_mm,main.Y13,s=11,color=COLORS[year],alpha=.32,rasterized=True)
        from phaseC_nsga3 import nondominated
        for values,color,style in [(main,COLORS[year],'-'),(control,'#69757B','--')]:
            union=nondominated(values)
            ax.plot(union.Irrigation_mm,union.Y13,c=color,ls=style,lw=1.5)
        b=baselines[year];c=chosen[chosen.Year==year].iloc[0]
        ax.scatter(b['Irrigation_mm'],b['Y_13pct'],marker='*',s=135,c='#263E4A',edgecolors='white',linewidth=.7,zorder=6)
        ax.scatter(c.Irrigation_mm,c.Y13,s=65,facecolors='white',edgecolors=COLORS[year],lw=2,zorder=7)
        gate=.95*c.Observed_Y13
        ax.axhline(gate,c='#A86962',ls=':',lw=1.2)
        ax.set(title=str(year),xlabel='实际季节灌水量（mm）',ylabel='Y13（t/ha）')
        ax.grid(alpha=.15)
    handles=[Line2D([],[],c='#2878B5',lw=1.5,label='NSGA-III'),Line2D([],[],c='#69757B',ls='--',label='NSGA-II'),
        Line2D([],[],c='#263E4A',marker='*',ls='none',ms=11,label='模型基准'),
        Line2D([],[],c='#2878B5',marker='o',mfc='white',ls='none',label='ε约束主候选'),
        Line2D([],[],c='#A86962',ls=':',label='95%观测产量门槛')]
    fig.legend(handles=handles,loc='outside upper center',ncol=3,frameon=False)
    save(fig,folder,'R03_Actual_Pareto_fronts','四年真实模型可行Pareto前沿',
        '点为NSGA-III五个种子的实际可行解，实线为其非支配并集；灰虚线为同预算NSGA-II并集。所有前沿点满足年度灌水上限与观测产量95%门槛。星号是模型基准，不是观测产量；空心圆为门槛内最低灌水量候选。固定原灌水日期，未优化灌期。')
    fig,axes=plt.subplots(1,2,figsize=(10.2,4.85),layout='constrained');x=np.arange(4)
    for j,year in enumerate(YEARS):
        b=baselines[year];c=chosen[chosen.Year==year].iloc[0]
        axes[0].bar(j-.18,b['Irrigation_mm'],.32,color='#D1D8DC')
        axes[0].bar(j+.18,c.Irrigation_mm,.32,color=COLORS[year])
        axes[0].annotate(f'{c.Water_saving_pct:.1f}%',(j+.18,c.Irrigation_mm),xytext=(0,6),textcoords='offset points',ha='center',fontsize=11)
        axes[1].scatter(j-.17,c.Observed_Y13,c='#273F4C',marker='_',s=220,lw=2.1)
        axes[1].scatter(j,b['Y_13pct'],c='#AEBAC2',marker='D',s=48)
        axes[1].scatter(j+.17,c.Y13,c=COLORS[year],s=65)
        axes[1].plot([j-.3,j+.3],[.95*c.Observed_Y13]*2,c='#A86962',ls=':',lw=1.1)
    for ax in axes:ax.set_xticks(x,YEARS);ax.grid(axis='y',alpha=.16)
    axes[0].set(ylabel='灌水量（mm）',title='基准与主候选；标注为节水率',ylim=(0,max(b['Irrigation_mm'] for b in baselines.values())*1.12))
    axes[1].set(ylabel='Y13（t/ha）',title='观测、模型基准与主候选')
    axes[0].legend(handles=[plt.Rectangle((0,0),1,1,fc='#D1D8DC',label='原DI基准'),plt.Rectangle((0,0),1,1,fc='#2878B5',label='主候选')],frameon=False)
    axes[1].legend(handles=[Line2D([],[],c='#273F4C',marker='_',ls='none',ms=12,label='观测'),
        Line2D([],[],c='#AEBAC2',marker='D',ls='none',label='模型基准'),Line2D([],[],c='#2878B5',marker='o',ls='none',label='主候选')],frameon=False)
    save(fig,folder,'R04_Water_and_yield','四年主候选的节水与产量权衡',
        '节水率相对于各年原DI灌水量计算，产量门槛相对于发表观测计算；观测、模型基准和优化模拟严格区分。保产约束允许相对观测最多5%减产，因此结果不能写成无条件节水不减产。')
    fig,axes=plt.subplots(2,2,figsize=(10.2,5.8),layout='constrained')
    for ax,year in zip(axes.flat,YEARS):
        d=schedules[schedules.Year==year];xx=np.arange(len(d))
        ax.bar(xx-.18,d.Baseline_mm,.34,color='#D1D8DC')
        ax.bar(xx+.18,d.Candidate_actual_mm,.34,color=COLORS[year])
        ax.set(xticks=xx,xticklabels=d.Date.str[5:],title=str(year),ylabel='单次灌水量（mm）')
        ax.tick_params(axis='x',rotation=40);ax.grid(axis='y',alpha=.15)
    fig.legend(handles=[plt.Rectangle((0,0),1,1,fc='#D1D8DC',label='原DI'),plt.Rectangle((0,0),1,1,fc='#2878B5',label='主候选')],
        loc='outside upper center',ncol=2,frameon=False)
    save(fig,folder,'R05_Actual_irrigation_schedules','四年逐次灌水量分配',
        '横坐标为各年真实基准灌水日期，优化调整四个有序窗口的总量并保持各窗口内原比例。图展示逐次水量，不表示灌溉日期发生优化；若作物提前结束，后续计划灌水按接口规则取消并在源表保留计划与实际差额。')
    fig,axes=plt.subplots(2,2,figsize=(10.2,5.8),layout='constrained')
    for ax,year in zip(axes.flat,YEARS):
        d=history[history.Year==year]
        for alg,color,style in [('NSGA3',COLORS[year],'-'),('NSGA2','#69757B','--')]:
            h=d[d.Algorithm==alg].pivot(index='Generation',columns='Seed',values='Hypervolume')
            ax.fill_between(h.index,h.min(axis=1),h.max(axis=1),color=color,alpha=.14,lw=0)
            ax.plot(h.index,h.median(axis=1),c=color,ls=style,lw=1.8)
        ax.set(title=str(year),xlabel='代数',ylabel='归一化超体积 HV');ax.grid(alpha=.15)
    fig.legend(handles=[Line2D([],[],c='#2878B5',label='NSGA-III中位数与五种子范围'),
        Line2D([],[],c='#69757B',ls='--',label='NSGA-II中位数与五种子范围')],loc='outside upper center',ncol=2,frameon=False)
    save(fig,folder,'R06_Seeded_convergence','四年多随机种子收敛记录',
        '每算法各100个体、100代、5种子。线为五种子的HV中位数，阴影为最小至最大范围；归一化使用年度观测产量及基准灌水量，参考点为[0,1.01]。只在同年比较算法，不把不同年HV差异解释为算法优劣。')
    if len(conditional):
        c=conditional[conditional.Candidate_ID.str.endswith('_C1')]
        fig,axes=plt.subplots(1,2,figsize=(10.2,4.9),layout='constrained')
        for j,year in enumerate(YEARS):
            for group,offset,marker in [('phase1_conditional',-.13,'o'),('phase2_conditional',.13,'s')]:
                r=c[(c.Year==year)&(c.Group==group)].iloc[0];pos=j+offset
                p=r.Probability_above_absolute_gate
                axes[0].errorbar(p,pos,xerr=[[max(0.,p-r.Wilson_low)],[max(0.,r.Wilson_high-p)]],fmt=marker,c=COLORS[year],capsize=3,ms=6)
                axes[1].scatter(r.Q05_Y13,pos,marker=marker,c=COLORS[year],s=42)
            gate=.95*chosen[chosen.Year==year].iloc[0].Observed_Y13
            axes[1].plot([gate,gate],[j-.31,j+.31],c='#A86962',ls=':',lw=1.5)
        for ax in axes:ax.set_yticks(np.arange(4),YEARS);ax.set_ylim(3.55,-.55);ax.grid(axis='x',alpha=.16)
        axes[0].set(xlabel='超过观测产量95%门槛的条件比例',xlim=(-.03,1.03),title='每组128次条件扰动')
        axes[1].set(xlabel='产量5%分位数（t/ha）',title='尾部产量与观测门槛（虚线）')
        fig.legend(handles=[Line2D([],[],marker='o',c='#536D7B',ls='none',label='扰动阶段一，固定阶段二'),
            Line2D([],[],marker='s',c='#536D7B',ls='none',label='扰动阶段二，固定阶段一')],loc='outside upper center',ncol=2,frameon=False)
        save(fig,folder,'R07_Conditional_candidate_checks','四年主候选的条件参数扰动',
            '分别整行抽取阶段一或阶段二冻结样本，并固定另一组中心参数，不拼成八维联合后验。左图区间只描述给定经验样本池下独立重采样的Monte Carlo误差，未包含原MCMC误差、模型结构误差或田间风险；128次扰动不是128个有效后验样本。')


def storage_screening(model,study,run,chosen,baselines,tables,figures):
    """Post-filter existing real evaluations, explicitly not a constrained rerun."""
    from phaseC_nsga3 import hard_feasible
    from model_adapter import roundoff_tolerance
    rows=[]
    for year in YEARS:
        collected=[]
        for path in sorted((run/'optimization'/str(year)).glob('*_seed*/run.json')):
            identity=read(path)['identity'];folder=path.parent
            if (folder/'evaluations.csv.gz').exists():d=pd.read_csv(folder/'evaluations.csv.gz',float_precision='round_trip')
            else:
                from publication_tools.read_complete_results import load_columns
                d=load_columns(folder/'all_evaluations_columns.npz')
            d['Algorithm']=identity['algorithm'];d['Seed']=identity['seed'];d['Evaluation_row']=np.arange(len(d))
            collected.append(d)
        all_points=pd.concat(collected,ignore_index=True)
        feasible=all_points[hard_feasible(all_points.Y_13pct,all_points.Irrigation_mm,.95*study['observed_Y13'][str(year)],study['baseline_irrigation_mm'][str(year)])]
        for label,floor in [('same_baseline_end_storage',baselines[year]['Profile_final_mm']),('no_net_initial_storage_depletion',baselines[year]['Profile_initial_mm'])]:
            subset=feasible[feasible.Profile_final_mm>=floor-roundoff_tolerance(floor)]
            if subset.empty:
                rows.append(dict(Year=year,Screen=label,Storage_floor_mm=floor,Status='NO_POINT_FOUND_IN_EXISTING_EVALUATIONS',Irrigation_mm=None,Y13=None,
                    Water_saving_pct=None,Final_storage_mm=None,Source='post-filter only; not proof of infeasibility'))
                continue
            best=subset.sort_values(['Irrigation_mm','Y_13pct'],ascending=[True,False]).iloc[0]
            spec=model.management_space(year);x=np.array([best[n] for n in spec['names']]);request=management(spec,x)
            r=model.simulate(study['_centers'][year],year,request)
            if (not np.isclose(r['Y_13pct'],best.Y_13pct,atol=1e-8,rtol=1e-8)
                or r['Profile_final_mm']<floor-roundoff_tolerance(floor)
                or not hard_feasible(r['Y_13pct'],r['Irrigation_mm'],.95*study['observed_Y13'][str(year)],study['baseline_irrigation_mm'][str(year)])):
                raise ValueError('Storage-screened point did not reproduce')
            rows.append(dict(Year=year,Screen=label,Storage_floor_mm=floor,Status='EXISTING_REAL_POINT_REPLAYED',Irrigation_mm=r['Irrigation_mm'],Y13=r['Y_13pct'],
                Water_saving_pct=100*(1-r['Irrigation_mm']/study['baseline_irrigation_mm'][str(year)]),Final_storage_mm=r['Profile_final_mm'],
                ET_mm=r['ET_mm'],Algorithm=best.Algorithm,Seed=int(best.Seed),Evaluation_row=int(best.Evaluation_row),
                **dict(zip(spec['names'],map(float,x))),Source='minimum I among already evaluated points meeting new storage filter; NOT a new constrained optimum'))
            write(tables/f'Storage_screen_{year}_{label}_replay.json',{'params':study['_centers'][year],'management':request,'response':r,
                'source_algorithm':best.Algorithm,'source_seed':int(best.Seed),'source_row':int(best.Evaluation_row),'not_new_constrained_optimization':True})
    d=csv(tables/'Terminal_storage_screening.csv',rows)
    fig,ax=plt.subplots(figsize=(6.2,5.0),layout='constrained')
    for j,year in enumerate(YEARS):
        main=chosen[chosen.Year==year].iloc[0]
        screened=d[(d.Year==year)&(d.Screen=='same_baseline_end_storage')].iloc[0]
        ax.bar(j-.24,baselines[year]['Irrigation_mm'],.22,color='#CCD5DB')
        ax.bar(j,main.Irrigation_mm,.22,color=COLORS[year],alpha=.4)
        if pd.notna(screened.Irrigation_mm):ax.bar(j+.24,screened.Irrigation_mm,.22,color=COLORS[year])
    ax.set(xticks=np.arange(4),xticklabels=YEARS,ylabel='季节灌水量（mm）',title='增加季末储水门槛后的事后筛查')
    ax.grid(axis='y',alpha=.16)
    fig.legend(handles=[plt.Rectangle((0,0),1,1,fc='#CCD5DB',label='原DI基准'),plt.Rectangle((0,0),1,1,fc='#0072B2',alpha=.4,label='原双约束主候选'),
        plt.Rectangle((0,0),1,1,fc='#0072B2',label='储水不低于基准的已评估点')],loc='outside upper center',frameon=False,fontsize=11)
    save(fig,figures,'R09_Terminal_storage_screening','季末储水条件对候选解释的影响',
        '深色柱是在原40次搜索的已评估可行点中，追加季末储水不低于原DI基准条件后筛出的最低灌水点，并已回代。这是事后筛查，不是带储水约束重新优化，不证明该约束下全局最优。浅色为原双约束主候选；所有方案仍使用相同初始水分、95%观测产量门槛及灌水上限。','portrait')
    return d


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,default=HERE/'output_real_20261019');p.add_argument('--out',type=Path,default=HERE/'actual_publication_20261019');args=p.parse_args()
    study=load_study();model=RealModel(study);out=args.out;tables=out/'tables';figures=out/'figures'
    status=read(args.run/'EXPERIMENT_STATUS.json')
    if status['status']!='COMPLETE':raise RuntimeError('Only a complete supervised experiment can be published as complete')
    sensitivity=pd.read_csv(args.run/'sobol_final/sobol_indices.csv')
    from phaseB_sobol import rank_checks
    checks=rank_checks(sensitivity,study)
    csv(args.run/'sobol_final/scramble_checks.csv',checks)
    csv(tables/'Sobol_all_seed_indices.csv',sensitivity);csv(tables/'Sobol_numerical_stability.csv',checks)
    means=sensitivity.groupby(['Year','N','Output','Parameter']).agg(ST_mean=('ST','mean'),ST_seed_min=('ST','min'),ST_seed_max=('ST','max'),S1_mean=('S1','mean'),max_ST_CI_halfwidth=('ST_conf','max'),variance_mean=('Variance','mean')).reset_index()
    csv(tables/'Sobol_four_year_summary.csv',means)
    fronts=pd.concat([pd.read_csv(args.run/'optimization'/str(y)/'all_seed_fronts.csv') for y in YEARS],ignore_index=True)
    history=pd.concat([pd.read_csv(args.run/'optimization'/str(y)/'convergence_history.csv') for y in YEARS],ignore_index=True)
    candidates=pd.concat([pd.read_csv(args.run/'optimization'/str(y)/'epsilon_candidates.csv').assign(Year=y) for y in YEARS],ignore_index=True)
    conditional=pd.concat([pd.read_csv(args.run/'optimization'/str(y)/'conditional_validation.csv') for y in YEARS],ignore_index=True)
    chosen=candidates[candidates.Selection=='epsilon_min_irrigation'].copy()
    baselines={y:read(args.run/'baselines'/f'baseline_{y}.json')['response'] for y in YEARS}
    schedules=[];ledger=[];calendar=[]
    for y in YEARS:
        spec=model.management_space(y);c=chosen[chosen.Year==y].iloc[0]
        request=management(spec,[c[n] for n in spec['names']])
        raw,f,g=model.module.simulate(params=study['_centers'][y],year=y,management=request,details=True)
        csv(tables/f'Candidate_{y}_daily_water.csv',f);csv(tables/f'Candidate_{y}_daily_growth.csv',g)
        write(tables/f'Candidate_{y}_complete_response.json',raw)
        annual,data=model.module._load(y)
        calendar.append(dict(Year=y,Planting_date=annual.PLANT.strftime('%Y-%m-%d'),Calendar_cutoff=annual.HARVEST.strftime('%Y-%m-%d'),
            Calendar_days=len(annual.DATES),WP_switch=annual.SWITCH.strftime('%Y-%m-%d'),Irrigation_events=len(data['schedule']),
            Baseline_I_mm=float(data['schedule'].Depth.sum()),
            Actual_used_ETo_mm=float(data['weather'].set_index('Date').loc[annual.DATES,'ReferenceET'].sum()),
            Rain_mm=float(data['weather'].set_index('Date').loc[annual.DATES,'Precipitation'].sum())))
        for j,(date,base) in enumerate(zip(data['schedule'].Date,data['schedule'].Depth)):
            event=raw['irrigation_events'][j]
            schedules.append(dict(Year=y,Date=date.strftime('%Y-%m-%d'),Window=event['stage']+1,
                Baseline_mm=float(base),Candidate_planned_mm=request['events'][j]['mm'],Candidate_actual_mm=event['mm']))
        for scenario,r in [('baseline',baselines[y]),('candidate',raw)]:
            ledger.append(dict(Year=y,Scenario=scenario,**{k:r[k] for k in OUTPUTS+LEDGER}))
    schedule=pd.DataFrame(schedules)
    csv(tables/'Annual_model_calendar.csv',calendar)
    for name,d in [('NSGA_all_seed_Pareto_points',fronts),('NSGA_convergence_history',history),('NSGA_epsilon_candidates',candidates),
        ('NSGA_main_candidates',chosen),('NSGA_conditional_validation',conditional),('NSGA_event_schedules',schedule),('Water_ledger_baseline_and_candidate',ledger)]:csv(tables/(name+'.csv'),d)
    algorithms=pd.concat([pd.read_csv(args.run/'optimization'/str(y)/'algorithm_comparison.csv').assign(Year=y) for y in YEARS],ignore_index=True)
    csv(tables/'NSGA_algorithm_comparison.csv',algorithms)
    sobol_figures(sensitivity,figures,checks)
    optimize_figures(fronts,history,chosen,baselines,schedule,conditional,figures)
    context_figures(model,figures)
    ledger_frame=pd.DataFrame(ledger);decomposition=[]
    for y in YEARS:
        a=ledger_frame[(ledger_frame.Year==y)&(ledger_frame.Scenario=='baseline')].iloc[0]
        b=ledger_frame[(ledger_frame.Year==y)&(ledger_frame.Scenario=='candidate')].iloc[0]
        et=a.ET_mm-b.ET_mm
        soil=(a.Profile_final_mm-a.Profile_initial_mm)-(b.Profile_final_mm-b.Profile_initial_mm)
        surface=(a.Surface_final_mm-a.Surface_initial_mm)-(b.Surface_final_mm-b.Surface_initial_mm)
        losses=sum(a[k]-b[k] for k in ['DeepPerc_mm','Runoff_mm','TileDrain_mm'])
        inflow=-(a.CR_mm-b.CR_mm+a.GwIn_mm-b.GwIn_mm+a.Rain_mm-b.Rain_mm)
        saved=a.Irrigation_mm-b.Irrigation_mm
        if not np.isclose(et+soil+surface+losses+inflow,saved,atol=1e-5):raise ValueError('Saving decomposition does not close')
        decomposition.append(dict(Year=y,Irrigation_saving_mm=saved,ET_reduction_mm=et,Reduced_soil_storage_gain_mm=soil,
            Reduced_surface_storage_gain_mm=surface,Loss_reduction_mm=losses,External_inflow_adjustment_mm=inflow,
            Baseline_final_soil_mm=a.Profile_final_mm,Candidate_final_soil_mm=b.Profile_final_mm,
            Interpretation='lower end-of-season soil storage can supply apparent irrigation savings; no terminal storage constraint was imposed'))
    decomp=csv(tables/'Irrigation_saving_decomposition.csv',decomposition)
    fig,ax=plt.subplots(figsize=(6.2,5.0),layout='constrained');pos=np.zeros(4);neg=np.zeros(4)
    for column,label,color in [('ET_reduction_mm','耗水减少','#2878B5'),('Reduced_soil_storage_gain_mm','季末土壤储水减少','#D58A2C'),
        ('Loss_reduction_mm','排水/径流减少','#2F8A68'),('Reduced_surface_storage_gain_mm','地表储水变化','#8A63A4'),
        ('External_inflow_adjustment_mm','其他入水差额','#9AA8B0')]:
        values=decomp[column].to_numpy()
        if np.max(abs(values))<1e-8:continue
        bottom=np.where(values>=0,pos,neg)
        ax.bar(np.arange(4),values,.62,bottom=bottom,color=color,label=label)
        pos+=np.maximum(values,0);neg+=np.minimum(values,0)
    ax.scatter(np.arange(4),decomp.Irrigation_saving_mm,c='#253E4B',marker='D',s=36,zorder=5,label='灌水减少合计')
    ax.axhline(0,c='#89979F',lw=.7);ax.set(xticks=np.arange(4),xticklabels=YEARS,ylabel='水量差额（mm）',title='灌水减少量来自哪里？')
    ax.grid(axis='y',alpha=.16);fig.legend(loc='outside upper center',ncol=2,fontsize=11,frameon=False)
    save(fig,figures,'R08_Water_saving_decomposition','灌水减少与耗水、季末储水的区别',
        '按完整水量账分解I基准−I候选：耗水减少、排水/径流减少、季末储水增量减少和其他差额之和等于灌水减少量。模型未约束候选季末储水不低于基准；因此灌水节省不能全部解释为耗水效率提升或长期可持续节水。','portrait')
    storage_screening(model,study,args.run,chosen,baselines,tables,figures)
    write(out/'FIGURE_REGISTRY.json',{'years':YEARS,'palette':COLORS,'figures':REGISTRY})
    write(out/'PUBLICATION_PROVENANCE.json',{'engine':model.identity,'experiment_status':status,'all_figures_real_model':True,
        'MCMC_unchanged':True,'figure_count':len(REGISTRY),'sobol_outputs':OUTPUTS,'warning':'Any remaining numerical-stability failures must be reported; no forced ranking'})
    print('Published',len(REGISTRY),'figure pairs',flush=True)


if __name__=='__main__':main()
