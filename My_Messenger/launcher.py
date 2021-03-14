import subprocess

process = []

while True:
    action = input('Выберите действие: exit - выход , server - запустить сервер и клиенты, x - закрыть все окна:')

    if action == 'exit':
        break
    elif action == 'server':
        process.append(subprocess.Popen('python Server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
        process.append(subprocess.Popen('python Client.py -c multi -u test1', creationflags=subprocess.CREATE_NEW_CONSOLE))
        process.append(subprocess.Popen('python Client.py -c multi -u test2', creationflags=subprocess.CREATE_NEW_CONSOLE))
    elif action == 'x':
        while process:
            proc = process.pop()
            proc.kill()