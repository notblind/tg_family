from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import settings
from database.models import Base
from contextlib import asynccontextmanager

# Support both PostgreSQL and SQLite
db_url = settings.database_url
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    db_url,
    echo=False
)

async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@asynccontextmanager
async def get_session():
    async with async_session() as session:
        yield session
