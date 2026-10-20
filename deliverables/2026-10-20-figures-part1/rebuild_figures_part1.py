"""Rebuild English figure 10 and two vector workflow layout alternatives.

No calibration or optimization is rerun. Existing annual weather inputs are
exported on the exact calendar used by the current Figure 10.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch,Rectangle,FancyArrowPatch,Patch
from matplotlib.lines import Line2D

OUT=Path(__file__).resolve().parent
PROJECT=OUT.parents[1]/'DI_PHASE3_NEXTGEN_UPDATED'
YEARS=[2019,2020,2021,2022]
COLORS={2019:'#0072B2',2020:'#D55E00',2021:'#009E73',2022:'#A85AA0'}
INK='#243746';LINE='#78909D'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':11,
    'axes.labelsize':10,'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':9,
    'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,
    'svg.fonttype':'none','hatch.linewidth':.35,'savefig.facecolor':'white'})
TEXT_BOXES=[]


def save(fig,name):
    for suffix in ['png','pdf','svg']:
        fig.savefig(OUT/f'{name}.{suffix}',dpi=600,facecolor='white')
    plt.close(fig)


def node(ax,xy,w,h,title,lines,face='#F7F9FA',title_size=9.4,body_size=8.3):
    x,y=xy
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.006,rounding_size=.008',
        lw=.8,edgecolor='#AAB9C2',facecolor=face,zorder=3))
    ax.text(x+w/2,y+h-.031,title,ha='center',va='center',fontsize=title_size,fontweight='bold',color=INK,zorder=4)
    ax.text(x+w/2,y+h*.39,'\n'.join(lines),ha='center',va='center',fontsize=body_size,
        color=INK,linespacing=1.45,zorder=4)
    TEXT_BOXES.append((title,xy,w,h))


def arrow(ax,points,dashed=False,color=LINE):
    style=(0,(4,3)) if dashed else '-'
    for p,q in zip(points[:-2],points[1:-1]):
        ax.plot([p[0],q[0]],[p[1],q[1]],c=color,lw=.95,ls=style,zorder=2)
    ax.add_patch(FancyArrowPatch(points[-2],points[-1],arrowstyle='-|>',mutation_scale=9,
        lw=.95,ls=style,color=color,zorder=2))


def header(ax,x,w,number,title,hatch,face):
    ax.add_patch(Rectangle((x,.905),w,.065,facecolor=face,edgecolor='#BCC8CE',lw=.6,zorder=1))
    ax.add_patch(Rectangle((x,.905),.031,.065,facecolor='none',edgecolor='#AEBFC8',lw=0,hatch=hatch,zorder=2))
    ax.text(x+.044,.937,f'{number}. {title}',va='center',ha='left',fontweight='bold',fontsize=9.5,linespacing=1.1,color=INK)


def three_column():
    fig,ax=plt.subplots(figsize=(7.2,5.7));fig.subplots_adjust(0,0,1,1)
    ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    xs=[.025,.365,.705];w=.27;ys=[.705,.445,.185];h=.16
    header(ax,xs[0],w,'1','Data inputs','///','#EDF3F6')
    header(ax,xs[1],w,'2','Model &\ncalibration','...','#F0F4F2')
    header(ax,xs[2],w,'3','Analysis &\nevaluation','xx','#F5F1F6')
    node(ax,(xs[0],ys[0]),w,h,'Meteorological drivers',['Temperature, ET0 and rain','2019, 2020, 2021 and 2022'])
    node(ax,(xs[0],ys[1]),w,h,'Soil & management',['Soil and initial water profile','Original irrigation events'])
    node(ax,(xs[0],ys[2]),w,h,'Calibration targets',['Canopy/Tr/Es targets (stage 1)','Biomass/yield targets (stage 2)'])
    node(ax,(xs[1],ys[0]),w,h,'Annual DI crop model',['Input audit and baseline replay','Common model for both analyses'])
    node(ax,(xs[1],ys[1]),w,h,'Stage 1 MCMC',['CC, Tr and Es targets','5 parameters; frozen samples'])
    node(ax,(xs[1],ys[2]),w,h,'Stage 2 MCMC',['Early/late WP and HI0','Conditional on stage 1 center'])
    node(ax,(xs[2],ys[0]),w,h,'Sobol sensitivity',['Independent common ranges','First-order and total effects'])
    node(ax,(xs[2],ys[1]),w,h,'NSGA-III optimization',['Fixed yearly parameter centers','Yield and irrigation objectives','Same-budget NSGA-II benchmark'],body_size=8.1)
    node(ax,(xs[2],ys[2]),w,h,'Candidate evaluation',['Yield, irrigation and ET','Stage-specific perturbations','End-of-season soil storage'],body_size=8.1)
    arrow(ax,[(.295,.785),(.365,.785)])
    arrow(ax,[(.295,.525),(.325,.525),(.325,.745),(.365,.745)])
    arrow(ax,[(.295,.265),(.335,.265),(.335,.485),(.365,.485)])
    arrow(ax,[(.335,.265),(.365,.265)])
    arrow(ax,[(.50,.705),(.50,.605)])
    arrow(ax,[(.50,.445),(.50,.345)])
    arrow(ax,[(.635,.785),(.705,.785)])
    # Yearly frozen centers feed the optimizer; Sobol does not filter parameters.
    arrow(ax,[(.635,.565),(.705,.565)],dashed=True)
    arrow(ax,[(.635,.285),(.662,.285),(.662,.525),(.705,.525)],dashed=True)
    # Stage-specific frozen samples separately feed candidate checking.
    arrow(ax,[(.635,.485),(.679,.485),(.679,.265),(.705,.265)],dashed=True)
    arrow(ax,[(.635,.225),(.705,.225)],dashed=True)
    arrow(ax,[(.84,.445),(.84,.345)])
    ax.plot([.045,.095],[.103,.103],color=LINE,lw=1)
    ax.text(.107,.103,'Model/data flow',va='center',fontsize=8.4,color=INK)
    ax.plot([.45,.50],[.103,.103],color=LINE,lw=1,ls=(0,(4,3)))
    ax.text(.512,.103,'Frozen centers or stage-specific samples',va='center',fontsize=8.4,color=INK)
    ax.text(.5,.042,'Sensitivity and optimization use the same annual model, with separately defined inputs.',
        ha='center',fontsize=8.3,color='#536979')
    save(fig,'Figure1_three_column_EN')


def tree():
    fig,ax=plt.subplots(figsize=(7.2,5.9));fig.subplots_adjust(0,0,1,1)
    ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    node(ax,(.20,.85),.60,.12,'Four-year data and annual DI crop models',
        ['Weather, soil, management and calibration observations','Input checks and baseline replay'],body_size=9,title_size=10.1)
    node(ax,(.035,.61),.43,.15,'Sobol sensitivity analysis',
        ['8 independent uniform parameter inputs','N = 512; 3 scrambles; six model outputs'],face='#EDF3F6',body_size=9)
    node(ax,(.535,.61),.43,.15,'Two-stage MCMC calibration',
        ['Frozen stage-specific samples and yearly centers','Conditional stage 2 inference'],face='#F0F4F2',body_size=9)
    node(ax,(.035,.355),.43,.15,'Sensitivity interpretation',
        ['First-order and total-effect indices','Intervals and ranking stability'],face='#EDF3F6',body_size=9)
    node(ax,(.535,.355),.43,.15,'Irrigation optimization',
        ['NSGA-III; same-budget NSGA-II benchmark','Fixed yearly centers; four irrigation windows'],face='#F5F1F6',body_size=9)
    node(ax,(.15,.105),.70,.15,'Integrated interpretation and candidate evaluation',
        ['Yield–irrigation trade-offs; stage-wise conditional perturbations',
         'Seasonal water balance and terminal soil water storage'],body_size=9,title_size=10)
    arrow(ax,[(.5,.85),(.5,.81),(.25,.81),(.25,.76)])
    arrow(ax,[(.5,.81),(.75,.81),(.75,.76)])
    arrow(ax,[(.25,.61),(.25,.505)])
    arrow(ax,[(.75,.61),(.75,.505)],dashed=True)
    arrow(ax,[(.25,.355),(.25,.30),(.42,.30),(.42,.255)])
    arrow(ax,[(.75,.355),(.75,.30),(.58,.30),(.58,.255)])
    arrow(ax,[(.965,.685),(.985,.685),(.985,.18),(.85,.18)],dashed=True)
    for x,y,pattern in [(.035,.61,'///'),(.535,.61,'...'),(.535,.355,'xx')]:
        ax.add_patch(Rectangle((x-.003,y+.006),.016,.138,facecolor='none',edgecolor='#AEBFC8',lw=0,hatch=pattern,zorder=4))
    ax.text(.5,.045,'Solid arrows: model/data flow. Dashed arrows: frozen centers or stage-specific samples.',
        ha='center',fontsize=8.3,color='#536979')
    save(fig,'Figure1_tree_EN')


def weather():
    data_path=OUT/'Figure10_daily_environment.csv'
    if not data_path.exists():
        sys.path.insert(0,str(PROJECT))
        from real_model.four_year_adapter import _load
        all_years=[]
        for year in YEARS:
            source,data=_load(year)
            w=data['weather'].set_index('Date').loc[source.DATES]
            assert w.index.is_unique and len(w)==len(source.DATES)
            all_years.append(pd.DataFrame({'Year':year,'Date':w.index,
                'Reference_ET0_mm_d':w.ReferenceET.to_numpy(),
                'Precipitation_mm':w.Precipitation.to_numpy()}))
        daily=pd.concat(all_years,ignore_index=True)
        daily.to_csv(data_path,index=False,float_format='%.17g')
    daily=pd.read_csv(data_path,parse_dates=['Date'],float_precision='round_trip')
    assert sorted(daily.Year.unique())==YEARS
    assert np.isfinite(daily[['Reference_ET0_mm_d','Precipitation_mm']].to_numpy()).all()
    assert (daily[['Reference_ET0_mm_d','Precipitation_mm']]>=0).all().all()
    fig,axes=plt.subplots(2,2,figsize=(7.2,4.95),layout='constrained')
    summary=[]
    for i,(ax,year) in enumerate(zip(axes.flat,YEARS)):
        w=daily[daily.Year==year]
        twin=ax.twinx()
        twin.bar(w.Date,w.Precipitation_mm,width=1,color='#C4CDD3',alpha=.85,zorder=1)
        twin.set_ylim(0,60);twin.set_yticks([0,20,40,60])
        twin.spines['top'].set_visible(False)
        twin.tick_params(axis='y',colors='#657682',labelsize=9,length=3)
        ax.set_zorder(twin.get_zorder()+1);ax.patch.set_visible(False)
        ax.plot(w.Date,w.Reference_ET0_mm_d,color=COLORS[year],lw=1.05,zorder=3)
        ax.set(title=f'({chr(97+i)}) {year}',ylim=(0,11),yticks=[0,2,4,6,8,10])
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.tick_params(axis='both',length=3,pad=3)
        ax.grid(axis='y',alpha=.18,lw=.5)
        if i%2==0:
            twin.tick_params(labelright=False)
        else:
            ax.tick_params(labelleft=False)
            twin.set_ylabel('Precipitation (mm)',color='#657682',fontsize=10)
        if i>=2:ax.set_xlabel('Date (MM–DD)')
        summary.append({'Year':year,'Window_start':w.Date.min().date().isoformat(),
            'Window_end':w.Date.max().date().isoformat(),'Days':len(w),
            'Reference_ET0_sum_mm':w.Reference_ET0_mm_d.sum(),
            'Reference_ET0_mean_mm_d':w.Reference_ET0_mm_d.mean(),
            'Precipitation_sum_mm':w.Precipitation_mm.sum()})
    fig.supylabel(r'Reference evapotranspiration, $ET_0$ (mm d$^{-1}$)',fontsize=10)
    fig.legend(handles=[Line2D([],[],color='#536979',lw=1.2,label=r'Reference evapotranspiration ($ET_0$)'),
        Patch(facecolor='#C4CDD3',label='Precipitation')],loc='outside upper center',ncol=2,frameon=False)
    save(fig,'Figure10_environment_EN')
    pd.DataFrame(summary).to_csv(OUT/'Figure10_window_summary.csv',index=False)
    provenance={'years':YEARS,'data_source':'exact weather/date selection used by current publish_actual_results.context_figures',
        'all_original_daily_values_preserved':True,'smoothing_or_annual_scaling_applied':False,
        'same_axis_limits_all_panels':{'ET0_mm_d':[0,11],'precipitation_mm':[0,60]},
        'original_model_sources_changed':False,'MCMC_or_optimization_rerun':False,
        'data_sha256':hashlib.sha256(data_path.read_bytes()).hexdigest(),
        'summary':summary,'source_figure':'DI_PHASE3_NEXTGEN_UPDATED/four_year_figures/F10_climate.png',
        'english_labels':{'参考蒸散 ETo（mm/d）':'Reference evapotranspiration, ET0 (mm d−1)',
            '降水（mm）':'Precipitation (mm)','日期':'Date (MM–DD)'},
        'recommended_print_width_mm':183,'figure10_source_fonts_pt':{'ticks':9,'axis':10,'titles':11},
        'export':{'PNG_dpi':600,'PDF':'vector text and marks','SVG':'editable text'}}
    (OUT/'FIGURE_PROVENANCE.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2))


if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    three_column();tree();weather()
    print('Built two Figure 1 layouts and English Figure 10; daily inputs exported unchanged.')
