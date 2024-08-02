import pytest

from fastapi import HTTPException
from fastapi.responses import FileResponse

from unittest.mock import AsyncMock

from src.apps.files.router import upload_file, get_file
from src.exceptions import RecordNotFound


@pytest.mark.asyncio
async def test_upload_file(post_request, background_tasks, storage, file_repo, file):
    storage, uid = storage
    res = await upload_file(post_request, background_tasks, storage, storage, file_repo, (file,))

    assert isinstance(res, dict)
    assert res.get('uri', False)


@pytest.mark.asyncio
async def test_get_file(storage, file, file_repo):
    storage, uid = storage
    res = await get_file(uid, storage, file_repo)
    assert isinstance(res, FileResponse)


@pytest.mark.asyncio
async def test_get_file_no_metadata(session, storage, file_repo):
    storage, uid = storage
    file_repo.get_file_metadata = AsyncMock(side_effect=RecordNotFound(uid, 'file'))
    with pytest.raises(HTTPException):
        await get_file(uid, storage, file_repo)
