import os
import threading
import time

import pytest

from uav_downloader.core.urls_watch import iter_url_batches


def test_yields_initial_urls_immediately_without_touching_disk(tmp_path):
    path = tmp_path / 'missing' / 'urls.txt'
    gen = iter_url_batches(str(path), 'once', initial_urls=['https://a.example/'])

    assert next(gen) == ['https://a.example/']
    with pytest.raises(StopIteration):
        next(gen)
    assert not path.parent.exists()


def test_yields_existing_file_content_immediately(tmp_path):
    path = tmp_path / 'urls.txt'
    path.write_text(
        'https://a.example/\n# comment\n\nhttps://b.example/\n', encoding='utf-8')

    gen = iter_url_batches(str(path), 'once')

    assert next(gen) == ['https://a.example/', 'https://b.example/']


def test_dedupes_initial_urls_against_existing_file_content(tmp_path):
    path = tmp_path / 'urls.txt'
    path.write_text('https://a.example/\nhttps://b.example/\n', encoding='utf-8')

    gen = iter_url_batches(
        str(path), 'once', initial_urls=['https://a.example/'])

    assert next(gen) == ['https://a.example/', 'https://b.example/']


def test_invalid_mode_raises():
    with pytest.raises(ValueError):
        list(iter_url_batches('/nonexistent/urls.txt', 'bogus'))


def test_once_waits_for_file_to_be_created_then_stops(tmp_path):
    path = tmp_path / 'sub' / 'urls.txt'
    result = {}

    def worker():
        gen = iter_url_batches(str(path), 'once')
        result['batch'] = next(gen)
        with pytest.raises(StopIteration):
            next(gen)

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    time.sleep(0.3)
    assert 'batch' not in result  # still waiting

    os.makedirs(path.parent, exist_ok=True)
    path.write_text('https://a.example/\n', encoding='utf-8')

    t.join(timeout=5)
    assert not t.is_alive()
    assert result.get('batch') == ['https://a.example/']


def test_forever_yields_each_new_batch_without_repeating_earlier_urls(tmp_path):
    path = tmp_path / 'urls.txt'
    path.write_text('https://a.example/\n', encoding='utf-8')
    batches = []
    gen = iter_url_batches(str(path), 'forever')

    batches.append(next(gen))

    def append_more():
        time.sleep(0.3)
        with open(path, 'a', encoding='utf-8') as fh:
            fh.write('https://b.example/\n')

    t = threading.Thread(target=append_more, daemon=True)
    t.start()
    batches.append(next(gen))
    t.join(timeout=5)

    assert batches == [['https://a.example/'], ['https://b.example/']]
    gen.close()
