import os
import aiofiles
from typing import List, Optional
from datetime import datetime
from aiofiles import os as aios
from urllib import parse

from aiofiles.base import AsyncBase
from fastapi import UploadFile, Request

from .base import BaseStorage, FileInfo, StatFileInfo
from src.settings import settings


class LocalStorage(BaseStorage):
    STREAM_CHUNK_SIZE = 8192

    async def upload_file(self, file: UploadFile | str, **kwargs) -> FileInfo:
        metadata = self.get_metadata(file)
        upload_path = self.get_upload_path(metadata.storage_filename)

        with open(upload_path, "w+b") as f:
            file_size = 0
            while content := await file.read(self.STREAM_CHUNK_SIZE):
                f.write(content)
                file_size += len(content)

        return metadata

    async def get_file(self, filepath: str, open_options: Optional[dict] = None, **kwargs) -> AsyncBase:
        if open_options is None:
            open_options = {}
        f = await aiofiles.open(filepath, **open_options)
        return f

    def get_file_url(self, request: Request, filepath: str) -> str:
        full_path = os.path.join(settings.MEDIA_ROOT, filepath)
        return parse.urljoin(str(request.base_url), full_path)

    async def delete(self, filepath: str) -> None:
        full_path = self.get_upload_path(filepath)
        await aios.remove(full_path)

    async def list_files(self) -> List[StatFileInfo]:
        async def _list_files(dir_path):
            res = []
            for name in await aios.listdir(dir_path):
                if await aios.path.isdir(name):
                    inner = os.path.join(dir_path, name)
                    stat_files = await _list_files(inner)
                    res = [*res, *stat_files]
                else:
                    path = os.path.join(dir_path, name)
                    stat = await aios.stat(path)
                    stat_file = StatFileInfo(
                        path,
                        datetime.fromtimestamp(stat.st_atime),
                        datetime.fromtimestamp(stat.st_mtime)
                    )
                    res.append(stat_file)
            return res

        return await _list_files(self.path)
