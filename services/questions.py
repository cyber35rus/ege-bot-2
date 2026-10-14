from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
from models import DiagnosticResult, Question, User, UserProgress

LETTERS = ["A", "B", "C", "D", "E", "F"]


def can_answer(user: User) -> bool:
    if user.role in ("premium", "admin"):
        return True
    return user.daily_count < settings.free_daily_limit


def format_question(q: Question) -> str:
    return f"📖 <b>{q.topic}</b>\n\n{q.task_text}"


async def pick_train_question(session: AsyncSession, user: User) -> Question | None:
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
    weak = list(dr.weak_topics or []) if dr else []

    if weak:
        stmt = (
            select(Question)
            .where(
                Question.subject == user.subject_current,
                Question.topic.in_(weak),
            )
            .order_by(func.random())
            .limit(1)
        )
        q = (await session.execute(stmt)).scalar_one_or_none()
        if q:
            return q

    stmt = (
        select(Question)
        .where(Question.subject == user.subject_current)
        .order_by(func.random())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def log_answer(
    session: AsyncSession, user: User, question: Question, is_correct: bool
) -> None:
    session.add(
        UserProgress(
            user_id=user.id,
            question_id=question.id,
            answered_correctly=is_correct,
        )
    )
    user.daily_count += 1
    await session.commit()
