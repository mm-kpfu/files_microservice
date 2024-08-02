from loguru import logger
import sys
import os
from src.settings import settings


if not os.path.exists(settings.LOG_DIR):
    os.makedirs(settings.LOG_DIR)


log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

logger.remove()
logger.add(sys.stdout, format=log_format, level='DEBUG', serialize=True)
logger.add(sys.stdout, format=log_format, level="INFO", serialize=True)
logger.add(os.path.join(settings.LOG_DIR, "app.log"), format=log_format, level="INFO", serialize=True)
logger.add(os.path.join(settings.LOG_DIR, "error.log"), format=log_format, level="ERROR", serialize=True)
