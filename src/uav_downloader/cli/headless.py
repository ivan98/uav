#!/usr/bin/env python
# coding: utf-8
"""UAV Downloader CLI CLI downloader for Docker and NAS use — no GUI.

Downloads one or more supported URLs to $DOWNLOAD_DIR (default /downloads).
URLs are taken from, in order: command-line args, the $URLS / $URL env var
(space/comma separated), and a mounted text file ($URLS_FILE, default
/downloads/urls.txt — one URL per line, '#' comments allowed).

If no URL is available yet, this waits for one to show up in that file
instead of failing — event-driven (via `watchdog`), not polling. Controlled
by $URLS_WATCH_MODE:
  once    (default) process whatever's found, then exit.
  forever keep watching indefinitely; new lines appended to the file later
          are picked up and downloaded without restarting the container.

A URL's line is removed from the file once it's been fully handled
(downloaded, or already on disk) — the in-memory dedup used in `forever`
mode doesn't survive a restart, so this keeps a restarted container from
re-processing everything still sitting in the file. Failed URLs are left
in place so a restart retries them.

Examples:
  docker run --rm -v /nas/videos:/downloads ghcr.io/alos21750/uav-downloader https://jable.tv/videos/abc-123/
  docker run --rm -v /nas/videos:/downloads -e URLS_FILE=/downloads/urls.txt ghcr.io/alos21750/uav-downloader
  docker run --rm -v /nas/videos:/downloads -e URLS_WATCH_MODE=forever ghcr.io/alos21750/uav-downloader
"""
import os
import sys

# --- issue #23: point SSL/curl_cffi at certifi's ASCII-safe CA bundle BEFORE any
# curl_cffi import, so a non-UTF-8 default cert path can't crash the resolver. ---
try:
    import certifi as _certifi
    _ca = _certifi.where()
    if _ca and os.path.exists(_ca):
        os.environ.setdefault('SSL_CERT_FILE', _ca)
        os.environ.setdefault('SSL_CERT_DIR', os.path.dirname(_ca))
except Exception:
    pass

from uav_downloader import sites as M3U8Sites
from uav_downloader.core import config
from uav_downloader.core.urls_watch import iter_url_batches, remove_consumed_url
from uav_downloader.core.storage import StorageWriteError
from uav_downloader.sites import base as M3U8Crawler


def gather_initial_urls():
    urls = [u for u in sys.argv[1:] if u.strip()]
    env = (os.environ.get('URLS') or os.environ.get('URL') or '')
    urls += [u.strip() for u in env.replace(',', ' ').split() if u.strip()]
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u); out.append(u)
    return out


def urls_file_path(dest):
    return os.environ.get('URLS_FILE', os.path.join(dest, 'urls.txt'))


def watch_mode():
    mode = (os.environ.get('URLS_WATCH_MODE') or 'once').strip().lower()
    return mode if mode in ('once', 'forever') else 'once'


def main():
    dest = os.environ.get('DOWNLOAD_DIR', '/downloads')
    os.makedirs(dest, exist_ok=True)
    res = os.environ.get('RESOLUTION')
    if res:
        try:
            M3U8Crawler.set_resolution_pref(res)
        except Exception:
            pass

    max_workers = None
    raw_workers = os.environ.get('MAX_WORKERS_PER_VIDEO')
    if raw_workers is not None and raw_workers.strip():
        max_workers = config.normalize_max_workers_per_video(raw_workers)

    worker_label = (
        max_workers if max_workers is not None
        else config.get_max_workers_per_video())
    mode = watch_mode()
    urls_path = urls_file_path(dest)
    print(f"下載目錄: {dest} | 解析度: {M3U8Crawler.get_resolution_pref()} | "
          f"每片執行緒: {worker_label} | watching {urls_path} for URLs "
          f"(mode={mode})", flush=True)

    ok = fail = 0
    storage_failed = False
    for urls in iter_url_batches(
            urls_path, mode, initial_urls=gather_initial_urls()):
        for url in urls:
            print(f"\n========== {url} ==========", flush=True)
            try:
                site = M3U8Sites.CreateSite(
                    url, dest, max_workers=max_workers)
                if site is None:
                    print(f"[跳過] 不支援的網址: {url}", flush=True); fail += 1; continue
                if not site.is_url_vaildate():
                    print(f"[失敗] 無法解析影片（版面改版 / 被 Cloudflare 阻擋 / 影片不存在）: {url}", flush=True); fail += 1; continue
                site.start_download()
                print(f"[完成] {url}", flush=True); ok += 1
                remove_consumed_url(urls_path, url)
            except StorageWriteError as exc:
                print(f'[Storage error] {url}: {exc}', flush=True)
                fail += 1
                storage_failed = True
                break
            except Exception as exc:
                print(f"[錯誤] {url}: {exc}", flush=True); fail += 1
        print(f"\n===== 完成 {ok} 個，失敗 {fail} 個 =====", flush=True)
        if storage_failed:
            break  # a broken destination won't recover; don't keep watching
    return 0 if fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
