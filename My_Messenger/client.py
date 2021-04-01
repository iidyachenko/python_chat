import argparse
import queue
import sys
import threading
import time
import logging

from PyQt5.QtWidgets import QApplication

import log.Client.client_log_config
from datetime import datetime

from socket import socket, AF_INET, SOCK_STREAM

from client.client_storage import ClientDB
from common.metaclasses import ClientVerifier
from common.utils import send_message, get_data_from_message, load_setting
from client.main_window_gui import ClientMainWindow
from client.receiver import ClientReceiver

logger = logging.getLogger('client')


def parser_args():
    SETTINGS = load_setting(is_server=False, filename='common/settings.json')
    parser = argparse.ArgumentParser(description='Client arguments')
    parser.add_argument('addr', type=str, nargs='*', default='', help='Server address')
    parser.add_argument('port', type=int, nargs='*', default='', help='server port')
    parser.add_argument('-u', '--username', nargs='*', default='anonymous', help='type of client')
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
    username = args.username[0]

    return server_addr, server_port, username


if __name__ == '__main__':
    server_addr, server_port, username = parser_args()
    db = ClientDB(username)

    # Создаём графическое приложение
    client_app = QApplication(sys.argv)

    transport = ClientReceiver(server_port, server_addr, db, username)
    transport.setDaemon(True)
    transport.start()

    main_window = ClientMainWindow(db, transport)
    # main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа alpha release - {username}')
    main_window.make_connection(transport)
    client_app.exec_()
