from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from src.logging import logger
from src.settings import settings


engine = create_async_engine(str(settings.DSN__DB))

Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=AsyncSession)

Base = declarative_base()


async def get_db():
    async with Session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(e)
            await session.rollback()
            raise
