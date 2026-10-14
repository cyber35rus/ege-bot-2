import time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery, LabeledPrice, Message, PreCheckoutQuery,
)
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from keyboards.inline import subscribe_kb
from models import User
from services.payments import record_payment
from services.subscription import extend_subscription
from texts import INVOICE_DESCRIPTION, PAYMENT_SUCCESS, SUBSCRIBE_MENU

router = Router()


@router.message(Command("subscribe"))
async def sub_cmd(message: Message):
    await message.answer(_menu_text(), reply_markup=subscribe_kb())


@router.callback_query(F.data == "sub:menu")
async def sub_menu(call: CallbackQuery):
    await call.message.edit_text(_menu_text(), reply_markup=subscribe_kb())
    await call.answer()


def _menu_text() -> str:
    return SUBSCRIBE_MENU.format(
        month=settings.price_stars_month,
        year=settings.price_stars_year,
    )


@router.callback_query(F.data == "sub:buy:month")
async def buy_month(call: CallbackQuery, user: User):
    await _send_invoice(call, user, "month")
    await call.answer()


@router.callback_query(F.data == "sub:buy:year")
async def buy_year(call: CallbackQuery, user: User):
    await _send_invoice(call, user, "year")
    await call.answer()


async def _send_invoice(call: CallbackQuery, user: User, period: str):
    if period == "month":
        amount, label = settings.price_stars_month, "Подписка на 1 месяц"
    else:
        amount, label = settings.price_stars_year, "Подписка на 1 год"

    payload = f"sub:{period}:{user.id}:{int(time.time())}"
    await call.bot.send_invoice(
        chat_id=call.message.chat.id,
        title=label,
        description=INVOICE_DESCRIPTION,
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=label, amount=amount)],
    )


@router.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await q.answer(ok=True)


@router.message(F.successful_payment)
async def on_success(
    message: Message,
    session: AsyncSession,
    user: User,
):
    sp = message.successful_payment
    parts = sp.invoice_payload.split(":")
    period = parts[1] if len(parts) >= 2 else "month"
    days = 30 if period == "month" else 365

    await extend_subscription(session, user, days)
    await record_payment(session, user, sp, status="succeeded")

    until = user.subscription_until.strftime("%d.%m.%Y") if user.subscription_until else "—"
    await message.answer(PAYMENT_SUCCESS.format(until=until))
