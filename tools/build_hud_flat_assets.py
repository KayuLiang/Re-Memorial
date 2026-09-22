"""Build HUD vectors: licensed navigation icons and reference-led meter geometry."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1] / "game/gui/hud_flat"
IVORY = "#f3eee3"
INK = "#292923"


def svg(name, width, height, content):
    # Keep the approved vector geometry; rasterize at native QHD dimensions.
    (ROOT / (name + ".svg")).write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s">%s</svg>'
        % (round(width * 4 / 3), round(height * 4 / 3), width, height, content), encoding="utf-8")


def icon_paths(name, color, outline=False):
    root = ET.parse(ROOT / "source" / (name + ".svg")).getroot()
    border = ' stroke="#292923" stroke-width="6" stroke-linejoin="round"' if outline else ''
    return ''.join('<path d="%s" fill="%s"%s/>' % (p.attrib["d"], color, border)
                   for p in root.iter() if p.tag.endswith("path"))


def build():
    # Single-colour cover: no corner shading or cast shadow. Widen only the
    # paper, preserving the outer footprint and all content/hit-box anchors.
    page = '<rect x="0" y="8" width="1840" height="236" rx="4" fill="#aa824d"/>'
    # Exposed cover 12px + tightly stacked paper 8px on either side.
    page += '<path d="M18 12 H1822 Q1828 12 1828 18 V233 Q1828 240 1822 240 H18 Q12 240 12 234 V18 Q12 12 18 12 Z" fill="#d9d2c3"/>'
    page += '<path d="M20 10 H1820 Q1825 10 1825 15 V233 Q1825 238 1820 238 H20 Q15 238 15 233 V15 Q15 10 20 10 Z" fill="#e8e2d6"/>'
    page += '<path d="M24 8 H1816 Q1820 8 1820 12 V232 Q1820 236 1816 236 H24 Q20 236 20 232 V12 Q20 8 24 8 Z" fill="%s"/>' % IVORY
    # No water mark: the vector trial read as a brush decoration at game scale.
    svg("notebook_page", 1840, 252, page)
    svg("photo_mount", 144, 160,
        '<rect x="3" y="4" width="141" height="156" fill="#292923" fill-opacity=".12"/>'
        '<rect x=".5" y=".5" width="139" height="155" fill="#fcf8ee" stroke="#b1a58e"/>'
        '<rect x="10" y="10" width="120" height="132" fill="#ded7c7"/>')
    svg("photo_clip", 22, 44,
        '<path d="M7 34 V10 C7 2 18 2 18 10 V34 C18 43 3 43 3 34 V14 C3 9 11 9 11 14 V31" fill="none" stroke="#6a6558" stroke-width="2.3" stroke-linecap="round"/>')

    for name in ("pill", "device-mobile", "backpack", "dice-five", "user-square", "play", "clock-counter-clockwise"):
        # Original silhouettes, same 256-unit icon family and optical canvas.
        for variant, color in (("idle", IVORY), ("hover", "#c5b889"), ("ink", INK)):
            svg(name + "_" + variant, 72, 72,
                '<g transform="translate(4 4) scale(.25)">%s</g>' % icon_paths(name, color, variant != "ink"))

    # Long stems are occluded by the foreground page; only the tips protrude.
    for name in ("article", "eye-slash", "arrows-clockwise", "fast-forward", "sliders-horizontal"):
        for variant, color in (("idle", "#514d43"), ("hover", INK), ("selected", "#40502d")):
            paper = {"idle": "#e5dcc6", "hover": IVORY, "selected": "#dbe0ca"}[variant]
            content = '<path d="M3 88 V9 Q3 3 9 3 H64 Q69 3 69 9 V88" fill="#292923" fill-opacity=".15"/>'
            content += '<path d="M1 88 V8 Q1 1 8 1 H64 Q71 1 71 8 V88" fill="%s"/>' % paper
            content += '<path d="M1 88 V8 Q1 1 8 1 H64 Q71 1 71 8 V88" fill="none" stroke="%s" stroke-opacity=".42" stroke-width=".8"/>' % color
            # Clean library placeholder. Final PS/brush artwork belongs to user.
            content += '<g transform="translate(16 4) scale(.15625)">%s</g>' % icon_paths(name, color)
            if variant == "selected":
                content += '<path d="M25 45 Q36 44 47 45" fill="none" stroke="%s" stroke-width="1.5" stroke-linecap="round"/>' % color
            svg("dialogue_" + name + "_" + variant, 72, 88, content)

    # The scientific library icon did not match the approved flat silhouette.
    # User-approved custom soma, short rounded dendrites and a blue nucleus.
    neuron = (
        'M104 42 C79 42 65 45 61 31 '
        'C59 25 59 19 60 11 C61 6 59 3 56 3 C52 3 51 6 52 11 '
        'C53 23 49 29 41 27 C35 25 29 19 26 13 '
        'C24 8 19 10 20 15 C21 20 29 27 29 33 '
        'C29 39 23 43 17 40 L10 36 C5 34 3 38 7 41 '
        'L15 44 C20 47 19 50 14 51 L6 53 C1 54 2 60 7 59 '
        'L17 55 C26 51 32 56 33 64 C34 73 27 80 20 86 '
        'C15 89 17 94 22 93 C27 92 29 85 35 82 '
        'C44 76 50 79 52 86 L55 96 C57 101 63 99 62 94 '
        'C57 85 61 72 70 66 C77 62 88 62 104 62 Z'
    )
    svg("neuron", 108, 104,
        '<path d="%s" fill="%s" stroke="#29292390" stroke-width="1.2" stroke-linejoin="round"/>'
        '<circle cx="48" cy="52" r="11" fill="#518fc2"/>' % (neuron, IVORY))

    for name, color in (("lightning", "#778252"),):
        # Track and icon overlap. The coloured neck is drawn last across the
        # icon's right outline: no cap or white seam at the horizontal join.
        for suffix, fill in (("track", IVORY), ("fill", color)):
            content = '<rect x="36" y="18" width="376" height="16" rx="8" fill="%s"/>' % IVORY
            content += '<g transform="translate(-2 -2) scale(.21875)">%s</g>' % icon_paths(name, IVORY)
            content += '<g transform="scale(.203125)">%s</g>' % icon_paths(name, color)
            content += '<rect x="37" y="21" width="372" height="10" rx="5" fill="%s"/>' % fill
            content += '<rect x="36" y="21" width="24" height="10" fill="%s"/>' % color
            svg(name + "_" + suffix, 416, 52, content)

    for name, color in (("heart", "#b4776e"), ("star", "#956aac")):
        svg(name + "_reserved", 64, 64,
            '<circle cx="32" cy="32" r="29" fill="#292923" stroke="%s" stroke-width="2"/><g transform="translate(16 16) scale(.125)">%s</g>'
            % (IVORY, icon_paths(name, color)))

    svg("mood_track", 548, 24, '<defs><linearGradient id="m"><stop stop-color="#518fc2"/><stop offset=".5" stop-color="#e5e0d3"/><stop offset="1" stop-color="#bc4946"/></linearGradient></defs><rect x="1" y="2" width="546" height="20" rx="10" fill="%s"/><rect x="4" y="5" width="540" height="14" rx="7" fill="url(#m)"/>' % IVORY)
    svg("needle", 20, 38, '<path d="M10 1 L19 19 L10 37 L1 19 Z" fill="%s"/><path d="M10 5 L15 19 L10 33 Z" fill="%s"/><path d="M10 5 L10 33 L5 19 Z" fill="%s"/>' % (IVORY, IVORY, INK))
    for state in ("past", "current", "future"):
        circles = '<circle cx="9" cy="9" r="6" fill="%s" stroke="%s" stroke-width="1.5"/>' % (IVORY if state == "past" else INK, IVORY)
        if state == "current":
            circles = '<circle cx="9" cy="9" r="8" fill="none" stroke="%s" stroke-width="1.5"/>' % IVORY + circles
        svg("hole_" + state, 18, 18, circles)
    svg("clock_case", 336, 168, '<rect x="0" y="3" width="336" height="165" rx="18" fill="#1d1e1c"/><rect x="2" y="1" width="332" height="164" rx="17" fill="%s"/><rect x="5" y="4" width="326" height="158" rx="14" fill="%s"/><rect x="8" y="7" width="320" height="152" rx="12" fill="none" stroke="#716f65" stroke-width="1"/>' % (IVORY, INK))
    # Seven-segment display geometry, not an icon or font dependency.
    # Bevelled, thick seven-segment strokes with a slight rightward lean.
    segments = ["9,1 35,1 40,6 35,11 9,11 4,6", "39,8 44,13 44,34 39,39 34,34 34,13", "39,41 44,46 44,67 39,72 34,67 34,46", "9,70 35,70 40,75 35,80 9,80 4,75", "5,41 10,46 10,67 5,72 0,67 0,46", "5,8 10,13 10,34 5,39 0,34 0,13", "9,35 35,35 40,40 35,45 9,45 4,40"]
    mapping = ("012345", "12", "01643", "01263", "5612", "05623", "056234", "012", "0123456", "012356")
    for mode, color in (("day", IVORY), ("night", "#cd5047")):
        for digit, on in enumerate(mapping):
            content = ''.join('<polygon points="%s" fill="%s"/>' % (segments[int(s)], color) for s in on)
            svg("digit_%s_%s" % (mode, digit), 54, 82, '<g transform="translate(8 0) skewX(-6)">%s</g>' % content)
        svg("colon_" + mode, 14, 80, '<circle cx="7" cy="25" r="3" fill="%s"/><circle cx="7" cy="56" r="3" fill="%s"/>' % (color, color))


if __name__ == "__main__":
    build()
