"""
6. Создать текстовый файл test_file.txt, заполнить его тремя строками: «сетевое программирование», «сокет», «декоратор».
 Проверить кодировку файла по умолчанию. Принудительно открыть файл в формате Unicode и вывести его содержимое.
"""

import locale


def_coding = locale.getpreferredencoding()
print(def_coding)
filename = 'test_file.txt'

with open(filename, 'r', encoding='utf-8') as file:
    print(file)
    for line in file:
        print(line)