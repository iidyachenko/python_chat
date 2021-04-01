import argparse
import json
import select
import sys
import threading
import time
import dis
from json import JSONDecodeError
from socket import AF_INET, socket, SOCK_STREAM
import logging

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

import log.Server.server_log_config
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from storage import ServerDB
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


def send_contact_list(client, contact_list):
    """Возвращаем список контактов"""
    msg_response = {
        "action": 'contacts',
        "time": int(time.time()),
        "response": '202',
        "alert": contact_list,
    }
    send_message(client, msg_response)


def send_users_list(client, contact_list):
    """Возвращаем список контактов"""
    msg_response = {
        "action": 'users',
        "time": int(time.time()),
        "response": '202',
        "alert": contact_list,
    }
    send_message(client, msg_response)



class Server(threading.Thread, metaclass=ServerVerifier):
    server_port = Port()

    def __init__(self, SETTINGS):

        parser = argparse.ArgumentParser(description='Server arguments')
        parser.add_argument('addr', type=str, nargs='*', default='', help='Clients address')
        parser.add_argument('port', type=int, nargs='*', default='', help='server port')
        args = parser.parse_args()
        if not args.port:
            self.server_port = int(SETTINGS["DEFAULT_PORT"])
            logger.warning("Успользуются порт сервера по умолчанию")
        else:
            self.server_port = args.port
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.bind((args.addr, self.server_port))
        self.socket.listen(SETTINGS['MAX_CONNECTION'])
        self.socket.settimeout(0.1)
        self.db = ServerDB(SETTINGS['DATABASE'])
        self.new_connection = False
        super().__init__()

    def read_requests(self, r_clients, w_clients, all_clients_dict):
        """Читаем накопишившиеся запросы на чтение"""
        responses = {}  # Словарь ответов сервера вида {сокет: запрос}

        for sock in r_clients:
            try:
                data = sock.recv(1024).decode('utf-8')
                responses[sock] = json.loads(data)
                if responses[sock]['action'] == 'presence':
                    print(f"Клиент {sock.getpeername()[0]} {responses[sock]['user']['account_name']} вошел")
                    all_clients_dict[sock] = responses[sock]['user']['account_name']
                    self.db.user_login(responses[sock]['user']['account_name'], sock.getpeername()[0],
                                       sock.getpeername()[1])
                if responses[sock]['action'] == 'add_contact':
                    self.db.add_contact(responses[sock]['from'], responses[sock]['to'])
                if responses[sock]['action'] == 'del_contact':
                    self.db.remove_contact(responses[sock]['from'], responses[sock]['to'])

            except:
                print(f' r Клиент {all_clients_dict[sock]} {sock.getpeername()} отключился')
                self.db.user_logout(all_clients_dict[sock])
                client_quit_req = {sock: {'action': 'quit', 'username': all_clients_dict[sock],"time": int(time.time())}}
                # оправляем всем сообщение что пользователь отключился
                self.write_responses(client_quit_req, w_clients, all_clients_dict)
                if all_clients_dict.get(sock):
                    all_clients_dict.pop(sock)

        return responses

    def write_responses(self, requests, w_clients, all_clients_dict):
        """Отправляем накопишившиеся запросы на отправку"""
        for sock in w_clients:
            for _, request in requests.items():
                try:
                    print(request,sock)
                    # Подготовить и отправить всем слушающм клиентам ответ в чат или личным сообщением
                    if request['action'] == 'get_contacts':
                        if request['user_login'] == all_clients_dict[sock]:
                            # print(self.db.contact_list(request['user_login']))
                            send_contact_list(sock, self.db.contact_list(request['user_login']))
                        else:
                            continue
                    elif request['action'] == 'get_users':
                        if request['user_login'] == all_clients_dict[sock]:
                            send_users_list(sock, [x[0] for x in self.db.users_list()])
                        else:
                            continue
                    elif request['action'] == 'quit':
                        send_message(sock, request)
                        continue
                    elif request['action'] == 'presence' or request['to'] == all_clients_dict[sock] or request[
                        'to'] == '#':
                        if request['action'] == 'msg' and request['to'] != '#':
                            print(f"Сообщение от пользователя {request['from']} пользователю {request['to']}")
                            self.db.user_send_message(request['from'], request['to'])
                        if request['action'] == 'presence':
                            self.new_connection = True
                        send_message(sock, request)
                    else:
                        send_success_code(sock)
                except:  # Сокет недоступен, клиент отключился
                    print(f' w Клиент {sock.fileno()} {sock.getpeername()} отключился')
                    self.db.user_logout(sock.fileno())
                    sock.close()
                    if all_clients_dict.get(sock):
                        all_clients_dict.pop(sock)

    def run(self):
        clients_info = {}
        print('Сервер запущен')
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

                requests = self.read_requests(r, w, clients_info)  # Сохраним запросы клиентов
                if requests:
                    self.write_responses(requests, w, clients_info)


if __name__ == '__main__':
    def list_update():
        main_window.active_clients_table.setModel(
            gui_create_model(database))
        main_window.active_clients_table.resizeColumnsToContents()
        main_window.active_clients_table.resizeRowsToContents()
        # server.new_connection = False

    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

        # Функция создающяя окно с настройками сервера.
    def server_config():
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(SETTINGS['DATABASE'].split('///')[1])
        config_window.port.insert(str(SETTINGS['DEFAULT_PORT']))
        config_window.ip.insert(SETTINGS['DEFAULT_IP_ADDRESS'])
        config_window.show()
        config_window.save_btn.clicked.connect(save_server_config)

        # Функция сохранения настроек
    def save_server_config():
        global config_window
        message = QMessageBox()
        SETTINGS['DATABASE'] = 'sqlite:///' + config_window.db_path.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            SETTINGS['DEFAULT_IP_ADDRESS'] = config_window.ip.text()
            if 1023 < port < 65536:
                SETTINGS['DEFAULT_PORT'] = str(port)
                with open('common/settings.json', 'w') as j_file:
                    json.dump(SETTINGS, j_file, indent=4)
                print(SETTINGS)
            else:
                message.warning(config_window, 'Ошибка', 'Порт должен быть от 1024 до 65536')
        message.information(config_window, 'OK', 'Настройки успешно сохранены!')

    SETTINGS = load_setting(is_server=False, filename='common/settings.json')
    database = ServerDB(SETTINGS['DATABASE'])
    server = Server(SETTINGS)
    server.daemon = True
    server.start()
    print('Запуск интерфейса')
    server_app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()
    # Таймер, обновляющий список клиентов 1 раз в секунду
    # timer = QTimer()
    # timer.timeout.connect(list_update)
    # timer.start(1000)
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    server_app.exec_()
    # sys.exit(server_app.exec_())
