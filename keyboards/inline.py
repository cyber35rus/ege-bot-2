from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import settings
from models import Question
from services.questions import LETTERS


def subjects_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📐 Математика", callback_data="subject:math")],
        [InlineKeyboardButton(text="📖 Русский язык", callback_data="subject:rus")],
    ])


def diagnostic_intro_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧪 Пройти диагностику", callback_data="diag:start")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:subjects")],
    ])


def question_kb(q: Question, prefix: str) -> InlineKeyboardMarkup:
    rows = []
    for i, opt in enumerate(q.options):
        rows.append([InlineKeyboardButton(
            text=f"{LETTERS[i]}) {opt}", callback_data=f"{prefix}:{q.id}:{i}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def next_question_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Следующий вопрос", callback_data="train:start")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:main")],
    ])


def diagnostic_result_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Начать тренировку", callback_data="train:start")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats:show")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:main")],
    ])


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Тренировка", callback_data="train:start")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats:show")],
        [InlineKeyboardButton(text="⭐ Подписка", callback_data="sub:menu")],
        [InlineKeyboardButton(text="🔄 Сменить предмет", callback_data="menu:subjects")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help:menu")],
    ])


def subscribe_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"Месяц — {settings.price_stars_month} ⭐",
            callback_data="sub:buy:month",
        )],
        [InlineKeyboardButton(
            text=f"Год — {settings.price_stars_year} ⭐ (−40%)",
            callback_data="sub:buy:year",
        )],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:main")],
    ])


def support_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Написать поддержке", callback_data="help:support")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:main")],
    ])


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:main")],
    ])
