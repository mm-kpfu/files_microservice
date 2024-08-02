import os
from pydantic import PostgresDsn, DirectoryPath
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    RETURN_FILES_LOCALLY: bool = True  # False if nginx
    DSN__DB: PostgresDsn = 'postgresql+asyncpg://admin:1111@db:5432/files'
    UPLOAD_DIR: DirectoryPath = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "media"
    )
    MEDIA_ROOT: str = 'media'
    LOG_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "logs"
    )

    if not os.path.exists(UPLOAD_DIR):
        os.mkdir(UPLOAD_DIR)

    BUCKET_NAME: str = 'files'


settings = Settings()
