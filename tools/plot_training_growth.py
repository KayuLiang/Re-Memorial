"""Figures and report for the provisional complete training model."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
from matplotlib import font_manager
import matplotlib.pyplot as plt
import numpy as np

POLICIES={'random':'随机选牌与目标','greedy':'优先提高本次检定期望'}


def name_for(name):
    if name=='pow':
        return '意志 POW（借用力量训练）'
    if name=='con':
        return '体质 CON（慢跑）'
    attr,initial=name.split('_')
    return ('力量 STR' if attr=='str' else '灵巧 DEX')+f' · 初始 {initial}'


def number(row, key):
    return row.get(key, np.nan)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('directory',type=Path)
    parser.add_argument('--wake-only',action='store_true',help='Update only the wake figure and report, keeping other figures unchanged.')
    args=parser.parse_args()
    data=json.loads((args.directory/'summary.json').read_text(encoding='utf-8'))
    meta=data['metadata']
    font=Path('C:/Windows/Fonts/msyh.ttc')
    font_manager.fontManager.addfont(str(font))
    plt.rcParams.update({'font.family':font_manager.FontProperties(fname=str(font)).get_name(),
        'axes.spines.top':False,'axes.spines.right':False,'axes.unicode_minus':False,
        'font.size':10,'savefig.dpi':160})
    scenarios={(r['name'],r['policy']):r for r in data['scenarios']}
    names=list(dict.fromkeys(r['name'] for r in data['scenarios']))
    colors=plt.colormaps['viridis'](np.linspace(.07,.88,7))
    probabilities=(.2,.3,.4,.5,.6,.7,.8)
    for name in ([] if args.wake_only else names):
        fig,axes=plt.subplots(2,2,figsize=(13,7),sharex='col',gridspec_kw={'height_ratios':[3,1]})
        for col,policy in enumerate(POLICIES):
            rows=scenarios[name,policy]['rows']
            x=[r['formal_attribute'] for r in rows]
            for p,color in zip(probabilities,colors):
                y=[r.get('thresholds',{}).get(str(p)) for r in rows]
                axes[0,col].plot(x,[np.nan if v is None else v for v in y],color=color,label=f'{p:.0%}',linewidth=1.7)
            axes[0,col].set_title(POLICIES[policy],pad=12)
            axes[0,col].set_ylabel('目标值（已含每个样本的实际属性修正）')
            axes[1,col].bar(x,[r['n']/meta['trials']*100 for r in rows],color='#7C8B92',width=.7)
            axes[1,col].set_ylim(0,105)
            axes[1,col].set_ylabel('命中路径（%）')
            axes[1,col].set_xlabel('正式属性值')
            for ax in axes[:,col]:
                ax.set_xlim(min(x)-.4,max(x)+.4)
                ax.set_xticks([min(x)]+[n for n in range(5,max(x)+1,5) if n>min(x)])
                ax.grid(axis='y',alpha=.18)
        ymin=min(ax.get_ylim()[0] for ax in axes[0,:])
        ymax=max(ax.get_ylim()[1] for ax in axes[0,:])
        for ax in axes[0,:]:
            ax.set_ylim(ymin,ymax)
        fig.suptitle(name_for(name)+'｜完整训练链的 20%–80% 通过率目标',fontsize=15,y=.98)
        handles,labels=axes[0,0].get_legend_handles_labels()
        fig.legend(handles,labels,ncol=7,loc='upper center',bbox_to_anchor=(.5,.94),frameon=False)
        fig.text(.5,.018,'每天六轮，精力不足休息，按时睡觉；取正式属性首次出现的早晨。跳过的属性不补值，结果以实际命中路径为条件。',ha='center',fontsize=9)
        fig.subplots_adjust(top=.80,bottom=.12,hspace=.20,wspace=.22,left=.08,right=.98)
        fig.savefig(args.directory/(name+'-curves.png'))
        plt.close(fig)

    if not args.wake_only:
        selected=[n for n in ('pow','con','str_3','dex_3') if n in names]
        selected+=( [n for n in names if n not in selected][:4-len(selected)] )
        fig,axes=plt.subplots(2,2,figsize=(13,8))
        for ax,name in zip(axes.flat,selected):
            for policy,color in zip(POLICIES,('#2863A0','#B4512B')):
                rows=scenarios[name,policy]['rows']; x=[r['formal_attribute'] for r in rows]
                ax.plot(x,[number(r,'mean') for r in rows],color=color,label=POLICIES[policy],linewidth=2)
                ax.fill_between(x,[number(r,'p10') for r in rows],[number(r,'p90') for r in rows],color=color,alpha=.13)
            ax.set_title(name_for(name),fontsize=11)
            ax.set_xlabel('正式属性值'); ax.set_ylabel('全力检定总值的期望')
            ax.set_xticks([min(x)]+[n for n in range(5,max(x)+1,5) if n>min(x)])
            ax.grid(axis='y',alpha=.18)
        for ax in list(axes.flat)[len(selected):]:
            ax.set_visible(False)
        fig.suptitle('完整成长过程｜均值与不同养成路径的 10%–90% 范围',fontsize=15)
        fig.legend(*axes.flat[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.955),ncol=2,frameon=False)
        fig.text(.5,.015,'含加成、加值、三类成长计数、退化与附魔；阴影不是投骰结果区间，也不是置信区间。',ha='center',fontsize=9)
        fig.subplots_adjust(top=.85,bottom=.10,wspace=.24,hspace=.38)
        fig.savefig(args.directory/'expectation-comparison.png'); plt.close(fig)

    if data['wake_fits']:
        fig,axes=plt.subplots(2,2,figsize=(13,8),sharex=True)
        for col,(policy,fit) in enumerate(data['wake_fits'].items()):
            rows=fit['rows']; x=np.array([r['pow'] for r in rows]); z=x-6
            axes[0,col].plot(x,15+fit['a']*z*z+fit['b']*z,label='二次函数（取整前）',color='#2863A0')
            axes[0,col].plot(x,[r['target'] for r in rows],'o',label='实际整数目标',color='#B4512B',markersize=4)
            axes[0,col].set_title(POLICIES[policy]+f"\na={fit['a']:.3f}，b={fit['b']:.2f}",fontsize=11)
            axes[0,col].set_ylabel('起床检定目标'); axes[0,col].legend(frameon=False,fontsize=9)
            rates=np.array([r['success'] for r in rows])*100
            error=np.array([r['mc_se'] for r in rows])*196
            axes[1,col].axhline(75,color='#57795B',linestyle='--',label='75% 目标（允许偏高）')
            axes[1,col].errorbar(x,rates,yerr=error,fmt='o-',capsize=2,markersize=4,label='实际通过率 ± 1.96 SE')
            axes[1,col].set_ylim(min(68,min(rates-error)-2),max(78,max(rates+error)+2))
            axes[1,col].set_ylabel('通过率（%）'); axes[1,col].set_xlabel('正式意志 POW')
            axes[1,col].legend(frameon=False,fontsize=9,loc='best')
            for ax in axes[:,col]:
                ax.set_xticks(range(6,21,2)); ax.grid(axis='y',alpha=.18)
        fig.suptitle('完整成长后的二次函数候选｜T = 四舍五入 [15 + a(POW−6)² + b(POW−6)]',fontsize=14)
        fig.text(.5,.017,'初始目标 15 对应 72.5%；随机选牌曲线已作为游戏统一难度。右侧择优曲线仅供比较，不随玩家选牌策略切换。',ha='center',fontsize=9)
        fig.subplots_adjust(top=.85,bottom=.11,hspace=.25,wspace=.23)
        fig.savefig(args.directory/'wake-quadratic-candidates.png'); plt.close(fig)

    lines=['# 完整训练成长模拟 · 第一版','',
        '本版是指定训练安排下的完整成长链，不是整个剧情流程的玩家平均值。没有新增正式意志训练日程；2026年9月20日起床检定采用本版随机选牌拟合曲线作为统一基础难度。','',
        '## 本版采用的条件','',
        f"- 每个配置、每种策略 {meta['trials']:,} 条独立路径；种子 {meta['seed']}；最多模拟 {meta['max_days']} 天，正式属性到达或跨过 {meta['max_attribute']} 后结束。",
        '- 每天六个普通行动轮集中培养目标属性；投入当前期望最高的合法最多三骰，精力不足或没有合法骰组时休息；每晚按时睡觉。休息实际投体质骰恢复精力，训练疲劳真实累积、休息减层、睡眠清空。',
        '- 为隔离养成因素，全程固定心情平稳；不模拟训练成败带来的心情偏移。按时睡觉仍正常累积良好作息。测量通过率时不限精力，但成长过程按实际精力消耗。',
        '- 意志借用力量的成功奖励概率、已有加成衰减和训练进度；骰子仍为意志 d20，最多三颗。力量使用原模型；灵巧只有训练进度转加成；体质使用慢跑，包含 CON/STR/DEX 混合选骰及多属性奖励，初始其他属性 STR3/DEX3/INT2。',
        '- 力量和灵巧分别模拟初始 1～6。智识没有训练日程，本版不冒充已有智识全日程曲线；其骰子奖励规则仍与力量、灵巧同类。',
        '- 随机策略：先均匀选卡位，再随机选合法目标。期望优先策略：根据已展示卡面，最大化结算后当次全力检定期望；随机效果按所有可能结果平均，不偷看随机结果。退化时同样尽量保留期望。不是长期最优或精力效率最优。','',
        '## 完整结算与程序差异','',
        '- 包含加成 → 每晚小休 → 加值 → 每周大休 → 正式属性。加成每累计获得 4 层、加值每累计获得 2 点、正式属性每增长 1 点，三个计数器分别累计骰子成长奖励。流失也按现有核心规则处理。',
        '- 训练等级进度 0/1/2/3/6 封顶 6，满 6 在晚上转为一层属性加成，不是直接发一次骰子奖励；溢出不保留，沿用测试模型。慢跑不使用这条训练进度。',
        '- 小休先兑换骰子成长进度，大休后产生的正式属性奖励要等下一晚小休才兑换，没有为了测量提前发奖。待选奖励先于退化卡结算，包含新骰、合法骰型变化、骰面变化、附魔、封印、束缚与解除负面附魔。',
        '- 每周调用临时附魔衰退；本训练场景没有临时附魔来源，奖励卡提供的轻盈/轻捷是永久附魔，不能每周擅自删除。',
        '- **程序连接已补齐：** 训练进度在实际睡眠的小休开始时转为加成；普通训练的大失败在心情变化前累计退化，待选惩罚在进入下一轮前处理。意志仍仅为离线训练代理，没有新增意志训练日程。原数据库保留生成时的说明，未重算或覆盖数值结果。',
        '- 未配置的剧情事件奖励不虚构；迷雾未进入当前奖励 UI，因此不加入。按时睡觉的本场景不会产生熬夜疲劳或深度疲劳。','',
        '## 如何读图','',
        '- 横轴只用正式属性。每条路径只记录该值第一次实际出现的早晨，初始值记录开局。每周可能一次增加多个正式点，跳过的整数属性不补样本。',
        '- 每点样本数可能小于总路径数；下方柱状图显示命中比例。曲线是“确实命中该值”的路径的条件分布，不能代表未命中或更晚停留在该值的角色。未到达上限的路径也保留在停止统计中。',
        '- 每条样本使用当时完整属性：正式值 + 加值 + 加成，先封顶 20，再乘 50% 向下取整。分别计算总值分布后才混合，不能先平均属性修正再算概率。',
        '- 封印骰不参与，束缚骰强制参与。全部封印时记为不可检定，所有目标均失败；分布表中概率质量之和等于可检定比例。若连最低目标也达不到指定通过率，目标留空。',
        '- 20%～80% 曲线取满足通过率不低于标签的最高整数目标；骰子离散，实际概率未必恰等于标签。样本骰池内部用精确卷积，仅成长路径使用随机抽样。',
        '- 阴影表示不同养成路径的检定期望 10%～90% 范围；误差条 ±1.96 SE 只衡量抽样误差，不包括代理模型不确定性。','',
        '![期望对比](expectation-comparison.png)','',
        '## 达到高属性的情况','',
        '| 配置 | 选牌策略 | 到达或跨过上限 | 到天数上限 | 正式20命中数 | 正式20平均天数 | 正式20平均已领本属性奖励 |',
        '|---|---|---:|---:|---:|---:|---:|']
    if 'pow' in names:
        power_summary=['## 意志结果速览','',
            '以下是每天集中培养的代理场景，不是普通剧情安排下的平均养成。成长奖励数量不再等于“正式意志 − 6”。','',
            '| 正式意志 | 随机：命中数 | 随机：已领奖励 | 随机：总值期望 | 随机：70%目标 | 期望优先：命中数 | 期望优先：已领奖励 | 期望优先：总值期望 | 期望优先：70%目标 |',
            '|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for value in (6,10,15,20):
            cells=[str(value)]
            for policy in POLICIES:
                row=next((r for r in scenarios['pow',policy]['rows'] if r['formal_attribute']==value and r['n']),None)
                cells+=([str(row['n']),f"{row['mean_rewards']:.1f}",f"{row['mean']:.2f}",str(row['thresholds']['0.7'])] if row else ['—']*4)
            power_summary.append('| '+' | '.join(cells)+' |')
        power_summary+=['','奖励数为命中路径的平均已领取数量；尚未兑换的成长进度另存数据库。开局目标15对应72.5%，而表中“70%目标”是至少70%通过率允许的最高整数目标，两者定义不同。','']
        lines[4:4]=power_summary
    for result in data['scenarios']:
        row=next((r for r in result['rows'] if r['formal_attribute']==20 and r['n']),None)
        values=[str(row['n']),f"{row['mean_day']:.1f}",f"{row['mean_rewards']:.1f}"] if row else ['—']*3
        lines.append('| '+' | '.join([name_for(result['name']),POLICIES[result['policy']],
            str(result['stopped'].get('reached_or_crossed_max',0)),str(result['stopped'].get('day_limit',0))]+values)+' |')
    lines+=['','## 各配置通过率曲线','']
    lines += [f'- [{name_for(name)}]({name}-curves.png)' for name in names]
    lines+=['','## 起床目标二次函数','',
        '初始意志6、目标15、两枚初始骰全部投入，精确通过率仍为72.5%，保留这个固定起点。以下候选要求目标值在6～20内单调不减；这不等于通过率单调上升。非起始档仅使用至少100条路径命中的属性点拟合（小规模试运行则使用其全体路径数），全部有样本的属性点仍验算并展示。',
        '搜索 a=-0.500～0.500（步长0.001，排除0）、b=0～8（步长0.01），令 z=POW−6。参与拟合的非起始档实测通过率须不低于75%，在可行曲线中最小化与75%的平方偏差；允许后期偏高，不为了压低通过率加大难度。无可行曲线则不输出候选。这个75%约束针对当前样本估计，不是统计置信下限保证。',
        '随机选牌曲线已接入游戏：T=floor(15+1.88*z-0.063*z*z+0.5)，z=限定在6～20的正式POW−6。范围外取边界目标15或29，不继续外推。疲劳、属性加成和加值不改变基础目标；通用情绪难度修正照常。界面与结算共享同一目标。择优曲线只供比较，不根据玩家选牌方式动态调整难度。',
        '只重拟合已有分布，没有重新模拟或修改原始数据库。采用统一曲线后，随机选牌的POW 10/15/20通过率约为87.0%/77.1%/76.4%；择优选牌在同一目标下约为96.4%/96.6%/98.1%。下文择优表格显示的是其独立拟合结果，不是游戏统一目标。',
        '早期正式属性未增长时，已可能累计大量骰子奖励，因此正式意志7～10的条件通过率明显偏高。固定起点与单条单调二次函数无法同时消除这一跃升；如实保留，不插值改写成长数据。','']
    for policy,fit in data['wake_fits'].items():
        lines += [f'### {POLICIES[policy]}','',f"T = floor(15 + ({fit['a']:.3f}) × z² + {fit['b']:.2f} × z + 0.5)",'',
            f"全部有样本档通过率范围 **{fit['minimum_success']:.2%}～{fit['maximum_success']:.2%}**，含初始72.5%与低样本档；各档并非都接近75%。",'',
            '| 正式意志 | 样本数 | 参与拟合 | 目标 | 通过率 | 约95%抽样误差 | 可落在70%～75%的整数目标 |',
            '|---:|---:|---|---:|---:|---:|---|']
        for row in fit['rows']:
            band='、'.join(map(str,row['attainable_targets_70_75'])) or '无'
            used='固定起点' if row['pow']==6 else ('是' if row.get('used_for_fit',True) else '否，样本较少')
            lines.append(f"| {row['pow']} | {row['n']} | {used} | {row['target']} | {row['success']:.2%} | ±{1.96*row['mc_se']:.2%} | {band} |")
        lines.append('')
    if data['wake_fits']:
        lines+=['![起床函数候选](wake-quadratic-candidates.png)','']
    lines+=['## 数据库与复现','',
        '- `dice-growth.sqlite`：`growth` 保存命中数、期望、天数及已领取奖励；`samples` 保留每条路径首次命中的具体修正、加成、加值与待兑现进度。',
        '- `distribution` 的 `total_score` 已经包含各样本实际属性修正；查通过率时**不要再减属性的一半**。`target_curve` / `lookup` 保存20%～80%目标及相邻目标概率、标准误。',
        '- `summary.json`：同一结果的可读导出及完整运行条件。此前正式属性每点仅发一次奖励的数据库保留作历史对比，不再作为本版结果。','',
        '```sql',"SELECT target, actual_probability, probability_at_next_target, pass_mc_se, n",
        "FROM lookup WHERE scenario='pow' AND policy='greedy'",
        'AND formal_attribute=10 AND requested_probability=0.7;','```','',
        '```text',f"python tools/simulate_training_growth.py --trials {meta['trials']} --max-days {meta['max_days']} --max-attribute {meta['max_attribute']} --seed {meta['seed']} --output <新的结果目录>",
        'python tools/plot_training_growth.py <结果目录>','```','',
        '只调整拟合时可运行 `python tools/simulate_training_growth.py --refit-only --output <已有结果目录>`，再运行 `python tools/plot_training_growth.py <已有结果目录> --wake-only` 更新起床图与报告；不会重新模拟或改写数据库。','',
        '验证覆盖初始72.5%、实际属性修正、三个成长计数器、周末奖励延迟、封印/束缚、选牌评分、随机惩罚平均、训练进度转加成、种子复现与数据库一致性。']
    (args.directory/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Wrote {int(bool(data["wake_fits"])) if args.wake_only else len(names)+1+bool(data["wake_fits"])} figures and README.md')


if __name__=='__main__':
    main()
