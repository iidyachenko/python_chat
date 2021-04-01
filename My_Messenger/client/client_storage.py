import datetime
import os

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger('client')


class ClientDB:
    Base = declarative_base()

    # таблица всех пользователей
    class Users(Base):
        __tablename__ = 'known_users'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)

        def __init__(self, login):
            self.login = login

    class Contacts(Base):
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        name = Column(String, unique=True)

        def __init__(self, name):
            self.name = name

    class MessageHistory(Base):
        __tablename__ = 'message_history'
        id = Column(Integer, primary_key=True)
        user = Column(String)
        income = Column(Boolean)
        text = Column(Text)
        date = Column(DateTime)

        def __init__(self, user, income, text):
            self.user = user
            self.income = income
            self.text = text
            self.date = datetime.datetime.now()

    def __init__(self, client_name):
        path = os.path.dirname(os.path.realpath(__file__))
        name = f'client_{client_name}.db3'
        self.engine = create_engine(f'sqlite:///{os.path.join(path, name)}', echo=False,
                                    connect_args={'check_same_thread': False})
        self.Base.metadata.create_all(self.engine)
        session = sessionmaker(bind=self.engine)
        self.session = session()

    def add_users_from_server(self, users_list):
        self.session.query(self.Users).delete()
        for user in users_list:
            user_row = self.Users(user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, user, income, message):
        message_row = self.MessageHistory(user, income, message)
        self.session.add(message_row)
        self.session.commit()

    # Функция добавления контактов
    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    # Функция удаления контакта
    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(name=contact).delete()

    def get_users(self):
        return self.session.query(self.Users.login).all()

    def get_contacts(self):
        return self.session.query(self.Contacts.name).all()

    # Функция возвращающая историю переписки
    def get_history(self, name):
        query = self.session.query(self.MessageHistory).filter_by(user=name).all()
        return [(history_row.user, history_row.income, history_row.text, history_row.date)
                for history_row in query]

    def check_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

if __name__ == '__main__':
    db = ClientDB('Rick')
    # db.add_users(['Rick', 'Roland'])
    # print(db.session.query(db.Users.id, db.Users.login).all())
    # db.save_message('Nick', False, 'Hi Nick!')
    print(db.get_history('Nick'))
    # print(db.get_contacts())
