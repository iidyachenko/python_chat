import argparse
import sys
import time
import logging
import log.Client.client_log_config

from socket import socket, AF_INET, SOCK_STREAM
from common.utils import send_message, get_data_from_message, load_setting, Log, log

logger = logging.getLogger('client')


def presence(sock):
    msg_presence = {
        "action": "presence",
        "time": int(time.time()),
        "type": "status",
        "user": {
            "account_name": "Игорь",
            "status": "Connect to server"
        }
    }
    send_message(sock, msg_presence)
    try:
        response = sock.recv(1000000)
    except Exception:
        logger.exception('Ошибка при приеме ответа с сервера')
        sys.exit(1)
    return get_data_from_message(response)


def join_massage(sock):
    msg_join = {
        "action": "join",
        "time": int(time.time()),
        "room": "main_chat"
    }
    send_message(sock, msg_join)
    try:
        response = sock.recv(1000000)
    except Exception:
        logger.exception('Ошибка при приеме ответа с сервера')
        sys.exit(1)
    return get_data_from_message(response)


def user_massage(sock, msg):
    msg_join = {
        "action": "msg",
        "time": int(time.time()),
        "room": "main_chat",
        "to": "#",
        "from": "account_name",
        "encoding": "utf-8",
        "message": msg
    }
    send_message(sock, msg_join)
    try:
        response = sock.recv(1000000)
    except Exception:
        logger.exception('Ошибка при приеме ответа с сервера')
        sys.exit(1)
    return get_data_from_message(response)


def parse_answer(req_dict):
    """Парсим полученный ответ"""

    if req_dict['action'] == 'presence':  # статус отправляем только отправителю при получении
        print(f"Пользователь {req_dict['user']['account_name']} вошел в чат")
    elif req_dict['action'] == 'msg':
        print(f"Пользователь {req_dict['from']}: {req_dict['message']}")
    elif req_dict['action'] == 'quit':
        print(f"Пользователь {req_dict['username']} покинул чат")


def main():
    SETTINGS = load_setting(is_server=False, filename='common/settings.json')
    parser = argparse.ArgumentParser(description='Client arguments')
    parser.add_argument('addr', type=str, nargs='*', default='', help='Server address')
    parser.add_argument('port', type=int, nargs='*', default='', help='server port')
    parser.add_argument('-c', '--client_type', nargs='*', default='input', help='type of client')
    args = parser.parse_args()
    if not args.addr:
        server_addr = SETTINGS["DEFAULT_IP_ADDRESS"]
        logger.warning("Успользуются адрес сервера по умолчанию")
    else:
        server_addr = args.addr

    if not args.port:
        server_port = SETTINGS["DEFAULT_PORT"]
        logger.warning("Успользуются порт сервера по умолчанию")
    else:
        server_port = args.port

    with socket(AF_INET, SOCK_STREAM) as sock:  # Создать сокет TCP
        sock.connect((server_addr, server_port))  # Соединиться с сервером
        presence(sock)
        if args.client_type[0] == 'input':
            while True:
                msg = input('Ваше сообщение: ')
                if msg == 'exit':
                    break
                response = user_massage(sock, msg)
                logger.debug('Сообщение от сервера: ', response)
        else:
            while True:
                try:
                    response = sock.recv(1000000)
                except Exception:
                    logger.exception('Ошибка при приеме ответа с сервера')
                    sys.exit(1)
                parse_answer(get_data_from_message(response))


if __name__ == '__main__':
    main()
