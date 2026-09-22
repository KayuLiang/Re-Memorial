"""Static scientific figures and readable report for simulate_dice_growth.py."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
from matplotlib import font_manager
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    data = json.loads((args.directory/'summary.json').read_text(encoding='utf-8'))
    font = Path('C:/Windows/Fonts/msyh.ttc')
    if font.exists():
        font_manager.fontManager.addfont(str(font))
        plt.rcParams['font.family'] = font_manager.FontProperties(fname=str(font)).get_name()
    plt.rcParams.update({'axes.spines.top':False, 'axes.spines.right':False,
                         'axes.unicode_minus':False, 'font.size':11, 'savefig.dpi':160})
    names = {'pow':'意志 POW', 'con':'体质 CON'}
    names.update({f'allocated_{n}':f'力量 / 灵巧 / 智识 · 初始属性 {n}' for n in range(1,7)})
    policies = {'random':'随机选牌与目标', 'greedy':'优先提高本次检定期望'}
    scenarios = {(r['name'],r['policy']):r for r in data['scenarios']}
    probabilities = [.2,.3,.4,.5,.6,.7,.8]
    colors = plt.colormaps['viridis'](np.linspace(.07,.88,7))
    for name in dict.fromkeys(r['name'] for r in data['scenarios']):
        fig, axes = plt.subplots(1,2,figsize=(13,5.8),sharex=True,sharey=True)
        for ax, policy in zip(axes,policies):
            r = scenarios[name,policy]
            x = [row['formal_attribute'] for row in r['rows']]
            for p,color in zip(probabilities,colors):
                ax.plot(x,[row['thresholds'][str(p)]+row['modifier'] for row in r['rows']],
                        color=color,label=f'{p:.0%}',linewidth=1.6)
            ax.set_title(policies[policy],fontsize=12,pad=12)
            ax.set_xlabel('正式属性值')
            ax.grid(axis='y',alpha=.18)
            ax.set_xlim(min(x),max(x))
            ax.set_xticks([min(x)] + [v for v in range(5,max(x)+1,5) if v > min(x)])
        axes[0].set_ylabel('整数目标值（含当前属性的 50% 修正）')
        fig.suptitle(names[name]+'｜20%–80% 通过率对应目标',fontsize=16,y=.98)
        handles,labels = axes[0].get_legend_handles_labels()
        fig.legend(handles,labels,ncol=7,loc='upper center',bbox_to_anchor=(.5,.92),frameon=False)
        fig.text(.5,.025,f"每组 {data['metadata']['trials_per_scenario_policy']:,} 条路径；仅计正式属性每升 1 点自带的奖励，不含加成、加值、日程额外奖励。",ha='center',fontsize=10)
        fig.subplots_adjust(top=.77,bottom=.17,wspace=.10,left=.08,right=.97)
        fig.savefig(args.directory/(name+'-curves.png'))
        plt.close(fig)

    fig, axes = plt.subplots(2,2,figsize=(13,8))
    for ax,name in zip(axes.flat,('pow','con','allocated_1','allocated_6')):
        for policy,color in zip(policies,('#2863A0','#B4512B')):
            r=scenarios[name,policy]
            x=[row['formal_attribute'] for row in r['rows']]
            ax.plot(x,[row['mean']+row['modifier'] for row in r['rows']],color=color,label=policies[policy],linewidth=2)
            ax.fill_between(x,[row['p10']+row['modifier'] for row in r['rows']],
                            [row['p90']+row['modifier'] for row in r['rows']],color=color,alpha=.12)
        ax.set_title(names[name],fontsize=12)
        ax.set_xlabel('正式属性值')
        ax.set_ylabel('全力检定期望值')
        ax.grid(axis='y',alpha=.18)
    fig.suptitle('成长选择的影响｜实线为平均值，阴影为养成结果的 10%–90% 范围',fontsize=15)
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,ncol=2,loc='upper center',bbox_to_anchor=(.5,.955),frameon=False)
    fig.text(.5,.018,'仅正式属性自身成长基准；阴影不是置信区间，不代表投骰结果范围。',ha='center',fontsize=10)
    fig.subplots_adjust(top=.85,bottom=.10,wspace=.24,hspace=.38)
    fig.savefig(args.directory/'expectation-comparison.png')
    plt.close(fig)

    if data['wake_fits']:
        fig, axes=plt.subplots(2,2,figsize=(13,8),sharex=True)
        for col,(policy,fit) in enumerate(data['wake_fits'].items()):
            rows=fit['rows']; x=np.array([r['pow'] for r in rows]); z=x-6
            formula=15+fit['a']*z*z+fit['b']*z
            axes[0,col].plot(x,formula,color='#2863A0',label='二次函数（取整前）')
            axes[0,col].plot(x,[r['target'] for r in rows],'o',color='#B4512B',label='实际整数目标',markersize=4)
            axes[0,col].set_title(policies[policy]+f"\na={fit['a']:.3f}，b={fit['b']:.2f}",fontsize=12)
            axes[0,col].set_ylabel('起床检定目标')
            axes[0,col].legend(frameon=False,fontsize=9)
            rates=np.array([r['success'] for r in rows])*100
            errors=np.array([r['mc_se'] for r in rows])*196
            axes[1,col].axhspan(70,75,color='#57795B',alpha=.12,label='期望范围 70%–75%')
            axes[1,col].errorbar(x,rates,yerr=errors,fmt='o-',color='#2863A0',markersize=4,capsize=2,label='模拟通过率 ± 1.96 SE')
            axes[1,col].set_ylim(min(68,min(rates-errors)-1),max(78,max(rates+errors)+1))
            axes[1,col].set_xlabel('正式意志 POW')
            axes[1,col].set_ylabel('通过率（%）')
            axes[1,col].legend(frameon=False,fontsize=9,loc='upper left')
            for ax in axes[:,col]:
                ax.set_xticks(range(6,21,2)); ax.grid(axis='y',alpha=.18)
        fig.suptitle('起床目标二次函数候选｜T = 四舍五入 [15 + a(POW−6)² + b(POW−6)]',fontsize=15)
        fig.text(.5,.02,'仅正式意志自身成长触发的奖励，全部兑现后测量；不含日程额外成长。候选曲线未写入游戏。',ha='center',fontsize=10)
        fig.subplots_adjust(top=.85,bottom=.11,hspace=.24,wspace=.23)
        fig.savefig(args.directory/'wake-quadratic-candidates.png')
        plt.close(fig)

    lines=['# 按正式属性值模拟骰子成长','',
           '横轴为正式属性值，比较随机选择与优先提高本次全力检定期望两种策略。本版已修正满面值强化和替换骰面规则，并重新运行模拟；旧版奖励次数曲线不再用于本版平衡参考。','',
           '## 模拟范围','',
           f"- 随机种子：{data['metadata']['seed']}；每配置每策略 {data['metadata']['trials_per_scenario_policy']:,} 条独立成长路径，从该配置初始属性成长至 {data['metadata']['max_attribute']}。",
           '- 配置：意志、体质，以及力量/灵巧/智识的初始分配 1～6。后三项使用相同规则，因此复用同一组分配结果，不重复模拟。',
           '- 稳定心情，无疲劳、负面附魔或精力限制。每次检定选择实际投掷期望最高的最多三颗骰；迅捷按两次取高计算。',
           '- 随机策略：三张卡位等概率选择；需要指定骰子或骰面时，也均匀随机选择。',
           '- 期望优先策略：根据已知卡面，精确计算本次奖励后最佳三骰的期望；随机目标按所有可能结果平均，不偷看结算结果。同分取最先列出的选择。它不是长期最优或通过率最优策略。',
           '- 两策略使用相同初始骰面种子，后续各自独立的随机流；不强行让已经分叉的奖励池抽到相同卡。',
           '- 成长口径：只计算正式属性自身增长。每增加 1 点正式属性，调用实际属性成长计数器、小休进度转换、待领奖励抽取与结算；奖励兑现后记录该属性点的数据。',
           '- 不包含属性加成、属性加值、日程和事件额外奖励，也不模拟退化、睡眠疲劳或迷雾。因此这是统一参考路径，不是完整日程养成的平均结果。',
           '- 每个骰池的投掷概率由精确卷积获得；抽样误差只来自成长路径，不来自重复投骰。',
           '', '## 期望对比','',
           '下表包含各属性点的 floor(min(属性, 20) × 0.5) 修正。不同初始分配分别保留，不能把相同最终属性但不同初始骰面的路径混为一条曲线。', '',
           '| 配置 | 策略 | 初始 | 属性 10 | 属性 15 | 属性 20 | 无变化奖励比例 |',
           '|---|---|---:|---:|---:|---:|---:|']
    for r in data['scenarios']:
        by_attribute={row['formal_attribute']:row for row in r['rows']}
        values=[f"{by_attribute[x]['mean']+by_attribute[x]['modifier']:.2f}" if x in by_attribute else '—'
                for x in (r['initial'],10,15,20)]
        total=data['metadata']['trials_per_scenario_policy']*(len(r['rows'])-1)
        lines.append('| '+ ' | '.join([names[r['name']],policies[r['policy']]]+values+[f"{r['outcomes'].get('no_change',0)/max(1,total):.1%}"])+ ' |')
    lines += ['', '![期望比较](expectation-comparison.png)','',
              '阴影为不同成长路径中“检定期望”的第 10～90 百分位，不是投骰结果区间，也不是平均值的置信区间。',
              '', '## 通过率曲线与数据库口径','',
              '每条曲线取满足 P(最终结果 ≥ 目标) 不低于指定通过率的最高整数目标。因此实际通过率可能高于标签；整数骰值不一定能精确实现 20%、30% 等概率。数据库同时保留该目标、实际概率、目标再加 1 的概率以及 Monte Carlo 标准误。',
              '以随机养成路径等权混合计算曲线，不能据此保证每一个具体骰组都达到标注概率。期望优先也可能降低某些阈值的通过率。','']
    for name in names:
        lines.append(f"- [{names[name]}的两策略曲线]({name}-curves.png)")
    lines += ['', '数据库：`dice-growth.sqlite`；可读数值导出：`summary.json`。',
              '', '- `growth`：按初始配置、策略、正式属性保存骰子期望、养成离散程度、当点修正和已结算奖励数。',
              '- `distribution`：0～60 原始骰点的完整混合概率、尾概率及尾概率标准误。',
              '- `target_curve`：20%～80% 的原始整数阈值。',
              '- `lookup`：加入当点正式属性修正的目标；按实际模拟的属性点查询，不再把任意属性和任意奖励次数交叉组合。',
              '- `expected_value`：加入属性修正的检定期望。',
              '- `metadata`：种子、模型范围、统计方法和局限。', '',
              '查询示例：正式意志 10，选择期望优先，目标通过率不低于 70%。', '',
              '```sql', "SELECT target, actual_probability, probability_at_next_target, pass_mc_se",
              "FROM lookup WHERE scenario='pow' AND policy='greedy'",
              'AND formal_attribute=10 AND requested_probability=0.7;', '```',
              '', '对 `distribution` 可计算任意已有目标的通过率：先减去属性修正，再查询对应 `raw_score` 的 `pass_probability`。95% 抽样区间可近似取概率 ± 1.96×标准误；这只反映成长抽样精度，不反映规则遗漏或未来改版误差。',
              '', '## 起床检定二次函数候选','',
              '初始意志 6、两枚初始骰全部投入、目标 15，通过率精确为 72.5%，结果期望为 19。两策略在未发生任何成长时完全一致。',
              '', '以下候选使用与主图一致的正式属性自身成长基准。其他成长来源会使同一意志值下的骰组不同，不能把这条参考路径当作所有玩家的平均成长。',
              '', '拟合区间 POW 6～20；令 z = POW − 6。下列公式按 floor(值 + 0.5) 四舍五入，锚定目标 15，并在此区间内单调不减。以逐级通过率接近 72.5% 为目标搜索简短系数。未修改现有程序的固定目标 15。','']
    for policy,fit in data['wake_fits'].items():
        outside=[str(r['pow']) for r in fit['rows'] if not .7-1e-12 <= r['success'] <= .75+1e-12]
        impossible=[str(r['pow']) for r in fit['rows'] if not r['attainable_targets_70_75']]
        lines += [f"### {policies[policy]}", '',
                  f"T = floor(15 + ({fit['a']:.3f}) × z² + {fit['b']:.2f} × z + 0.5)", '',
                  f"整数目标对应通过率范围：{fit['minimum_success']:.2%}～{fit['maximum_success']:.2%}。",
                  '超出 70%～75% 的意志档位：'+('、'.join(outside) or '无')+'。',
                  '连任意整数目标都无法落在 70%～75% 的档位：'+('、'.join(impossible) or '无')+'。','',
                  '| 意志 | 成长奖励 | 目标 | 通过率 | 约 95% 抽样误差 |','|---:|---:|---:|---:|---:|']
        lines += [f"| {r['pow']} | {r['reward_count']} | {r['target']} | {r['success']:.2%} | ±{1.96*r['mc_se']:.2%} |" for r in fit['rows']]
        lines.append('')
    lines += ['![二次函数候选及逐级通过率](wake-quadratic-candidates.png)','',
              '## 本版规则修正与边界','',
              '- 按手册 5.9：满面值不能作为强化目标；抽卡、选择列表和实际结算均排除。所有骰面均满时不抽强化卡；失效选择不消耗待领奖励。',
              '- 替换值按目标骰型生成，不再用骰池最大骰型。低值段为 ceil(骰型 × 0.1) 至 floor(骰型 × 0.4)，例如 d20 为 2～8。',
              '- 保留抽卡时预览数值：混合骰型卡分别显示各骰型的替换值，目标确定后采用对应值。同骰型共用该卡的一个面值；此预览方式是现有交互的延续，不是手册新增规则。',
              '- 无变化奖励仍可能来自替换成原值等合法情况，不能把该比例等同于程序错误。',
              '- 贪心会回避即时收益低的奖励，包括可能在以后才有价值的新骰或骰型升级；不能据此认定这些奖励设计无价值。',
              '- 这里没有采用现有训练难度函数推导成长频率，也没有模拟完整日程循环。二次函数的适用性取决于以后确认的参考成长路径。',
              '- 本次没有改变游戏里的检定难度或重写手册。','',
              '## 复现','',
              '程序：`tools/simulate_dice_growth.py`；绘图：`tools/plot_dice_growth.py`。依赖 NumPy，绘图额外依赖 Matplotlib。', '',
              '```text',
              'python tools/simulate_dice_growth.py --trials 2000 --max-attribute 20 --seed 20260920 --output <新的结果目录>',
              'python tools/plot_dice_growth.py <结果目录>', '```',
              '', '初始概率、迅捷精确分布、选牌评分、随机目标平均、种子复现、阈值顺序和长期骰型/数量限制均有可运行单元测试。']
    (args.directory/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Wrote 10 figures and README.md')


if __name__=='__main__':
    main()
