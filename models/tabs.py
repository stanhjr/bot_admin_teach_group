from contextlib import contextmanager

from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, Table, Time
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


association_table_admins = Table(
    "association_table_admins",
    Base.metadata,
    Column("admins_id", ForeignKey("admins.id")),
    Column("telegram_groups_id", ForeignKey("telegram_groups.id")),
)

association_table_students = Table(
    "association_table_students",
    Base.metadata,
    Column("students_id", ForeignKey("students.id")),
    Column("telegram_groups_id", ForeignKey("telegram_groups.id")),
)


class Admins(Base):
    __tablename__ = 'admins'
    id = Column(Integer, unique=True, primary_key=True)
    telegram_id = Column(BigInteger, unique=True)
    username = Column(String(120))
    first_name = Column(String(120))
    last_name = Column(String(120))
    is_admin = Column(Integer, default=1)
    groups = relationship(
        "Groups", secondary=association_table_admins, back_populates="admins"
    )
    lessons = relationship("Lessons", back_populates="admin")

    def __init__(self, telegram_id, username, first_name, last_name):
        self.telegram_id = telegram_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username


class Students(Base):
    __tablename__ = 'students'
    id = Column(Integer, unique=True, primary_key=True)
    telegram_id = Column(BigInteger, unique=True)
    username = Column(String(120))
    first_name = Column(String(120))
    last_name = Column(String(120))
    groups = relationship(
        "Groups", secondary=association_table_students, back_populates="students"
    )

    def __init__(self, telegram_id, username, first_name, last_name):
        self.telegram_id = telegram_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username


class Groups(Base):
    __tablename__ = 'telegram_groups'
    id = Column(Integer, unique=True, primary_key=True)
    chat_id = Column(BigInteger, unique=True)
    is_active = Column(Integer, default=1)
    title = Column(String(240))
    is_admin_group = Column(Integer, default=0)
    is_reply_chat = Column(Integer, default=0)
    admins = relationship(
        "Admins", secondary=association_table_admins, back_populates="groups"
    )
    students = relationship(
        "Students", secondary=association_table_students, back_populates="groups"
    )

    def __init__(self, chat_id, title):
        self.chat_id = chat_id
        self.title = title


class Lessons(Base):
    __tablename__ = 'lessons'
    id = Column(Integer, unique=True, primary_key=True)
    chat_id = Column(BigInteger)
    title = Column(String(240))
    time_lesson = Column(Time())
    send_10_min = Column(Integer, default=0)
    send_60_min = Column(Integer, default=0)
    parent_id = Column(Integer, ForeignKey("admins.id"))
    admin = relationship("Admins", back_populates="lessons")

    def __init__(self, title, time_lesson, chat_id):
        self.title = title
        self.chat_id = chat_id
        self.time_lesson = time_lesson


Base.metadata.create_all(engine)
