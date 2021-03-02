import json
import os
import sys
import logging
import inspect
import log.func_log


class Log:
    def __init__(self, level='debug'):
        self.logger = logging.getLogger('func_log')
        self.level = level

    def __call__(self, func):
        def decorator(*args, **kwargs):
            frame = inspect.currentframe().f_back
            if self.level == 'info':
                self.logger.info(
                    f"Вызываем функцию {func.__name__} с агументами: {args}{kwargs} вызвана из функции {frame.f_code.co_name}")
            else:
                self.logger.debug(
                    f"Вызываем функцию {func.__name__} с агументами: {args}{kwargs} вызвана из функции {frame.f_code.co_name}")
            return func(*args, **kwargs)

        return decorator


def my_log(func):
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('server')
        frame = inspect.currentframe().f_back
        logger.debug(
            f"Вызываем функцию {func.__name__} с агументами: {args}{kwargs}{frame.f_code.co_name} вызвана из функции {frame.f_code.co_name}")
        return func(*args, **kwargs)

    return wrapper


def get_logger(is_server=True):
    if is_server:
        return logging.getLogger('server')
    else:
        return logging.getLogger('client')


def get_data_from_message(response, is_server=True):
    logger = get_logger(is_server)
    try:
        response_str = response.decode('utf-8')
        logger.debug(f'это респонс {response_str}')
        return json.loads(response_str)
    except Exception as ex:
        print(response, ex)
        raise Exception


def send_message(socket, data_dict, is_server=True):
    logger = get_logger(is_server)
    if isinstance(data_dict, dict):
        data = json.dumps(data_dict)
        logger.debug(f'Сообщение отправлено  {socket}')
        return socket.send(bytes(data, encoding="utf-8"))
    else:
        logger.critical(f"Некорректный формат сообщения {data_dict} {type(data_dict)}")
        raise TypeError


def load_setting(is_server=True, filename='common/settings.json'):
    logger = get_logger(is_server)

    config_keys = ["DEFAULT_IP_ADDRESS", "DEFAULT_PORT", "MAX_CONNECTION", "MAX_PACKAGE_LENGTH", "USER"]
    if not is_server:
        config_keys.append("DEFAULT_IP_ADDRESS")
    with open(filename, 'r') as file:
        configs = json.load(file)
    for key in config_keys:
        if key not in configs:
            logger.critical(f"В конфигурации отсутсвует ключ: {key}")
            raise ValueError
    return configs


def main():
    print(load_setting(is_server=False))


if __name__ == '__main__':
    main()
