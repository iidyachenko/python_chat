import argparse
import sys
import time
import logging
import log.Client.client_log_config

from socket import socket, AF_INET, SOCK_STREAM
from common.utils import send_message, get_data_from_message, load_setting

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


def main():
    SETTINGS = load_setting(is_server=False)
    parser = argparse.ArgumentParser(description='Client arguments')
    parser.add_argument('addr', type=str, nargs='*', default='', help='Server address')
    parser.add_argument('port', type=int, nargs='*', default='', help='server port')
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

    s = socket(AF_INET, SOCK_STREAM)  # Создать сокет TCP
    try:
        s.connect((server_addr, server_port))  # Соединиться с сервером
    except ConnectionRefusedError:
        logger.critical('Ошибка при подключении к серверу')
        sys.exit(1)
    response = presence(s)
    logger.debug('Сообщение от сервера: ', response)
    s.close()


if __name__ == '__main__':
    main()
