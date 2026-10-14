from aiogram.fsm.state import State, StatesGroup


class DiagnosticStates(StatesGroup):
    answering = State()


class SupportStates(StatesGroup):
    waiting = State()


class AddQuestion(StatesGroup):
    subject = State()
    topic = State()
    exam_type = State()
    task_text = State()
    options = State()
    correct = State()
    explanation = State()
    difficulty = State()
