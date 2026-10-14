from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from keyboards.inline import back_to_menu_kb
from models import DiagnosticResult, User, UserProgress
from services.subscription import subscription_status
from texts import STATS_TEMPLATE, SUB_TOPIC_NONE

router = Router()


@router.message(Command("stats"))
async def stats_cmd(message: Message, session: AsyncSession, user: User):
    await message.answer(await _build(session, user), reply_markup=back_to_menu_kb())


@router.callback_query(F.data == "stats:show")
async def stats_cb(call: CallbackQuery, session: AsyncSession, user: User):
    await call.message.answer(await _build(session, user), reply_markup=back_to_menu_kb())
    await call.answer()


async def _build(session: AsyncSession, user: User) -> str:
    total = (await session.execute(
        select(func.count()).select_from(UserProgress).where(UserProgress.user_id == user.id)
    )).scalar() or 0

    correct = (await session.execute(
        select(func.count()).select_from(UserProgress).where(
            UserProgress.user_id == user.id,
            UserProgress.answered_correctly.is_(True),
        )
    )).scalar() or 0

    pct = int(round(100 * correct / total)) if total else 0

    stmt = (
        select(DiagnosticResult)
        .where(
            DiagnosticResult.user_id == user.id,
            DiagnosticResult.subject == user.subject_current,
        )
        .order_by(DiagnosticResult.created_at.desc())
        .limit(1)
    )
    dr = (await session.execute(stmt)).scalar_one_or_none()
    weak = ", ".join(dr.weak_topics) if dr and dr.weak_topics else SUB_TOPIC_NONE

    return STATS_TEMPLATE.format(
        solved=total,
        correct=correct,
        pct=pct,
        topic=weak,
        sub=subscription_status(user),
        limit=f"{user.daily_count}/{settings.free_daily_limit}",
    )
