from aiogram.dispatcher.filters.state import StatesGroup, State


class SetAdminGroup(StatesGroup):
    group_id = State()


class CreateLesson(StatesGroup):
    chat_id = State()
    title = State()
    date_time = State()


class StudentReview(StatesGroup):
    text = State()





