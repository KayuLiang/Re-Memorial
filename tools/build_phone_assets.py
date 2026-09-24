"""Small native vector controls; character art remains in the existing sprite files."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1] / "game/gui/phone_modern"


def svg(name, w, h, content):
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / (name + ".svg")).write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{content}</svg>', encoding="utf-8")


def build():
    svg("device", 660, 1320, '''
      <rect x="1" y="208" width="6" height="62" rx="3" fill="#899099"/>
      <rect x="1" y="294" width="6" height="106" rx="3" fill="#899099"/>
      <rect x="653" y="274" width="6" height="124" rx="3" fill="#899099"/>
      <rect x="5" y="1" width="650" height="1318" rx="75" fill="#555c65"/>
      <rect x="8" y="4" width="644" height="1312" rx="72" fill="#15191f" stroke="#aab0b6" stroke-width="2"/>
      <rect x="17" y="14" width="626" height="1292" rx="63" fill="#f5f6f8"/>
      <rect x="267" y="29" width="126" height="32" rx="16" fill="#171b22"/>
      <rect x="293" y="41" width="54" height="4" rx="2" fill="#454c57"/>
      <circle cx="370" cy="45" r="7" fill="#2e3743"/>
      <circle cx="370" cy="45" r="3" fill="#17252e"/>
    ''')
    for name, color in [("white", "#ffffff"), ("blue", "#2868c7"), ("soft", "#e8edf4"), ("avatar", "#dce6e9"), ("dark", "#202b3c")]:
        # Fixed-size nine-slice source avoids SVG raster seams in Ren'Py Frame.
        tile = Image.new("RGBA", (256, 256))
        ImageDraw.Draw(tile).rounded_rectangle((0, 0, 255, 255), radius=80, fill=color)
        tile.resize((64, 64), Image.Resampling.LANCZOS).save(ROOT / (name + ".png"))
    paths = {
        "messages": '<path d="M11 10h26v19H24l-8 7v-7h-5z"/><path d="M17 17h14M17 22h10"/>',
        "phone": '<path d="M15 9l7 7-5 5c3 5 5 7 10 10l5-5 7 7c-3 8-10 7-20-3S7 12 15 9z"/>',
        "weather": '<circle cx="19" cy="18" r="7"/><path d="M19 5v3M6 18h3M10 9l3 3M28 9l-3 3M15 35h21a7 7 0 0 0 0-14 10 10 0 0 0-18 3 6 6 0 0 0-3 11z"/>',
        "calendar": '<rect x="10" y="12" width="28" height="27" rx="4"/><path d="M10 21h28M17 8v8M31 8v8M17 28h4M27 28h4M17 33h4"/>',
        "notes": '<rect x="11" y="8" width="27" height="33" rx="4"/><path d="M17 17h15M17 24h15M17 31h10"/>',
        "recorder": '<rect x="19" y="7" width="10" height="23" rx="5"/><path d="M13 23a11 11 0 0 0 22 0M24 34v7M18 41h12"/>',
        "clock": '<circle cx="24" cy="24" r="16"/><path d="M24 13v12l8 5"/>',
        "album": '<rect x="8" y="10" width="32" height="28" rx="4"/><circle cx="18" cy="19" r="3"/><path d="M9 34l11-10 7 6 6-6 7 8"/>',
        "calculator": '<rect x="12" y="6" width="24" height="36" rx="4"/><path d="M17 13h14M17 21h3M28 21h3M17 28h3M28 28h3M17 35h3M28 35h3"/>',
        "back": '<path d="M29 10L15 24l14 14"/>',
        "close": '<path d="M14 14l20 20M34 14L14 34"/>',
        "send": '<path d="M24 37V11M13 22l11-11 11 11"/>',
    }
    for name, path in paths.items():
        color = "#2868c7" if name == "back" else "#ffffff"
        svg(name, 48, 48, f'<g fill="none" stroke="{color}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">{path}</g>')


if __name__ == "__main__":
    build()
