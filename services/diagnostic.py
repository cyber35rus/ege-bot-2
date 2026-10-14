from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from models import DiagnosticResult, Question, User


async def pick_diagnostic_questions(
    session: AsyncSession, subject: str, n: int
) -> list[Question]:
    stmt = (
        select(Question)
        .where(Question.subject == subject)
        .order_by(func.random())
        .limit(n)
    )
    return list((await session.execute(stmt)).scalars().all())


async def save_diagnostic_result(
    session: AsyncSession,
    user: User,
    subject: str,
    score: int,
    wrong_topics: list[str],
) -> None:
    dr = DiagnosticResult(
        user_id=user.id,
        subject=subject,
        total_score=score,
        weak_topics=sorted(set(wrong_topics)),
    )
    session.add(dr)
    if user.role == "guest":
        user.role = "free"
    await session.commit()
