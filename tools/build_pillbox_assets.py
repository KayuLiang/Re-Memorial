"""Cut supplied art into runtime layers. No generated or repainted artwork.

Usage: python tools/build_pillbox_assets.py EMPTY_BOX.png PILL_SHEET.png
"""
from collections import deque
from pathlib import Path
import math
import sys
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BOX = ROOT / "game/gui/pillbox"
PILLS = ROOT / "game/gui/pills"


def component(mask, seed):
    """Keep a connected silhouette, including the opaque black ink inside it."""
    pix = mask.load()
    result = Image.new("L", mask.size)
    out = result.load()
    queue = deque([seed])
    out[seed] = 255
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0 <= nx < mask.width and 0 <= ny < mask.height and pix[nx,ny] and not out[nx,ny]:
                out[nx,ny] = 255
                queue.append((nx,ny))
    return result


def build(box_path, sheet_path):
    BOX.mkdir(parents=True, exist_ok=True)
    PILLS.mkdir(parents=True, exist_ok=True)
    original = Image.open(box_path).convert("RGBA")
    original.save(BOX / "pillbox_empty.png")
    white = original.convert("L").point(lambda v: 255 if v > 230 else 0)
    outside = component(white, (0,0))
    original.putalpha(ImageChops.invert(outside))
    # Preserve the printed centre (627,577), including asymmetric hinge/latch.
    shell = original.crop((47,-3,1207,1157))
    shell.save(BOX / "pillbox_outer.png")
    inner_mask = Image.new("L", shell.size)
    ImageDraw.Draw(inner_mask).ellipse((111,111,1049,1049), fill=255)
    tray = shell.copy()
    tray.putalpha(ImageChops.multiply(shell.getchannel("A"), inner_mask))
    tray.save(BOX / "pillbox_inner.png")
    pointer = shell.copy()
    pointer_mask = Image.new("L", shell.size)
    ImageDraw.Draw(pointer_mask).rectangle((469,1053,686,1152), fill=255)
    pointer.putalpha(ImageChops.multiply(shell.getchannel("A"), pointer_mask))
    pointer.save(BOX / "pillbox_pointer.png")
    for slot in range(8):
        # Native 1020px UI coordinates; bottom is slot 0, clockwise positive.
        mask = Image.new("RGBA", (1020,1020))
        points = []
        for radius, angles in ((412,range(-21,22)), (135,range(21,-22,-1))):
            points += [(510-radius*math.sin(math.radians(slot*45+a)),
                        510+radius*math.cos(math.radians(slot*45+a))) for a in angles]
        ImageDraw.Draw(mask).polygon(points, fill="white")
        mask.save(BOX / ("slot_%d.png" % slot))
    sheet = Image.open(sheet_path).convert("RGBA")
    sheet.save(PILLS / "source_sheet.png")
    alpha = sheet.getchannel("A")
    mask = alpha.point(lambda v: 255 if v > 100 else 0)
    # Stable, distinct silhouettes from the user's sheet; no random reassignment.
    seeds = dict(venlafaxine=(750,310), trazodone=(520,310), alprazolam=(220,245),
                 lithium=(1000,280), aripiprazole=(650,645), lamotrigine=(148,640))
    for drug, seed in seeds.items():
        part = component(mask,seed)
        bounds = part.getbbox()
        sprite = sheet.copy()
        # Extend one pixel to retain the source's antialiased contour.
        from PIL import ImageFilter
        part = part.filter(ImageFilter.MaxFilter(3))
        sprite.putalpha(ImageChops.multiply(alpha,part))
        sprite = sprite.crop((bounds[0]-2,bounds[1]-2,bounds[2]+2,bounds[3]+2))
        sprite.save(PILLS / (drug+".png"))
        print(drug, sprite.size)


if __name__ == "__main__":
    build(*sys.argv[1:])
