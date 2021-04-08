from ipaddress import ip_address, ip_network
from Lesson2_1.ip_ping import host_ping


# Что бы не повторять код с урока. Я немного изменил задния ввести надо адрес сети и маску.
# Таким образом модуль ip_network еще попробовал использовать
def host_range_ping():
    while True:
        try:
            address = input('введите IP адрес сети: ')
            subnet = input('введите двузначный номер подсети: ')
            subnet = ip_network(f"{address}/{subnet}")
        except ValueError:
            print('Вы ввели некорректный адрес, повторите попытку')
            continue
        return host_ping(subnet.hosts(), timeout=500, req=1)


if __name__ == '__main__':
    print(host_range_ping())