from src.storages.cloud import CloudStorage
from src.storages.local import LocalStorage
from src.settings import settings

LOCAL_STORAGE = 1
CLOUD_STORAGE = 2


STORAGES = {
    CLOUD_STORAGE: CloudStorage(settings.BUCKET_NAME, settings.UPLOAD_DIR),
    LOCAL_STORAGE: LocalStorage(settings.UPLOAD_DIR)
}


def get_storage(storage_key: int = LOCAL_STORAGE):
    async def inner():
        # async to run not in thread
        return STORAGES[storage_key]

    return inner
