import os
from typing import Optional, List
from urllib import parse
import aioboto3
from aiofiles.base import AsyncBase
from botocore.exceptions import ClientError
from fastapi import UploadFile, Request
from aiofiles.tempfile import TemporaryFile
from src.logging import logger
from .base import BaseStorage, FileInfo, StatFileInfo


class CloudStorage(BaseStorage):
    def __init__(
            self,
            bucket_name: str,
            path: str,
            session_options: Optional[dict] = None,
            client_options: Optional[dict] = None,
    ):
        self.bucket_name = bucket_name
        if session_options is None:
            session_options = {}
        if client_options is None:
            client_options = {}

        self.session = aioboto3.Session(**session_options)
        self.s3 = self.session.client('s3', **client_options)
        self.endpoint_url = client_options.get('endpoint_url')
        super().__init__(path)

    async def upload_file(self, file: str | UploadFile, **kwargs) -> Optional[FileInfo]:
        try:
            if isinstance(file, str):
                filename = os.path.basename(file)
                filepath = os.path.join(self.path, filename)
                async with self.s3 as s3:
                    await s3.upload_file(file, Bucket=self.bucket_name, Key=filepath, **kwargs)
            else:
                metadata = self.get_metadata(file)
                filepath = os.path.join(self.path, metadata.storage_filename)
                async with self.s3 as s3:
                    await s3.upload_fileobj(file.file, Bucket=self.bucket_name, Key=filepath, **kwargs)

                return metadata
        except Exception as e:
            logger.error(e)
            raise e

    async def get_file(self, filepath: str, open_options: Optional[dict] = None, **kwargs) -> AsyncBase:
        if open_options is None:
            open_options = {}
        path = os.path.join(self.path, filepath)
        async with self.s3 as s3:
            f = await TemporaryFile(**open_options)
            try:
                downloaded = await s3.download_fileobj(self.bucket_name, path, f, **kwargs)
                return downloaded
            except ClientError as e:
                raise FileNotFoundError

    def get_file_url(self, request: Request, filepath: str) -> str:
        full_path = self.get_upload_path(filepath)
        return parse.urljoin(self.endpoint_url, full_path)

    async def delete(self, filepath: str) -> None:
        full_path = self.get_upload_path(filepath)
        async with self.s3 as s3:
            await s3.Object(self.bucket_name, full_path).delete()

    async def list_files(self) -> List[StatFileInfo]:
        res = []
        async with self.s3 as s3:
            bucket = await s3.Bucket(self.bucket_name)
            async for obj in bucket.objects.all():
                res.append(StatFileInfo(
                    path=obj.key,
                    modified_time=obj.last_modified,
                ))

        return res
