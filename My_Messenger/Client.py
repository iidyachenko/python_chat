import argparse
import time
from socket import socket, AF_INET, SOCK_STREAM

from common.utils import send_message, get_data_from_message


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

    data = get_data_from_message(sock.recv(1000000))
    print('Сообщение от сервера: ', data)


parser = argparse.ArgumentParser(description='Client arguments')
parser.add_argument('addr', type=str, help='Server address')
parser.add_argument('port', type=int, nargs='*', default=7777, help='server port')
args = parser.parse_args()

s = socket(AF_INET, SOCK_STREAM)  # Создать сокет TCP
s.connect((args.addr, args.port))  # Соединиться с сервером
presence(s)

s.close()
