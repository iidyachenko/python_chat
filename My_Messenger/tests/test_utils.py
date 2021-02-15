import json
import time
import unittest
from json import JSONDecodeError
from socket import socket, AF_INET, SOCK_STREAM

from common.utils import send_message, get_data_from_message, load_setting


class UtilsTests(unittest.TestCase):

    def setUp(self):
        self.server_addr = 'localhost'
        self.server_port = 7777
        self.socket = socket(AF_INET, SOCK_STREAM)

    def tearDown(self):
        self.socket.close()

    def test_correct_send(self):
        message = {
            "action": "test",
            "time": int(time.time()),
            "type": "status",
            "user": {
                "account_name": "Test",
                "status": "Connect to server"
            }
        }
        self.socket.connect((self.server_addr, self.server_port))
        self.assertTrue(send_message(self.socket, message))
        self.socket.close()

    def test_send_not_dict_message(self):
        message = 'asdfg'
        self.socket.connect((self.server_addr, self.server_port))
        with self.assertRaises(TypeError):
            send_message(self.socket, message)
        self.socket.close()

    def test_get_correct_message(self):
        message = b'{"response": "200", "time": 1612953360}'
        self.assertEqual(get_data_from_message(message), {'response': '200', 'time': 1612953360})

    def test_empty_message_error(self):
        message = b''
        with self.assertRaises(JSONDecodeError):
            get_data_from_message(message)

    def test_load_settings_normal(self):
        dict_to_json = {
            "DEFAULT_IP_ADDRESS": "127.0.0.1",
            "DEFAULT_PORT": 7777,
            "MAX_CONNECTION": 5,
            "MAX_PACKAGE_LENGTH": 100000,
            "USER": "Igor"
        }
        with open('test_settings.json', 'w') as f_n:
            f_n.write(json.dumps(dict_to_json))

        settings = load_setting(is_server=False, filename='test_settings.json')
        self.assertEqual(settings, dict_to_json)

    def test_load_settings_not_all_param(self):
        dict_to_json = {
            "DEFAULT_IP_ADDRESS": "127.0.0.1",
            "DEFAULT_PORT": 7777,
            "MAX_CONNECTION": 5,
            "USER": "Igor"
        }
        with open('test_settings.json', 'w') as f_n:
            f_n.write(json.dumps(dict_to_json))
        with self.assertRaises(ValueError):
            settings = load_setting(is_server=False, filename='test_settings.json')


if __name__ == '__main__':
    unittest.main()
