import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from sqlalchemy import select

from models import User, UserProgress
from services.db import SessionLocal
from services.users import utcnow_naive

MSK = timezone(timedelta(hours=3))


async def _daily_loop(bot: Bot) -> None:
    """Раз в сутки в 12:00 МСК — проверка подписок и напоминания."""
    while True:
        try:
            await notify_subscriptions(bot)
            await notify_reminders(bot)
        except Exception as e:
            logging.exception("notify loop error: %s", e)

        now = datetime.now(MSK)
        target = now.replace(hour=12, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())


async def notify_subscriptions(bot: Bot) -> None:
    from texts import SUB_EXPIRY_3D, SUB_EXPIRY_TODAY

    today = datetime.now(MSK).date()
    async with SessionLocal() as session:
        users = (await session.execute(
            select(User).where(
                User.role == "premium",
                User.subscription_until.is_not(None),
            )
        )).scalars().all()

        for u in users:
            if u.subscription_until is None:
                continue
            days_left = (u.subscription_until.date() - today).days

            if days_left == 3 and not u.sub_notified_3d:
                try:
                    await bot.send_message(
                        u.id,
                        SUB_EXPIRY_3D.format(
                            until=u.subscription_until.strftime("%d.%m.%Y")
                        ),
                    )
                    u.sub_notified_3d = True
                except Exception:
                    pass

            if days_left == 0 and not u.sub_notified_today:
                try:
                    await bot.send_message(u.id, SUB_EXPIRY_TODAY)
                    u.sub_notified_today = True
                except Exception:
                    pass

        await session.commit()


async def notify_reminders(bot: Bot) -> None:
    from texts import TRAIN_REMINDER

    now = utcnow_naive()
    cutoff = now - timedelta(days=3)

    async with SessionLocal() as session:
        users = (await session.execute(
            select(User).where(User.role.in_(["free", "premium"]))
        )).scalars().all()

        for u in users:
            last_answer = (await session.execute(
                select(UserProgress.answered_at)
                .where(UserProgress.user_id == u.id)
                .order_by(UserProgress.answered_at.desc())
                .limit(1)
            )).scalar_one_or_none()

            if last_answer is None or last_answer > cutoff:
                continue
            if u.last_reminder_at is not None and u.last_reminder_at > cutoff:
                continue

            try:
                await bot.send_message(u.id, TRAIN_REMINDER)
                u.last_reminder_at = now
            except Exception:
                pass

        await session.commit()
