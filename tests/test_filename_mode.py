import json

from uav_downloader import sites as M3U8Sites
from uav_downloader.core import config
from uav_downloader.sites.base import M3U8Crawler


_TITLES = {}


class _NamingCrawler(M3U8Crawler):
    website_dirname_pattern = r'https://example\.test/([^/]+)/$'

    def get_url_infos(self):
        self._targetName = _TITLES[self._dirName]
        self._imageUrl = None
        self._m3u8url = 'https://cdn.example.test/master.m3u8'


def _crawler(tmp_path, monkeypatch, title, mode):
    monkeypatch.setattr(
        config, 'get_filename_mode', lambda: mode, raising=False)
    slug = f'video-{len(_TITLES)}'
    _TITLES[slug] = title
    return _NamingCrawler(
        f'https://example.test/{slug}/', savepath=str(tmp_path), silence=True)


def test_filename_mode_defaults_persists_and_rejects_unknown_values(
        tmp_path, monkeypatch):
    path = tmp_path / 'ui_prefs.json'
    monkeypatch.setattr(config, '_ui_prefs_path', lambda: str(path))

    assert config.get_filename_mode() == 'full-title'
    assert config.set_filename_mode('code-only') == 'code-only'
    assert config.get_filename_mode() == 'code-only'
    assert json.loads(path.read_text(encoding='utf-8'))['filename_mode'] == (
        'code-only')

    assert config.set_filename_mode('unknown') == 'full-title'
    assert config.get_filename_mode() == 'full-title'


def test_code_only_uses_everything_before_the_first_whitespace(
        tmp_path, monkeypatch):
    normal = _crawler(
        tmp_path, monkeypatch,
        'ABCD-123 A complete title with spaces', 'code-only')
    fc2 = _crawler(
        tmp_path, monkeypatch,
        'FC2-PPV-1234567　full-width space title', 'code-only')

    assert normal.target_name() == 'ABCD-123'
    assert fc2.target_name() == 'FC2-PPV-1234567'


def test_code_only_strips_leading_bracket_prefixes(tmp_path, monkeypatch):
    tagged = _crawler(
        tmp_path, monkeypatch,
        '[Uncensored][Leaked] ABCD-123 A complete title', 'code-only')

    assert tagged.target_name() == 'ABCD-123'


def test_code_only_keeps_a_title_without_whitespace(tmp_path, monkeypatch):
    crawler = _crawler(
        tmp_path, monkeypatch, 'FC2-PPV-1234567', 'code-only')

    assert crawler.target_name() == 'FC2-PPV-1234567'


def test_full_title_mode_remains_the_backward_compatible_default(
        tmp_path, monkeypatch):
    title = 'ABCD-123 A complete title'
    crawler = _crawler(tmp_path, monkeypatch, title, 'full-title')

    assert crawler.target_name() == title


def test_explicit_filename_mode_overrides_the_persisted_preference(
        tmp_path, monkeypatch):
    monkeypatch.setattr(
        config, 'get_filename_mode', lambda: 'full-title', raising=False)
    title = 'ABCD-123 A complete title with spaces'
    slug = f'video-{len(_TITLES)}'
    _TITLES[slug] = title

    crawler = _NamingCrawler(
        f'https://example.test/{slug}/', savepath=str(tmp_path),
        silence=True, filename_mode='code-only')

    assert crawler.target_name() == 'ABCD-123'


def test_create_site_forwards_explicit_filename_mode(monkeypatch, tmp_path):
    captured = {}

    class _FakeSite:
        @classmethod
        def validate_url(cls, url):
            return 'video'

        def __init__(self, url, savepath='', silence=False,
                     filename_mode=None):
            captured.update(
                url=url, savepath=savepath, silence=silence,
                filename_mode=filename_mode)

    monkeypatch.setattr(M3U8Sites, 'siteList', (_FakeSite,))

    result = M3U8Sites.CreateSite(
        'https://example.test/video', str(tmp_path), silence=True,
        filename_mode='code-only')

    assert isinstance(result, _FakeSite)
    assert captured['filename_mode'] == 'code-only'


def test_consoles_main_forwards_filename_mode_to_create_site(monkeypatch):
    captured = {}

    def _fake_create_site(url, dest, max_workers=None, filename_mode=None):
        captured.update(
            url=url, dest=dest, max_workers=max_workers,
            filename_mode=filename_mode)
        return None

    monkeypatch.setattr(M3U8Sites, 'create_site', _fake_create_site)

    M3U8Sites.consoles_main(
        'https://example.test/video', 'dest', filename_mode='code-only')

    assert captured == {
        'url': 'https://example.test/video',
        'dest': 'dest',
        'max_workers': None,
        'filename_mode': 'code-only',
    }
