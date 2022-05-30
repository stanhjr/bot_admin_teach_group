from aiogram.dispatcher.filters.state import StatesGroup, State


class SetAdminGroup(StatesGroup):
    group_id = State()


class CreateLesson(StatesGroup):
    chat_id = State()
    text = State()
    time = State()


class UpdateLesson(StatesGroup):
    lesson_id = State()
    text = State()
    time = State()


class DeleteLesson(StatesGroup):
    lesson_id = State()


class StudentReview(StatesGroup):
    text = State()


class SendMessageForStudent(StatesGroup):
    chat_id = State()
    text = State()


class SendMessageForAllStudent(StatesGroup):
    text = State()





