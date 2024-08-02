import argparse
import asyncio
import uuid
from datetime import timedelta, datetime
from typing import Iterable, List
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.storages.base import BaseStorage, StatFileInfo
from loguru import logger

from src.storages.registry import STORAGES, LOCAL_STORAGE
from src.apps.files.services import FilesMetaRepository
from src.db import get_db


STORAGES_FOR_CLEAR = (
    STORAGES[LOCAL_STORAGE],
)


class ClearOldFiles:
    DELETE_IF_NOT_ACCESSED_IN_LAST = timedelta(days=30)
    DELETE_IF_NOT_MODIFIED_IN_LAST = timedelta(days=30)

    def __init__(self, storages: Iterable[BaseStorage]):
        self.storages = storages

    async def clear_storages(self):
        tasks = [asyncio.create_task(self.clear_storage(storage)) for storage in self.storages]
        await asyncio.gather(*tasks)

    async def clear_storage(self, storage: BaseStorage):
        files = await storage.list_files()
        files_for_delete = []
        for file in files:
            if self.is_file_for_delete(file):
                files_for_delete.append(file)

        await self.delete_files(files_for_delete, storage)

    @classmethod
    def is_file_for_delete(cls, file_info: StatFileInfo):
        now = datetime.now()
        remove = False
        if file_info.accessed_time is not None:
            if file_info.accessed_time < now - cls.DELETE_IF_NOT_ACCESSED_IN_LAST:
                remove = True
        if file_info.modified_time is not None:
            if file_info.modified_time < now - cls.DELETE_IF_NOT_MODIFIED_IN_LAST:
                remove = True

        return remove

    async def delete_files(self, files: List[StatFileInfo], storage: BaseStorage):
        ids = [uuid.UUID(storage.get_filename_from_path(f.path)) for f in files]
        logger.debug(f'Deleting files: {ids}')

        async for session in get_db():
            await FilesMetaRepository(session).delete_files(ids)

        tasks = [asyncio.create_task(self.delete_from_storage(f.path, storage)) for f in files]
        await asyncio.gather(*tasks)

    @staticmethod
    async def delete_from_storage(path: str, storage: BaseStorage):
        try:
            await storage.delete(path)
        except FileNotFoundError:
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--schedule', default='0 0 * * *')
    parser.add_argument(
        '--run-once',
        action='store_true',
        help="Specify this option if you want to run the scheduler only once or use some other cron, "
             "K8s CronJob for example")
    cmd_args = parser.parse_args()
    command = ClearOldFiles(STORAGES_FOR_CLEAR)

    if cmd_args.run_once:
        asyncio.run(command.clear_storages())
    else:
        trigger = CronTrigger.from_crontab(cmd_args.schedule)
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            func=command.clear_storages,
            trigger=trigger
        )
        scheduler.start()

        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            pass


if __name__ == "__main__":
    main()
