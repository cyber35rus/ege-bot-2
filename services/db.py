from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine,
)
from config import settings
from models import Base

engine = create_async_engine(settings.async_database_url, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def migrate() -> None:
    """Добавляет новые колонки в существующую БД (идемпотентно)."""
    stmts = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS sub_notified_3d BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS sub_notified_today BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_reminder_at TIMESTAMP",
    ]
    async with engine.begin() as conn:
        for s in stmts:
            try:
                await conn.execute(text(s))
            except Exception:
                pass
