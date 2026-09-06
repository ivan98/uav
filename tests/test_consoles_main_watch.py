import builtins
import threading
import time

from uav_downloader import sites as M3U8Sites


class _FakeSite:
    def is_url_vaildate(self):
        return True

    def start_download(self):
        return True


def test_no_url_and_no_watch_mode_falls_back_to_input_prompt(monkeypatch):
    captured = {}

    def _fake_create_site(url, dest, max_workers=None, filename_mode=None):
        captured['url'] = url
        return _FakeSite()

    monkeypatch.setattr(M3U8Sites, 'create_site', _fake_create_site)
    monkeypatch.setattr(
        builtins, 'input', lambda prompt='': 'https://example.test/typed')

    M3U8Sites.consoles_main('', 'dest')

    assert captured['url'] == 'https://example.test/typed'


def test_no_url_with_watch_mode_waits_for_urls_file(monkeypatch, tmp_path):
    captured = []

    def _fake_create_site(url, dest, max_workers=None, filename_mode=None):
        captured.append(url)
        return _FakeSite()

    monkeypatch.setattr(M3U8Sites, 'create_site', _fake_create_site)

    def _fail_if_called(prompt=''):
        raise AssertionError('input() must not be called in watch mode')

    monkeypatch.setattr(builtins, 'input', _fail_if_called)

    result = {}

    def worker():
        M3U8Sites.consoles_main(
            '', str(tmp_path), watch_urls_file='once')
        result['done'] = True

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    time.sleep(0.3)
    assert 'done' not in result

    (tmp_path / 'urls.txt').write_text(
        'https://example.test/watched\n', encoding='utf-8')
    t.join(timeout=5)

    assert not t.is_alive()
    assert captured == ['https://example.test/watched']
