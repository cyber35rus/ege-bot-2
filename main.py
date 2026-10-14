import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import select

from config import settings
from middlewares.db import DbUserMiddleware
from services.db import SessionLocal, init_db

from handlers import (
    admin, diagnostic, start, stats, subscribe, support, train,
)


async def auto_seed() -> None:
    """Подгружает вопросы из data/*.json, добавляя только те, которых нет в БД."""
    import json
    from pathlib import Path
    from models import Question

    paths = [
        Path("data/questions_full.json"),
        Path("data/questions_sample.json"),
    ]
    found = next((p for p in paths if p.exists()), None)
    if not found:
        logging.warning("No seed file found")
        return

    data = json.loads(found.read_text(encoding="utf-8"))
    async with SessionLocal() as session:
        existing = set()
        for row in (await session.execute(select(Question.task_text))).scalars().all():
            existing.add(row)
        added = 0
        for item in data:
            if item["task_text"] in existing:
                continue
            session.add(Question(**item))
            added += 1
        await session.commit()
        logging.info("Auto-seed: added %s new questions (file=%s)", added, found.name)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.outer_middleware(DbUserMiddleware())

    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(diagnostic.router)
    dp.include_router(train.router)
    dp.include_router(subscribe.router)
    dp.include_router(stats.router)
    dp.include_router(support.router)

    await init_db()
    await auto_seed()
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
