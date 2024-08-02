import os
import uuid
import magic
from datetime import datetime
from typing import Optional, BinaryIO, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID
from aiofiles.base import AsyncBase
from fastapi import UploadFile, Request

from src.settings import settings


@dataclass
class FileInfo:
    size: int
    name: UUID
    file_format: Optional[str] = None
    original_filename: Optional[str] = None
    extension: Optional[str] = None

    @property
    def storage_filename(self):
        return f'{self.name}.{self.extension}'


@dataclass
class StatFileInfo:
    path: str
    accessed_time: Optional[datetime] = None
    modified_time: Optional[datetime] = None


class BaseStorage(ABC):
    def __init__(self, path: str) -> None:
        self.path = path

    def get_file_format(self, file: BinaryIO) -> Optional[str]:
        return magic.from_buffer(file.read(4048), mime=True)

    @abstractmethod
    async def list_files(self) -> List[StatFileInfo]:
        ...

    def generate_stem(self) -> UUID:
        """
        Generate filename without extension.
        """
        return uuid.uuid4()

    @staticmethod
    def splitext(path: str) -> list[str]:
        d = path.split('.')
        if len(d) < 2:
            return [path, '']
        return d

    def filename_to_storage_filename(self, filename: str) -> str:
        _, extension = self.splitext(filename)
        stem = self.generate_stem()
        return f'{stem}.{extension}'

    @abstractmethod
    def get_file_url(self, request: Request, filepath: str) -> str:
        ...

    @abstractmethod
    async def upload_file(self, file: str | UploadFile, **kwargs) -> FileInfo:
        ...

    @abstractmethod
    async def get_file(self, filepath: str, open_options: Optional[dict] = None, **kwargs) -> AsyncBase:
        ...

    @abstractmethod
    async def delete(self, filepath: str) -> None:
        ...

    def get_metadata(self, file: UploadFile, filename_from_io: bool = True) -> FileInfo:
        if filename_from_io:
            path, extension = self.splitext(file.file.name)
            name = os.path.basename(path)
        else:
            name = self.generate_stem()

        original_filename, extension = self.splitext(file.filename)
        return FileInfo(
            size=file.size,
            file_format=self.get_file_format(file.file),
            original_filename=original_filename,
            extension=extension,
            name=name
        )

    def get_upload_path(self, filename: str, check_exists: bool = False) -> str:
        upload_path = os.path.join(settings.UPLOAD_DIR, filename)
        if check_exists:
            if not os.path.exists(upload_path):
                raise FileNotFoundError
        return upload_path

    def get_filename_from_path(self, filepath: str) -> str:
        filename = os.path.basename(filepath)
        filename, extension = self.splitext(filename)
        return filename
