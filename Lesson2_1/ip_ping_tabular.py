from Lesson2_1.ip_ping_range import host_range_ping
from tabulate import tabulate


def host_range_ping_tab():
    result = dict(host_range_ping())
    print(result)
    print(tabulate([result], headers='keys', tablefmt="pipe", stralign='center'))


if __name__ == '__main__':
    host_range_ping_tab()