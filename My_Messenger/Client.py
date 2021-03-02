import argparse
import queue
import sys
import threading
import time
import logging
from datetime import datetime

import log.Client.client_log_config

from socket import socket, AF_INET, SOCK_STREAM
from common.utils import send_message, get_data_from_message, load_setting, Log, log


class InputThread(threading.Thread):
    def __init__(self, func, sock):
        super().__init__()
        self.daemon = True
        self.func = func
        self.sock = sock

    def run(self):
        self.func(self.sock)


class Client():

    __slots__ = ('logger', 'server_addr', 'server_port', 'client_type', 'username', 'lock', 'work_flag')

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

    def join_massage(self, sock):
        msg_join = {
            "action": "join",
            "time": int(time.time()),
            "room": "main_chat"
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

    def send_message_loop(self, sock):
        while True:
            self.lock.acquire()
            to = input('Введите адресат сообщения(что бы отправить сообщение всем нажмите #): ')
            if to == 'exit':
                self.lock.release()
                self.work_flag = False
                print("Осуществляется выход из чата")
                break
            msg = input(f'Ваше сообщение пользователю {to}: ')
            if msg == 'exit':
                self.lock.release()
                self.work_flag = False
                print("Осуществляется выход из чата")
                break
            self.user_massage(sock, to, msg)
            self.lock.release()
            print('Новые сообщения:')
            time.sleep(1)

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

    def run(self):

        with socket(AF_INET, SOCK_STREAM) as sock:  # Создать сокет TCP
            sock.connect((self.server_addr, self.server_port))  # Соединиться с сервером
            self.presence(sock)
            if self.client_type == 'input':
                self.send_message_loop(sock)
            elif self.client_type == 'multi':
                recv_t = InputThread(self.recv_message, sock)
                interface_t = InputThread(self.send_message_loop, sock)
                interface_t.start()
                recv_t.start()
                interface_t.join()

            else:
                self.recv_message(sock)


if __name__ == '__main__':
    client = Client()
    client.run()
