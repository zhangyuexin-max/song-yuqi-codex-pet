"""Install the release assets without replacing existing user content."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PET_ID = "song-yuqi-stage"
FILES = ("pet.json", "spritesheet.webp", "LICENSE.txt")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    configured_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    parser.add_argument("--pets-dir", type=Path, default=configured_home / "pets")
    args = parser.parse_args()
    source = ROOT / PET_ID
    payloads = {name: (source / name).read_bytes() for name in FILES}
    manifest = json.loads(payloads["pet.json"].decode("utf-8"))
    if manifest.get("id") != PET_ID or manifest.get("spritesheetPath") != "spritesheet.webp":
        raise ValueError("Unexpected pet manifest")
    checksums = {}
    for line in (ROOT / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        checksum, name = line.split("  ", 1)
        if not re.fullmatch(r"[0-9a-f]{64}", checksum):
            raise ValueError("Invalid checksum file")
        checksums[name] = checksum
    for name, data in payloads.items():
        if digest(data) != checksums.get(f"{PET_ID}/{name}"):
            raise ValueError(f"Integrity check failed: {name}")
    pets_dir = args.pets_dir.expanduser().resolve()
    target = pets_dir / PET_ID
    if target.is_symlink():
        raise FileExistsError("Refusing to use a symbolic-link pet directory")
    if target.exists():
        if target.is_dir() and all((target / name).is_file() and (target / name).read_bytes() == data
                                   for name, data in payloads.items()):
            print(f"Already installed; existing files preserved: {target}")
            return 0
        raise FileExistsError(f"Existing pet differs; nothing replaced: {target}")
    pets_dir.mkdir(parents=True, exist_ok=True)
    target.mkdir()
    for name, data in payloads.items():
        with (target / name).open("xb") as stream:
            stream.write(data)
        if (target / name).read_bytes() != data:
            raise OSError(f"Installed copy verification failed: {name}")
    print(f"Installed and verified: {target}")
    print("Open Settings > Pets > Refresh and choose the mint-stage pet.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit(str(exc)) from None
