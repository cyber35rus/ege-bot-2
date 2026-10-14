import asyncio

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import Payment, Question, User
from states import AddQuestion
from handlers.support import TICKET_PREFIX

router = Router()


def admin_only(message: Message) -> bool:
    return message.from_user is not None and message.from_user.id in settings.admins


@router.message(Command("addquestion"))
async def addq_start(message: Message, state: FSMContext):
    if not admin_only(message):
        return
    await state.set_state(AddQuestion.subject)
    await message.answer("Предмет? (math/rus)")


@router.message(AddQuestion.subject)
async def addq_subject(message: Message, state: FSMContext):
    if message.text not in ("math", "rus"):
        await message.answer("Только math или rus")
        return
    await state.update_data(subject=message.text)
    await state.set_state(AddQuestion.topic)
    await message.answer("Тема? (например: Квадратные уравнения)")


@router.message(AddQuestion.topic)
async def addq_topic(message: Message, state: FSMContext):
    await state.update_data(topic=message.text)
    await state.set_state(AddQuestion.exam_type)
    await message.answer("Тип экзамена? (ege/oge)")


@router.message(AddQuestion.exam_type)
async def addq_exam(message: Message, state: FSMContext):
    if message.text not in ("ege", "oge"):
        await message.answer("Только ege или oge")
        return
    await state.update_data(exam_type=message.text)
    await state.set_state(AddQuestion.task_text)
    await message.answer("Текст задания?")


@router.message(AddQuestion.task_text)
async def addq_text(message: Message, state: FSMContext):
    await state.update_data(task_text=message.text)
    await state.set_state(AddQuestion.options)
    await message.answer("Варианты ответа (4 шт., через ` | `)?")


@router.message(AddQuestion.options)
async def addq_options(message: Message, state: FSMContext):
    parts = [p.strip() for p in (message.text or "").split("|") if p.strip()]
    if len(parts) < 2:
        await message.answer("Минимум 2 варианта, разделитель ` | `")
        return
    await state.update_data(options=parts)
    await state.set_state(AddQuestion.correct)
    await message.answer("Номер правильного (с 1)?")


@router.message(AddQuestion.correct)
async def addq_correct(message: Message, state: FSMContext):
    try:
        idx = int(message.text) - 1
    except (TypeError, ValueError):
        await message.answer("Нужно число")
        return
    data = await state.get_data()
    if idx < 0 or idx >= len(data["options"]):
        await message.answer("Вне диапазона")
        return
    await state.update_data(correct_option=idx)
    await state.set_state(AddQuestion.explanation)
    await message.answer("Разбор (объяснение)?")


@router.message(AddQuestion.explanation)
async def addq_explanation(message: Message, state: FSMContext):
    await state.update_data(explanation=message.text)
    await state.set_state(AddQuestion.difficulty)
    await message.answer("Сложность (1-3)?")


@router.message(AddQuestion.difficulty)
async def addq_difficulty(message: Message, state: FSMContext, session: AsyncSession):
    try:
        d = int(message.text)
    except (TypeError, ValueError):
        await message.answer("Нужно число 1-3")
        return
    if d not in (1, 2, 3):
        await message.answer("Только 1, 2 или 3")
        return
    data = await state.get_data()
    q = Question(
        subject=data["subject"],
        topic=data["topic"],
        exam_type=data["exam_type"],
        task_text=data["task_text"],
        options=data["options"],
        correct_option=data["correct_option"],
        explanation=data["explanation"],
        difficulty=d,
    )
    session.add(q)
    await session.commit()
    await state.clear()
    await message.answer(f"✅ Вопрос #{q.id} добавлен")


@router.message(Command("broadcast"))
async def broadcast(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
):
    if not admin_only(message):
        return
    text = (command.args or "").strip()
    if not text:
        await message.answer("Использование: /broadcast <текст>")
        return

    ids = [row for row in (await session.execute(select(User.id))).scalars().all()]
    sent, failed = 0, 0
    for uid in ids:
        try:
            await message.bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await message.answer(f"📢 Отправлено: {sent}, ошибок: {failed}")


@router.message(Command("stats_global"))
async def stats_global(message: Message, session: AsyncSession):
    if not admin_only(message):
        return
    total = (await session.execute(select(func.count()).select_from(User))).scalar() or 0
    premium = (await session.execute(
        select(func.count()).select_from(User).where(User.role == "premium")
    )).scalar() or 0
    paid = (await session.execute(
        select(func.count()).select_from(Payment).where(Payment.status == "succeeded")
    )).scalar() or 0
    mrr = (await session.execute(
        select(func.coalesce(func.sum(Payment.stars_amount), 0)).where(Payment.status == "succeeded")
    )).scalar() or 0

    conversion = f"{premium / total * 100:.1f}%" if total else "0%"
    await message.answer(
        f"👥 Пользователей: {total}\n"
        f"⭐ Premium: {premium} ({conversion})\n"
        f"💳 Успешных платежей: {paid}\n"
        f"💰 Всего Stars: {mrr}"
    )


@router.message(
    F.reply_to_message,
    F.reply_to_message.text.startswith(TICKET_PREFIX),
)
async def admin_reply(message: Message):
    if not admin_only(message):
        return
    src = message.reply_to_message.text
    try:
        first_line = src.split("\n", 1)[0]
        user_id = int(first_line.replace(TICKET_PREFIX, "").strip())
    except (ValueError, IndexError):
        return
    try:
        await message.bot.send_message(user_id, f"💬 Ответ поддержки:\n\n{message.text}")
        await message.answer("✅ Отправлено")
    except Exception as e:
        await message.answer(f"⚠️ Не доставлено: {e}")


@router.message(Command("fake_pay"))
async def fake_pay(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    user: User,
):
    if not admin_only(message):
        return
    days = 30
    if command.args:
        try:
            days = int(command.args.strip())
        except ValueError:
            await message.answer("Использование: /fake_pay [дней] (по умолчанию 30)")
            return

    from services.subscription import extend_subscription
    from models import Payment

    await extend_subscription(session, user, days)
    session.add(Payment(
        user_id=user.id,
        stars_amount=0,
        payload=f"fake:{days}",
        telegram_charge_id=None,
        status="succeeded",
    ))
    await session.commit()

    until_str = user.subscription_until.strftime("%d.%m.%Y") if user.subscription_until else "—"
    await message.answer(
        f"✅ Fake-оплата на {days} дней.\n"
        f"Подписка активна до <b>{until_str}</b>."
    )
