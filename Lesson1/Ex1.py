str_dev = "разработка"
str_socket = "сокет"
str_decorator = "декоратор"

print(type(str_dev), str_dev)
print(type(str_socket), str_socket)
print(type(str_decorator), str_decorator)

# перевожу в юникод с помощью https://unicode-table.com/

unicode_dev = "\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430"
unicode_socket = "\u0441\u043e\u043a\u0435\u0442"
unicode_decorator = "\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440"

print(type(str_dev), str_dev)
print(type(str_socket), str_socket)
print(type(str_decorator), str_decorator)

# Несмотря на разные кодировки Python понимает что данные одного типа и имеют одно и тоже значение
