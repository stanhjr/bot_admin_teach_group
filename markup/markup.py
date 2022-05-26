from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from models.db_api import data_api


def get_student_group_for_admin(message: types.Message):
    groups = data_api.get_student_group_for_admin(message)
    if groups:
        inline_kb_full = InlineKeyboardMarkup(row_width=2)
        for chat_id, group_title in groups:
            inline_kb_full.add(InlineKeyboardButton(group_title, callback_data=f"s_m_{chat_id}"))
        return inline_kb_full


def get_groups_for_super_admin():
    groups = data_api.get_active_group()
    inline_kb_full = InlineKeyboardMarkup(row_width=2)
    for group_id, group_title in groups:
        inline_kb_full.add(InlineKeyboardButton(group_title, callback_data=f"g_a_{group_id}"))
    return inline_kb_full


def get_groups_for_bind():
    groups = data_api.get_active_group_for_bind()
    if groups:
        inline_kb_full = InlineKeyboardMarkup(row_width=2)
        for group_id, group_title in groups:
            inline_kb_full.add(InlineKeyboardButton(group_title, callback_data=f"g_b_{group_id}"))
        return inline_kb_full


def get_groups_for_bind_review():
    groups = data_api.get_active_group_for_bind()
    if groups:
        inline_kb_full = InlineKeyboardMarkup(row_width=2)
        for group_id, group_title in groups:
            inline_kb_full.add(InlineKeyboardButton(group_title, callback_data=f"g_r_{group_id}"))
        return inline_kb_full


def get_admins_for_bind():
    admins = data_api.get_admin_users_for_bind()
    inline_kb_full = InlineKeyboardMarkup(row_width=2)
    for user_id, user_first_name in admins:
        inline_kb_full.add(InlineKeyboardButton(user_first_name, callback_data=f"u_a_{user_id}"))
    return inline_kb_full


def get_student_group_for_bind(message: types.Message):
    groups = data_api.get_student_group_for_admin(message)
    if groups:
        inline_kb_full = InlineKeyboardMarkup(row_width=2)
        for chat_id, group_title in groups:
            inline_kb_full.add(InlineKeyboardButton(group_title, callback_data=f"g_s_{chat_id}"))
        return inline_kb_full


cancel_menu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
cancel_button = KeyboardButton("❌Отмена")
cancel_menu.add(cancel_button)

super_admin_menu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
enter_super_group_button = KeyboardButton("➕ Назначить супер группу")
create_admin_for_group = KeyboardButton("➕ Установить преподователя для группы")
create_reply_group = KeyboardButton("➕ Назначить группу для получения отзывов")
send_message_for_all_students = KeyboardButton("➕ Отправить сообщение всем студентам")
super_admin_menu.add(enter_super_group_button)
super_admin_menu.add(create_admin_for_group)
super_admin_menu.add(create_reply_group)
super_admin_menu.add(send_message_for_all_students)
# super_admin_menu.add(cancel_button)


admin_menu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
create_lesson = KeyboardButton("➕ Создать новый урок")
create_message = KeyboardButton("➕ Отправить сообщение группе студентов")
admin_menu.add(create_lesson)
admin_menu.add(create_message)
admin_menu.add(cancel_button)


student_menu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
create_reply = KeyboardButton("➕ Оставить отзыв")
student_menu.add(create_reply)


empty_menu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
