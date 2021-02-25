import argparse
import json
import select
import time
from json import JSONDecodeError
from socket import AF_INET, socket, SOCK_STREAM
import logging
import log.Server.server_log_config

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
            print(responses[sock], type(responses[sock]))
            if responses[sock]['action'] == 'presence':
                all_clients_dict[sock] = responses[sock]['user']['account_name']
        except:
            print(f' r Клиент { all_clients_dict[sock]} {sock.getpeername()} отключился')
            client_quit_req = {sock: {'action': 'quit', 'username': all_clients_dict[sock]}}
            write_responses(client_quit_req, w_clients, all_clients_dict)
            all_clients_dict.pop(sock)

    return responses


def write_responses(requests, w_clients, all_clients_dict):
    """Отправляем накопишившиеся запросы на отправку"""
    for sock in w_clients:
        for _, request in requests.items():
            try:
                # Подготовить и отправить всем слушающм клиентам ответ в чат
                send_message(sock, request)
            except:  # Сокет недоступен, клиент отключился
                print(f' w Клиент {sock.fileno()} {sock.getpeername()} отключился')
                sock.close()
                # all_clients.remove(sock)
                all_clients_dict.pop(sock)


def main():
    SETTINGS = load_setting(is_server=False, filename='common/settings.json')
    parser = argparse.ArgumentParser(description='Server arguments')
    parser.add_argument('addr', type=str, nargs='*', default='', help='Clients address')
    parser.add_argument('port', type=int, nargs='*', default='', help='server port')
    args = parser.parse_args()

    if not args.port:
        server_port = SETTINGS["DEFAULT_PORT"]
        logger.warning("Успользуются порт сервера по умолчанию")
    else:
        server_port = args.port
    s = socket(AF_INET, SOCK_STREAM)
    s.bind((args.addr, server_port))
    s.listen(SETTINGS['MAX_CONNECTION'])
    s.settimeout(2)

    # clients = []
    clients_info = {}

    while True:

        try:
            conn, addr = s.accept()  # Проверка подключений
        except OSError as e:
            pass  # timeout вышел
        else:
            print("Получен запрос на соединение от %s" % str(addr))
            # clients.append(conn)
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
                print(requests)
                write_responses(requests, w, clients_info)


if __name__ == '__main__':
    main()
