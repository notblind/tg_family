from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import settings
from database.models import Base
from pathlib import Path

# Ensure database directory exists
db_path = Path(settings.database_path)
db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    f"sqlite+aiosqlite:///{settings.database_path}",
    connect_args={"check_same_thread": False},
)

async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
