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
    """Подгружает вопросы из всех data/*.json, добавляя только те, которых нет в БД."""
    import json
    from pathlib import Path
    from models import Question

    files = sorted(Path("data").glob("questions_*.json"))
    if not files:
        logging.warning("No seed files in data/")
        return

    async with SessionLocal() as session:
        existing = set(
            (await session.execute(select(Question.task_text))).scalars().all()
        )
        total_added = 0
        for path in files:
            data = json.loads(path.read_text(encoding="utf-8"))
            added = 0
            for item in data:
                if item["task_text"] in existing:
                    continue
                session.add(Question(**item))
                existing.add(item["task_text"])
                added += 1
            total_added += added
            logging.info("Seed %s: +%s", path.name, added)
        await session.commit()
        logging.info("Auto-seed total: +%s questions", total_added)


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
