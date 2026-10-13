"""Validate release assets, atlas cell bounds, and download integrity."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
COUNTS = [6, 8, 8, 4, 5, 8, 6, 6, 6]
PET_ID = "song-yuqi-stage"


def main():
    for line in (ROOT / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError("Checksum path escapes repository")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Checksum mismatch: {name}")
    manifest = json.loads((ROOT / PET_ID / "pet.json").read_text(encoding="utf-8"))
    assert manifest["id"] == PET_ID and manifest["spritesheetPath"] == "spritesheet.webp"
    with Image.open(ROOT / PET_ID / manifest["spritesheetPath"]) as source:
        source.load()
        assert source.format == "WEBP" and source.mode == "RGBA" and source.size == (1536, 1872)
        used = unused = 0
        for row, count in enumerate(COUNTS):
            unique = set()
            for col in range(8):
                cell = source.crop((col * 192, row * 208, (col + 1) * 192, (row + 1) * 208))
                alpha = cell.getchannel("A")
                if col >= count:
                    assert alpha.getextrema() == (0, 0)
                    unused += 1
                    continue
                box = alpha.point(lambda value: 255 if value >= 32 else 0).getbbox()
                assert box is not None
                x0, y0, x1, y1 = box
                assert x0 >= 6 and y0 >= 6 and x1 <= 186 and y1 <= 202, (row, col, box)
                edges = [alpha.crop((0, 0, 192, 1)), alpha.crop((0, 207, 192, 208)),
                         alpha.crop((0, 0, 1, 208)), alpha.crop((191, 0, 192, 208))]
                assert all(edge.getextrema() == (0, 0) for edge in edges)
                unique.add(hashlib.sha256(cell.tobytes()).hexdigest())
                used += 1
            assert len(unique) == count
        assert used == 57 and unused == 15
    with zipfile.ZipFile(ROOT / "downloads" / f"{PET_ID}.zip") as archive:
        assert archive.testzip() is None
        assert sorted(archive.namelist()) == [f"{PET_ID}/LICENSE.txt", f"{PET_ID}/pet.json", f"{PET_ID}/spritesheet.webp"]
        for name in ("pet.json", "spritesheet.webp", "LICENSE.txt"):
            assert archive.read(f"{PET_ID}/{name}") == (ROOT / PET_ID / name).read_bytes()
    with Image.open(ROOT / "assets" / "preview.gif") as animation:
        assert animation.n_frames == 120 and animation.info["loop"] == 0
        for index in range(animation.n_frames):
            animation.seek(index)
            animation.load()
            assert animation.info["duration"] == 120
    print("PASS: release hashes, 57 frames, 15 empty cells, bounds, ZIP, and 120 GIF frames")


if __name__ == "__main__":
    main()
