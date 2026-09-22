"""Original vector moon discs. Run to regenerate Ren'Py UI assets, not AI images."""
from pathlib import Path
import math

OUT = Path(__file__).resolve().parents[1]/'game/gui/dice_obsidian'
for count in (4,6,8,10,12,20):
    for index in range(count):
        phase = .12+.76*index/max(1,count-1)
        k = math.cos(math.tau*phase)
        if abs(k)<.4: k=.4 if k>=0 else -.4
        limb, terminator = [],[]
        for i in range(129):
            y=-90+180*i/128
            x=math.sqrt(max(0,90*90-y*y))
            sign=1 if phase<=.5 else -1
            limb.append((100+sign*x,100+y))
            terminator.append((100+sign*k*x,100+y))
        points=' '.join('%.3f,%.3f'%p for p in limb+list(reversed(terminator)))
        for selected in (False,True):
            stroke='#b69452' if selected else '#7b7c70'
            svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><circle cx="100" cy="100" r="90" fill="#11191d"/><polygon points="{points}" fill="#dfd4ae"/><circle cx="100" cy="100" r="90" fill="none" stroke="{stroke}" stroke-width="{5 if selected else 1}"/></svg>'
            (OUT/f'moon-{count}-{index}{"-selected" if selected else ""}.svg').write_text(svg,encoding='utf-8')
(OUT/'moon-focus.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><circle cx="100" cy="100" r="94" fill="none" stroke="#b69452" stroke-width="3"/></svg>',encoding='utf-8')
print('120 moon variants and focus ring generated')
