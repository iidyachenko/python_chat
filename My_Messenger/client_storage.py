import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
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
        user_from = Column(ForeignKey('known_users.id'))
        user_to = Column(ForeignKey('known_users.id'))
        text = Column(Text)
        date = Column(DateTime)

        def __init__(self, user_from, user_to, text):
            self.user_from = user_from
            self.user_to = user_to
            self.text = text
            self.date = datetime.datetime.now()

    def __init__(self, client_name):
        self.engine = create_engine(f'sqlite:///client_{client_name}.db3', echo=False)
        self.Base.metadata.create_all(self.engine)
        session = sessionmaker(bind=self.engine)
        self.session = session()

        # Функция добавления известных пользователей.
        # Пользователи получаются только с сервера, поэтому таблица очищается.
    def add_users(self, users_list):
        self.session.query(self.Users).delete()
        for user in users_list:
            user_row = self.Users(user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, from_user, to_user, message):
        from_user_id = self.session.query(self.Users).filter_by(login=from_user).first().id
        to_user_id = self.session.query(self.Users).filter_by(login=to_user).first().id
        message_row = self.MessageHistory(from_user_id, to_user_id, message)
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

    def get_contacts(self):
        return self.session.query(self.Contacts.name).all()


if __name__ == '__main__':
    db = ClientDB('Test')
    # db.add_users(['Rick', 'Roland'])
    # print(db.session.query(db.Users.id, db.Users.login).all())
    # db.save_message('Rick', 'Roland', 'Hi')

