"""
Выполнить пинг веб-ресурсов yandex.ru, youtube.com
и преобразовать результаты из байтовового в строковый тип на кириллице.
"""
import chardet
import subprocess

args = ['ping', 'yandex.ru']
subproc_ping = subprocess.Popen(args, stdout=subprocess.PIPE)

# пинг до преобразования кодировки
for line in subproc_ping.stdout:
    print(line)
    encode = chardet.detect(line)



# пинг после преобразования кодировки
subproc_ping = subprocess.Popen(args, stdout=subprocess.PIPE)
for line in subproc_ping.stdout:
    print(line.decode(f'{encode["encoding"]}'))


args = ['ping', 'youtube.com']
subproc_ping = subprocess.Popen(args, stdout=subprocess.PIPE)
for line in subproc_ping.stdout:
    print(line.decode(f'{encode["encoding"]}'))