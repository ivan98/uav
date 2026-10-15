# Changelog

All notable changes to this fork are documented here, one entry per commit.
Entries marked **(major)** are also appended to the "Changelog" section at
the end of `README.ilgw.md`. History before the fork point belongs to
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
- **(major)** Added `--filename-mode {full-title,code-only}` to `uav-browser
  --nogui`, matching the filename-format setting that was previously GUI-only.
  Threaded an optional `filename_mode` override through
  `M3U8Crawler.__init__`, `create_site`/`CreateSite`, and `consoles_main`.
  Defaults to a hardcoded `code-only` — the CLI does not depend on
  `ui_prefs.json`'s `filename_mode`; pass `--filename-mode full-title`
  explicitly to get the GUI's default instead. GUI behavior is unchanged.
  Also fixes `_apply_filename_mode` leaving leading `[Tag][Tag]`-style
  bracket prefixes in place under `code-only` — it previously just kept
  everything before the first whitespace, so a title like
  `[Uncensored][Leaked] ABCD-123 ...` produced `[Uncensored][Leaked]`
  instead of the actual code; now strips any run of leading
  `[...]`-bracketed segments first. Documented the flag in `README.en.md`
  and added regression tests in `tests/test_nogui_cli.py` and
  `tests/test_filename_mode.py`.
- **(major)** Fixed `uav-browser --nogui` showing no download progress for
  SupJav/Hanime1's Streamtape (ST) fallback. The FST (fc2stream HLS) path
  already printed progress via the shared `M3U8Crawler._scrape` segment
  loop; the ST progressive-MP4 fallback (`SiteSupJav._download_direct_ranges`
  / `_download_direct_serial`) only invoked `_progress_callback`, a hook the
  GUI wires to its progress bar but the CLI never sets. Added a
  `_format_direct_progress` helper and console `print` alongside the
  existing callback, showing downloaded/total MB, percentage, speed, and ETA
  (falls back to bytes-only when the server doesn't report a total size).
  `SiteHanime1` inherits the same code path, so its Streamtape fallback is
  fixed too. Added regression tests in `tests/test_supjav.py`.

## 2026-09-06

- **(major)** Wired `uav-browser --nogui`'s console output through the
  existing `i18n` system instead of hardcoded Traditional Chinese. The GUI
  already called `set_lang(config.get_ui_lang() or 'en')` and rendered every
  label via `T(key)`; the headless path (`consoles_main` in
  `sites/__init__.py`, and every progress/status `print`/`raise Exception` in
  `sites/base.py` and `sites/supjav.py` — file name, save location, segment
  counts, merge/remux progress, download-complete, cancel, error messages)
  never imported `i18n` at all, so it printed raw zh-TW literals regardless
  of the user's language preference or locale. Added ~30 new `console_*`
  translation keys (en/zh/zh-Hans/ja) to `i18n/locales.py` and call
  `set_lang(config.get_ui_lang() or 'en')` at the top of `consoles_main`, so
  `--nogui` now defaults to English (or the persisted GUI language) like the
  GUI does. This first pass only covered the happy path, though — on
  failure, `sites/base.py`'s shared `_load_m3u8`/`_create_m3u8` (m3u8
  fetch/content-invalid, AES key fetch, no valid segments — used by every
  site's FST/HLS path, supjav.com included) and `sites/supjav.py`'s own ~12
  exceptions (page-parse failure, no server source, and the whole
  Streamtape (ST) direct-download error path: range mismatch, segment
  overflow, write failure, no data / connection-ended-early, resume/HTTP
  failure, incomplete download) were still hardcoded zh-TW, directly
  reachable from a plain SupJav download via `uav-browser --nogui`. Added
  16 more `console_*` keys (en/zh/zh-Hans/ja) to cover them too. Out of
  scope for this pass, still hardcoded zh-TW: `sites/missav.py` and
  `sites/hanime1.py`'s own error strings, `sites/jabletv.py`'s listing-page
  print, and the Docker/NAS `cli/headless.py` entrypoint.
- **(major)** The `uav-downloader` Docker/NAS CLI (`cli/headless.py`) no
  longer fails immediately with exit code 2 when no URL was given and
  `urls.txt` doesn't exist yet — it now waits for the file to be created or
  written to, event-driven via the new `watchdog` dependency (not polling).
  Added `src/uav_downloader/core/urls_watch.py`'s `iter_url_batches()`,
  shared logic that yields batches of not-yet-seen URLs from a
  line-delimited file, blocking between batches as needed. New
  `$URLS_WATCH_MODE` env var: `once` (default — process whatever shows up,
  then exit, matching today's one-shot semantics) or `forever` (never
  exit; new lines appended to `urls.txt` later are picked up and downloaded
  without restarting the container). Dedup in `forever` mode is in-memory
  only, not persisted across restarts. `uav-browser --nogui` reuses the
  same `iter_url_batches()` via a new opt-in `--watch-urls-file
  {once,forever}` flag that only takes effect when `--url` is omitted —
  without the flag, omitting `--url` still falls back to today's `input()`
  prompt exactly as before, so this is fully backward-compatible.
  `consoles_main` (`sites/__init__.py`) is restructured to loop over
  batches of URLs instead of handling exactly one; a directly-supplied
  `--url` still takes the same fast path as before, bypassing the watch
  logic entirely. Added `watchdog>=4.0.0` to
  `requirements.txt`/`requirements-docker.txt`. Documented in
  `cli/args.py`'s help text, `docs/docker-cli.md`, and all four README
  locales.
- **(major)** Closed a restart loophole in `urls.txt`-watch mode: the
  dedup in `iter_url_batches()` is in-memory only, so a killed-and-restarted
  process would re-read every URL still in the file and re-attempt it. Added
  `remove_consumed_url()` to `core/urls_watch.py`, called from both
  `cli/headless.py` and `consoles_main` right after a URL is fully handled
  (downloaded, or already on disk) — its line is dropped from the file so a
  restart won't see it again. Failed URLs are deliberately left in place so
  a restart retries them, rather than silently dropping a permanently-bad
  URL after one attempt. Added regression tests covering both the
  consumed-on-success and kept-on-failure paths.

## 2026-10-15

- **(major)** Merged the conflict-free part of upstream
  `Alos21750/UAV-Downloader` (upstream commits up to `6f3b57c`, via
  `7bd9ed2`, `bc06cfe`, `6f3b57c`). Brings in: SupJav search rate limits are
  now waited out with retries instead of being reported as a block (PR #49);
  `uav-browser` can generate AI subtitles for videos already on disk (PR #50,
  including a fix for reporting a moved file when retrying); plus upstream's
  star-history refreshes. Deliberately **not** merged yet because they
  conflict with this fork: slow-download requeue (`07c2b46`, `805e6fd`; clashes
  in `apps/browse.py` with the local-subtitles change), the storage-failure
  retry fix (`5f256d7`, conflicts in `cli/headless.py` and `sites/base.py`),
  the UAV 3.2 integration (`48e6b77`) and the frozen-startup Browser fix
  (`ebf29fb`).
- Reversed the fork-point README swap: `README.md` is once again upstream's
  file verbatim (so upstream README changes merge without conflicts, and the
  README-checking tests see what they expect), our own README now lives in
  `README.ilgw.md`, and the leftover `README.zh-TW.md` copy is removed. The
  fork-only docs that had been added to the zh-TW copy (`--watch-urls-file`,
  `URLS_WATCH_MODE`) moved into a "Fork-specific documentation" section of
  `README.ilgw.md`. The README changelog tail now lives in `README.ilgw.md`.
- **(major)** Merged the rest of upstream `Alos21750/UAV-Downloader`
  (`upstream/master`, UAV 3.2). Upstream brings: opt-in automatic requeue of
  slow downloads; storage-failure handling (`core/storage.py`) so a
  full/unplugged destination stops retries and source fallbacks instead of
  burning through them; the SupJav source refactor (EVS/LUC/VAS/VOE providers
  kept as ordered HLS fallbacks, SSRF-style URL validation); the UAV 3.2
  issue/PR integration; a safe Browser shutdown during frozen startup; and the
  Windows build/version updates. Conflict resolutions: took upstream's logic in
  `sites/supjav.py` and `sites/base.py` but kept this fork's i18n (`T(...)`)
  for user-visible strings and console progress for the Streamtape fallback;
  in `cli/headless.py` combined the fork's `urls.txt` wait/consume loop with
  upstream's `StorageWriteError` handling (a storage error now also ends
  watch-forever mode, since a broken destination won't recover). Adjusted
  `tests/test_storage_failures.py` (`gather_initial_urls`) and
  `tests/test_supjav.py` (locale-independent message match, `capsys`) to match.
- **(major)** Dev shells now use the system's Python instead of a pinned
  `python312` from a separate nixpkgs revision. `flake.nix`'s `nixpkgs` input
  is the registry's `nixpkgs` (the NixOS system's own), the interpreter is
  `pkgs.python3` (3.13.14 here) and the tkinter path is derived from
  `python.sitePackages` instead of a hardcoded 3.12 path, so `nix develop`
  no longer downloads a second Python. The shell hook recreates the venv when
  the Python minor version changes. `flake.lock` now pins the system's store
  path (machine-specific; refresh with `nix flake update nixpkgs` after a
  `nixos-rebuild`). Verified on 3.13: full test suite passes and the GUI/AI
  wheels (numpy, ctranslate2, sentencepiece, opencc, curl_cffi) import fine.
