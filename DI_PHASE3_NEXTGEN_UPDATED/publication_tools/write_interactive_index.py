"""Offline gallery and hoverable actual Pareto points, without remote assets."""
from pathlib import Path
import json
import html
import pandas as pd

COLORS={'2019':'#0072B2','2020':'#D55E00','2021':'#009E73','2022':'#A85AA0'}
OBS={'2019':16.55,'2020':17.29,'2021':15.86,'2022':14.08}
CAP={'2019':445.27,'2020':559.76,'2021':633.47,'2022':404.84}
MODEL={'2019':16.701690981890927,'2020':16.804038510033287,'2021':15.19713325177589,'2022':14.077782818070832}


def make_index(folder,entries,source_tables):
    data=pd.read_csv(source_tables/'NSGA_all_seed_Pareto_points.csv')
    points=[]
    for r in data.to_dict('records'):
        points.append({'year':int(r['Year']),'alg':r['Algorithm'],'seed':int(r['Seed']),
            'i':r['Irrigation_mm'],'y':r['Y13'],'w':[r[f'Window{k}_mm'] for k in range(1,5)]})
    candidates=pd.read_csv(source_tables/'NSGA_main_candidates.csv').to_dict('records')
    selected={str(int(r['Year'])):{'i':r['Irrigation_mm'],'y':r['Y13'],'w':[r[f'Window{k}_mm'] for k in range(1,5)]} for r in candidates}
    cards=[]
    for entry in entries:
        name=entry['name'];category='sobol' if name.startswith(('R01','R02')) else 'optimization' if name.startswith('R') else 'calibration'
        text=' '.join([entry['title'],entry['caption'],name]).lower()
        cards.append(f'''<article class="card" data-category="{category}" data-search="{html.escape(text,quote=True)}">
<a href="figures/{name}.png"><img src="figures/{name}.png" alt="{html.escape(entry['title'],quote=True)}" loading="lazy"></a>
<div class="caption"><h3>{html.escape(entry['title'])}</h3><p>{html.escape(entry['caption'])}</p>
<a href="figures/{name}.png">PNG</a> · <a href="figures/{name}.pdf">矢量PDF</a><small>2019 · 2020 · 2021 · 2022</small></div></article>''')
    payload=json.dumps({'points':points,'selected':selected,'colors':COLORS,'obs':OBS,'cap':CAP,'model':MODEL},ensure_ascii=False).replace('</','<\\/')
    text='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>URP · 四年真实敏感性与灌溉优化</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4f7f9;color:#243d4b;font:16px/1.65 system-ui,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:auto;padding:30px 24px}header{padding:28px 34px;background:white;border-radius:18px;border-top:5px solid #24556b}
h1{font-size:29px;line-height:1.35;margin:0 0 10px}h2{font-size:23px;margin:0 0 8px}p{margin:6px 0 12px}.muted,small{color:#657982}
.chips{display:flex;gap:9px;flex-wrap:wrap;margin:16px 0}button,input{font:inherit;border:1px solid #cbd7df;background:white;border-radius:8px;padding:7px 16px;cursor:pointer;color:inherit}
button.active{background:#24556b;color:white;border-color:#24556b}section{margin-top:25px;background:white;border-radius:16px;padding:25px}
.chart-layout{display:grid;grid-template-columns:minmax(0,3fr) minmax(230px,1fr);gap:18px}.chart{position:relative}svg{width:100%;height:auto;display:block}svg text{font:14px system-ui,"Microsoft YaHei",sans-serif;fill:#3f5662}
.detail{background:#f0f5f7;border-radius:10px;padding:16px;white-space:pre-line;font-size:15px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.card{overflow:hidden;border-radius:12px;border:1px solid #dce5ea;background:white}.card img{width:100%;height:310px;object-fit:contain;padding:10px;display:block;background:white}.caption{padding:10px 18px 18px}.caption h3{font-size:18px;margin:0 0 5px}.caption p{font-size:14px;color:#5d737e}.caption small{display:block;margin-top:6px}a{color:#17668d}details{margin-top:15px;border-left:3px solid #d58a2c;padding-left:12px}input{min-width:260px;cursor:text}.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:14px}.dot{display:inline-block;width:10px;height:10px;background:#0072b2;border-radius:50%;margin-right:6px}@media(max-width:760px){main{padding:15px}.grid,.chart-layout{grid-template-columns:1fr}h1{font-size:24px}.card img{height:260px}section,header{padding:20px}}
</style><main><header><h1>URP · 四年敏感性与灌溉优化</h1>
<p class="muted">2019—2022 · 原年度模型真实计算 · MCMC冻结 · 32组当前图件</p>
<p>Sobol最终61,440条响应；NSGA-III与NSGA-II各100个体×100代×5种子，四年合计400,000次评估。</p>
<details><summary>计算口径与结论边界</summary><p>Sobol使用公共独立范围，2022年产量的WP early与Kcb贡献接近，保留排序不确定性。优化只调整四个窗口总水量，原日期不变；门槛为发表观测产量的95%。条件参数扰动不是八维联合后验，原MCMC严格诊断限制仍保留。节水量应结合耗水和季末储水变化解释。</p></details>
</header><section><h2>查看真实Pareto权衡</h2><p class="muted">切换年份，悬停点查看对应的灌水总量、产量和四个窗口的计划水量。图中点均为已计算的可行方案。</p>
<div class="chips" id="years"></div><div class="legend"><span><i class="dot"></i>NSGA-III</span><span><i class="dot" style="background:#84949d"></i>NSGA-II</span><span>★ 模型基准</span><span>◎ ε约束主候选</span></div>
<div class="chart-layout"><div class="chart"><svg id="pareto" viewBox="0 0 900 430" aria-label="真实Pareto散点图"></svg></div><aside class="detail" id="pointDetail">悬停某个方案查看数值。</aside></div>
<p class="muted" id="yearSummary"></p></section><section><h2>四年图件</h2><p class="muted">点击图片查看原尺寸；PDF可用于论文矢量排版。所有图均含四年。</p>
<div class="chips" id="filters"><button class="active" data-filter="all">全部</button><button data-filter="sobol">Sobol</button><button data-filter="optimization">优化与核验</button><button data-filter="calibration">校准背景</button><input id="search" type="search" placeholder="搜索参数、产量或图名"></div>
<div class="grid">__CARDS__</div></section><p class="muted">完整数据表、Word和核验记录见同包README；本页可离线打开，不调用外部服务。</p></main>
<script>const DATA=__DATA__;const NS='http://www.w3.org/2000/svg';let current='2019';
function el(name,attrs,parent,text){const n=document.createElementNS(NS,name);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;parent.append(n);return n;}
function detail(p,label){const save=100*(1-p.i/DATA.cap[current]);document.getElementById('pointDetail').textContent=label+'\\n产量 Y13：'+p.y.toFixed(4)+' t/ha\\n实际灌水：'+p.i.toFixed(2)+' mm\\n相对原DI节水：'+save.toFixed(2)+'%\\n\\n四窗口计划量（mm）\\n'+p.w.map((v,i)=>'窗口'+(i+1)+'：'+v.toFixed(2)).join('\\n');}
function draw(year){current=year;const svg=document.getElementById('pareto');svg.replaceChildren();const pts=DATA.points.filter(p=>String(p.year)===year);const c=DATA.selected[year],cap=DATA.cap[year],gate=.95*DATA.obs[year];const xmin=Math.max(0,Math.min(...pts.map(p=>p.i))*.9),xmax=cap*1.06,ymin=gate*.985,ymax=Math.max(DATA.obs[year],DATA.model[year],...pts.map(p=>p.y))*1.012;const X=v=>65+(v-xmin)/(xmax-xmin)*795,Y=v=>365-(v-ymin)/(ymax-ymin)*330;
for(let j=0;j<=5;j++){let x=xmin+(xmax-xmin)*j/5,y=ymin+(ymax-ymin)*j/5;el('line',{x1:X(x),y1:35,x2:X(x),y2:365,stroke:'#e6edf1'},svg);el('line',{x1:65,y1:Y(y),x2:860,y2:Y(y),stroke:'#e6edf1'},svg);el('text',{x:X(x),y:389,'text-anchor':'middle'},svg,x.toFixed(0));el('text',{x:55,y:Y(y)+5,'text-anchor':'end'},svg,y.toFixed(2));}
el('line',{x1:65,y1:Y(gate),x2:860,y2:Y(gate),stroke:'#a86962','stroke-dasharray':'5 5'},svg);el('text',{x:850,y:Y(gate)-7,'text-anchor':'end'},svg,'95%观测门槛');
for(const p of pts){const n=el('circle',{cx:X(p.i),cy:Y(p.y),r:3.8,fill:p.alg==='NSGA3'?DATA.colors[year]:'#84949d',opacity:.48},svg);n.addEventListener('mouseenter',()=>{n.setAttribute('r','7');n.setAttribute('opacity','1');detail(p,p.alg+' · seed '+p.seed)});n.addEventListener('mouseleave',()=>{n.setAttribute('r','3.8');n.setAttribute('opacity','.48')});}
el('text',{x:X(cap),y:Y(DATA.model[year])+7,'text-anchor':'middle',style:'font-size:27px;fill:#253f4c'},svg,'★');const n=el('circle',{cx:X(c.i),cy:Y(c.y),r:8,fill:'white',stroke:DATA.colors[year],'stroke-width':3},svg);n.addEventListener('mouseenter',()=>detail(c,'ε约束主候选'));el('text',{x:455,y:420,'text-anchor':'middle'},svg,'实际季节灌水量（mm）');el('text',{x:18,y:200,transform:'rotate(-90 18 200)','text-anchor':'middle'},svg,'Y13（t/ha）');detail(c,'ε约束主候选');document.getElementById('yearSummary').textContent=year+' · 发表观测 '+DATA.obs[year].toFixed(2)+' t/ha · 原DI '+cap.toFixed(2)+' mm · 模型基准 '+DATA.model[year].toFixed(4)+' t/ha';}
const yearBox=document.getElementById('years');for(const y of ['2019','2020','2021','2022']){const b=document.createElement('button');b.textContent=y;b.style.borderColor=DATA.colors[y];b.addEventListener('click',()=>{for(const n of yearBox.children)n.classList.remove('active');b.classList.add('active');draw(y)});if(y===current)b.classList.add('active');yearBox.append(b)}draw(current);
let category='all';function filter(){const q=document.getElementById('search').value.toLowerCase();for(const c of document.querySelectorAll('.card'))c.hidden=!((category==='all'||c.dataset.category===category)&&c.dataset.search.includes(q));}for(const b of document.querySelectorAll('[data-filter]'))b.addEventListener('click',()=>{category=b.dataset.filter;for(const c of document.querySelectorAll('[data-filter]'))c.classList.remove('active');b.classList.add('active');filter()});document.getElementById('search').addEventListener('input',filter);
</script></html>'''
    text=text.replace('__CARDS__','\n'.join(cards)).replace('__DATA__',payload)
    (Path(folder)/'图表索引.html').write_text(text,encoding='utf-8')
