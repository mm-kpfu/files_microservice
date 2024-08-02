from typing import Tuple

from fastapi import Request, UploadFile, HTTPException
from fastapi import status
from starlette.formparsers import MultiPartException

from src.parsers import TargetFileMultipartParser


async def parse_files_from_request(request: Request) -> Tuple[UploadFile, ...]:
    try:
        parser = TargetFileMultipartParser(request.headers, request.stream())
        form_data = await parser.parse()
        files = tuple(form_data.values())
    except MultiPartException:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='Unable to parse file(s)')
    return files
