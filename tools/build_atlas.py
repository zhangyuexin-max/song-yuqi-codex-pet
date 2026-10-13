"""Rebuild the v1 sheet by mechanically locating and packing approved AI poses."""
from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
COUNTS = [6, 8, 8, 4, 5, 8, 6, 6, 6]
SCALE = 1.2
JUMP = [0, 10, 20, 10, 0]


def components(image):
    width, height = image.size
    mask = bytearray(image.getchannel("A").point(lambda value: 1 if value >= 32 else 0).tobytes())
    figures = []
    for start in range(len(mask)):
        if not mask[start]:
            continue
        queue = deque([start])
        mask[start] = 0
        x0 = x1 = start % width
        y0 = y1 = start // width
        pixels = 0
        while queue:
            index = queue.popleft()
            x, y = index % width, index // width
            pixels += 1
            x0, x1, y0, y1 = min(x0, x), max(x1, x), min(y0, y), max(y1, y)
            for ny in range(max(0, y - 1), min(height, y + 2)):
                for nx in range(max(0, x - 1), min(width, x + 2)):
                    neighbor = ny * width + nx
                    if mask[neighbor]:
                        mask[neighbor] = 0
                        queue.append(neighbor)
        if pixels >= 1000:
            assert x1 - x0 < 200 and y1 - y0 < 200, "Touching figures need artwork repair"
            figures.append({"cx": (x0 + x1) / 2, "cy": (y0 + y1) / 2,
                            "crop": (max(0, x0 - 2), max(0, y0 - 2), min(width, x1 + 3), min(height, y1 + 3))})
    assert len(figures) == sum(COUNTS), "Expected exactly 57 separate figures"
    return sorted(figures, key=lambda figure: figure["cy"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "sources" / "approved-motion-atlas.png")
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "rebuilt.webp")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Output already exists; choose a new output filename")
    source = Image.open(args.source).convert("RGBA")
    figures = components(source)
    sheet = Image.new("RGBA", (1536, 1872), (0, 0, 0, 0))
    offset = 0
    for row, count in enumerate(COUNTS):
        group = figures[offset:offset + count]
        assert max(item["cy"] for item in group) - min(item["cy"] for item in group) < 35
        offset += count
        for col, item in enumerate(sorted(group, key=lambda figure: figure["cx"])):
            crop = source.crop(item["crop"])
            pose = crop.resize(tuple(round(value * SCALE) for value in crop.size), Image.Resampling.LANCZOS)
            x = (192 - pose.width) // 2
            y = 194 - pose.height - (JUMP[col] if row == 4 else 0)
            assert x >= 0 and y >= 0 and x + pose.width <= 192 and y + pose.height <= 208
            sheet.alpha_composite(pose, (col * 192 + x, row * 208 + y))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, format="WEBP", lossless=True, quality=100, method=6)
    with Image.open(args.output) as saved:
        assert saved.size == sheet.size and saved.mode == "RGBA"
        assert saved.getchannel("A").tobytes() == sheet.getchannel("A").tobytes()
        for expected, actual in zip(sheet.get_flattened_data(), saved.get_flattened_data()):
            assert expected[3] == 0 or expected == actual
    print(f"Rebuilt and decoded: {args.output}")


if __name__ == "__main__":
    main()
