import binascii
import hashlib
import hmac
import logging
import queue
import sys
import threading
import time
from datetime import datetime
from socket import socket, AF_INET, SOCK_STREAM

from PyQt5.QtCore import QObject, pyqtSignal

from common.utils import send_message, get_data_from_message, ServerError

logger = logging.getLogger('client')
socket_lock = threading.Lock()


class ClientReceiver(threading.Thread, QObject):
    """
    Основной класс для взаимодействия клиента и сервера.
    """

    # Сигналы новое сообщение и потеря соединения
    new_message = pyqtSignal(str, str, str)
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username, passwd, keys):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.db = database
        self.username = username
        self.passwd = passwd
        self.work_flag = True
        self.port = port
        self.ip = ip_address
        self.keys = keys
        self.sock = socket(AF_INET, SOCK_STREAM)

    def connection_init(self):
        """
        Запускаем процедуру авторизации
        Получаем хэш пароля
        """

        self.sock.connect((self.ip, int(self.port)))
        self.sock.settimeout(5)

        passwd_bytes = self.passwd.encode('utf-8')
        salt = self.username.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)
        logger.debug(f'Passwd hash ready: {passwd_hash_string}')
        self.presence(passwd_hash_string)

    def presence(self, passwd_hash_string):
        """
        Отправка сообщения о подключении к серверу
        :param passwd_hash_string:
        """
        msg_presence = {
            "action": "presence",
            "time": int(time.time()),
            "type": "status",
            "user": {
                "account_name": self.username,
                "status": "Connect to server"
            }
        }
        with socket_lock:
            send_message(self.sock, msg_presence)
            try:
                response = self.sock.recv(1000000)
                ans = get_data_from_message(response)
                print('Начинаем авторизацию!', response)
                if 'response' in ans:
                    if ans['response'] == 400:
                        raise ServerError(ans['error'])
                    elif ans['response'] == 511:
                        # Если всё нормально, то продолжаем процедуру
                        # авторизации.
                        ans_data = ans['data']
                        hash = hmac.new(passwd_hash_string, ans_data.encode('utf-8'), 'MD5')
                        digest = hash.digest()
                        pubkey = self.keys.publickey().export_key().decode('ascii')
                        print(pubkey)
                        my_ans = {'action': 'join', 'username': self.username, 'response': 511,
                                  'data': binascii.b2a_base64(digest).decode('ascii'), 'keys': pubkey}
                        send_message(self.sock, my_ans)
                        response = self.sock.recv(1000000)
                        ans = get_data_from_message(response)
                        print(ans['response'])
                        if ans['response'] != '200':
                            print('Неверный пароль!')
                            raise ServerError(ans['error'])
                        else:
                            print('Авторизация прошла успешно!')
                else:
                    raise ServerError(ans['error'])
            except Exception:
                logger.exception('Ошибка при авторизации на сервере')
                self.connection_lost.emit()
                sys.exit(1)

    def key_request(self, user):
        """Метод запрашивающий с сервера публичный ключ пользователя."""
        logger.debug(f'Запрос публичного ключа для {user}')
        msg = {
            "action": "public_key_request",
            "time": int(time.time()),
            "username": user
        }
        with socket_lock:
            send_message(self.sock, msg)
            try:
                response = self.sock.recv(1000000)
                ans = get_data_from_message(response)
            except Exception:
                self.logger.exception('Ошибка при приеме ответа с сервера')
                self.connection_lost.emit()
                sys.exit(1)
            else:
                if 'response' in ans and ans['response'] == '511':
                    return ans['data']
                else:
                    logger.error(f'Не удалось получить ключ собеседника{user}.')

    def get_contacts(self, sock):
        """
        Запрос списка контактов с сервера
        """
        msg_join = {
            "action": "get_contacts",
            "time": int(time.time()),
            "user_login": self.username
        }
        with socket_lock:
            send_message(sock, msg_join)
            try:
                response = sock.recv(1000000)
            except Exception:
                self.logger.exception('Ошибка при приеме ответа с сервера')
                self.connection_lost.emit()
                sys.exit(1)
            else:
                contacts = get_data_from_message(response)
                self.db.add_users_from_server(contacts["alert"])

    def get_users(self, sock):
        """
        Запрос списка пользователей с сервера
        """
        msg_join = {
            "action": "get_users",
            "time": int(time.time()),
            "user_login": self.username
        }
        with socket_lock:
            send_message(sock, msg_join)
            try:
                response = sock.recv(1000000)
            except Exception:
                logger.exception('Ошибка при загрузке списка пользователей')
                self.connection_lost.emit()
                sys.exit(1)
            else:
                users = get_data_from_message(response)
                self.db.add_users_from_server(users["alert"])

    def user_massage(self, to, msg):
        """
        Отправка пользовательского сообщения на сервер
        """
        msg_join = {
            "action": "msg",
            "time": int(time.time()),
            "room": "main_chat",
            "to": to,
            "from": self.username,
            "encoding": "utf-8",
            "message": msg
        }
        with socket_lock:
            send_message(self.sock, msg_join)

    def add_contact_massage(self, sock, to):
        """
        Запрос на добавление контакта
        """
        msg_join = {
            "action": "add_contact",
            "time": int(time.time()),
            "to": to,
            "from": self.username,
            "encoding": "utf-8"
        }
        with socket_lock:
            send_message(sock, msg_join)

    def del_contact_massage(self, to):
        """
        Запрос на удаление контакта
        """
        msg_join = {
            "action": "del_contact",
            "time": int(time.time()),
            "to": to,
            "from": self.username,
            "encoding": "utf-8"
        }
        send_message(self.sock, msg_join)

    def parse_answer(self, req_dict):
        """Парсим полученный ответ"""
        if 'response' in req_dict:
            if req_dict['response'] == 200:
                return
            elif req_dict['response'] == 400:
                logger.error(f'Приянята неизвестная ошибка с сервера')
                raise ServerError(f'{req_dict["error"]}')
            else:
                logger.debug(f'Принят неизвестный код подтверждения {req_dict["response"]}')
                return
        msg_time = datetime.utcfromtimestamp(req_dict['time']).strftime('%Y-%m-%d %H:%M:%S')
        # if req_dict.get('action') == 'presence':
        #     print(f"{msg_time} Пользователь {req_dict['user']['account_name']} вошел в чат")
        #     self.db.save_message(req_dict['user']['account_name'], True,
        #                          f"Пользователь {req_dict['user']['account_name']} вошел в чат")
        #     message = f"Пользователь {req_dict['user']['account_name']} вошел в чат"
        #     self.new_message.emit(req_dict['user']['account_name'], req_dict['message'])
        if req_dict.get('action') == 'msg':
            print(f"{msg_time} {req_dict['from']}: {req_dict['message']}")
            # self.db.save_message(req_dict['from'], True, req_dict['message'])
            self.new_message.emit(req_dict['from'], req_dict['message'], 'msg')
        elif req_dict.get('action') == 'quit':
            print(f"{msg_time} Пользователь {req_dict['username']} покинул чат")
            msg = f"Пользователь {req_dict['username']} покинул чат"
            # self.db.save_message(req_dict['username'], True, f"Пользователь {req_dict['username']} вышел из чата")
            self.new_message.emit(req_dict['username'], msg, 'quit')
        # elif req_dict.get('action') == 'contacts':
        #     print(req_dict['alert'])

    def run(self):
        """
        Запуск цикла основного потока.
        """
        response_list = queue.Queue()
        self.connection_init()
        self.get_users(self.sock)
        print("Поехали")
        while self.work_flag:
            time.sleep(1)
            with socket_lock:
                try:
                    self.sock.settimeout(1)
                    response = self.sock.recv(1000000)
                except Exception as er:
                    # print('timeout')
                    pass
                else:
                    response_list.put(response)
                finally:
                    self.sock.settimeout(5)
                if not response_list.empty():
                    try:
                        while not response_list.empty():
                            resp = response_list.get()
                            print(resp)
                            if resp:
                                self.parse_answer(get_data_from_message(resp))
                    except Exception:
                        self.logger.exception("Ошибка при конвертации ответа")
                        self.connection_lost.emit()
                        sys.exit(1)
