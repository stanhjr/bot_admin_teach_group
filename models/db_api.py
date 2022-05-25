from datetime import datetime
import time

from aiogram import types
from pandas import DataFrame
from sqlalchemy import and_
from sqlalchemy.sql import func

from models.tabs import session, Users, Groups, Lessons


def is_number(string):
    try:
        string = string.replace(" ", "")
        string = string.replace(",", ".")
        return float(string)
    except ValueError:
        return False


class DataApi:
    def __init__(self):
        self.session = session

    def create_user(self, message: types.Message, new_member, is_admin):
        with self.session() as s:
            user = s.query(Users).filter(Users.telegram_id == new_member.id).first()

            if not user:
                user = Users(telegram_id=new_member.id,
                             username=new_member.username,
                             first_name=new_member.first_name,
                             last_name=new_member.last_name)
            group = s.query(Groups).filter(Groups.chat_id == message.chat.id).first()
            if not group:
                group = Groups(chat_id=message.chat.id,
                               title=message.chat.title)
            group.is_active = 1
            user.is_admin = int(is_admin)
            user.groups.append(group)
            s.add(user)
            s.commit()

    def admin_status_delete(self, left_member):
        with self.session() as s:
            s.query(Users).filter(Users.telegram_id == left_member.id).update({"is_admin": 0})
            s.commit()

    def activate_group(self, message: types.Message):
        with self.session() as s:
            group = s.query(Groups).filter(Groups.chat_id == message.chat.id).first()
            if not group:
                group = Groups(chat_id=message.chat.id,
                               title=message.chat.title)
            group.is_active = 1
            s.add(group)
            s.commit()


    def deactivate_group(self, message: types.Message):
        with self.session() as s:
            s.query(Groups).filter(Groups.chat_id == message.chat.id).update({"is_active": 0})
            s.commit()

    def get_active_group(self):
        with self.session() as s:
            # [(1, 'тестим нового бота')]
            return s.query(Groups.id, Groups.title).filter(Groups.is_active == 1).all()

    def get_active_group_for_bind(self):
        with self.session() as s:
            return s.query(Groups.id, Groups.title).filter(
                and_(Groups.is_active == 1, Groups.is_admin_group == 0)).all()

    def get_admin_users_for_bind(self):
        with self.session() as s:
            return s.query(Users.id, Users.first_name).filter(Users.is_admin == 1).all()

    def set_admin_group(self, group_id):
        with self.session() as s:
            s.query(Groups).filter(Groups.id == group_id).update({"is_admin_group": 1})
            s.query(Groups).filter(Groups.id != group_id).update({"is_admin_group": 0})
            s.commit()

    def get_admin_group_chat_id(self):
        with self.session() as s:
            return s.query(Groups.chat_id).filter(Groups.is_admin_group == 1).first()[0]

    def get_admin_telegram_id(self):
        with self.session() as s:
            result = s.query(Users.telegram_id).filter(Users.is_admin == 1).all()
            if result:
                return [x[0] for x in result]
            return []

    def set_user_admin_for_group(self, user_id, group_id):
        with self.session() as s:
            user = s.query(Users).filter(Users.id == user_id).first()
            group = s.query(Groups).filter(Groups.id == group_id).first()
            user.groups.append(group)
            s.add(user)
            s.commit()
            return True

    def create_lesson(self, title, date_time, chat_id):
        with self.session() as s:
            lesson = Lessons(title=title,
                             date_time=date_time,
                             chat_id=chat_id)
            s.add(lesson)
            s.commit()

    def get_lesson_for_time(self, date_time):
        with self.session() as s:
            return s.query(Lessons.title, Lessons.chat_id).filter(Lessons.date_time > date_time).first()


data_api = DataApi()
date_time_str = '25/05/22 21:00'
date_time_obj = datetime.strptime(date_time_str, '%d/%m/%y %H:%M')
# data_api.create_lesson("Первый урок", date_time_obj, 123456)

print(data_api.get_lesson_for_time(date_time_obj))

