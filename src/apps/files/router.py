from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status, Request, UploadFile
from fastapi.responses import FileResponse

from src.storages.base import BaseStorage
from src.storages.registry import get_storage, CLOUD_STORAGE
from src.settings import settings
from .services import FilesMetaRepository
from .schemas import UploadFileResponseSchema
from src.exceptions import RecordNotFound
from src.logging import logger
from src.utils import parse_files_from_request

router = APIRouter(prefix='/files')


@router.post(
    '/upload',
    responses={
        201: {'model': UploadFileResponseSchema},
    },
    response_model=UploadFileResponseSchema,
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "properties": {
                          "file": {
                            "type": "string",
                            "format": "binary",
                            "title": "File"
                          },
                        },
                        "type": "object",
                        "required": [
                          "file"
                        ],
                        "title": "Body_upload_file_files_upload_post"
                      }
                }
            },
            "required": True
        }}
)
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    storage: BaseStorage = Depends(get_storage()),
    copy_storage: BaseStorage = Depends(get_storage(CLOUD_STORAGE)),
    file_meta_repo: FilesMetaRepository = Depends(),
    files: List[UploadFile] = Depends(parse_files_from_request)
):
    """
    Write directly to file, instead of using tempfiles for optimization
    """
    file = files[0]
    metadata = storage.get_metadata(file)
    background_tasks.add_task(copy_storage.upload_file, file=file.file.name)
    await file_meta_repo.save_file_metadata(metadata)
    return {'uri': storage.get_file_url(request, str(metadata.name))}


if settings.RETURN_FILES_LOCALLY:
    @router.get(f'/{settings.MEDIA_ROOT}/{{uuid}}')
    async def get_file(
        uuid: UUID,
        storage: BaseStorage = Depends(get_storage()),
        files_repo: FilesMetaRepository = Depends()
    ):
        try:
            metadata = await files_repo.get_file_metadata(uuid)
        except RecordNotFound as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'File with id {uuid} not found'
            )

        try:
            upload_path = storage.get_upload_path(metadata.storage_filename, check_exists=True)
        except FileNotFoundError:
            logger.warning(f'A file record with id {uuid} exists in the database, but the file itself does not exist')
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'File with id {uuid} not found'
            )

        return FileResponse(upload_path)
