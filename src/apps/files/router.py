from uuid import UUID

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, status, Request
from fastapi.responses import FileResponse

from src.storages.base import BaseStorage
from src.storages.registry import get_storage, CLOUD_STORAGE
from src.settings import settings
from .services import FilesMetaRepository
from .schemas import UploadFileResponseSchema
from src.exceptions import RecordNotFound
from src.request import TargetFileRoute
from src.logging import logger


router = APIRouter(prefix='/files')

# recording directly to the desired file without temporary
# check src.request.TargetFileRoute
router.route_class = TargetFileRoute


@router.post(
    '/upload',
    responses={
        201: {'model': UploadFileResponseSchema},
    },
    response_model=UploadFileResponseSchema
)
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    storage: BaseStorage = Depends(get_storage()),
    copy_storage: BaseStorage = Depends(get_storage(CLOUD_STORAGE)),
    file: UploadFile = File(...),
    file_meta_repo: FilesMetaRepository = Depends()
):
    metadata = storage.get_metadata(file)
    background_tasks.add_task(copy_storage.upload_file, file=metadata.storage_filename)
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
