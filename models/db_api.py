from datetime import datetime, timedelta

from aiogram import types
from sqlalchemy import and_
from sqlalchemy.sql import func

from models.tabs import session, Admins, Groups, Lessons, Students


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

    def create_student(self, message: types.Message, new_member):
        with self.session() as s:
            student = s.query(Students).filter(Students.telegram_id == new_member.id).first()

            if not student:
                student = Students(telegram_id=new_member.id,
                                   username=new_member.username,
                                   first_name=new_member.first_name,
                                   last_name=new_member.last_name)
            group = s.query(Groups).filter(Groups.chat_id == message.chat.id).first()
            if not group:
                group = Groups(chat_id=message.chat.id,
                               title=message.chat.title)
            student.groups.append(group)
            s.add(student)
            s.commit()

    def create_admin(self, message: types.Message, new_member, is_admin):
        with self.session() as s:
            admin = s.query(Admins).filter(Admins.telegram_id == new_member.id).first()

            if not admin:
                admin = Admins(telegram_id=new_member.id,
                               username=new_member.username,
                               first_name=new_member.first_name,
                               last_name=new_member.last_name)

            group = s.query(Groups).filter(Groups.chat_id == message.chat.id).first()
            if not group:
                group = Groups(chat_id=message.chat.id,
                               title=message.chat.title)
            admin.is_admin = int(is_admin)
            admin.groups.append(group)
            s.add(admin)
            s.commit()

    def admin_status_delete(self, left_member):
        with self.session() as s:
            s.query(Admins).filter(Admins.telegram_id == left_member.id).update({"is_admin": 0})
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
            return s.query(Admins.id, Admins.first_name).filter(Admins.is_admin == 1).all()

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
            result = s.query(Admins.telegram_id).filter(Admins.is_admin == 1).all()
            if result:
                return [x[0] for x in result]
            return []

    def get_students_telegram_id(self):
        with self.session() as s:
            result = s.query(Students.telegram_id).all()
            if result:
                return [x[0] for x in result]
            return []

    def set_user_admin_for_group(self, user_id, group_id):
        with self.session() as s:
            admin = s.query(Admins).filter(Admins.id == user_id).first()
            group = s.query(Groups).filter(Groups.id == group_id).first()
            admin.groups.append(group)
            s.add(admin)
            s.commit()
            return True

    def get_groups_for_admin(self, message: types.Message):
        with self.session() as s:
            result_list = []
            admin = s.query(Admins).filter(and_(Admins.id == message.from_user.id, Admins.is_admin == 1)).first()

            for group in admin.groups:
                group_tuple = group.id, group.title
                result_list.append(group_tuple)

            return result_list

    def create_lesson(self, title, chat_id, date_time_obj):
        with self.session() as s:
            # date_time_obj = datetime.strptime(date_time_str, '%d/%m/%y %H:%M')
            lesson = Lessons(title=title,
                             date_time=date_time_obj,
                             chat_id=chat_id)
            s.add(lesson)
            s.commit()

    def get_lesson_for_time_in_10_min(self, date_time_obj):
        with self.session() as s:
            lessons_list = []
            lessons = s.query(Lessons).filter(
                and_(Lessons.date_time - timedelta(minutes=10) >= date_time_obj,
                     Lessons.date_time - timedelta(minutes=11) <= date_time_obj,
                     Lessons.send_10_min == 0)).all()

            for lesson in lessons:
                lesson_tuple = lesson.chat_id, lesson.title
                lessons_list.append(lesson_tuple)
                lesson.send_10_min = 1
                s.add(lesson)
            s.commit()
            return lessons_list

    def get_lesson_for_time_60_min(self, date_time_obj):
        with self.session() as s:
            lessons_list = []
            lessons = s.query(Lessons).filter(
                and_(Lessons.date_time - timedelta(minutes=60) >= date_time_obj,
                     Lessons.date_time - timedelta(minutes=61) <= date_time_obj,
                     Lessons.send_60_min == 0)).all()

            for lesson in lessons:
                lesson_tuple = lesson.chat_id, lesson.title
                lessons_list.append(lesson_tuple)
                lesson.send_60_min = 1
                s.add(lesson)
            s.commit()
            return lessons_list

    def get_students_telegram_id_for_group(self, group_id):
        with self.session() as s:
            group = s.query(Groups).filter(and_(Groups.id == group_id,
                                                Groups.is_active == 1,
                                                Groups.is_admin_group == 0)).first()
            # for students in group.students:
            return [students.id for students in group.students]


data_api = DataApi()
date_time_str = '31/03/22 20:30'
date_time_obj = datetime.strptime(date_time_str, '%d/%m/%y %H:%M')
print(date_time_obj)
# data_api.create_lesson("Первый урок", date_time_obj, 123456)

# print(data_api.get_lesson_for_time_60_min(date_time_obj))

