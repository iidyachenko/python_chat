import argparse
import json
import sys
import logging

from PyQt5.QtWidgets import QApplication, QMessageBox

import log.Server.server_log_config
from server.server_core import Server
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from storage import ServerDB

from common.utils import load_setting

logger = logging.getLogger('server')

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
    parser = argparse.ArgumentParser(description='Server arguments')
    parser.add_argument('addr', type=str, nargs='*', default='', help='Clients address')
    parser.add_argument('port', type=int, nargs='*', default='', help='server port')
    args = parser.parse_args()
    if not args.port:
        server_port = int(SETTINGS["DEFAULT_PORT"])
        logger.warning("Успользуются порт сервера по умолчанию")
    else:
        server_port = args.port
    if not args.addr:
        addr = SETTINGS["DEFAULT_IP_ADDRESS"]
        logger.warning("Успользуются адрес сервера по умолчанию")
    else:
        addr = args.addr
    database = ServerDB(SETTINGS['DATABASE'])
    server = Server(SETTINGS, addr, server_port)
    server.daemon = True
    server.start()
    print('Запуск интерфейса')
    server_app = QApplication(sys.argv)
    main_window = MainWindow(database, server)
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
