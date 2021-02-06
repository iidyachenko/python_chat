import argparse
import time
from socket import AF_INET, socket, SOCK_STREAM

from common.utils import send_message, get_data_from_message


def send_success_code(client):
    msg_response = {
        "response": '200',
        "time": int(time.time()),
    }
    send_message(client, msg_response)


parser = argparse.ArgumentParser(description='Server arguments')
parser.add_argument('addr', type=str, nargs='*', default='', help='Clients address')
parser.add_argument('port', type=int, nargs='*', default=7777, help='server port')
args = parser.parse_args()

s = socket(AF_INET, SOCK_STREAM)
s.bind((args.addr, args.port))
s.listen(5)

while True:
    client, addr = s.accept()
    data = get_data_from_message(client.recv(1000000))
    print('Сообщение: ', data, ', было отправлено клиентом: ', addr)

    send_success_code(client)

    client.close()
