import argparse
import queue
import sys
import threading
import time
import logging
from datetime import datetime

import log.Client.client_log_config

from socket import socket, AF_INET, SOCK_STREAM

from client_storage import ClientDB
from common.metaclasses import ClientVerifier
from common.utils import send_message, get_data_from_message, load_setting, Log, log


class InputThread(threading.Thread):
    def __init__(self, func, sock):
        super().__init__()
        self.daemon = True
        self.func = func
        self.sock = sock

    def run(self):
        self.func(self.sock)


class Client(metaclass=ClientVerifier):

    __slots__ = ('logger', 'server_addr', 'server_port', 'client_type', 'username', 'lock', 'work_flag', 'db')

    def __init__(self):
        self.work_flag = True
        self.logger = logging.getLogger('client')
        self.lock = threading.Lock()
        SETTINGS = load_setting(is_server=False, filename='common/settings.json')
        parser = argparse.ArgumentParser(description='Client arguments')
        parser.add_argument('addr', type=str, nargs='*', default='', help='Server address')
        parser.add_argument('port', type=int, nargs='*', default='', help='server port')
        parser.add_argument('-c', '--client_type', nargs='*', default='input', help='type of client')
        parser.add_argument('-u', '--username', nargs='*', default='anonymous', help='type of client')
        args = parser.parse_args()
        if not args.addr:
            self.server_addr = SETTINGS["DEFAULT_IP_ADDRESS"]
            self.logger.warning("Успользуются адрес сервера по умолчанию")
        else:
            self.server_addr = args.addr

        if not args.port:
            self.server_port = SETTINGS["DEFAULT_PORT"]
            self.logger.warning("Успользуются порт сервера по умолчанию")
        else:
            self.server_port = args.port
        self.client_type = args.client_type[0]
        self.username = args.username[0]
        self.db = ClientDB(self.username)

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
        send_message(sock, msg_presence)
        try:
            response = sock.recv(1000000)
        except Exception:
            self.logger.exception('Ошибка при приеме ответа с сервера')
            sys.exit(1)
        return get_data_from_message(response)

    # def join_massage(self, sock):
    #     msg_join = {
    #         "action": "join",
    #         "time": int(time.time()),
    #         "room": "main_chat"
    #     }
    #     send_message(sock, msg_join)
    #     try:
    #         response = sock.recv(1000000)
    #     except Exception:
    #         self.logger.exception('Ошибка при приеме ответа с сервера')
    #         sys.exit(1)
    #     return get_data_from_message(response)

    def get_contacts(self, sock):
        msg_join = {
            "action": "get_contacts",
            "time": int(time.time()),
            "user_login": self.username
        }
        send_message(sock, msg_join)
        try:
            response = sock.recv(1000000)
        except Exception:
            self.logger.exception('Ошибка при приеме ответа с сервера')
            sys.exit(1)
        return get_data_from_message(response)

    def user_massage(self, sock, to, msg):
        msg_join = {
            "action": "msg",
            "time": int(time.time()),
            "room": "main_chat",
            "to": to,
            "from": self.username,
            "encoding": "utf-8",
            "message": msg
        }
        return send_message(sock, msg_join)

    def add_contact_massage(self, sock, to):
        msg_join = {
            "action": "add_contact",
            "time": int(time.time()),
            "to": to,
            "from": self.username,
            "encoding": "utf-8"
        }
        return send_message(sock, msg_join)

    def del_contact_massage(self, sock, to):
        msg_join = {
            "action": "del_contact",
            "time": int(time.time()),
            "to": to,
            "from": self.username,
            "encoding": "utf-8"
        }
        return send_message(sock, msg_join)

    def send_message_loop(self, sock):
        while True:
            self.lock.acquire()
            choice = input('Выберите действие: \n'
                           'mes - создать сообщение \n'
                           'contact - просмотреть контакты \n'
                           'add - создать контакт \n'
                           'remove - удалить контакт \n'
                           'exit - выход \n')
            if choice == 'mes':
                to = input('Введите адресат сообщения(что бы отправить сообщение всем нажмите #): ')
                msg = input(f'Ваше сообщение пользователю {to}: ')
                self.user_massage(sock, to, msg)
            elif choice == 'contact':
                print(self.db.get_contacts())
            elif choice == 'add':
                to = input('Введите имя пользователя для добавления в контакты: ')
                self.add_contact_massage(sock, to)
            elif choice == 'remove':
                to = input('Введите имя пользователя для удаления из контактов: ')
                self.del_contact_massage(sock, to)
            elif choice == 'exit':
                self.lock.release()
                break
            else:
                print("Вы ввели неверный код")
            self.lock.release()
            print('Новые сообщения:')
            time.sleep(2)

    def recv_message(self, sock):
        response_list = queue.Queue()
        while self.work_flag:
            if self.lock.locked():
                response = sock.recv(1000000)
                response_list.put(response)
            else:
                if not response_list.empty():
                    try:
                        self.lock.acquire()
                        while not response_list.empty():
                            resp = response_list.get()
                            self.parse_answer(get_data_from_message(resp))
                    except Exception:
                        self.logger.exception("Ошибка при конвертации ответа")
                        self.lock.release()
                        sys.exit(1)
                    self.lock.release()

    def parse_answer(self, req_dict):
        """Парсим полученный ответ"""

        msg_time = datetime.utcfromtimestamp(req_dict['time']).strftime('%Y-%m-%d %H:%M:%S')
        if req_dict.get('action') == 'presence':
            print(f"{msg_time} Пользователь {req_dict['user']['account_name']} вошел в чат")
        elif req_dict.get('action') == 'msg':
            print(f"{msg_time} {req_dict['from']}: {req_dict['message']}")
        elif req_dict.get('action') == 'quit':
            print(f"{msg_time} Пользователь {req_dict['username']} покинул чат")
        # elif req_dict.get('action') == 'contacts':
        #     print(req_dict['alert'])

    def run(self):

        with socket(AF_INET, SOCK_STREAM) as sock:  # Создать сокет TCP
            sock.connect((self.server_addr, int(self.server_port)))  # Соединиться с сервером
            self.presence(sock)
            print(self.get_contacts(sock))
            contacts = self.get_contacts(sock)['alert']
            for contact in contacts:
                self.db.add_contact(contact)
            if self.client_type == 'input':
                self.send_message_loop(sock)
            elif self.client_type == 'multi':
                recv_t = InputThread(self.recv_message, sock)
                interface_t = InputThread(self.send_message_loop, sock)
                recv_t.start()
                interface_t.start()
                # interface_t.join()
                while True:
                    time.sleep(2)
                    if interface_t.is_alive() and recv_t.is_alive():
                        continue
                    break
            else:
                self.recv_message(sock)


if __name__ == '__main__':
    client = Client()
    client.run()
