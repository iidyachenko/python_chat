import base64
import json
import logging

from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtWidgets import QMainWindow, QApplication, qApp, QMessageBox

from client.add_contact_gui import AddContactDialog
from client.del_contact_gui import DelContactDialog
from client.main_window_template import Ui_MainWindow

logger = logging.getLogger('client')


class ClientMainWindow(QMainWindow):
    """
    Основной интерфейс пользовтеля, сделан на Qt
    """
    def __init__(self, database, receiver, keys):
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
        self.ui.remove_contact.triggered.connect(self.delete_contact_window)
        self.ui.send_button.clicked.connect(self.send_message)
        self.decrypter = PKCS1_OAEP.new(keys)
        self.current_chat = None
        self.current_chat_key = None
        self.encryptor = None
        self.messages = QMessageBox()
        self.show()

    def set_disabled_input(self):
        """
        Устанавливаем блокировку на поля ввода при запуске
        """
        self.ui.message_label.setText('Для выбора получателя дважды кликните на нем в окне контактов.')
        self.ui.edit_message.clear()
        self.history_model.clear()
        self.ui.send_button.setDisabled(True)
        self.ui.edit_message.setDisabled(True)
        self.encryptor = None
        self.current_chat = None
        self.current_chat_key = None

    def clients_list_update(self):
        """
        Обновляем список контактов
        """
        self.contacts_model.clear()
        contacts_list = self.db.get_contacts()
        for i in sorted(contacts_list):
            item = QStandardItem(i[0])
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.contact_list.setModel(self.contacts_model)

    def add_contact_window(self):
        """
        Функция добавления контакта
        """
        global select_dialog
        select_dialog = AddContactDialog(self.receiver, self.db)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    def add_contact_action(self, item):
        """
        Функция - обработчик добавления, сообщает серверу, обновляет таблицу и список контактов
        :param item:
        """
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    def add_contact(self, new_contact):
        """
        Функция добавляющяя контакт в базы
        :param new_contact:
        """
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

    def delete_contact_window(self):
        """
        Окно удаления контактов
        """
        global remove_dialog
        remove_dialog = DelContactDialog(self.db)
        remove_dialog.btn_ok.clicked.connect(lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    def delete_contact(self, item):
        """
        Функция обработчик удаления контакта, сообщает на сервер, обновляет таблицу контактов
        :param item:
        """
        selected = item.selector.currentText()
        try:
            self.receiver.del_contact_massage(selected)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.db.del_contact(selected)
            self.clients_list_update()
            logger.info(f'Успешно удалён контакт {selected}')
            self.messages.information(self, 'Успех', 'Контакт успешно удалён.')
            item.close()
            # Если удалён активный пользователь, то деактивируем поля ввода.
            if selected == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    def set_active_user(self):
        """
        Выбираем активного пользователя
        """
        self.current_chat = self.ui.contact_list.currentIndex().data()
        self.select_active_user()

    def select_active_user(self):
        """
        Запрашиваем публичный ключ пользователя и создаём объект шифрования
        Если ключа нет то ошибка, что не удалось начать чат с пользователем
        Ставим надпись и активируем кнопки
        Заполняем окно историю сообщений по требуемому пользователю.
        """
        try:
            self.current_chat_key = self.receiver.key_request(self.current_chat)
            print(self.current_chat, self.current_chat_key)
            logger.debug(f'Загружен открытый ключ для {self.current_chat}')
            if self.current_chat_key:
                self.encryptor = PKCS1_OAEP.new(RSA.import_key(self.current_chat_key))
        except (OSError, json.JSONDecodeError):
            self.current_chat_key = None
            self.encryptor = None
            logger.debug(f'Не удалось получить ключ для {self.current_chat}')
        if not self.current_chat_key:
            self.messages.warning(self, 'Ошибка', 'Для выбранного пользователя нет ключа шифрования.')
            return
        self.ui.message_label.setText(f'Введите сообщенние для {self.current_chat}:')
        self.ui.send_button.setDisabled(False)
        self.ui.edit_message.setDisabled(False)
        self.history_list_update()

    def send_message(self):
        """
        Функция отправки сообщения пользователяю
        Шифруем сообщение ключом получателя и упаковываем в base64.
        """
        message_text = self.ui.edit_message.toPlainText()
        self.ui.edit_message.clear()
        if not message_text:
            return
        try:
            message_text_encrypted = self.encryptor.encrypt(message_text.encode('utf8'))
            message_text_encrypted_base64 = base64.b64encode(message_text_encrypted)
            self.receiver.user_massage(self.current_chat, message_text_encrypted_base64.decode('ascii'))
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
        """
        Обновляем историю переписки пользователя и выводим на экран
        Берём не более 20 последних записей.
        Заполнение модели записями, так-же стоит разделить входящие и исходящие выравниванием и разным фоном.
        Записи в обратном порядке, поэтому выбираем их с конца и не более 20
        """
        list = sorted(self.db.get_history(self.current_chat), key=lambda item: item[3])
        self.history_model.clear()
        length = len(list)
        start_index = 0
        if length > 20:
            start_index = length - 20

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

    @pyqtSlot(str, str, str)
    def message(self, sender, msg, type):
        """
        Слот обработчик поступаемых сообщений, выполняет дешифровку
        поступаемых сообщений и их сохранение в истории сообщений.
        Запрашивает пользователя если пришло сообщение не от текущего
        собеседника. При необходимости меняет собеседника.
        """
        if type == 'msg':
            print("Сообщение", msg)
            encrypted_message = base64.b64decode(msg)
            print("encrypted_message", encrypted_message)
            try:
                decrypted_message = self.decrypter.decrypt(encrypted_message)
            except (ValueError, TypeError) as er:
                logger.exception(er)
                self.messages.warning(
                    self, 'Ошибка', 'Не удалось декодировать сообщение.')
                return

        if sender == self.current_chat:
            if type == 'msg':
                self.db.save_message(sender, True, decrypted_message.decode('utf8'))
            else:
                self.db.save_message(sender, True, msg)
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
                if self.messages.question(self, 'Новое сообщение',
                                          f'Получено новое сообщение от {sender}.\n Данного пользователя нет в вашем '
                                          f'контакт-листе.\n Добавить в контакты и открыть чат с ним?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    if type == 'msg':
                        self.db.save_message(sender, True, decrypted_message.decode('utf8'))
                    else:
                        self.db.save_message(sender, True, msg)
                    self.select_active_user()

    @pyqtSlot()
    def connection_lost(self):
        """
        Слот обработчик потери соеднинения с сервером.
        Выдаёт окно предупреждение и завершает работу приложения.
        """
        self.messages.warning(
            self,
            'Сбой соединения',
            'Потеряно соединение с сервером. ')
        self.close()

    def make_connection(self, trans_obj):
        """
        Связываем события и функции из обработчика
        :param trans_obj:
        """
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)


if __name__ == '__main__':
    pass
