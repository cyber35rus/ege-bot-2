from sqlalchemy import Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject: Mapped[str] = mapped_column(String(8), index=True)
    topic: Mapped[str] = mapped_column(String(128), index=True)
    exam_type: Mapped[str] = mapped_column(String(8), default="ege")
    task_text: Mapped[str] = mapped_column(Text)
    options: Mapped[list[str]] = mapped_column(JSON)
    correct_option: Mapped[int] = mapped_column(Integer)
    explanation: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
