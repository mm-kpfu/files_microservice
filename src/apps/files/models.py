import uuid

from sqlalchemy import Column, BigInteger, String
from sqlalchemy.dialects.postgresql import UUID

from src.db import Base


class FileMetadata(Base):
    __tablename__ = 'files_metadata'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    size = Column(BigInteger, nullable=False)
    file_format = Column(String)
    original_filename = Column(String, nullable=False)
    extension = Column(String)
