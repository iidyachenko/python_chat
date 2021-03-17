import logging
logger = logging.getLogger('server')


class Port:

    def __set__(self, instance, value):
        if not 1024 < value < 65536:
            logger.critical('Порт вне требуемого диапазона (1024 - 65535)')
            raise ValueError("Порт вне требуемого диапазона (1024 - 65535)")
        instance.__dict__[self.my_attr] = value

    def __set_name__(self, owner, my_attr):
        self.my_attr = my_attr


if __name__ == '__main__':
    pass
