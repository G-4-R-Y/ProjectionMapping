from __future__ import annotations

from contextlib import contextmanager
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from projection_mapping.studio_server import start_server


@contextmanager
def running_server():
    server, url = start_server()
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield url
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)


def test_assets_and_local_only_binding():
    with running_server() as url:
        assert url.startswith('http://127.0.0.1:')
        with urlopen(url) as res:
            assert res.status == 200
            assert b'SPATIAL MEMORIES' in res.read()
            assert "'none'" in res.headers['Content-Security-Policy']
        with urlopen(url + 'studio.js') as res:
            code = res.read()
            assert b'parsePly' in code
            assert b'gl.clearColor(0,0,0,1)' in code
        with urlopen(url + 'studio.css') as res:
            assert b'.viewport' in res.read()


def test_no_upload_or_path_traversal():
    with running_server() as url:
        for path in ('../README.md', '.git/config', 'api/run', '%2e%2e/README.md'):
            with pytest.raises(HTTPError) as exc:
                urlopen(url + path)
            assert exc.value.code == 404
        with pytest.raises(HTTPError) as exc:
            urlopen(Request(url, method='POST', data=b'test'))
        assert exc.value.code == 405


def test_bad_port():
    with pytest.raises(ValueError):
        start_server(port=-1)
