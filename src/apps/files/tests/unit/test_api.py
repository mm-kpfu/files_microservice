import pytest

from fastapi import HTTPException
from fastapi.responses import FileResponse

from unittest.mock import AsyncMock

from src.apps.files.router import upload_file, get_file
from src.exceptions import RecordNotFound


@pytest.mark.asyncio
async def test_upload_file(post_request, background_tasks, session, storage, file, mocker):
    mocker.patch('src.apps.files.router.save_file_metadata', side_effect=AsyncMock())
    storage, uid = storage
    res = await upload_file(post_request, background_tasks, session, storage, storage)

    assert isinstance(res, dict)
    assert res.get('uri', False)


@pytest.mark.asyncio
async def test_get_file(session, storage, file, mocker):
    mocker.patch('src.apps.files.router.get_file_metadata', side_effect=AsyncMock())
    storage, uid = storage
    res = await get_file(uid, session, storage)
    assert isinstance(res, FileResponse)


@pytest.mark.asyncio
async def test_get_file_no_metadata(session, storage, file, mocker):
    storage, uid = storage
    mocker.patch('src.apps.files.router.get_file_metadata', side_effect=RecordNotFound(uid, 'file'))
    with pytest.raises(HTTPException):
        await get_file(uid, session, storage)
