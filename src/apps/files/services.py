from typing import List
from uuid import UUID

from fastapi import Depends
from sqlalchemy import insert, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.files.models import FileMetadata
from src.db import Base, get_db
from src.exceptions import RecordNotFound
from src.storages.base import FileInfo


class FilesMetaRepository:
    model: Base = FileMetadata

    def __init__(self, session: AsyncSession = Depends(get_db)) -> None:
        self.session = session

    async def save_file_metadata(self, data: FileInfo):
        stmt = insert(self.model).values(
            id=data.name,
            size=data.size,
            file_format=data.file_format,
            original_filename=data.original_filename,
            extension=data.extension,
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_file_metadata(self, id: UUID) -> FileInfo:
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        file_meta = result.scalars().first()
        if not file_meta:
            raise RecordNotFound(id, 'File')

        return FileInfo(
            size=file_meta.size,
            name=file_meta.id,
            file_format=file_meta.file_format,
            original_filename=file_meta.original_filename,
            extension=file_meta.extension,
        )

    async def delete_files(self, ids: List[UUID]):
        stmt = delete(self.model).where(self.model.id.in_(ids))
        await self.session.execute(stmt)
        await self.session.commit()
