import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger('server')

class ServerDB:
    Base = declarative_base()

    # таблица всех пользователей
    class Users(Base):
        __tablename__ = 'all_users'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)
        last_conn = Column(DateTime)

        def __init__(self, login):
            self.login = login
            self.last_conn = datetime.datetime.now()

    # таблица с историей всех входов пользователя в систему
    class LoginHistory(Base):
        __tablename__ = 'login_history'
        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey('all_users.id'))
        ip = Column(String)
        port = Column(Integer)
        conn_time = Column(DateTime)

        def __init__(self, user, ip, port, last_conn):
            self.user = user
            self.ip = ip
            self.port = port
            self.conn_time = last_conn

    # таблица с контактами пользователей(записываются те кому отправляли личные сообщения)
    class LoginContact(Base):
        __tablename__ = 'login_contact'
        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey('all_users.id'))
        user_contact = Column(String, ForeignKey('all_users.id'))
        first_contact_time = Column(DateTime)

        def __init__(self, user, user_contact, first_contact_time):
            self.user = user
            self.user_contact = user_contact
            self.first_contact_time = first_contact_time

    # Таблица с активными пользователями
    class ActiveUsers(Base):
        __tablename__ = 'active_users'
        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey('all_users.id'), unique=True)
        ip = Column(String)
        port = Column(Integer)
        time_conn = Column(DateTime)

        def __init__(self, user, ip, port, time_conn):
            self.user = user
            self.ip = ip
            self.port = port
            self.time_conn = time_conn

    def __init__(self, database):
        self.engine = create_engine(database, echo=False)
        self.Base.metadata.create_all(self.engine)
        session = sessionmaker(bind=self.engine)
        self.session = session()
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ip, port):
        """
        Добавлям пользователя в таблицы: all_user(при необходимости),active_users, login_history
        :param username:
        :param ip:
        :param port:
        :return:
        """
        query = self.session.query(self.Users).filter_by(login=username)
        if query.count():
            user = query.first()
            user.last_conn = datetime.datetime.now()
        else:
            user = self.Users(username)
            self.session.add(user)
            self.session.commit()
        try:
            history = self.LoginHistory(user.id, ip, port, datetime.datetime.now())
            self.session.add(history)
            active_user = self.ActiveUsers(user.id, ip, port, datetime.datetime.now())
            self.session.add(active_user)
            self.session.commit()
        except:
            logger.exception("Ошибка при вставке в Базу данных")

    def user_logout(self, username):
        """
        При выходе удаляем пользователя из таблицы активных пользователей
        :param username:
        :return:
        """
        user = self.session.query(self.Users).filter_by(login=username).first()
        if user:
            self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
            self.session.commit()

    def user_send_message(self, user_from, user_to):
        """Проверяем есть ли данный контакт в таблице, если нет то добавляем"""
        user = self.session.query(self.LoginContact).filter_by(user=user_from, user_contact=user_to).first()
        if not user:
            new_user_from = self.session.query(self.Users).filter_by(login=user_from).first()
            new_user_to = self.session.query(self.Users).filter_by(login=user_to).first()
            # проверям что пользователь корректно заполнил имя пользователя при отправке
            if new_user_from and new_user_to:
                contact = self.LoginContact(new_user_from.login, new_user_to.login, datetime.datetime.now())
                self.session.add(contact)
                self.session.commit()

    def users_list(self):
        """ список пользователей"""
        query = self.session.query(
            self.Users.login,
            self.Users.last_conn,
        )
        return query.all()

    #
    def active_users_list(self):
        """Функция возвращает список активных пользователей"""
        query = self.session.query(
            self.Users.login,
            self.ActiveUsers.ip,
            self.ActiveUsers.port,
            self.ActiveUsers.time_conn
        ).join(self.Users)
        return query.all()

    #
    def login_history(self, username=None):
        """Функция возвращающая историю входов по пользователю или всем пользователям"""
        query = self.session.query(self.Users.login,
                                   self.LoginHistory.conn_time,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port
                                   ).join(self.Users)
        if username:
            query = query.filter(self.Users.login == username)
        return query.all()


if __name__ == '__main__':
    db = ServerDB('sqlite:///storage_base.db3')
    # db.user_login('Rick', '1/1/1//1', '222222')
    # print(db.users_list())
    # print(db.active_users_list())
    # print(db.login_history())
    # db.user_logout('Rick')
    db.user_send_message('Rick', 'Bob')
