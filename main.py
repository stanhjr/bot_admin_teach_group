import re
from datetime import datetime, timedelta

from aiogram import Bot, types
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import ChatTypeFilter, Text
from aiogram.types import PreCheckoutQuery, ContentType, ChatType
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import ChatNotFound, PaymentProviderInvalid, BotKicked

from deploy.config import TOKEN, ADMIN_IDS
from markup.markup import super_admin_menu, admin_menu, student_menu, get_groups_for_super_admin, get_groups_for_bind, \
    get_admins_for_bind, cancel_menu

from messages import MESSAGES
from models.db_api import data_api
from states import SetAdminGroup, CreateLesson

bot = Bot(token=TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())


async def get_reply_markup(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        return super_admin_menu
    if message.from_user.id in data_api.get_admin_telegram_id():
        return admin_menu
    if message.from_user.id in data_api.get_students_telegram_id():
        return student_menu


@dp.message_handler(text="❌Отмена")
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


# test
@dp.message_handler(ChatTypeFilter(chat_type=ChatType.GROUP))
async def get_user_group(message: types.Message):
    admins = await bot.get_chat_administrators(message.chat.id)
    for admin in admins:
        print(admin, type(admin))


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


@dp.message_handler(ChatTypeFilter(chat_type=ChatType.PRIVATE), Text('➕ Привязать админа к группе'))
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
                               text=MESSAGES["enter_title_lesson"],
                               reply_markup=cancel_menu)

        await CreateLesson.first()


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
        try:
            date_time_obj = datetime.strptime(message.text, '%d/%m/%y %H:%M')
            print(title)
            print(date_time_obj)
            await bot.send_message(message.from_user.id,
                                   text=MESSAGES["enter_lesson_ok"],
                                   reply_markup=admin_menu)
            await state.finish()
        except ValueError:
            await CreateLesson.previous()












if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
