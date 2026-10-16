"""Draw two new evidence figures and insert them into the reviewed paper."""
from pathlib import Path
import os
import sys
import inspect
import shutil

ROOT = Path(__file__).resolve().parent
os.environ.setdefault('XDG_CACHE_HOME', str(ROOT / '.cache'))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

OLD = Path('/workspace/urp_followup_20261016/revision')
F = ROOT / 'figures'
F.mkdir(exist_ok=True)
for path in (OLD / 'figures').iterdir():
    shutil.copyfile(path, F / path.name)

font = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
fm.fontManager.addfont(font)
plt.rcParams.update({'font.family': [fm.FontProperties(fname=font).get_name(), 'DejaVu Sans'],
                     'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.unicode_minus': False, 'pdf.fonttype': 42, 'legend.frameon': False,
                     'grid.color': '#E4E9EE'})
COLORS = ['#176B87', '#A8762A', '#805CA2', '#8595A2']
DARK = '#25384A'


def save(fig, name, title, note):
    fig.suptitle(title, fontsize=15, fontweight='bold', color=DARK, y=1.13)
    fig.text(.01, -.035, note, fontsize=8.5, va='top', color='#526474')
    for suffix in ['png', 'pdf']:
        fig.savefig(F / f'{name}.{suffix}', dpi=300, bbox_inches='tight', pad_inches=.17)
    plt.close(fig)


domains = pd.read_csv(ROOT / 'tables/annual_sampling_domains.csv')
gates = pd.read_csv(ROOT / 'tables/observed_yield_gate_headroom.csv')
fig, axes = plt.subplots(1, 3, figsize=(12, 4.3), layout='constrained')
for a, name in zip(axes, ['WP_early', 'WP_late', 'HI0']):
    d = domains[domains.Parameter == name].sort_values('Year')
    for i, r in enumerate(d.itertuples()):
        a.plot([r.Low, r.High], [i, i], lw=8, color=COLORS[i], solid_capstyle='round', alpha=.9)
        a.text(r.Low, i + .18, f'{r.Low:g}', color=COLORS[i], ha='center', fontsize=9)
        a.text(r.High, i + .18, f'{r.High:g}', color=COLORS[i], ha='center', fontsize=9)
    a.set(title=name, yticks=range(4), yticklabels=range(2019, 2023), ylim=(-.4, 3.6), xlabel='原始检查点支持范围')
    a.invert_yaxis()
    a.grid(axis='x', alpha=.7)
save(fig, 'E01_annual_supports', '先声明输入空间：2022 年三个参数的范围与前三年不同',
     '来源：原始NPZ中的contract.priors。新设计在这些范围内独立均匀采样；这不等于原MCMC先验密度或后验。其余五参数范围四年相同。')

fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout='constrained', width_ratios=[1.45, 1])
for i, r in enumerate(gates.itertuples()):
    gate, base, obs = r.Absolute_95pct_gate_t_ha, r.Original_model_baseline_Y13_t_ha, r.Observed_Y13_t_ha
    axes[0].plot([gate, base], [i, i], lw=10, alpha=.25, color=COLORS[i], solid_capstyle='round')
    axes[0].scatter([gate], [i], marker='|', s=230, color=COLORS[i], lw=2, zorder=3)
    axes[0].scatter([base], [i], marker='o', s=75, color=COLORS[i], zorder=3)
    axes[0].scatter([obs], [i], marker='D', s=45, facecolor='white', edgecolor=COLORS[i], zorder=3)
    axes[0].text(gate, i + .18, f'门槛 {gate:.3f}', fontsize=8, ha='center', color=COLORS[i])
    axes[0].text(base, i - .15, f'基准 {base:.3f}', fontsize=8, ha='center', color=COLORS[i])
    v = r.Remaining_loss_allowed_pct_of_model_baseline
    axes[1].bar(i, v, color=COLORS[i], width=.55)
    axes[1].text(i, v + .17, f'{v:.2f}%', ha='center', fontsize=12, fontweight='bold', color=COLORS[i])
axes[0].set(yticks=range(3), yticklabels=[2019, 2020, 2021], ylim=(-.55, 2.6), xlim=(14.7, 17.6),
            xlabel='13% 含水率产量 / (t/ha)', title='圆点：同模型中心点基准；空心菱形：文献观测')
axes[0].invert_yaxis()
axes[0].grid(axis='x')
axes[1].set(xticks=range(3), xticklabels=[2019, 2020, 2021], ylim=(0, 7),
            ylabel='相对模型基准还能允许的减产 / %', title='严格使用 Y ≥ 0.95 × 文献观测产量')
axes[1].grid(axis='y')
axes[1].set_axisbelow(True)
save(fig, 'E02_yield_gate_headroom', '保产约束的实际余量：2021 年仅余约 0.86%',
     '由已有真实模型summary.json重新计算，未重跑模型。余量=100×[1−0.95×观测产量/模型基准产量]；不表示节水率，也不是置信区间。2022缺可核验配套输出，未绘入。')


def table(d):
    def fmt(v):
        if isinstance(v, (float, np.floating)):
            return f'{v:.4f}'
        return str(v)
    return '| ' + ' | '.join(d.columns) + ' |\n| ' + ' | '.join(['---'] * len(d.columns)) + ' |\n' + '\n'.join(
        '| ' + ' | '.join(fmt(v) for v in row) + ' |' for row in d.itertuples(index=False, name=None)) + '\n'


paper = (OLD / 'URP_20261016_论文框架_确定性主线.md').read_text()
paper = paper.replace('论文框架修订稿（2026-10-16）', '论文框架修订稿（2026-10-16，执行准备增补版）')
domain_table = domains.pivot(index='Parameter', columns='Year', values=['Low', 'High']).reindex(
    ['CCx', 'CGC_CD', 'CDC_CD', 'SenescenceCD', 'Kcb', 'WP_early', 'WP_late', 'HI0'])
compact = pd.DataFrame({'参数': domain_table.index,
                        '2019—2021范围': [f'[{r["Low", 2019]:g}, {r["High", 2019]:g}]' for _, r in domain_table.iterrows()],
                        '2022范围': [f'[{r["Low", 2022]:g}, {r["High", 2022]:g}]' for _, r in domain_table.iterrows()]})
new_methods = '''### 4.1 年度范围与输入概率密度
本轮从原始NPZ的contract.priors提取支持范围，各年度现有检查点之间一致。它们是历史校准的支持范围，农艺适用性仍需由来源解释，不因为写在代码里就自动成为物理定律。
''' + table(compact) + '''
![年度参数范围](figures/E01_annual_supports.png)

图注：前三年WP_early、WP_late均为10—40，HI0为0.35—0.60；2022分别为10—22、20—38、0.35—0.50。五个冠层/蒸腾参数支持范围一致。

旧脚本把2022也放在前三年的较宽范围内，改变了该年输入方差与可行参数空间。新的年度范围设计忠实记录原始支持，但四年Sobol差异会同时受气象、模型年度设置和范围变化影响，不能直接归因为气候。
若研究重点是控制输入空间后的跨年比较，应另外预声明共同范围，例如四年支持的交集，并让四年都在该空间重新运行；不能只从不同范围的结果中做气候归因。当前仅生成年度范围设计，没有生成或运行共同范围模型响应。
原MCMC在部分参数上含正态先验成分，2022含正态成分的参数更多。独立均匀设计与这些原先验、条件后验均不同，不再使用“后验Sobol”或“校准吸收率”解释本设计。

### 4.2 本轮已经生成的输入与尚未运行的响应
四年各3个scramble种子101、202、303，N=128、D=8、不算二阶，共12组设计、15360行。每个块按A、AB_1至AB_8、B固定顺序保存NPY和带row_id的CSV；设计与配置均有SHA256。相同种子扩大到N=512时，现有N128是前缀，可复用已有成功响应，仍需核对软件版本与输入哈希。
real_model_pipeline.py提供设计生成、基准复现、逐点调用、断点续算和S1/ST分析。模板因缺真实模型而明确失败。常量输出标记为不可辨识的归一化指数，未赋予伪零排名；缺点、重复行、非有限响应和水量不闭合均阻止分析。bootstrap区间只是给定设计的抽样区间，不涵盖模型结构或田间误差。
程序用Ishigami解析函数及合成软件夹具测试；没有将这些测试输出写成玉米模型响应。真实Sobol响应矩阵仍未生成。

'''
paper = paper.replace('## 5 确定性双目标NSGA-III的正式实施方案', new_methods + '\n## 5 确定性双目标NSGA-III的正式实施方案')
small = gates[['Year', 'Observed_Y13_t_ha', 'Original_model_baseline_Y13_t_ha',
               'Absolute_95pct_gate_t_ha', 'Remaining_loss_allowed_pct_of_model_baseline']].copy()
small.columns = ['年份', '文献观测', '模型基准', '95%绝对门槛', '可减产余量_pct']
new_constraint = '''### 5.4 观测门槛与模型基准必须同时报告
基准模型对2020、2021观测产量已有负偏差。优化时Y≥0.95×观测不能替换为Y≥0.95×模型基准，否则会叠加减产。例如2021的观测15.86、模型基准15.1971，绝对门槛应为15.0670，而不是14.4373 t/ha。
''' + table(small) + '''
![保产余量](figures/E02_yield_gate_headroom.png)

图注：由2019—2021原始summary.json的DI和Yield字段计算；本轮未重跑真实模型。2021可减产余量约0.1301 t/ha、相对模型基准0.8563%。这只限定产量空间，不给出任何节水潜力结论，也不能据此推断该年一定没有可行节水方案。
新候选应同时报告相对观测和相对同模型基准的变化，保留绝对门槛、总灌水上限与逐日/季节水量守恒。2022中心点验收仍需原阶段二链和配套模拟输出，不使用报告中的汇总数充当已验收基准。

'''
paper = paper.replace('## 6 条件扰动与适用范围', new_constraint + '\n## 6 条件扰动与适用范围')
paper_path = ROOT / 'paper_framework_execution_ready.md'
paper_path.write_text(paper, encoding='utf-8')
sys.path.insert(0, '/workspace/urp_review/src')
import make_documents as renderer
renderer.OUT = ROOT
renderer.TABLES = ROOT / 'tables'
source = inspect.getsource(renderer.pdf_report).replace('2026-10-15', '2026-10-16')
exec(source, renderer.__dict__)
renderer.pdf_report(paper, paper_path.with_suffix('.pdf'))
renderer.word_report(paper_path.name)
with pd.ExcelWriter(ROOT / 'execution_evidence.xlsx', engine='openpyxl') as book:
    domains.to_excel(book, sheet_name='annual_domains', index=False)
    gates.to_excel(book, sheet_name='yield_gate_headroom', index=False)
    manifest = renderer.read(ROOT / 'designs_N128/design_manifest.json')
    pd.DataFrame(manifest['runs']).to_excel(book, sheet_name='designs_not_responses', index=False)
print('Two new figure pairs and the updated illustrated paper created.')
