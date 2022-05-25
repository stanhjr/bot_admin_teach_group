from aiogram.dispatcher.filters.state import StatesGroup, State


class SetAdminGroup(StatesGroup):
    group_id = State()


class CreateLesson(StatesGroup):
    title = State()
    date_time = State()



