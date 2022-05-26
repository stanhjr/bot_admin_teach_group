import re
from datetime import datetime, timedelta

from aiogram import Bot, types
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import ChatTypeFilter, Text
from aiogram.types import ContentType, ChatType
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import ChatNotFound, PaymentProviderInvalid, BotKicked

from deploy.config import TOKEN, ADMIN_IDS
from markup.markup import super_admin_menu, admin_menu, student_menu, get_groups_for_super_admin, get_groups_for_bind, \
    get_admins_for_bind, cancel_menu, get_student_group_for_bind, get_groups_for_bind_review, get_student_group_for_admin

from messages import MESSAGES
from models.db_api import data_api
from states import SetAdminGroup, CreateLesson, StudentReview, SendMessageForStudent, SendMessageForAllStudent

bot = Bot(token=TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())


async def get_reply_markup(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        return super_admin_menu
    if message.from_user.id in data_api.get_admin_telegram_id():
        return admin_menu
    if message.from_user.id in data_api.get_students_telegram_id():
        return student_menu


@dp.message_handler(text="❌Отмена", state='*')
async def cancel_currency(message: types.Message, state: FSMContext):
    await state.reset_data()
    await state.finish()
    reply_markup = await get_reply_markup(message)
    if reply_markup:
        await bot.send_message(message.chat.id, MESSAGES["сanceled"], reply_markup=reply_markup)


@dp.message_handler(ChatTypeFilter(chat_type=ChatType.PRIVATE), commands=['start'])
async def start(message: types.Message):
    reply_markup = await get_reply_markup(message)
    if reply_markup:
        await bot.send_message(message.chat.id, MESSAGES["start_ok"], reply_markup=reply_markup)


# add user in group
@dp.message_handler(content_types=[ContentType.NEW_CHAT_MEMBERS])
async def new_members_handler(message: types.Message):
    bot_obj = await bot.get_me()
    bot_id = bot_obj.id
    new_member = message.new_chat_members[0]
    if new_member.id != bot_id:
        if message.chat.id == data_api.get_admin_group_chat_id():
            data_api.create_admin(message, new_member, is_admin=True)
        else:
            data_api.create_student(message, new_member)
    else:
        data_api.activate_group(message)


@dp.message_handler(ChatTypeFilter(chat_type=ChatType.PRIVATE), Text('➕ Отправить сообщение всем студентам'))
async def send_message_for_all_student(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["enter_message_for_all_student"],
                               reply_markup=cancel_menu)
        await SendMessageForAllStudent.first()


@dp.message_handler(ChatTypeFilter(chat_type=ChatType.PRIVATE), state=SendMessageForAllStudent.text)
async def call_set_admin_group(message: types.Message, state: FSMContext):
    students_telegram_id = data_api.get_all_students_telegram_id()
    if students_telegram_id:
        for chat_id in students_telegram_id:
            await bot.send_message(chat_id=chat_id, text=message.text)

    await bot.send_message(message.from_user.id,
                           text=MESSAGES["enter_message_ok"],
                           reply_markup=super_admin_menu)
    await state.finish()


@dp.message_handler(ChatTypeFilter(chat_type=ChatType.PRIVATE), Text('➕ Отправить сообщение группе студентов'))
async def send_message_for_all_student(message: types.Message):
    if message.from_user.id in data_api.get_admin_telegram_id():
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["bind_group"],
                               reply_markup=get_student_group_for_admin(message))
        await SendMessageForStudent.first()


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('s_m_'), state=SendMessageForStudent.chat_id)
async def create_lesson_step_two(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id in data_api.get_admin_telegram_id():
        chat_id = callback_query.data[4:]
        await state.update_data(chat_id=chat_id)
        await bot.send_message(callback_query.from_user.id,
                               text=MESSAGES["enter_message_for_group"],
                               reply_markup=cancel_menu)
        await SendMessageForStudent.next()


@dp.message_handler(ChatTypeFilter(chat_type=ChatType.PRIVATE), state=SendMessageForStudent.text)
async def send_message_for_all_student(message: types.Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    students_telegram_id = data_api.get_students_telegram_id_for_chat_id_group(chat_id=chat_id)
    for chat_id in students_telegram_id:
        await bot.send_message(chat_id=chat_id, text=message.text)
    await bot.send_message(message.from_user.id,
                           text=MESSAGES["enter_message_ok"],
                           reply_markup=admin_menu)
    await state.finish()





















# left admin is admin group
@dp.message_handler(content_types=[ContentType.LEFT_CHAT_MEMBER])
async def left_members_handler(message: types.Message):
    bot_obj = await bot.get_me()
    bot_id = bot_obj.id
    left_member = message.left_chat_member

    if left_member.id != bot_id and message.chat.id == data_api.get_admin_group_chat_id():
        data_api.admin_status_delete(left_member)
    if left_member.id == bot_id:
        data_api.deactivate_group(message)


@dp.message_handler(ChatTypeFilter(chat_type=ChatType.PRIVATE), Text('➕ Назначить супер группу'))
async def set_admin_group(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["edit_admin_group"],
                               reply_markup=get_groups_for_super_admin())


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('g_a_'))
async def call_set_admin_group(callback_query: types.CallbackQuery):
    group_id = callback_query.data[4:]
    data_api.set_admin_group(group_id)
    await bot.send_message(callback_query.from_user.id,
                           text=MESSAGES["new_admin_group"],
                           reply_markup=super_admin_menu)


@dp.message_handler(ChatTypeFilter(chat_type=ChatType.PRIVATE), Text('➕ Назначить группу для получения отзывов'))
async def set_admin_group(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["bind_group"],
                               reply_markup=get_groups_for_bind_review())


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('g_r_'))
async def call_set_admin_group(callback_query: types.CallbackQuery):
    group_id = callback_query.data[4:]
    data_api.set_review_group(group_id)
    await bot.send_message(callback_query.from_user.id,
                           text=MESSAGES["bind_group_review"],
                           reply_markup=super_admin_menu)


@dp.message_handler(ChatTypeFilter(chat_type=ChatType.PRIVATE), Text("➕ Установить преподователя для группы"))
async def bind_admin_group(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        reply_markup = get_groups_for_bind()
        if reply_markup:
            await bot.send_message(message.from_user.id,
                                   text=MESSAGES["bind_group"],
                                   reply_markup=reply_markup)
        else:
            await bot.send_message(message.from_user.id,
                                   text=MESSAGES["bind_not_group"],
                                   reply_markup=super_admin_menu)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('g_b_'))
async def call_set_admin_group(callback_query: types.CallbackQuery, state: FSMContext):
    group_id = callback_query.data[4:]
    await state.update_data(group_id=group_id)
    await bot.send_message(callback_query.from_user.id,
                           text=MESSAGES["bind_admin"],
                           reply_markup=get_admins_for_bind())
    await SetAdminGroup.first()


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('u_a_'), state=SetAdminGroup.group_id)
async def call_set_admin_group(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback_query.data[4:]
    group_id = data.get("group_id")
    if data_api.set_user_admin_for_group(user_id=user_id, group_id=group_id):
        await bot.send_message(callback_query.from_user.id,
                               text=MESSAGES["bind_ok"],
                               reply_markup=super_admin_menu)
    else:
        await bot.send_message(callback_query.from_user.id,
                               text=MESSAGES["bind_error"],
                               reply_markup=super_admin_menu)
    await state.finish()


@dp.message_handler(ChatTypeFilter(chat_type=ChatType.PRIVATE), Text('➕ Создать новый урок'))
async def create_lesson(message: types.Message, state: FSMContext):
    if message.from_user.id in data_api.get_admin_telegram_id():
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["bind_group"],
                               reply_markup=get_student_group_for_bind(message))
        await CreateLesson.first()


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('g_s_'), state=CreateLesson.chat_id)
async def create_lesson_step_two(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id in data_api.get_admin_telegram_id():
        chat_id = callback_query.data[4:]
        await state.update_data(chat_id=chat_id)
        await bot.send_message(callback_query.from_user.id,
                               text=MESSAGES["enter_title_lesson"],
                               reply_markup=cancel_menu)

        await CreateLesson.next()


@dp.message_handler(state=CreateLesson.title)
async def create_lesson(message: types.Message, state: FSMContext):
    if message.from_user.id in data_api.get_admin_telegram_id():
        await state.update_data(title=message.text)
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["enter_time_lesson"],
                               reply_markup=cancel_menu)
        await CreateLesson.next()


@dp.message_handler(state=CreateLesson.date_time)
async def create_lesson(message: types.Message, state: FSMContext):
    if message.from_user.id in data_api.get_admin_telegram_id():
        data = await state.get_data()
        title = data.get("title")
        chat_id = data.get("chat_id")
        try:
            date_time_obj = datetime.strptime(message.text.strip(), '%d/%m/%y %H:%M')
            if data_api.create_lesson(title=title,
                                      chat_id=chat_id,
                                      date_time_obj=date_time_obj):
                await bot.send_message(message.from_user.id,
                                       text=MESSAGES["enter_lesson_ok"],
                                       reply_markup=admin_menu)
            else:
                await bot.send_message(message.from_user.id,
                                       text=MESSAGES["enter_lesson_error"],
                                       reply_markup=admin_menu)
            await state.finish()
        except ValueError:
            await bot.send_message(message.from_user.id,
                                   text=MESSAGES["enter_time_lesson"],
                                   reply_markup=cancel_menu)
            await CreateLesson.previous()


@dp.message_handler(ChatTypeFilter(chat_type=ChatType.PRIVATE), Text('➕ Оставить отзыв'))
async def create_lesson(message: types.Message):
    if message.from_user.id in data_api.get_students_telegram_id():
        await bot.send_message(message.from_user.id,
                               text=MESSAGES["enter_review"],
                               reply_markup=cancel_menu)
        await StudentReview.first()


@dp.message_handler(state=StudentReview.text)
async def create_lesson(message: types.Message, state: FSMContext):
    reply_chat_id = data_api.get_chat_id_for_reply()
    await bot.forward_message(chat_id=reply_chat_id, from_chat_id=message.chat.id, message_id=message.message_id)
    await bot.send_message(message.from_user.id,
                           text=MESSAGES["enter_review_cancel"],
                           reply_markup=student_menu)

    await state.finish()





if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
