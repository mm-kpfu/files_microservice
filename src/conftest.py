import uuid

import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.requests import Request

from src.storages.base import FileInfo


get_scope = {
    'type': 'http',
    'asgi': {'version': '3.0', 'spec_version': '2.4'}, 'http_version': '1.1', 'server': ('172.18.0.3', 8000),
    'client': ('172.18.0.1', 55968), 'scheme': 'http', 'root_path': '',
    'headers': [
        (
            b'host', b'0.0.0.0:8000'), (b'connection', b'keep-alive'), (b'accept', b'application/json'), (
            b'user-agent',
            b'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        ),
        (b'referer', b'http://0.0.0.0:8000/docs'),
        (b'accept-encoding', b'gzip, deflate'),
        (b'accept-language', b'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7')
    ],
    'state': {},
    'method': 'GET',
    'path': '/files/media/',
    'raw_path': b'/files/media/',
    'query_string': b''
}

post_scope = {**get_scope, 'method': 'POST'}


@pytest.fixture
def get_request():
    return Request(get_scope)


@pytest.fixture
def post_request():
    return Request(post_scope)


@pytest.fixture
def background_tasks():
    return MagicMock()


@pytest.fixture
def session():
    return MagicMock()


@pytest.fixture
def storage():
    storage = MagicMock()
    uid = uuid.uuid4()
    storage.upload_file = AsyncMock(return_value=FileInfo(1, 'pdf', 'origin', 'pdf', id=uid))
    storage.get_upload_path = MagicMock()
    return storage, uid


@pytest.fixture
def file():
    return MagicMock()
