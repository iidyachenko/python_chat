import argparse
import json
import select
import time
import dis
from json import JSONDecodeError
from socket import AF_INET, socket, SOCK_STREAM
import logging
import log.Server.server_log_config
from common.descriptors import Port
from common.metaclasses import ServerVerifier

from common.utils import send_message, get_data_from_message, load_setting

logger = logging.getLogger('server')


def send_success_code(client):
    """Отправляем код успешного подключения"""
    msg_response = {
        "response": '200',
        "time": int(time.time()),
    }
    send_message(client, msg_response)


def read_requests(r_clients, w_clients, all_clients_dict):
    """Читаем накопишившиеся запросы на чтение"""
    responses = {}  # Словарь ответов сервера вида {сокет: запрос}

    for sock in r_clients:
        try:
            data = sock.recv(1024).decode('utf-8')
            responses[sock] = json.loads(data)
            if responses[sock]['action'] == 'presence':
                all_clients_dict[sock] = responses[sock]['user']['account_name']

        except:
            print(f' r Клиент {all_clients_dict[sock]} {sock.getpeername()} отключился')
            client_quit_req = {sock: {'action': 'quit', 'username': all_clients_dict[sock]}}
            # оправляем всем сообщение что пользователь отключился
            write_responses(client_quit_req, w_clients, all_clients_dict)
            if all_clients_dict.get(sock):
                all_clients_dict.pop(sock)

    return responses


def write_responses(requests, w_clients, all_clients_dict):
    """Отправляем накопишившиеся запросы на отправку"""
    for sock in w_clients:
        for _, request in requests.items():
            try:
                print(request)
                print(all_clients_dict[sock])
                # Подготовить и отправить всем слушающм клиентам ответ в чат или личным сообщением
                if request['action'] != 'msg' or request['to'] == all_clients_dict[sock] or request['to'] == '#':
                    send_message(sock, request)
                else:
                    send_success_code(sock)
            except:  # Сокет недоступен, клиент отключился
                print(f' w Клиент {sock.fileno()} {sock.getpeername()} отключился')
                sock.close()
                if all_clients_dict.get(sock):
                    all_clients_dict.pop(sock)


class Server(metaclass=ServerVerifier):
    server_port = Port()

    def __init__(self):
        SETTINGS = load_setting(is_server=False, filename='common/settings.json')
        parser = argparse.ArgumentParser(description='Server arguments')
        parser.add_argument('addr', type=str, nargs='*', default='', help='Clients address')
        parser.add_argument('port', type=int, nargs='*', default='', help='server port')
        args = parser.parse_args()
        if not args.port:
            self.server_port = SETTINGS["DEFAULT_PORT"]
            logger.warning("Успользуются порт сервера по умолчанию")
        else:
            self.server_port = args.port
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.bind((args.addr, self.server_port))
        self.socket.listen(SETTINGS['MAX_CONNECTION'])
        self.socket.settimeout(0.1)

    def run(self):
        clients_info = {}

        while True:

            try:
                conn, addr = self.socket.accept()  # Проверка подключений
            except OSError as e:
                pass  # timeout вышел
            else:
                print("Получен запрос на соединение от %s" % str(addr))
                clients_info[conn] = ''
            finally:
                # Проверить наличие событий ввода-вывода
                wait = 10
                r = []
                w = []
                try:
                    r, w, e = select.select(list(clients_info.keys()), list(clients_info.keys()), [], wait)
                except:
                    pass  # Ничего не делать, если какой-то клиент отключился

                requests = read_requests(r, w, clients_info)  # Сохраним запросы клиентов
                if requests:
                    write_responses(requests, w, clients_info)


if __name__ == '__main__':
    server = Server()
    server.run()
