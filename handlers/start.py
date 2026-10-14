from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.inline import (
    diagnostic_intro_kb, main_menu_kb, subjects_kb,
)
from models import User
from services.referral import attach_referrer
from config import settings
from texts import (
    DIAGNOSTIC_INTRO, MAIN_MENU, REFERRAL_INVITE, START_GREETING,
)

router = Router()


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    session: AsyncSession,
    user: User,
):
    await state.clear()

    if command.args and command.args.startswith("ref_"):
        try:
            ref_id = int(command.args[4:])
            await attach_referrer(session, user, ref_id)
        except ValueError:
            pass

    if user.role == "guest" or user.subject_current is None:
        await message.answer(START_GREETING, reply_markup=subjects_kb())
    else:
        await message.answer(MAIN_MENU, reply_markup=main_menu_kb())


@router.callback_query(F.data == "menu:subjects")
async def menu_subjects(call: CallbackQuery):
    await call.message.edit_text(START_GREETING, reply_markup=subjects_kb())
    await call.answer()


@router.callback_query(F.data.startswith("subject:"))
async def choose_subject(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User,
):
    subj = call.data.split(":", 1)[1]
    if subj not in ("math", "rus"):
        await call.answer()
        return
    user.subject_current = subj
    await session.commit()

    me = await call.bot.me()
    link = f"https://t.me/{me.username}?start=ref_{user.id}"
    invite = REFERRAL_INVITE.format(days=settings.referral_reward_days, link=link)

    await call.message.edit_text(
        DIAGNOSTIC_INTRO.format(n=settings.diagnostic_size)
        + "\n\n" + invite,
        reply_markup=diagnostic_intro_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "menu:main")
async def menu_main(call: CallbackQuery):
    await call.message.edit_text(MAIN_MENU, reply_markup=main_menu_kb())
    await call.answer()
