import logging
import queue
import sys
import threading
import time
from datetime import datetime
from socket import socket, AF_INET, SOCK_STREAM

from PyQt5.QtCore import QObject, pyqtSignal

from common.utils import send_message, get_data_from_message

logger = logging.getLogger('client')
socket_lock = threading.Lock()


class ClientReceiver(threading.Thread, QObject):
    # Сигналы новое сообщение и потеря соединения
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username):
        # Вызываем конструктор предка
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.db = database
        self.username = username
        self.work_flag = True
        self.port = port
        self.ip = ip_address
        self.sock = socket(AF_INET, SOCK_STREAM)

    def connection_init(self):
        self.sock.connect((self.ip, int(self.port)))

    def presence(self, sock):
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
            send_message(sock, msg_presence)
            try:
                response = sock.recv(1000000)
            except Exception:
                self.logger.exception('Ошибка при приеме ответа с сервера')
                sys.exit(1)

    def get_contacts(self, sock):
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
                sys.exit(1)
            else:
                contacts = get_data_from_message(response)
                self.db.add_users_from_server(contacts["alert"])

    def get_users(self, sock):
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
                self.logger.exception('Ошибка при приеме ответа с сервера')
                sys.exit(1)
            else:
                users = get_data_from_message(response)
                self.db.add_users_from_server(users["alert"])

    def user_massage(self, to, msg):
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
        msg_join = {
            "action": "add_contact",
            "time": int(time.time()),
            "to": to,
            "from": self.username,
            "encoding": "utf-8"
        }
        with socket_lock:
            send_message(sock, msg_join)

    def del_contact_massage(self, sock, to):
        msg_join = {
            "action": "del_contact",
            "time": int(time.time()),
            "to": to,
            "from": self.username,
            "encoding": "utf-8"
        }
        return send_message(sock, msg_join)

    def parse_answer(self, req_dict):
        """Парсим полученный ответ"""
        if 'response' in req_dict:
            if req_dict['response'] == 200:
                return
            elif req_dict['response'] == 400:
                logger.error(f'Приянята неизвестная ошибка с сервера')
                return
            else:
                logger.debug(f'Принят неизвестный код подтверждения {req_dict["response"]}')
                return
        msg_time = datetime.utcfromtimestamp(req_dict['time']).strftime('%Y-%m-%d %H:%M:%S')
        if req_dict.get('action') == 'presence':
            print(f"{msg_time} Пользователь {req_dict['user']['account_name']} вошел в чат")
            self.db.save_message(req_dict['user']['account_name'], True, f"Пользователь {req_dict['user']['account_name']} вошел в чат")
            self.new_message.emit(req_dict['user']['account_name'])
        elif req_dict.get('action') == 'msg':
            print(f"{msg_time} {req_dict['from']}: {req_dict['message']}")
            self.db.save_message(req_dict['from'], True, req_dict['message'])
            self.new_message.emit(req_dict['from'])
        elif req_dict.get('action') == 'quit':
            print(f"{msg_time} Пользователь {req_dict['username']} покинул чат")
            self.db.save_message(req_dict['username'], True, f"Пользователь {req_dict['username']} вышел из чата")
            self.new_message.emit(req_dict['username'])
        # elif req_dict.get('action') == 'contacts':
        #     print(req_dict['alert'])

    def run(self):
        response_list = queue.Queue()
        self.connection_init()
        self.presence(self.sock)
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
                        sys.exit(1)
