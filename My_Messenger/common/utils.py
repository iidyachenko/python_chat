import json
import os
import sys


def get_data_from_message(response):
    print('это респонс ', response)
    response_str = response.decode('utf-8')
    return json.loads(response_str)


def send_message(socket, data_dict):
    if isinstance(data_dict, dict):
        data = json.dumps(data_dict)
        print('сообщение отправлеено')
        return socket.send(bytes(data, encoding="utf-8"))
    else:
        raise TypeError


def load_setting(is_server=True, filename='settings.json'):
    config_keys = ["DEFAULT_IP_ADDRESS", "DEFAULT_PORT", "MAX_CONNECTION", "MAX_PACKAGE_LENGTH", "USER"]
    if not is_server:
        config_keys.append("DEFAULT_IP_ADDRESS")
    with open(filename, 'r') as file:
        configs = json.load(file)
    for key in config_keys:
        if key not in configs:
            print(f"В конфигурации отсутсвует ключ: {key}")
            raise ValueError
    return configs


