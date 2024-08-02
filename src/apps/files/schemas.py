from pydantic import BaseModel, HttpUrl


class UploadFileResponseSchema(BaseModel):
    uri: HttpUrl
