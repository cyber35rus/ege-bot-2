import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from middlewares.db import DbUserMiddleware
from services.db import init_db

from handlers import (
    admin, diagnostic, start, stats, subscribe, support, train,
)


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
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
