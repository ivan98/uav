
This is a fork of https://github.com/Alos21750/UAV-Downloader

## Fork-specific documentation

Docs for fork-only features, kept here so `README.md` can stay identical to
upstream's.

- `uav-browser --nogui --watch-urls-file {once,forever}`: only applies when
  `--url` is omitted. Instead of prompting, waits (event-driven, not polling)
  for URLs to appear in `<output>/urls.txt`. `once` processes what it finds and
  exits; `forever` keeps watching for new URLs. Examples:
  `uav-browser --nogui --watch-urls-file once` and
  `uav-browser --nogui --watch-urls-file forever --output "/path/to/downloads"`.
- Docker: if no URL is passed and `URLS_FILE` (default `/downloads/urls.txt`)
  does not exist yet or is empty, the container waits for it instead of exiting.
  `URLS_WATCH_MODE` is `once` (default; process what is found, then exit) or
  `forever` (keep watching `URLS_FILE`, never exit).

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
- Fixed `uav-browser --nogui` showing no download progress for
  SupJav/Hanime1's Streamtape fallback (it now prints downloaded/total MB,
  percentage, speed, and ETA, matching the FST/HLS path).

### 2026-09-06

- Fixed `uav-browser --nogui` always printing console output in Traditional
  Chinese regardless of language/locale settings. It now goes through the
  same `i18n` system as the GUI and defaults to English, including the
  error messages a SupJav download hits on failure (shared m3u8/AES parsing
  errors, and SupJav's own page-parse / no-source / direct-download error
  messages).
- The Docker/NAS CLI no longer exits immediately when no URL is given and
  `urls.txt` doesn't exist yet — it now waits for the file (event-driven,
  no polling). New `URLS_WATCH_MODE=once|forever` env var; `forever` keeps
  the container running and picks up new URLs appended to `urls.txt` later.
  `uav-browser --nogui` gets the same behavior via a new opt-in
  `--watch-urls-file {once,forever}` flag when `--url` is omitted — without
  the flag, it still falls back to the interactive prompt exactly as
  before.
- Fixed a restart loophole in `urls.txt`-watch mode: a killed-and-restarted
  process used to re-read and re-attempt every URL still in the file,
  since dedup only lived in memory. A URL's line is now removed from the
  file once it's fully handled (downloaded, or already on disk); failed
  URLs are left in place so a restart retries them.
- Merged upstream: SupJav search rate-limit retries and AI subtitles for videos already on disk (slow-download requeue and storage-failure fixes still pending, they conflict with this fork).
- Merged the rest of upstream (UAV 3.2): slow-download requeue, storage-failure handling, SupJav multi-provider fallbacks, safe Browser shutdown.
- Nix dev shells now use the system's Python (3.13) instead of a separate pinned 3.12; flake.lock follows the system nixpkgs.
- Nix dev shells now editable-install the project, so `uav`, `uav-browser`, `uav-watcher` etc. are on PATH inside `nix develop`.
