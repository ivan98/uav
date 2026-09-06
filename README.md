
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
