from pathlib import Path
import random
import re
import struct
import zlib


ROOT = Path(__file__).resolve().parents[1]
GUI_FILE = ROOT / "game" / "gui.rpy"
OUTPUT_DIR = ROOT / "game" / "images" / "effects"

SCANLINE_SPACING = 8
SCANLINE_THICKNESS = 4
SCANLINE_ALPHA = 36
NOISE_ALPHA_MAX = 22
NOISE_DENSITY = 0.018
NOISE_SEEDS = (731, 941, 1151)


def project_size():
    match = re.search(r"gui\.init\(\s*(\d+)\s*,\s*(\d+)\s*\)", GUI_FILE.read_text(encoding="utf-8-sig"))
    return (int(match.group(1)), int(match.group(2))) if match else (1920, 1080)


def png_chunk(name, data):
    return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)


def write_rgba_png(path, width, height, rows):
    raw = b"".join(b"\x00" + row for row in rows)
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(raw, 9))
        + png_chunk(b"IEND", b"")
    )


def generate_scanlines(width, height):
    clear = bytes(width * 4)
    line = bytes((224, 230, 232, SCANLINE_ALPHA)) * width
    rows = (
        line if y % SCANLINE_SPACING < SCANLINE_THICKNESS else clear
        for y in range(height * 2)
    )
    write_rgba_png(OUTPUT_DIR / "crt_scanlines.png", width, height * 2, rows)


def generate_noise(width, height, seed, index):
    rng = random.Random(seed)
    rows = []
    for _ in range(height):
        row = bytearray(width * 4)
        for x in range(width):
            if rng.random() < NOISE_DENSITY:
                value = rng.randrange(180, 256)
                offset = x * 4
                row[offset:offset + 4] = bytes((value, value, value, rng.randrange(5, NOISE_ALPHA_MAX + 1)))
        rows.append(bytes(row))
    write_rgba_png(OUTPUT_DIR / f"crt_noise_{index:02}.png", width, height, rows)


def main():
    width, height = project_size()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generate_scanlines(width, height)
    noise_width = max(1, width // 4)
    noise_height = max(1, height // 4)
    for index, seed in enumerate(NOISE_SEEDS, 1):
        generate_noise(noise_width, noise_height, seed, index)
    print(f"Generated CRT assets for {width}x{height} in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
