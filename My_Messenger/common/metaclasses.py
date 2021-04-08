import dis
from socket import socket


class ServerVerifier(type):
    def __init__(self, clsname, bases, clsdict):
        methods = set()
        attrs = set()
        load_methods = set()
        for func in clsdict:
            try:
                res = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for el in res:
                    if el.opname == 'LOAD_GLOBAL':
                        methods.add(el.argval)
                    elif el.opname == 'LOAD_ATTR':
                        attrs.add(el.argval)
                    elif el.opname == 'LOAD_METHOD':
                        load_methods.add(el.argval)
        if 'connect' in methods or 'connect' in load_methods:
            raise TypeError("Используется недопустимая операция с сокетом")
        if 'AF_INET' not in methods and 'SOCK_STREAM' not in methods:
            raise TypeError("Используется недопустимый тип сокета")
        super().__init__(clsname, bases, clsdict)


class ClientVerifier(type):
    def __init__(self, clsname, bases, clsdict):
        methods = set()
        attrs = set()
        load_methods = set()
        for func in clsdict:
            if isinstance(clsdict[func], type(socket())):
                raise TypeError("Создание сокета на уровне класса")
            try:
                res = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for el in res:
                    if el.opname == 'LOAD_GLOBAL':
                        methods.add(el.argval)
                    elif el.opname == 'LOAD_ATTR':
                        attrs.add(el.argval)
                    elif el.opname == 'LOAD_METHOD':
                        load_methods.add(el.argval)

        if 'accept' in methods or 'accept' in load_methods or 'listen' in methods or 'listen' in load_methods:
            raise TypeError("Используется недопустимая операция с сокетом")
        if'AF_INET' not in methods and 'SOCK_STREAM' not in methods:
            raise TypeError("Используется недопустимый тип сокета")
        super().__init__(clsname, bases, clsdict)


if __name__ == '__main__':
    pass
