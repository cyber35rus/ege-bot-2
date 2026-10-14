from sqlalchemy.ext.asyncio import AsyncSession
from models import Payment, User


async def record_payment(
    session: AsyncSession, user: User, successful_payment, status: str = "succeeded"
) -> Payment:
    p = Payment(
        user_id=user.id,
        stars_amount=successful_payment.total_amount,
        payload=successful_payment.invoice_payload,
        telegram_charge_id=successful_payment.telegram_payment_charge_id,
        status=status,
    )
    session.add(p)
    await session.commit()
    return p
