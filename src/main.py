from fastapi import FastAPI

from src.apps.files.router import router as files_router

app = FastAPI()

app.include_router(files_router)
