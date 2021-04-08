import argparse
import os
import sys
import logging

from Cryptodome.PublicKey import RSA
from PyQt5.QtWidgets import QApplication

import log.Client.client_log_config


from client.client_storage import ClientDB
from client.start_window import UserNameDialog
from common.utils import load_setting
from client.main_window_gui import ClientMainWindow
from client.receiver import ClientReceiver

logger = logging.getLogger('client')


def parser_args():
    """
    Чтение аргументов командной строки
    """
    SETTINGS = load_setting(is_server=False, filename='common/settings.json')
    parser = argparse.ArgumentParser(description='Client arguments')
    parser.add_argument('addr', type=str, nargs='*', default='', help='Server address')
    parser.add_argument('port', type=int, nargs='*', default='', help='server port')
    parser.add_argument('-u', '--username', nargs='*', default='anonymous', help='user name')
    parser.add_argument('-p', '--password', nargs='*', default='qwe', help='password')
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
    passwd = args.password[0]

    return server_addr, server_port, username, passwd


if __name__ == '__main__':
    server_addr, server_port, username, passwd = parser_args()
    print(server_addr, server_port, username, passwd)
    # Создаём графическое приложение
    client_app = QApplication(sys.argv)
    # Если имя пользователя не было указано в командной строке то запросим его
    start_dialog = UserNameDialog()

    if not username or not passwd:
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и
        # удаляем объект, инааче выходим
        if start_dialog.ok_pressed:
            username = start_dialog.client_name.text()
            passwd = start_dialog.client_passwd.text()
            logger.debug(f'Using USERNAME = {username}, PASSWD = {passwd}.')
        else:
            exit(0)

    # Загружаем ключи с файла, если же файла нет, то генерируем новую пару.
    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{username}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())
    db = ClientDB(username)

    transport = ClientReceiver(server_port, server_addr, db, username, passwd, keys)
    transport.setDaemon(True)
    transport.start()
    del start_dialog
    main_window = ClientMainWindow(db, transport, keys)
    # main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа alpha release - {username}')
    main_window.make_connection(transport)
    client_app.exec_()
