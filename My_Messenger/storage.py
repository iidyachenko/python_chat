import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger('server')


class ServerDB:
    """
    Класс - для работы с базой данных сервера.
    Использует SQLite базу данных, реализован с помощью SQLAlchemy ORM и используется декларативный подход.
    """
    Base = declarative_base()

    # таблица всех пользователей
    class Users(Base):
        __tablename__ = 'all_users'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)
        last_conn = Column(DateTime)
        passwd_hash = Column(String)
        pubkey = Column(Text)

        def __init__(self, login, passwd_hash):
            self.login = login
            self.last_conn = datetime.datetime.now()
            self.passwd_hash = passwd_hash
            self.pubkey = None

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
        user = Column(ForeignKey('all_users.id'))
        user_contact = Column(ForeignKey('all_users.id'))
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

    class LoginMessageHistory(Base):
        __tablename__ = 'message_history'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('all_users.id'))
        send = Column(Integer)
        accepted = Column(Integer)

        def __init__(self, user, send, accepted):
            self.user = user
            self.send = send
            self.accepted = accepted

    def __init__(self, database):
        self.engine = create_engine(database, echo=False, pool_recycle=7200, connect_args={'check_same_thread': False})
        self.Base.metadata.create_all(self.engine)
        session = sessionmaker(bind=self.engine)
        self.session = session()
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ip, port, pubkey):
        """
        Добавлям пользователя в таблицы: all_user(при необходимости),active_users, login_history
        :param pubkey:
        :param username:
        :param ip:
        :param port:
        :return:
        """
        query = self.session.query(self.Users).filter_by(login=username)
        if query.count():
            user = query.first()
            user.last_conn = datetime.datetime.now()
            if user.pubkey != pubkey:
                user.pubkey = pubkey
        else:
            raise ValueError('Пользователь не зарегистрирован.')
        try:
            history = self.LoginHistory(user.id, ip, port, datetime.datetime.now())
            self.session.add(history)
            active_user = self.ActiveUsers(user.id, ip, port, datetime.datetime.now())
            self.session.add(active_user)
            self.session.commit()
        except:
            logger.exception("Ошибка при вставке в Базу данных")

    def add_user(self, name, passwd_hash):
        """
        Метод регистрации пользователя.
        Принимает имя и хэш пароля, создаёт запись в таблице статистики.
        """
        user_row = self.Users(name, passwd_hash)
        self.session.add(user_row)
        self.session.commit()

    def remove_user(self, name):
        """Метод удаляющий пользователя из базы."""

        user = self.session.query(self.Users).filter_by(name=name).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.query(self.LoginHistory).filter_by(user=user.id).delete()
        self.session.query(self.LoginContact).filter_by(user=user.id).delete()
        self.session.query(self.LoginContact).filter_by(user_contact=user.id).delete()
        self.session.query(self.LoginHistory).filter_by(user=user.id).delete()
        self.session.query(self.Users).filter_by(login=name).delete()
        self.session.commit()

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
        user_from = self.session.query(self.Users).filter_by(login=user_from).first().id
        user_to = self.session.query(self.Users).filter_by(login=user_to).first().id
        is_from = self.session.query(self.LoginMessageHistory).filter_by(user=user_from).first()
        is_to = self.session.query(self.LoginMessageHistory).filter_by(user=user_to).first()
        if not is_from:
            new_user = self.LoginMessageHistory(user_from, 1, 0)
            self.session.add(new_user)
        else:
            is_from.send += 1
        if not is_to:
            new_user = self.LoginMessageHistory(user_to, 0, 1)
            self.session.add(new_user)
        else:
            is_to.accepted += 1
        self.session.commit()

    def add_contact(self, user_from, user_to):
        new_user_from = self.session.query(self.Users).filter_by(login=user_from).first().id
        new_user_to = self.session.query(self.Users).filter_by(login=user_to).first().id
        user = self.session.query(self.LoginContact).filter_by(user=new_user_from, user_contact=new_user_to).first()
        if not user:
            # проверям что пользователь корректно заполнил имя пользователя при отправке
            if new_user_from and new_user_to:
                contact = self.LoginContact(new_user_from, new_user_to, datetime.datetime.now())
                self.session.add(contact)
                self.session.commit()

    def remove_contact(self, user_from, user_to):
        del_user_from = self.session.query(self.Users).filter_by(login=user_from).first().id
        del_user_to = self.session.query(self.Users).filter_by(login=user_to).first().id
        user = self.session.query(self.LoginContact).filter_by(user=del_user_from, user_contact=del_user_to)
        if user:
            # проверям что пользователь корректно заполнил имя пользователя при отправке
            user.delete()
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

    def contact_list(self, username):
        user = self.session.query(self.Users).filter_by(login=username).first()
        query = self.session.query(self.LoginContact.user_contact,
                                   self.Users.login).filter_by(user=user.id).join(self.Users,
                                                                        self.Users.id == self.LoginContact.user_contact).all()
        return [x[1] for x in query]

    def message_history(self):
        query = self.session.query(
            self.Users.login,
            self.Users.last_conn,
            self.LoginMessageHistory.send,
            self.LoginMessageHistory.accepted
        ).join(self.Users)
        # Возвращаем список кортежей
        return query.all()

    def get_hash(self, name):
        """Метод получения хэша пароля пользователя."""
        user = self.session.query(self.Users).filter_by(login=name).first()
        return user.passwd_hash

    def get_pubkey(self, name):
        """Метод получения публичного ключа пользователя."""
        user = self.session.query(self.Users).filter_by(login=name).first()
        return user.pubkey

    def check_user(self, name):
        """Метод проверяющий существование пользователя."""
        if self.session.query(self.Users).filter_by(login=name).count():
            return True
        else:
            return False

    def get_username(self):
        """Имена пользователей"""
        query = self.session.query(self.Users.login).all()
        return [x[0] for x in query]

    def get_active_username(self):
        """Имена активных пользователей"""
        return [x[0] for x in self.active_users_list()]


if __name__ == '__main__':
    db = ServerDB('sqlite:///server_base.db3')
    # db.user_login('Rick', '1/1/1//1', '222222')
    # print(db.users_list())
    # print(db.active_users_list())
    # print(db.login_history())
    # db.user_logout('Rick')
    # db.user_send_message('Rick', 'Roland')
    # db.add_contact('Rick', 'Nick')
    # db.remove_contact('Rick', 'Roland')
    # print(db.contact_list('Rick'))
    print(db.get_pubkey('Rick'))
    print(db.get_pubkey('Nick'))

