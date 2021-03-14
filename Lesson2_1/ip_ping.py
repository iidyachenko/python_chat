from collections import defaultdict
from ipaddress import ip_address
from subprocess import Popen, PIPE, call


def host_ping(address_list, timeout, req):
    result_dict = defaultdict(str)
    for address in address_list:
        try:
            ip_addr = ip_address(address)
        except ValueError:
            ip_addr = address

    # что бы не повторять код из урока написал решение через call() нам все равно по заданию нужен только код выполнения
        answer = call(f'ping {ip_addr} -w {timeout} -n {req}', shell=False, stdout=PIPE)
        if answer == 0:
            print(f"Адрес {address} доступен")
            result_dict['Доступные узлы'] += f"{address}\n"
        else:
            print(f"Адрес {address} недоступен")
            result_dict['Недоступные узлы'] += f"{address}\n"
    return result_dict


if __name__ == '__main__':
    res = host_ping(['yandex.ru', 'localhost', '5.255.255.5', '5.255.255.4'], 1000, 1)
    # print(res)
    # for key, value in res.items():
    #     print(key, value)