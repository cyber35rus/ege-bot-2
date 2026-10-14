from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from keyboards.inline import support_kb
from models import User
from states import SupportStates
from texts import HELP_TEXT, SUPPORT_SENT

router = Router()

TICKET_PREFIX = "📩 Тикет #"


@router.message(Command("help"))
async def help_cmd(message: Message, user: User):
    await message.answer(HELP_TEXT, reply_markup=support_kb())


@router.callback_query(F.data == "help:menu")
async def help_cb(call: CallbackQuery, user: User):
    await call.message.edit_text(HELP_TEXT, reply_markup=support_kb())
    await call.answer()


@router.callback_query(F.data == "help:support")
async def help_support(call: CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.waiting)
    await call.message.edit_text("✍️ Напиши сообщение для поддержки одним текстом.")
    await call.answer()


@router.message(SupportStates.waiting, F.chat.type == "private")
async def receive_support(
    message: Message,
    state: FSMContext,
    user: User,
):
    await state.clear()
    header = (
        f"{TICKET_PREFIX}{user.id}\n"
        f"От: @{user.username or '—'} ({user.first_name or '—'})\n"
        f"---\n"
    )
    for admin_id in settings.admins:
        try:
            await message.bot.send_message(admin_id, header + (message.text or ""))
        except Exception:
            pass
    await message.answer(SUPPORT_SENT)
