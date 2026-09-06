import sys
import threading
import time

from uav_downloader.cli import headless as docker_cli


def test_docker_worker_limit_is_forwarded_to_each_video(monkeypatch, tmp_path):
    captured = []

    class _FakeSite:
        def is_url_vaildate(self):
            return True

        def start_download(self):
            return True

    def _create(url, dest, max_workers=None):
        captured.append((url, dest, max_workers))
        return _FakeSite()

    monkeypatch.setattr(
        sys, 'argv', ['docker_cli.py', 'https://jable.tv/videos/example/'])
    monkeypatch.setenv('DOWNLOAD_DIR', str(tmp_path))
    monkeypatch.setenv('MAX_WORKERS_PER_VIDEO', '3')
    monkeypatch.delenv('URLS', raising=False)
    monkeypatch.delenv('URL', raising=False)
    monkeypatch.setattr(docker_cli.M3U8Sites, 'CreateSite', _create)

    assert docker_cli.main() == 0
    assert captured == [
        ('https://jable.tv/videos/example/', str(tmp_path), 3),
    ]


def test_docker_waits_for_urls_file_when_no_url_given(monkeypatch, tmp_path):
    captured = []

    class _FakeSite:
        def is_url_vaildate(self):
            return True

        def start_download(self):
            return True

    def _create(url, dest, max_workers=None):
        captured.append((url, dest, max_workers))
        return _FakeSite()

    monkeypatch.setattr(sys, 'argv', ['docker_cli.py'])
    monkeypatch.setenv('DOWNLOAD_DIR', str(tmp_path))
    monkeypatch.delenv('MAX_WORKERS_PER_VIDEO', raising=False)
    monkeypatch.delenv('URLS', raising=False)
    monkeypatch.delenv('URL', raising=False)
    monkeypatch.delenv('URLS_FILE', raising=False)
    monkeypatch.delenv('URLS_WATCH_MODE', raising=False)
    monkeypatch.setattr(docker_cli.M3U8Sites, 'CreateSite', _create)

    result = {}

    def worker():
        result['rc'] = docker_cli.main()

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    time.sleep(0.3)
    assert 'rc' not in result  # still waiting, nothing to download yet

    (tmp_path / 'urls.txt').write_text(
        'https://jable.tv/videos/example/\n', encoding='utf-8')
    t.join(timeout=5)

    assert not t.is_alive()
    assert result.get('rc') == 0
    assert captured == [
        ('https://jable.tv/videos/example/', str(tmp_path), None),
    ]
    assert (tmp_path / 'urls.txt').read_text(encoding='utf-8') == ''


def test_docker_leaves_a_failed_url_in_the_file_for_retry(monkeypatch, tmp_path):
    def _create(url, dest, max_workers=None):
        raise Exception('boom')

    monkeypatch.setattr(sys, 'argv', ['docker_cli.py'])
    monkeypatch.setenv('DOWNLOAD_DIR', str(tmp_path))
    monkeypatch.delenv('MAX_WORKERS_PER_VIDEO', raising=False)
    monkeypatch.delenv('URLS', raising=False)
    monkeypatch.delenv('URL', raising=False)
    monkeypatch.delenv('URLS_FILE', raising=False)
    monkeypatch.delenv('URLS_WATCH_MODE', raising=False)
    monkeypatch.setattr(docker_cli.M3U8Sites, 'CreateSite', _create)

    (tmp_path / 'urls.txt').write_text(
        'https://jable.tv/videos/broken/\n', encoding='utf-8')

    assert docker_cli.main() == 1
    assert (tmp_path / 'urls.txt').read_text(encoding='utf-8') == (
        'https://jable.tv/videos/broken/\n')
