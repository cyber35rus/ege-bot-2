from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from models import User


def utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def extend_subscription(session: AsyncSession, user: User, days: int) -> None:
    now = utcnow_naive()
    base = user.subscription_until if user.subscription_until and user.subscription_until > now else now
    user.subscription_until = base + timedelta(days=days)
    user.role = "premium"
    await session.commit()


def subscription_status(user: User) -> str:
    from texts import SUB_ACTIVE, SUB_FREE
    from config import settings
    if user.role == "premium" and user.subscription_until:
        return SUB_ACTIVE.format(until=user.subscription_until.strftime("%d.%m.%Y"))
    return SUB_FREE.format(limit=settings.free_daily_limit)
