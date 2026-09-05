# Changelog

All notable changes to this fork are documented here, one entry per commit.
Entries marked **(major)** are also appended to the "Changelog" section at
the end of `README.md`. History before the fork point belongs to
[Alos21750/UAV-Downloader](https://github.com/Alos21750/UAV-Downloader) and
is not repeated here.

## 2026-09-05

- Forked from `Alos21750/UAV-Downloader` as `ivan98/uav`. Changelog starts
  here.
- **(major)** Added `flake.nix` providing two per-project Nix dev shells:
  `nix develop` (headless/CLI, matches `requirements-docker.txt`) and
  `nix develop .#gui` (full GUI + local AI subtitles, matches
  `requirements.txt`). Both auto-create a venv and `pip install` from the
  matching requirements file on shell entry, and set `LD_LIBRARY_PATH` /
  `PYTHONPATH` so compiled wheels (numpy, ctranslate2, tkinter's
  `_tkinter`, etc.) load correctly under NixOS's non-FHS layout. Added
  `.envrc` for direnv.
