from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from keyboards.inline import (
    next_question_kb, question_kb, subscribe_kb,
)
from models import Question, User
from services.questions import (
    LETTERS, can_answer, format_question, log_answer, pick_train_question,
)
from texts import (
    ANSWER_CORRECT, ANSWER_EXPLANATION, ANSWER_WRONG,
    EXPLANATION_HEADER, LIMIT_REACHED,
)

router = Router()


@router.message(Command("train"))
async def train_cmd(message: Message, session: AsyncSession, user: User):
    await _start_training(message, session, user)


@router.callback_query(F.data == "train:start")
async def train_start(call: CallbackQuery, session: AsyncSession, user: User):
    await call.answer()
    await _start_training(call.message, session, user)


async def _start_training(message: Message, session: AsyncSession, user: User):
    if not user.subject_current:
        await message.answer("Сначала выбери предмет через /start")
        return
    if not can_answer(user):
        await message.answer(
            LIMIT_REACHED.format(limit=settings.free_daily_limit),
            reply_markup=subscribe_kb(),
        )
        return

    q = await pick_train_question(session, user)
    if q is None:
        await message.answer("Вопросы ещё не загружены 😔")
        return

    await message.answer(format_question(q), reply_markup=question_kb(q, "ans"))


@router.callback_query(F.data.startswith("ans:"))
async def on_answer(
    call: CallbackQuery,
    session: AsyncSession,
    user: User,
):
    if not can_answer(user):
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer(
            LIMIT_REACHED.format(limit=settings.free_daily_limit),
            reply_markup=subscribe_kb(),
        )
        await call.answer()
        return

    _, q_id_s, opt_s = call.data.split(":")
    q_id, opt = int(q_id_s), int(opt_s)
    q: Question = await session.get(Question, q_id)
    if q is None:
        await call.answer("Вопрос не найден")
        return

    is_correct = (opt == q.correct_option)
    await log_answer(session, user, q, is_correct)

    mark = ANSWER_CORRECT if is_correct else ANSWER_WRONG.format(letter=LETTERS[q.correct_option])
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(
        ANSWER_EXPLANATION.format(mark=mark, header=EXPLANATION_HEADER, explanation=q.explanation),
        reply_markup=next_question_kb(),
    )
    await call.answer()
