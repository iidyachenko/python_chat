import argparse
import sys
import time
import logging
import log.Client.client_log_config

from socket import socket, AF_INET, SOCK_STREAM
from common.utils import send_message, get_data_from_message, load_setting, Log, log


class Client():

    __slots__ = ('logger', 'server_addr', 'server_port', 'client_type', 'username')

    def __init__(self):

        self.logger = logging.getLogger('client')
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

    def user_massage(self, sock, msg):
        msg_join = {
            "action": "msg",
            "time": int(time.time()),
            "room": "main_chat",
            "to": "#",
            "from": self.username,
            "encoding": "utf-8",
            "message": msg
        }
        send_message(sock, msg_join)
        try:
            response = sock.recv(1000000)
        except Exception:
            self.logger.exception('Ошибка при приеме ответа с сервера')
            sys.exit(1)
        return get_data_from_message(response)

    def parse_answer(self, req_dict):
        """Парсим полученный ответ"""

        if req_dict['action'] == 'presence':  # статус отправляем только отправителю при получении
            print(f"Пользователь {req_dict['user']['account_name']} вошел в чат")
        elif req_dict['action'] == 'msg':
            print(f"Пользователь {req_dict['from']}: {req_dict['message']}")
        elif req_dict['action'] == 'quit':
            print(f"Пользователь {req_dict['username']} покинул чат")

    def run(self):

        with socket(AF_INET, SOCK_STREAM) as sock:  # Создать сокет TCP
            sock.connect((self.server_addr, self.server_port))  # Соединиться с сервером
            self.presence(sock)
            if self.client_type == 'input':
                while True:
                    msg = input('Ваше сообщение: ')
                    if msg == 'exit':
                        break
                    response = self.user_massage(sock, msg)
                    self.logger.debug('Сообщение от сервера: ', response)
            else:
                while True:
                    try:
                        response = sock.recv(1000000)
                    except Exception:
                        self.logger.exception('Ошибка при приеме ответа с сервера')
                        sys.exit(1)
                    self.parse_answer(get_data_from_message(response))


if __name__ == '__main__':
    client = Client()
    client.run()
