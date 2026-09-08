from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.models.db_models import Base

DATABASE_URL = "sqlite+aiosqlite:///faircharge.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
