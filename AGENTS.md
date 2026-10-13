# Project guide

- This repository contains one fan-made, AI-generated v1 desktop pet.
- `song-yuqi-stage/` contains the installable manifest and sprite sheet.
- `assets/` contains previews; `sources/` contains approved AI artwork and prompts.
- `tools/` contains standard-library installation code and Pillow-based build/validation tools.
- Code uses MIT. Artwork licensing is defined separately in `ARTWORK-LICENSE.md`; preserve that scope.
- Keep private paths, credentials, account identifiers and local diagnostic logs out of public files.
- Do not add the reference photograph or assets from other pets.
- Never replace an existing installed pet with different contents automatically.

## Verified commands

```sh
python tools/validate.py
python tools/build_atlas.py --output build/rebuilt.webp
python tools/install.py --pets-dir build/test-pets
```

For development, install `requirements-dev.txt`. Installation of the ready-made pet uses only the Python standard library.

Before publishing, validate the saved assets, compare rebuilt visible pixels with the released sheet, review README links, and confirm the account, repository visibility and artwork license. Do not claim native application playback was tested unless it was actually observed.
