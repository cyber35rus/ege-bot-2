from datetime import date, datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from models import User

MSK = timezone(timedelta(hours=3))


def msk_today() -> date:
    return datetime.now(MSK).date()


def utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def get_or_create_user(session: AsyncSession, tg_user) -> User:
    user = await session.get(User, tg_user.id)
    if user is None:
        user = User(
            id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            role="guest",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    elif user.username != tg_user.username or user.first_name != tg_user.first_name:
        user.username = tg_user.username
        user.first_name = tg_user.first_name
        await session.commit()
    return user


async def apply_daily_reset(session: AsyncSession, user: User) -> None:
    today = msk_today()
    if user.daily_reset_at != today:
        user.daily_count = 0
        user.daily_reset_at = today
        await session.commit()


async def apply_subscription_expiry(session: AsyncSession, user: User) -> None:
    if (
        user.role == "premium"
        and user.subscription_until is not None
        and user.subscription_until < utcnow_naive()
    ):
        user.role = "free"
        await session.commit()
