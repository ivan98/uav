
This is a fork of https://github.com/Alos21750/UAV-Downloader

## Changelog

Major changes only — see [CHANGELOG.md](CHANGELOG.md) for the full,
commit-by-commit history.

### 2026-09-05

- Added a Nix flake (`flake.nix`) for per-project dev environments:
  `nix develop` for headless/CLI work, `nix develop .#gui` for the full GUI +
  local AI subtitles stack.
- Added `--filename-mode {full-title,code-only}` to `uav-browser --nogui`,
  bringing the GUI-only filename-format setting to the CLI. Defaults to
  `code-only`, independent of the persisted GUI setting; pass
  `--filename-mode full-title` to get the GUI's default instead. Also fixed
  `code-only` leaving leading `[Tag][Tag]`-style bracket prefixes in the
  filename instead of just the actual code.

