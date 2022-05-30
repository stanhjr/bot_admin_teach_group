from datetime import datetime, timedelta

from aiogram import types
from sqlalchemy import and_

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
            return s.query(Groups.id, Groups.title).filter(Groups.is_active == 1).all()

    def get_active_group_for_bind(self):
        with self.session() as s:
            return s.query(Groups.id, Groups.title).filter(
                and_(Groups.is_active == 1, Groups.is_admin_group == 0)).all()

    def get_student_group_for_admin(self, message: types.Message):
        with self.session() as s:
            group_list = []
            admin = s.query(Admins).filter(Admins.telegram_id == message.from_user.id, Admins.is_admin == 1).first()
            if admin:
                for group in admin.groups:
                    if group.is_admin_group == 0 and group.is_reply_chat == 0:
                        tuple_group = group.chat_id, group.title
                        group_list.append(tuple_group)
            return group_list

    def get_admin_users_for_bind(self):
        with self.session() as s:
            return s.query(Admins.id, Admins.first_name).filter(Admins.is_admin == 1).all()

    def set_admin_group(self, group_id):
        with self.session() as s:
            s.query(Groups).filter(Groups.id == group_id).update({"is_admin_group": 1})
            s.query(Groups).filter(Groups.id != group_id).update({"is_admin_group": 0})
            s.commit()

    def set_review_group(self, group_id):
        with self.session() as s:
            s.query(Groups).filter(Groups.id == group_id).update({"is_reply_chat": 1})
            s.query(Groups).filter(Groups.id != group_id).update({"is_reply_chat": 0})
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

    def get_chat_id_for_reply(self):
        with self.session() as s:
            return s.query(Groups.chat_id).filter(Groups.is_reply_chat == 1).first()[0]

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
            if admin:
                for group in admin.groups:
                    group_tuple = group.id, group.title
                    result_list.append(group_tuple)
            return result_list

    def create_lesson(self, title, chat_id, time_obj, message: types.Message, weekday, text):
        with self.session() as s:
            admin = s.query(Admins).filter(Admins.telegram_id == message.from_user.id).first()
            lesson = Lessons(title=title,
                             time_lesson=time_obj,
                             chat_id=chat_id,
                             weekday=weekday,
                             text=text)
            admin.lessons.append(lesson)
            s.add(lesson)
            s.commit()
            return True

    def update_lesson(self, lesson_id, text, time_obg, weekday):
        with self.session() as s:
            if text:
                s.query(Lessons).filter(Lessons.id == lesson_id).update({"text": text})
            if time_obg:
                s.query(Lessons).filter(Lessons.id == lesson_id).update({"time_lesson": time_obg, "weekday": weekday})
            s.commit()
            return True

    def get_lesson_for_time_in_10_min(self):
        with self.session() as s:
            lessons_list = []
            lessons = s.query(Lessons).filter(
                and_(Lessons.time_lesson - timedelta(minutes=10) >= datetime.now().strftime('%H:%M'),
                     Lessons.time_lesson - timedelta(minutes=11) <= datetime.now().strftime('%H:%M'),
                     Lessons.send_10_min == 0,
                     Lessons.weekday == datetime.isoweekday(datetime.now()))).all()

            for lesson in lessons:
                student_tuple = self.get_students_telegram_id_for_chat_id_group(lesson.chat_id), lesson.title
                lessons_list.append(student_tuple)
                lesson.send_10_min = 1
                lesson.send_60_min = 1
                s.add(lesson)
            s.commit()
            return lessons_list

    def get_lesson_for_time_60_min(self):
        with self.session() as s:
            lessons_list = []
            lessons = s.query(Lessons).filter(
                and_(Lessons.time_lesson - timedelta(minutes=60) >= datetime.now().strftime('%H:%M'),
                     Lessons.time_lesson - timedelta(minutes=61) <= datetime.now().strftime('%H:%M'),
                     Lessons.send_60_min == 0,
                     Lessons.weekday == datetime.isoweekday(datetime.now()))).all()

            for lesson in lessons:
                student_tuple = self.get_students_telegram_id_for_chat_id_group(lesson.chat_id), lesson.title
                lessons_list.append(student_tuple)
                lesson.send_60_min = 1
                s.add(lesson)
            s.commit()
            return lessons_list

    def get_lessons_after_time(self):
        with self.session() as s:
            lessons_list = []
            lessons = s.query(Lessons).filter(
                and_(Lessons.time_lesson + timedelta(minutes=90) <= datetime.now().strftime('%H:%M'),
                     Lessons.time_lesson + timedelta(minutes=91) >= datetime.now().strftime('%H:%M'),
                     Lessons.send_text == 0,
                     Lessons.weekday == datetime.isoweekday(datetime.now()))).all()

            for lesson in lessons:
                student_tuple = self.get_students_telegram_id_for_chat_id_group(lesson.chat_id), lesson.text
                lessons_list.append(student_tuple)
                lesson.send_text = 1
                s.add(lesson)
            s.commit()
            return lessons_list

    def get_students_telegram_id_for_chat_id_group(self, chat_id):
        with self.session() as s:
            group = s.query(Groups).filter(and_(Groups.chat_id == chat_id,
                                                Groups.is_active == 1,
                                                Groups.is_admin_group == 0)).first()
            return [students.telegram_id for students in group.students]

    def get_all_students_telegram_id(self):
        with self.session() as s:
            students = s.query(Students.telegram_id).all()
            return [student[0] for student in students]

    def delete_lesson(self, lesson_id):
        with self.session() as s:
            s.query(Lessons).filter(Lessons.id == lesson_id).delete()
            s.commit()
            return True

    def get_title_for_lesson(self, lesson_chat_id):
        with self.session() as s:
            return s.query(Groups.title).filter(Groups.chat_id == lesson_chat_id).first()[0]

    def get_lessons_for_admin(self, message: types.Message):
        with self.session() as s:
            lessons_list = []
            admin = s.query(Admins).filter(Admins.telegram_id == message.from_user.id).first()
            for lesson in admin.lessons:
                lesson_tuple = lesson.id, lesson.title, lesson.time_lesson, lesson.weekday
                lessons_list.append(lesson_tuple)
            return lessons_list

    def auto_upgrade_lesson_status(self):
        with self.session() as s:
            s.query(Lessons).filter(Lessons.time_lesson + timedelta(minutes=65) < datetime.now().strftime('%H:%M')).\
                update({"send_10_min": 0})
            s.query(Lessons).filter(Lessons.time_lesson + timedelta(minutes=65) < datetime.now().strftime('%H:%M')). \
                update({"send_60_min": 0})
            s.query(Lessons).filter(Lessons.time_lesson + timedelta(minutes=100) < datetime.now().strftime('%H:%M')). \
                update({"send_text": 0})

            s.commit()

    def create_new_admin(self, ):
        with self.session() as s:
            admin = Admins(telegram_id=589380091,
                           username='stan',
                           first_name='Stan',
                           last_name='Stan')
            admin.is_admin = 1
            s.add(admin)
            s.commit()


data_api = DataApi()

