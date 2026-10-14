from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
from models import Referral, User
from services.subscription import extend_subscription


async def attach_referrer(session: AsyncSession, user: User, ref_id: int) -> None:
    if ref_id == user.id or user.referrer_id is not None:
        return
    referrer = await session.get(User, ref_id)
    if referrer is None:
        return
    user.referrer_id = ref_id
    session.add(
        Referral(
            referrer_id=ref_id,
            invited_id=user.id,
            reward_days=settings.referral_reward_days,
            granted=False,
        )
    )
    await session.commit()


async def try_grant_referral_reward(session: AsyncSession, user: User) -> User | None:
    if user.referrer_id is None:
        return None
    stmt = select(Referral).where(
        Referral.invited_id == user.id,
        Referral.granted.is_(False),
    )
    ref = (await session.execute(stmt)).scalar_one_or_none()
    if ref is None:
        return None
    referrer = await session.get(User, ref.referrer_id)
    if referrer is None:
        return None
    await extend_subscription(session, referrer, ref.reward_days)
    ref.granted = True
    await session.commit()
    return referrer
