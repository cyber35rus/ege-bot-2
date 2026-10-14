from datetime import date, datetime
from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    role: Mapped[str] = mapped_column(String(16), default="guest")
    subject_current: Mapped[str | None] = mapped_column(String(8), nullable=True)
    exam_type: Mapped[str] = mapped_column(String(8), default="ege")

    daily_count: Mapped[int] = mapped_column(Integer, default=0)
    daily_reset_at: Mapped[date] = mapped_column(Date, default=date.today)

    subscription_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    referrer_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
