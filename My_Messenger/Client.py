import argparse
import time
from socket import socket, AF_INET, SOCK_STREAM

from common.utils import send_message, get_data_from_message, load_setting


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
    response = sock.recv(1000000)
    return get_data_from_message(response)


if __name__ == '__main__':

    SETTINGS = load_setting(is_server=False)
    parser = argparse.ArgumentParser(description='Client arguments')
    parser.add_argument('addr', type=str, nargs='*', default='', help='Server address')
    parser.add_argument('port', type=int, nargs='*', default='', help='server port')
    args = parser.parse_args()

    if not args.addr:
        server_addr = SETTINGS["DEFAULT_IP_ADDRESS"]
    else:
        server_addr = args.addr

    if not args.port:
        server_port = SETTINGS["DEFAULT_PORT"]
    else:
        server_port = args.port

    s = socket(AF_INET, SOCK_STREAM)  # Создать сокет TCP
    s.connect((server_addr, server_port))  # Соединиться с сервером
    print('Сообщение от сервера: ', presence(s))

    s.close()