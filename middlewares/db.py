from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from services.db import SessionLocal
from services.users import (
    apply_daily_reset, apply_subscription_expiry, get_or_create_user,
)


class DbUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with SessionLocal() as session:
            data["session"] = session
            tg_user = data.get("event_from_user")
            if tg_user is not None and not tg_user.is_bot:
                user = await get_or_create_user(session, tg_user)
                await apply_daily_reset(session, user)
                await apply_subscription_expiry(session, user)
                data["user"] = user
            return await handler(event, data)
