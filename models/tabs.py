import time
from datetime import datetime
from contextlib import contextmanager

from aiogram import md
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, BigInteger, Table, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship

from deploy.config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False, connect_args={"options": "-c timezone=utc"})


@contextmanager
def session():
    connection = engine.connect()
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=engine))
    try:
        yield db_session
    except Exception as e:
        print(e)
    finally:
        db_session.remove()
        connection.close()


association_table = Table(
    "association",
    Base.metadata,
    Column("users_id", ForeignKey("users.id")),
    Column("telegram_groups_id", ForeignKey("telegram_groups.id")),
)


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, unique=True, primary_key=True)
    telegram_id = Column(BigInteger, unique=True)
    username = Column(String(120))
    first_name = Column(String(120))
    last_name = Column(String(120))
    is_admin = Column(Integer, default=0)
    date_add = Column(BigInteger)
    groups = relationship(
        "Groups", secondary=association_table, back_populates="users"
    )

    def __init__(self, telegram_id, username, first_name, last_name):
        self.telegram_id = telegram_id
        self.first_name = first_name
        self.last_name = last_name
        self.date_add = time.time()
        if not username:
            self.username = self.nice_print

    @property
    def get_date_add(self):
        return datetime.fromtimestamp(self.date_add).strftime('%Y-%m-%d')

    @property
    def url(self) -> str:
        return f"tg://user?id={self.telegram_id}"

    @property
    def mention(self) -> str:
        return md.hlink(self.first_name, self.url)

    @property
    def nice_print(self) -> str:
        out = self.mention
        if self.username:
            out += f" [@{self.username}]"
        return out


class Groups(Base):
    __tablename__ = 'telegram_groups'
    id = Column(Integer, unique=True, primary_key=True)
    chat_id = Column(BigInteger, unique=True)
    is_active = Column(Integer, default=1)
    title = Column(String(240))
    is_admin_group = Column(Integer, default=0)
    users = relationship(
        "Users", secondary=association_table, back_populates="groups"
    )

    def __init__(self, chat_id, title):
        self.chat_id = chat_id
        self.title = title


# class Payment(Base):
#     __tablename__ = 'payment'
#     id = Column(Integer, unique=True, primary_key=True)
#     payment_date = Column(Integer)
#     paid = Column(Boolean, default=False)
#     user_id = Column(Integer, ForeignKey('users.id'))
#
#     def __init__(self, user_id, payment_date):
#         self.user_id = user_id
#         self.payment_date = payment_date
#
#     @property
#     def get_paid(self):
#         if self.paid:
#             return "True"
#         return "False"
#
#     @property
#     def get_payment_date(self):
#         if self.payment_date:
#             return datetime.fromtimestamp(self.payment_date).strftime('%Y-%m-%d')
#
#     @property
#     def get_payment_time(self):
#         if self.payment_date:
#             return datetime.fromtimestamp(self.payment_date).strftime('%H:%M')

class Lessons(Base):
    __tablename__ = 'lessons'
    id = Column(Integer, unique=True, primary_key=True)
    chat_id = Column(BigInteger)
    title = Column(String(240))
    date_time = Column(DateTime())

    def __init__(self, title, date_time, chat_id):
        self.title = title
        self.chat_id = chat_id
        self.date_time = date_time


Base.metadata.create_all(engine)