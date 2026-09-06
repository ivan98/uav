#!/usr/bin/env python
# coding: utf-8
"""Wait for URLs to appear in a line-delimited text file (e.g. urls.txt).

Shared by the headless Docker/NAS entrypoint and `uav-browser --nogui` so
neither has to fail immediately (or block on a terminal prompt) when no URL
was supplied directly — instead they can wait for one to show up in a
watched file, using filesystem events (via `watchdog`) rather than polling.
"""

import os
import queue

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


def _read_urls_file(path):
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding='utf-8') as fh:
            return [ln.strip() for ln in fh
                    if ln.strip() and not ln.lstrip().startswith('#')]
    except OSError:
        return []


def _dedupe(urls):
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


class _FileChangeHandler(FileSystemEventHandler):
    """Wakes the waiting generator whenever `target_path` is created,
    written to, or replaced via an atomic rename."""

    def __init__(self, target_path, wake):
        self._target = os.path.abspath(target_path)
        self._wake = wake

    def _maybe_wake(self, src_path):
        if os.path.abspath(src_path) == self._target:
            self._wake()

    def on_created(self, event):
        self._maybe_wake(event.src_path)

    def on_modified(self, event):
        self._maybe_wake(event.src_path)

    def on_moved(self, event):
        self._maybe_wake(event.dest_path)


def iter_url_batches(path, mode, initial_urls=()):
    """Yield batches of new URLs, waiting on `path` for more as needed.

    `initial_urls` (already gathered from CLI args / env vars) and any URLs
    already present in the file are yielded first, with no waiting. If
    nothing is available yet, blocks — event-driven via `watchdog`, not
    polling — until the file is created, written to, or replaced, then
    re-reads it.

    mode='once': stop after the first non-empty batch.
    mode='forever': keep watching indefinitely, yielding only URLs not
    already seen this run. Dedup is in-memory only (not persisted across
    restarts).
    """
    if mode not in ('once', 'forever'):
        raise ValueError(f"unknown mode: {mode!r}")

    seen = set()

    def _new(urls):
        fresh = [u for u in _dedupe(urls) if u not in seen]
        seen.update(fresh)
        return fresh

    batch = _new(list(initial_urls) + _read_urls_file(path))
    if batch:
        yield batch
        if mode == 'once':
            return

    watch_target_dir = os.path.dirname(os.path.abspath(path)) or '.'
    os.makedirs(watch_target_dir, exist_ok=True)

    wake_queue = queue.Queue(maxsize=1)

    def _wake():
        try:
            wake_queue.put_nowait(None)
        except queue.Full:
            pass

    observer = Observer()
    observer.schedule(
        _FileChangeHandler(path, _wake), watch_target_dir, recursive=False)
    observer.start()
    try:
        while True:
            wake_queue.get()
            batch = _new(_read_urls_file(path))
            if batch:
                yield batch
                if mode == 'once':
                    return
    finally:
        observer.stop()
        observer.join()
