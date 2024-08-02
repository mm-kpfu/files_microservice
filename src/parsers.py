from typing import BinaryIO
from starlette.datastructures import UploadFile, Headers
from starlette.formparsers import MultiPartParser, MultiPartException, _user_safe_decode
from starlette.requests import parse_options_header

from src.storages.base import BaseStorage
from src.storages.registry import LOCAL_STORAGE, STORAGES


class TargetFileMultipartParser(MultiPartParser):
    """
    Write directly to the target file without using a temporary one
    Increase max_file_size
    """

    max_file_size = 1024 * 1024 * 1024 * 10  # 10 gb

    def __init__(self, *args, storage=STORAGES[LOCAL_STORAGE], **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.storage: BaseStorage = storage
        self._files_to_close_on_error: list[BinaryIO[bytes]] = []

    def get_file_to_write(self, filename: str) -> BinaryIO:
        storage_filename = self.storage.filename_to_storage_filename(filename)
        storage_upload_path = self.storage.get_upload_path(storage_filename)
        return open(storage_upload_path, 'w+b')

    def on_headers_finished(self) -> None:
        disposition, options = parse_options_header(
            self._current_part.content_disposition
        )
        try:
            self._current_part.field_name = _user_safe_decode(
                options[b"name"], self._charset
            )
        except KeyError:
            raise MultiPartException(
                'The Content-Disposition header field "name" must be ' "provided."
            )

        if b"filename" in options:
            self._current_files += 1
            if self._current_files > self.max_files:
                raise MultiPartException(
                    f"Too many files. Maximum number of files is {self.max_files}."
                )

            filename = _user_safe_decode(options[b"filename"], self._charset)

            file = self.get_file_to_write(filename)
            self._files_to_close_on_error.append(file)

            self._current_part.file = UploadFile(
                file=file,  # type: ignore[arg-type]
                size=0,
                filename=filename,
                headers=Headers(raw=self._current_part.item_headers),
            )
        else:
            self._current_fields += 1
            if self._current_fields > self.max_fields:
                raise MultiPartException(
                    f"Too many fields. Maximum number of fields is {self.max_fields}."
                )
            self._current_part.file = None
