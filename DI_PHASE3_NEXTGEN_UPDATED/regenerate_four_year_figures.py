"""Rebuild the current scientific figures with four-year coverage and one style."""
from pathlib import Path
import hashlib,json,shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Patch,FancyBboxPatch

import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parent)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
PROJECT=args.project.resolve();ROOT=args.out.resolve();ROOT.mkdir(parents=True,exist_ok=True)
ART=ROOT;T=ROOT/'tables';F=ROOT/'figures';F.mkdir(exist_ok=True)
shutil.copytree(PROJECT/'figure_source_tables',T,dirs_exist_ok=True)
YEARS=[2019,2020,2021,2022]
COLORS={2019:'#0072B2',2020:'#D55E00',2021:'#009E73',2022:'#A85AA0'}
INK='#293844';GRAY='#7B8792';GRID='#E6EBEF'
NAMES=['CCx','CGC_CD','CDC_CD','SenescenceCD','Kcb','WP_early','WP_late','HI0']
TITLES={'CCx':'CCx（比例）','CGC_CD':'CGC（日⁻¹）','CDC_CD':'CDC（日⁻¹）',
        'SenescenceCD':'衰老起始（日历日）','Kcb':'Kcb（无量纲）',
        'WP_early':'WP early（g/m²）','WP_late':'WP late（g/m²）','HI0':'HI0（比例）'}
font=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
if font.is_file():
 font_manager.fontManager.addfont(str(font));family=font_manager.FontProperties(fname=str(font)).get_name()
else:
 available={entry.name for entry in font_manager.fontManager.ttflist}
 family=next((name for name in ['Microsoft YaHei','SimHei','Noto Sans CJK SC'] if name in available),'DejaVu Sans')
plt.rcParams.update({'font.family':[family,'DejaVu Sans'],
 'font.size':12,'axes.titlesize':13,'axes.labelsize':12,'xtick.labelsize':11,'ytick.labelsize':11,
 'legend.fontsize':11,'legend.frameon':False,'axes.spines.top':False,'axes.spines.right':False,
 'axes.linewidth':.7,'axes.edgecolor':'#84919B','axes.labelcolor':INK,'text.color':INK,
 'xtick.color':INK,'ytick.color':INK,'grid.color':GRID,'grid.linewidth':.7,
 'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white',
 'axes.unicode_minus':False,'pdf.fonttype':42,'ps.fonttype':42})
caps=[];cases={};metrics=[]
def frame(name):return pd.read_csv(T/(name+'.csv'))
def normalized_pairs(p,kind):
 d=pd.read_csv(p,float_precision='round_trip',parse_dates=['Date'])
 if 'Included' in d:d=d[d.Included.astype(str).str.lower().eq('true')].copy()
 mapping=({'Observed_CC':'CC_observed','canopy_cover':'CC_simulated'} if kind=='CC'
          else {'Observed_B_t_ha':'B_observed_t_ha','Biomass_t_ha':'B_simulated_t_ha'})
 return d.rename(columns={k:v for k,v in mapping.items() if v not in d})
for year in YEARS:
 src=PROJECT/'frozen_inputs/year_outputs'/str(year)
 growth=pd.read_csv(src/'Daily_growth.csv',parse_dates=['Date'],float_precision='round_trip')
 cc=normalized_pairs(src/'CC_pairs.csv','CC');bio=normalized_pairs(src/'Biomass_pairs.csv','Biomass')
 assert set(growth.Date.dt.year)=={year} and growth.Date.is_unique
 for kind,d,oc,sc,gc in [('CC',cc,'CC_observed','CC_simulated','canopy_cover'),('Biomass',bio,'B_observed_t_ha','B_simulated_t_ha','Biomass_t_ha')]:
  observed=d[oc].to_numpy();pred=d[sc].to_numpy()
  np.testing.assert_allclose(pred,growth.set_index('Date').loc[d.Date,gc],atol=1e-10,rtol=0)
  metrics.append(dict(Year=year,Variable=kind,N=len(d),R2=1-np.sum((pred-observed)**2)/np.sum((observed-observed.mean())**2),
                      RMSE=np.sqrt(np.mean((pred-observed)**2)),MAE=np.mean(abs(pred-observed)),Bias=np.mean(pred-observed)))
 cases[year]=dict(growth=growth,CC=cc,Biomass=bio)
 dest=ART/'four_year_source_data'/str(year);dest.mkdir(parents=True,exist_ok=True)
 for base in ['Daily_growth.csv','CC_pairs.csv','Biomass_pairs.csv','summary.json']:
  shutil.copyfile(src/base,dest/base)
metrics=pd.DataFrame(metrics);metrics.to_csv(T/'calibration_metrics_recomputed.csv',index=False,encoding='utf-8-sig')
cal=frame('calibration_evidence_tiers')
for year in YEARS:
 for kind,prefix in [('CC','CC'),('Biomass','生物量')]:
  row=metrics[(metrics.Year==year)&(metrics.Variable==kind)].iloc[0]
  cal.loc[cal['年份']==year,prefix+'_R2']=row.R2;cal.loc[cal['年份']==year,prefix+'_RMSE']=row.RMSE
  cal.loc[cal['年份']==year,prefix+'样本数']=int(row.N)
 cal.loc[cal['年份']==year,'证据']='原配对表逐点复算；2022另有本次原模型回放'
for name in ['calibration_evidence_tiers','paper_calibration_table']:cal.to_csv(T/(name+'.csv'),index=False,encoding='utf-8-sig')

def panel_grid(height=6.6):
 fig,axes=plt.subplots(2,2,figsize=(9.8,height),layout='constrained')
 for ax,year in zip(axes.flat,YEARS):
  ax.set_title(str(year),loc='left',color=COLORS[year],fontweight='bold');ax.grid(alpha=.75);ax.set_axisbelow(True)
 return fig,axes

def save(fig,name,title,note,years=YEARS,role='current_four_year_evidence'):
 if fig.legends:
  rows=2 if max(len(legend.get_texts()) for legend in fig.legends)>4 else 1
  fig.set_layout_engine('constrained',rect=(0,0,1,1-(.72 if rows==2 else .5)/fig.get_figheight()))
 fig.suptitle(title,fontsize=15,fontweight='bold',y=1.085 if fig.legends else 1.04,color=INK)
 fig.text(.015,-.025,note,fontsize=10.5,color='#586874',va='top')
 fig.canvas.draw()
 texts=[t for t in fig.findobj(matplotlib.text.Text) if t.get_visible() and t.get_text()]
 sizes=[float(t.get_fontsize()) for t in texts]
 assert min(sizes)>=10.49,(name,min(sizes))
 for ext in ['png','pdf']:fig.savefig(F/(name+'.'+ext),dpi=300,bbox_inches='tight',pad_inches=.15)
 caps.append(dict(file=name+'.png',title=title,caption=note,years=list(years),role=role,
                  min_font_pt=min(sizes),year_colors={str(y):COLORS[y] for y in YEARS},
                  width_inches=fig.get_figwidth(),height_inches=fig.get_figheight()))
 plt.close(fig)

def flow():
 fig,ax=plt.subplots(figsize=(10,4.2),layout='constrained');ax.axis('off');ax.set(xlim=(0,10),ylim=(0,4.5))
 specs=[(.1,2.15,3.0,1.8,'四年冻结校准输入','2019 · 2020 · 2021 · 2022\n8 个参数组、32 个中心值\n观测—模拟配对均已核对',COLORS[2019]),
        (3.5,2.15,3.0,1.8,'图表与基准复现','四年比较统一版式\n2022 原模型与 data 已齐\n预审与均值点回放通过',COLORS[2022]),
        (6.9,2.15,3.0,1.8,'后续正式计算','独立范围 Sobol 响应\n固定中心的双目标优化\n候选真实回代与条件扰动',COLORS[2021])]
 for x,y,w,h,head,body,c in specs:
  ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.06',fc=c+'0D',ec=c,lw=1.1))
  ax.text(x+.12,y+h-.2,head,va='top',fontsize=13,color=c,fontweight='bold')
  ax.text(x+.12,y+h-.7,body,va='top',fontsize=11.5,linespacing=1.6)
 for x in [3.15,6.55]:ax.annotate('',xy=(x+.3,3),xytext=(x,3),arrowprops=dict(arrowstyle='->',color=GRAY,lw=1.3))
 ax.text(.15,1.2,'当前数据状态：2022 已补齐；MCMC 保持冻结。',fontsize=12.5,color=INK)
 ax.text(.15,.55,'执行边界：2019—2021 原模型尚待接入；完整 Sobol / 优化实验未完成。',fontsize=11.5,color=GRAY)
 save(fig,'F01_workflow','研究路线与当前数据状态','图中状态对应本轮核验；完整敏感性和优化数值不由历史代理图替代。')

def calibration_series(kind):
 fig,axes=panel_grid(6.8)
 oc,sc,gc,unit=('CC_observed','CC_simulated','canopy_cover','冠层覆盖度（比例）') if kind=='CC' else ('B_observed_t_ha','B_simulated_t_ha','Biomass_t_ha','地上干生物量（t/ha）')
 for ax,year in zip(axes.flat,YEARS):
  g=cases[year]['growth'];d=cases[year][kind];start=g.Date.min();m=metrics[(metrics.Year==year)&(metrics.Variable==kind)].iloc[0]
  ax.plot((g.Date-start).dt.days,g[gc],c=COLORS[year],lw=2.1)
  ax.scatter((d.Date-start).dt.days,d[oc],s=33,fc='white',ec=COLORS[year],lw=1.3,zorder=4)
  ax.set(xlim=(0,155),ylim=(0,1.06 if kind=='CC' else 40),xlabel='播后天数（d）',ylabel=unit)
  ax.text(.97,.08,f'R² {m.R2:.3f}  ·  RMSE {m.RMSE:.3f}',ha='right',transform=ax.transAxes,fontsize=11,
          bbox=dict(fc='white',ec='none',alpha=.9))
 handles=[Line2D([0],[0],c=GRAY,lw=2,label='模型日序列'),Line2D([0],[0],marker='o',ls='',mfc='white',mec=GRAY,label='校准观测')]
 fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.59,1.005),ncol=2)
 save(fig,'F02_CC_trajectories' if kind=='CC' else 'F03_Biomass_trajectories',
      '四年冠层覆盖度：模拟过程与校准观测' if kind=='CC' else '四年生物量：模拟过程与校准观测',
      '2019—2021 来自已核验原输出；2022 为本次冻结均值点回放。样本内校准评价。')

def scatters(kind):
 fig,axes=panel_grid(7.4)
 oc,sc=('CC_observed','CC_simulated') if kind=='CC' else ('B_observed_t_ha','B_simulated_t_ha')
 high=1.04 if kind=='CC' else 40
 for ax,year in zip(axes.flat,YEARS):
  d=cases[year][kind];m=metrics[(metrics.Year==year)&(metrics.Variable==kind)].iloc[0]
  ax.plot([0,high],[0,high],c='#9DA8B0',ls='--',lw=1.2)
  ax.scatter(d[oc],d[sc],c=COLORS[year],s=40,ec='white',lw=.7,zorder=4)
  ax.set(xlim=(0,high),ylim=(0,high),xlabel='校准观测'+('（比例）' if kind=='CC' else '（t/ha）'),ylabel='模型输出'+('（比例）' if kind=='CC' else '（t/ha）'))
  ax.text(.04,.94,f'n = {int(m.N)}\nR² = {m.R2:.3f}\nRMSE = {m.RMSE:.3f}',transform=ax.transAxes,va='top',fontsize=11,
          bbox=dict(boxstyle='round,pad=.35',fc='#F4F7F9',ec='none'));ax.set_aspect('equal',adjustable='box')
 save(fig,'F04_CC_pairs' if kind=='CC' else 'F05_Biomass_pairs',
      '四年冠层覆盖度：观测—模拟配对' if kind=='CC' else '四年生物量：观测—模拟配对',
      '虚线为 1:1；R² = 1 − SSE / SST。四年均由配对表计算，不是独立验证。')

def calibration_summary():
 fig,axes=plt.subplots(1,3,figsize=(10.3,3.6),layout='constrained')
 for ax,key,title,unit in zip(axes,['CC_RMSE','生物量_RMSE','产量误差_pct'],['冠层误差','生物量误差','产量相对观测偏差'],['RMSE（比例）','RMSE（t/ha）','偏差（%）']):
  for i,year in enumerate(YEARS):
   value=float(cal.loc[cal['年份']==year,key].iloc[0]);ax.scatter(i,value,c=COLORS[year],s=60,zorder=4)
  ax.set(xticks=range(4),xticklabels=YEARS,title=title,ylabel=unit,xlim=(-.5,3.5));ax.grid(axis='y');ax.set_axisbelow(True)
  if key=='产量误差_pct':
   ax.axhline(0,c=GRAY,lw=.8);ax.axhspan(-5,5,color='#EEF3F5',zorder=0);ax.set_ylim(-6,6)
 save(fig,'F06_calibration_summary','四年校准误差概览','灰带为项目 ±5% 产量容许幅度，不是置信区间。2022 配对指标与产量已核验。')

def intervals():
 d=frame('parameter_intervals_verified');fig,axes=plt.subplots(4,2,figsize=(9.8,10.6),layout='constrained')
 for ax,k in zip(axes.flat,NAMES):
  for year in YEARS:
   r=d[(d.Year==year)&(d.Parameter==k)].iloc[0]
   ax.errorbar(YEARS.index(year),r.Median,yerr=[[r.Median-r.P025],[r.P975-r.Median]],fmt='o',ms=5.5,
               color=COLORS[year],capsize=3,lw=1.8)
  ax.set(title=TITLES[k],xticks=range(4),xticklabels=YEARS,xlim=(-.4,3.4));ax.grid(axis='y');ax.set_axisbelow(True)
 save(fig,'F07_parameter_intervals','四年八参数的条件分布区间','点为中位数，线为 2.5%—97.5% 保留样本分位；分阶段结果不构成八维联合后验。')

def correlations():
 with np.load(PROJECT/'frozen_inputs/verified_phase_specific_draws.npz') as z:draws={y:z[f'p2_{y}'] for y in YEARS}
 fig,axes=panel_grid(6.6)
 for ax,year in zip(axes.flat,YEARS):
  x=draws[year];ids=np.linspace(0,len(x)-1,1800,dtype=int)
  ax.scatter(x[ids,2],x[ids,1],s=5,c=COLORS[year],alpha=.12,rasterized=True,edgecolors='none')
  ax.set(xlabel='HI0（比例）',ylabel='WP late（g/m²）')
  ax.text(.97,.93,f'r = {np.corrcoef(x[:,2],x[:,1])[0,1]:.3f}',transform=ax.transAxes,ha='right',fontsize=11.5)
 save(fig,'F08_phase2_compensation','四年第二阶段参数补偿','各年均按同一行保留样本绘制；相关系数使用全部样本，散点仅作等距抽稀展示。')

def water():
 d=frame('water_balance_recomputed');d=d[d.Scenario=='DI'].set_index('Year')
 fig,axes=panel_grid(6.7)
 components=[('灌溉','#5A8CA8'),('降水','#A2C6D5'),('储水消耗','#D7BA8A'),('ET','#6F9D86'),('径流/排水','#A9B2B9'),('储水增加','#ABA4C6')]
 for ax,year in zip(axes.flat,YEARS):
  r=d.loc[year];s=float(r.Storage_gain_mm)
  parts=[[r.Irrigation_mm,r.Rain_mm,max(-s,0)],[r.ET_mm,r.Runoff_mm+r.DeepPerc_mm+r.TileDrain_mm,max(s,0)]]
  for x,vals,offset in [(0,parts[0],0),(1,parts[1],3)]:
   bottom=0
   for j,v in enumerate(vals):ax.bar(x,v,.52,bottom=bottom,color=components[offset+j][1]);bottom+=v
  ax.set(xticks=[0,1],xticklabels=['入流及储水消耗','出流及储水增加'],ylabel='季节水量（mm）',ylim=(0,910),xlim=(-.7,1.7));ax.grid(axis='y')
  ax.text(.5,.93,f'ΔS = {s:+.1f} mm',transform=ax.transAxes,ha='center',fontsize=11.5)
 fig.legend(handles=[Patch(fc=c,label=t) for t,c in components],loc='upper center',bbox_to_anchor=(.55,1.005),ncol=3,fontsize=10.5)
 save(fig,'F09_water_ledger','四年 DI 季节水量账','入流/出流柱均包含储水变化；原模型水量账闭合。2022 已由本次原模型回放复现。')

def climate_and_roles():
 inputs=PROJECT/'frozen_inputs/inputs';clim=frame('climate_audit').set_index('Year')
 fig,axes=panel_grid(6.8)
 for ax,year in zip(axes.flat,YEARS):
  w=pd.read_csv(inputs/f'DI_Climate_{year}_FINAL.csv');date='Date' if 'Date' in w else 'date';w[date]=pd.to_datetime(w[date])
  a=cases[year]['growth'].Date.min();b=cases[year]['growth'].Date.max();w=w[w[date].between(a,b)].copy();days=(w[date]-a).dt.days
  p='Precip_mm' if 'Precip_mm' in w else 'Precipitation';e='ETo_mm' if 'ETo_mm' in w else 'ReferenceET'
  if year==2022:
   eto=pd.read_csv(PROJECT/'real_model/model_2022/data/inputs/ETO_FILE_DI_2022_ETo_Geometry_Daily.csv',parse_dates=['Date'])
   w[e]=w[date].map(eto.set_index('Date').ETo_B_mm)
  assert np.isfinite(w[[p,e]].to_numpy()).all()
  ax.bar(days,w[p],color='#C7D3DB',width=1);ax.plot(days,w[e],c=COLORS[year],lw=1.6)
  ax.set(xlabel='播后天数（d）',ylabel='日水量（mm）',xlim=(0,155));ax.grid(axis='y')
 fig.legend(handles=[Patch(fc='#C7D3DB',label='日降水'),Line2D([0],[0],c=GRAY,label='参考蒸散 ETo')],loc='upper center',bbox_to_anchor=(.59,1.005),ncol=2)
 save(fig,'F10_climate','四年生长季气象驱动','2022 ETo 使用已补齐的冻结 B 组数据；其余年份沿用原气象文件，不进行缺日插值。')
 field=pd.read_csv(inputs/'DI_2019_2022_FIELD_LAI_CC_LOCKED.csv',parse_dates=['Date'])
 fig,axes=panel_grid(6.8)
 for ax,year in zip(axes.flat,YEARS):
  start=cases[year]['growth'].Date.min();end=cases[year]['growth'].Date.max();d=field[field.Year==year]
  rs=pd.read_csv(inputs/f'Maize-{year}-RS_NDVI.csv');dc='date' if 'date' in rs else 'Date';rs[dc]=pd.to_datetime(rs[dc]);rs=rs[rs[dc].between(start,end)]
  ax.plot((d.Date-start).dt.days,d.Field_CC,'o-',c=COLORS[year],ms=4,lw=1.6)
  ax.plot((rs[dc]-start).dt.days,rs.CCquad/100,'s--',c='#A0AAB2',ms=3.5,lw=1.3)
  ax.set(xlim=(0,155),ylim=(0,1.05),xlabel='播后天数（d）',ylabel='冠层覆盖度（比例）');ax.grid(axis='y')
 fig.legend(handles=[Line2D([0],[0],c=GRAY,marker='o',label='DI：LAI 转换的 CC'),Line2D([0],[0],c='#A0AAB2',ls='--',marker='s',label='遥感辅助时序')],loc='upper center',bbox_to_anchor=(.6,1.005),ncol=2)
 save(fig,'F11_CC_evidence_roles','四年冠层资料的证据角色','LAI 转换值用于校准；遥感未进入似然，2019—2021 处理为 BI、2022 标签不全，均不称 DI 独立验证。')

def sampling():
 d=frame('sampling_group_summary');fig,axes=plt.subplots(1,2,figsize=(10,3.8),layout='constrained')
 for phase,marker,col in [(1,'o','#527C96'),(2,'s','#9B879D')]:
  s=d[d.Phase==phase].sort_values('Year')
  axes[0].plot(range(4),s.Retained_steps_per_walker,marker+'-',c=col,lw=1.7,label=f'阶段 {phase}')
  axes[1].plot(range(4),s.Steps_over_group_tau,marker+'-',c=col,lw=1.7,label=f'阶段 {phase}')
 axes[0].set(ylabel='每 walker 保留步数',ylim=(1500,1900),title='统一截断后的链长')
 axes[1].axhline(50,c=GRAY,ls='--',lw=1.1);axes[1].set(ylabel='总步数 / 最大 τ',title='链长参考',ylim=(15,75))
 for ax in axes:ax.set(xticks=range(4),xticklabels=YEARS,xlim=(-.2,3.2));ax.grid(axis='y');ax.legend(loc='lower right',fontsize=10.5)
 save(fig,'F12_sampling_record','四年两个阶段的冻结链记录','阶段一各 4 个 ensemble，阶段二各 1 个；50τ 仅为长度参考，不等于已认证收敛。')

def headroom():
 d=frame('observed_yield_gate_headroom');fig,axes=plt.subplots(1,2,figsize=(10,4.1),layout='constrained',width_ratios=[1.35,1])
 for i,r in enumerate(d.sort_values('Year').itertuples()):
  year=int(r.Year);color=COLORS[year];gate=r.Absolute_95pct_gate_t_ha;base=r.Original_model_baseline_Y13_t_ha
  axes[0].plot([gate,base],[i,i],lw=7,c=color,alpha=.23,solid_capstyle='round')
  axes[0].scatter(gate,i,marker='|',s=190,c=color,lw=2);axes[0].scatter(base,i,s=45,c=color)
  axes[0].scatter(r.Observed_Y13_t_ha,i,marker='D',s=35,fc='white',ec=color)
  value=r.Remaining_loss_allowed_pct_of_model_baseline;axes[1].bar(i,value,.55,color=color)
  axes[1].text(i,value+.12,f'{value:.2f}%',ha='center',fontsize=11)
 axes[0].set(yticks=range(4),yticklabels=YEARS,xlabel='Y13（t/ha）',title='模型基准与观测门槛');axes[0].invert_yaxis();axes[0].grid(axis='x')
 axes[1].set(xticks=range(4),xticklabels=YEARS,ylabel='允许减产余量（%）',ylim=(0,7),title='保产门槛内的余量');axes[1].grid(axis='y');axes[1].set_axisbelow(True)
 fig.legend(handles=[Line2D([0],[0],c=GRAY,marker='o',ls='',label='模型基准'),Line2D([0],[0],c=GRAY,marker='D',mfc='white',ls='',label='文献观测'),Line2D([0],[0],c=GRAY,marker='|',ls='',label='95% 观测门槛')],loc='upper center',bbox_to_anchor=(.53,1.005),ncol=3,fontsize=10.5)
 save(fig,'F13_yield_gate','四年确定性优化的保产门槛','余量是相对模型基准可允许的产量损失，不是节水率；2021 约 0.86%，2022 约 4.99%。')

def trace_panels():
 groups=frame('sampling_group_summary');groups=groups[groups.Phase==2].set_index('Year')
 with np.load(PROJECT/'frozen_inputs/verified_phase_specific_draws.npz') as z:draws={y:z[f'p2_{y}'].reshape(-1,32,3) for y in YEARS}
 for j,key in enumerate(NAMES[5:]):
  fig,axes=panel_grid(6.6)
  for ax,year in zip(axes.flat,YEARS):
   h=draws[year][:,:,j];steps=np.arange(len(h))+2000-len(h);q=np.quantile(h,[.1,.5,.9],axis=1)
   ax.fill_between(steps,q[0],q[2],color=COLORS[year],alpha=.14,lw=0)
   ax.plot(steps,q[1],c=COLORS[year],lw=.8)
   ax.set(xlabel='原始采样步数',ylabel=TITLES[key],xlim=(0,2000));ax.grid(axis='y')
  save(fig,f'F{14+j:02d}_phase2_trace_{key}',f'四年阶段二轨迹：{TITLES[key]}',
       '仅绘保留段；线为每步 32 个 walker 的中位数，浅带为 10%—90% 分位，不是独立链收敛认证。')

def centers_and_diagnostics():
 d=frame('central_vectors_with_provenance');fig,axes=plt.subplots(4,2,figsize=(9.8,10.2),layout='constrained')
 for ax,key in zip(axes.flat,NAMES):
  ax.plot(range(4),d.sort_values('Year')[key],ls='--',lw=1,c='#B2BCC4')
  for i,year in enumerate(YEARS):ax.scatter(i,d.loc[d.Year==year,key].iloc[0],c=COLORS[year],s=46,zorder=4)
  ax.set(title=TITLES[key],xticks=range(4),xticklabels=YEARS,xlim=(-.4,3.4));ax.grid(axis='y')
 save(fig,'F17_parameter_centers','四年冻结中心参数','各阶段保留样本的算术均值；连线仅用于年度比较，不表示已证明跨年趋势。')
 d=frame('mcmc_diagnostics_recomputed');d=d[d.Phase==1];fig,axes=plt.subplots(1,2,figsize=(10.2,4.2),layout='constrained')
 for ax,key,title in zip(axes,['Rhat_max','ESS_bulk_min'],['阶段一：秩标准化 R̂','阶段一：bulk ESS']):
  values=d.pivot(index='Parameter',columns='Year',values=key).reindex(NAMES[:5]).reindex(columns=YEARS)
  ax.imshow(values,aspect='auto',cmap='Blues',vmin=1 if key=='Rhat_max' else 0,vmax=1.3 if key=='Rhat_max' else 400)
  for i in range(5):
   for k in range(4):ax.text(k,i,f'{values.iloc[i,k]:.3f}' if key=='Rhat_max' else f'{values.iloc[i,k]:.0f}',ha='center',va='center',fontsize=11,color=INK)
  ax.set(xticks=range(4),xticklabels=YEARS,yticks=range(5),yticklabels=NAMES[:5],title=title)
 save(fig,'S01_phase1_diagnostics','四年阶段一补充采样诊断','沿用原检查点复核；四年未达原严格诊断阈值。该限制单列，不强制作为确定性下游分析的新门槛。',role='supplemental_four_year_diagnostics')

flow();calibration_series('CC');calibration_series('Biomass');scatters('CC');scatters('Biomass');calibration_summary()
intervals();correlations();water();climate_and_roles();sampling();headroom();trace_panels();centers_and_diagnostics()
assert len(caps)==18
(ROOT/'figure_captions.json').write_text(json.dumps(caps,ensure_ascii=False,indent=2),encoding='utf-8')
manifest=[]
for row in caps:
 for ext in ['png','pdf']:
  path=F/(Path(row['file']).stem+'.'+ext)
  manifest.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),years=YEARS,min_font_pt=row['min_font_pt']))
(ROOT/'FIGURE_COVERAGE_AND_STYLE.json').write_text(json.dumps(dict(date='2026-10-18',current_figure_pairs=len(caps),
 all_year_comparisons_include=YEARS,min_font_pt=10.5,year_palette={str(k):v for k,v in COLORS.items()},
 raster_dpi=300,vector_format='PDF',historical_proxy_figures_in_current_directory=False,figures=manifest),ensure_ascii=False,indent=2),encoding='utf-8')
print('Built',len(caps),'four-year figure pairs; all data pair checks and minimum-font checks passed.')
