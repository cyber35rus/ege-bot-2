from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from keyboards.inline import diagnostic_result_kb, question_kb
from models import Question, User
from services.diagnostic import pick_diagnostic_questions, save_diagnostic_result
from services.questions import LETTERS
from services.referral import try_grant_referral_reward
from states import DiagnosticStates
from texts import (
    ANSWER_EXPLANATION, ANSWER_CORRECT, ANSWER_WRONG,
    DIAGNOSTIC_RESULT, DIAGNOSTIC_STARTED, EXPLANATION_HEADER,
    QUESTION_HEADER, REFERRAL_REWARD,
)

router = Router()


@router.callback_query(F.data == "diag:start")
async def start_diag(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User,
):
    if not user.subject_current:
        await call.answer("Сначала выбери предмет", show_alert=True)
        return
    questions = await pick_diagnostic_questions(
        session, user.subject_current, settings.diagnostic_size
    )
    if not questions:
        await call.answer("Вопросы ещё не загружены", show_alert=True)
        return

    await state.set_state(DiagnosticStates.answering)
    await state.update_data(
        subject=user.subject_current,
        q_ids=[q.id for q in questions],
        pos=0,
        correct=0,
        wrong_topics=[],
    )
    await call.message.edit_text(DIAGNOSTIC_STARTED)
    await call.answer()
    await _send_current(call.message, state, session)


async def _send_current(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    pos = data["pos"]
    q_ids = data["q_ids"]
    if pos >= len(q_ids):
        return
    q = await session.get(Question, q_ids[pos])
    header = QUESTION_HEADER.format(n=pos + 1, total=len(q_ids), topic=q.topic)
    await message.answer(f"{header}\n\n{q.task_text}", reply_markup=question_kb(q, "diag"))


@router.callback_query(DiagnosticStates.answering, F.data.startswith("diag:"))
async def diag_answer(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User,
):
    _, q_id_s, opt_s = call.data.split(":")
    q_id, opt = int(q_id_s), int(opt_s)

    data = await state.get_data()
    pos = data["pos"]
    q_ids = data["q_ids"]
    if pos >= len(q_ids) or q_ids[pos] != q_id:
        await call.answer("Этот вопрос уже не актуален")
        return

    q = await session.get(Question, q_id)
    is_correct = (opt == q.correct_option)

    if is_correct:
        mark = ANSWER_CORRECT
    else:
        mark = ANSWER_WRONG.format(letter=LETTERS[q.correct_option])

    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(
        ANSWER_EXPLANATION.format(mark=mark, header=EXPLANATION_HEADER, explanation=q.explanation)
    )

    new_pos = pos + 1
    new_correct = data["correct"] + (1 if is_correct else 0)
    wrong = list(data["wrong_topics"])
    if not is_correct:
        wrong.append(q.topic)
    await state.update_data(pos=new_pos, correct=new_correct, wrong_topics=wrong)

    if new_pos >= len(q_ids):
        subject = data["subject"]
        total = len(q_ids)
        await save_diagnostic_result(session, user, subject, new_correct, wrong)

        referrer = await try_grant_referral_reward(session, user)
        if referrer is not None:
            try:
                await call.bot.send_message(
                    referrer.id,
                    REFERRAL_REWARD.format(days=settings.referral_reward_days),
                )
            except Exception:
                pass

        await state.clear()
        weak = ", ".join(sorted(set(wrong))) or "—"
        await call.message.answer(
            DIAGNOSTIC_RESULT.format(score=new_correct, total=total, weak=weak),
            reply_markup=diagnostic_result_kb(),
        )
    else:
        await _send_current(call.message, state, session)

    await call.answer()
