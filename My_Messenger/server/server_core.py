import binascii
import hmac
import json
import os
import select
import threading
import time
from socket import AF_INET, socket, SOCK_STREAM
import logging
from storage import ServerDB
from common.descriptors import Port
from common.metaclasses import ServerVerifier

from common.utils import send_message

logger = logging.getLogger('server')

RESPONSE_400 = {
    'response': 400,
    'error': ''
}


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


def send_user_keys(client, key):
    """Возвращаем список контактов"""
    msg_response = {
        "action": 'public_key_request',
        "time": int(time.time()),
        "response": '511',
        "data": key,
    }
    send_message(client, msg_response)


class Server(threading.Thread, metaclass=ServerVerifier):
    server_port = Port()

    def __init__(self, SETTINGS, address, port):
        self.address = address
        self.server_port = port
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.bind((self.address, self.server_port))
        self.socket.listen(SETTINGS['MAX_CONNECTION'])
        self.socket.settimeout(0.1)
        self.db = ServerDB(SETTINGS['DATABASE'])
        self.new_connection = False
        self.clients_info = {}
        self.clients_hash = {}
        super().__init__()

    def presence(self, message, sock):
        """Метод реализующий идентификацию пользователей.
        """
        # Если имя пользователя уже занято то возвращаем 400
        if message["user"]["account_name"] in self.db.get_active_username():
            print('Имя пользователя уже занято.')
            response = RESPONSE_400
            response['error'] = 'Имя пользователя уже занято.'
            try:
                logger.debug(f'Username busy, sending {response}')
                send_message(sock, response)
            except OSError:
                logger.debug('OS Error')
                pass
            if self.clients_info.get(sock):
                self.clients_info.pop(sock)
        # Проверяем что пользователь зарегистрирован на сервере.
        elif not self.db.check_user(message["user"]["account_name"]):
            print('Пользователь не зарегистрирован.')
            response = RESPONSE_400
            response['error'] = 'Пользователь не зарегистрирован.'
            try:
                logger.debug(f'Unknown username, sending {response}')
                send_message(sock, response)
            except OSError:
                pass
            if self.clients_info.get(sock):
                self.clients_info.pop(sock)
        else:
            logger.debug('Correct username, starting passwd check.')
            print('Correct username, starting passwd check.')
            # Иначе отвечаем 511 и высылаем запрос на авторизацию
            # Набор байтов в hex представлении
            random_str = binascii.hexlify(os.urandom(64))
            message_auth = {'response': 511, 'data': random_str.decode('ascii')}
            # Создаём хэш пароля и связки с рандомной строкой
            hash = hmac.new(self.db.get_hash(message["user"]["account_name"]), random_str, 'MD5')
            digest = hash.digest()
            logger.debug(f'Auth message = {message_auth}')
            print(f'Auth message = {message_auth}')
            try:
                # Обмен с клиентом
                send_message(sock, message_auth)
                self.clients_hash[message["user"]["account_name"]] = digest
            except OSError as err:
                logger.debug('Error in auth, data:', exc_info=err)
                sock.close()
                return

    def autorize_user(self, message, sock):
        """Метод реализующий аутентификацию и авторизацию пользователей."""
        client_digest = binascii.a2b_base64(message['data'])
        # Если ответ клиента корректный, то сохраняем его в список
        # пользователей.
        digest = self.clients_hash[message["username"]]
        if 'response' in message and message['response'] == 511 and hmac.compare_digest(digest, client_digest):
            self.clients_info[sock] = message["username"]
            client_ip, client_port = sock.getpeername()
            try:
                send_success_code(sock)
            except OSError:
                self.db.user_logout(message["username"])
            # добавляем пользователя в список активных и если у него изменился открытый ключ
            # сохраняем новый
            self.db.user_login(message["username"], client_ip, client_port, message["keys"])
            print('Корректный пароль')
        else:
            response = RESPONSE_400
            response['error'] = 'Неверный пароль.'
            try:
                send_message(sock, response)
            except OSError:
                pass
            print('Неверный пароль')
            self.db.user_logout(message["username"])
            if self.clients_info.get(sock):
                self.clients_info.pop(sock)

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
                if responses[sock]['action'] == 'add_contact':
                    self.db.add_contact(responses[sock]['from'], responses[sock]['to'])
                if responses[sock]['action'] == 'del_contact':
                    self.db.remove_contact(responses[sock]['from'], responses[sock]['to'])

            except:
                print(f' r Клиент {all_clients_dict[sock]} {sock.getpeername()} отключился')
                self.db.user_logout(all_clients_dict[sock])
                client_quit_req = {
                    sock: {'action': 'quit', 'username': all_clients_dict[sock], "time": int(time.time())}}
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
                    print(request, sock)
                    # Подготовить и отправить всем слушающм клиентам ответ в чат или личным сообщением
                    if request['action'] == 'get_contacts':
                        if request['user_login'] == all_clients_dict[sock]:
                            # print(self.db.contact_list(request['user_login']))
                            send_contact_list(sock, self.db.contact_list(request['user_login']))
                        else:
                            continue

                    elif request['action'] == 'public_key_request':
                        key = self.db.get_pubkey(request['username'])
                        print(key)
                        send_user_keys(sock, key)

                    elif request['action'] == 'get_users':
                        if request['user_login'] == all_clients_dict[sock]:
                            send_users_list(sock, [x[0] for x in self.db.users_list()])
                        else:
                            continue
                    elif request['action'] == 'quit':
                        send_message(sock, request)
                        continue

                    elif request['action'] == 'msg' and request['to'] == all_clients_dict[sock]:
                        print(f"Сообщение от пользователя {request['from']} пользователю {request['to']}")
                        self.db.user_send_message(request['from'], request['to'])
                        send_message(sock, request)

                    elif request['action'] == 'presence' and request['user']['account_name'] == all_clients_dict[sock]:
                        self.new_connection = True
                        self.presence(request, sock)

                    elif request['action'] == 'join' and request['username'] == all_clients_dict[sock]:
                        self.new_connection = True
                        self.autorize_user(request, sock)
                    else:
                        continue
                except:  # Сокет недоступен, клиент отключился
                    print(f' w Клиент {sock.fileno()} {sock.getpeername()} отключился')
                    self.db.user_logout(sock.fileno())
                    sock.close()
                    if all_clients_dict.get(sock):
                        all_clients_dict.pop(sock)

    def run(self):
        """
        Основной цикл потока. Оюработка пришедших запросов.
        """
        print('Сервер запущен')
        while True:

            try:
                conn, addr = self.socket.accept()  # Проверка подключений
            except OSError as e:
                pass  # timeout вышел
            else:
                print("Получен запрос на соединение от %s" % str(addr))
                self.clients_info[conn] = ''
            finally:
                # Проверить наличие событий ввода-вывода
                wait = 10
                r = []
                w = []
                try:
                    r, w, e = select.select(list(self.clients_info.keys()), list(self.clients_info.keys()), [], wait)
                except:
                    pass  # Ничего не делать, если какой-то клиент отключился

                requests = self.read_requests(r, w, self.clients_info)  # Сохраним запросы клиентов
                if requests:
                    self.write_responses(requests, w, self.clients_info)
