from typing import Tuple

from fastapi import Request, UploadFile

from src.parsers import TargetFileMultipartParser


async def parse_files_from_request(request: Request) -> Tuple[UploadFile, ...]:
    parser = TargetFileMultipartParser(request.headers, request.stream())
    form_data = await parser.parse()
    files = tuple(form_data.values())
    return files
