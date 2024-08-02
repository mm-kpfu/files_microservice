from typing import BinaryIO, Callable

from fastapi import Request, HTTPException
from fastapi.openapi.models import Response
from fastapi.routing import APIRoute

from starlette.datastructures import FormData, UploadFile, Headers
from starlette.formparsers import MultiPartParser, MultiPartException, FormParser, _user_safe_decode
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


class TargetFileUploadRequest(Request):
    async def _get_form(
        self, *, max_files: int | float = 1000, max_fields: int | float = 1000
    ) -> FormData:
        if self._form is None:
            assert (
                parse_options_header is not None
            ), "The `python-multipart` library must be installed to use form parsing."
            content_type_header = self.headers.get("Content-Type")
            content_type: bytes
            content_type, _ = parse_options_header(content_type_header)
            if content_type == b"multipart/form-data":
                try:
                    multipart_parser = TargetFileMultipartParser(
                        self.headers,
                        self.stream(),
                        max_files=max_files,
                        max_fields=max_fields,
                    )
                    self._form = await multipart_parser.parse()
                except MultiPartException as exc:
                    if "app" in self.scope:
                        raise HTTPException(status_code=400, detail=exc.message)
                    raise exc
            elif content_type == b"application/x-www-form-urlencoded":
                form_parser = FormParser(self.headers, self.stream())
                self._form = await form_parser.parse()
            else:
                self._form = FormData()
        return self._form


class TargetFileRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def target_file_request_route_handler(request: Request) -> Response:
            request = TargetFileUploadRequest(request.scope, request.receive)
            return await original_route_handler(request)

        return target_file_request_route_handler
