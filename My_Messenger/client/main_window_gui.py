import logging
import sys

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtWidgets import QMainWindow, QApplication, qApp, QMessageBox

from client.add_contact_gui import AddContactDialog
from client.main_window_template import Ui_MainWindow

logger = logging.getLogger('client')


class ClientMainWindow(QMainWindow):
    def __init__(self, database, receiver):
        super().__init__()
        # Загружаем конфигурацию окна из дизайнера
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.db = database
        self.receiver = receiver
        self.history_model = QStandardItemModel()
        self.ui.message_list.setModel(self.history_model)
        self.contacts_model = QStandardItemModel()
        self.clients_list_update()
        self.ui.exit_menu.triggered.connect(qApp.exit)
        self.set_disabled_input()
        self.ui.contact_list.clicked.connect(self.set_active_user)
        self.ui.contact_menu.triggered.connect(self.add_contact_window)
        self.ui.send_button.clicked.connect(self.send_message)
        self.current_chat = None
        self.messages = QMessageBox()
        self.show()

    def set_disabled_input(self):
        self.ui.message_label.setText('Для выбора получателя дважды кликните на нем в окне контактов.')
        self.ui.edit_message.clear()
        self.history_model.clear()
        self.ui.send_button.setDisabled(True)
        self.ui.edit_message.setDisabled(True)

    def clients_list_update(self):
        contacts_list = self.db.get_contacts()
        for i in sorted(contacts_list):
            item = QStandardItem(i[0])
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.contact_list.setModel(self.contacts_model)

    # Функция добавления контакта
    def add_contact_window(self):
        global select_dialog
        select_dialog = AddContactDialog(self.receiver, self.db)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    # Функция - обработчик добавления, сообщает серверу, обновляет таблицу и список контактов
    def add_contact_action(self, item):
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    # Функция добавляющяя контакт в базы
    def add_contact(self, new_contact):
        try:
            self.receiver.add_contact_massage(self.receiver.sock, new_contact)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.db.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            logger.info(f'Успешно добавлен контакт {new_contact}')
            self.messages.information(self, 'Успех', 'Контакт успешно добавлен.')

    def set_active_user(self):
        self.current_chat = self.ui.contact_list.currentIndex().data()
        self.select_active_user()

    def select_active_user(self):
        # Ставим надпись и активируем кнопки
        self.ui.message_label.setText(f'Введите сообщенние для {self.current_chat}:')
        self.ui.send_button.setDisabled(False)
        self.ui.edit_message.setDisabled(False)
        # Заполняем окно историю сообщений по требуемому пользователю.
        self.history_list_update()

    def send_message(self):
        message_text = self.ui.edit_message.toPlainText()
        self.ui.edit_message.clear()
        if not message_text:
            return
        try:
            self.receiver.user_massage(self.current_chat, message_text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
            self.close()
        else:
            self.db.save_message(self.current_chat, False, message_text)
            logger.debug(f'Отправлено сообщение для {self.current_chat}: {message_text}')
            self.history_list_update()

    def history_list_update(self):
        # Получаем историю сортированную по дате
        list = sorted(self.db.get_history(self.current_chat), key=lambda item: item[3])
        # Очистим от старых записей
        self.history_model.clear()
        # Берём не более 20 последних записей.
        length = len(list)
        start_index = 0
        if length > 20:
            start_index = length - 20
        # Заполнение модели записями, так-же стоит разделить входящие и исходящие выравниванием и разным фоном.
        # Записи в обратном порядке, поэтому выбираем их с конца и не более 20
        for i in range(start_index, length):
            item = list[i]
            if item[1]:
                mess = QStandardItem(f'{item[0]} {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            else:
                mess = QStandardItem(f'Вы {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(mess)
        self.ui.message_list.scrollToBottom()

        # Слот приёма нового сообщений

    @pyqtSlot(str)
    def message(self, sender):
        if sender == self.current_chat:
            self.history_list_update()
        else:
            # Проверим есть ли такой пользователь у нас в контактах:
            if self.db.check_contact(sender):
                # Если есть, спрашиваем и желании открыть с ним чат и открываем при желании
                if self.messages.question(self, 'Новое сообщение',
                                          f'Получено новое сообщение от {sender}, открыть чат с ним?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.select_active_user()
            else:
                print('NO')
                # Раз нету,спрашиваем хотим ли добавить юзера в контакты.
                if self.messages.question(self, 'Новое сообщение',f'Получено новое сообщение от {sender}.\n Данного пользователя нет в вашем контакт-листе.\n Добавить в контакты и открыть чат с ним?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.select_active_user()

    def make_connection(self, trans_obj):
        trans_obj.new_message.connect(self.message)


if __name__ == '__main__':
    pass
