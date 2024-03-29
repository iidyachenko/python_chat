MyMessenger модуль клиента
=================================================

Клиентское приложение для обмена сообщениями. Поддерживает
отправку сообщений пользователям которые находятся в сети, сообщения шифруются
с помощью алгоритма RSA с длинной ключа 2048 bit.

Поддерживает аргументы коммандной строки:

``python client.py {имя сервера} {порт} -u или --username {имя пользователя} -p или --password {пароль}``

1. {имя сервера} - адрес сервера сообщений.
2. {порт} - порт по которому принимаются подключения
3. -u или --username - имя пользователя с которым произойдёт вход в систему.
4. -p или --password - пароль пользователя.

Все опции командной строки являются необязательными, но имя пользователя и пароль необходимо использовать в паре.

Примеры использования:

* ``python client.py``

*Запуск приложения с параметрами по умолчанию.*

* ``python client.py ip_address some_port``

*Запуск приложения с указанием подключаться к серверу по адресу ip_address:port*

* ``python -u test1 -p 123``

*Запуск приложения с пользователем test1 и паролем 123*

* ``python client.py ip_address some_port -u test1 -p 123``

*Запуск приложения с пользователем test1 и паролем 123 и указанием подключаться к серверу по адресу ip_address:port*

client.py
~~~~~~~~~

Запускаемый модуль,содержит парсер аргументов командной строки и функционал инициализации приложения.

client. **arg_parser** ()
    Парсер аргументов командной строки, возвращает кортеж из 4 элементов:

	* адрес сервера
	* порт
	* имя пользователя
	* пароль

    Выполняет проверку на корректность номера порта.


database.py
~~~~~~~~~~~~~~

.. autoclass:: client.client_storage.ClientDB
	:members:

add_contact_gui.py
~~~~~~~~~~~~~~~~~~

.. autoclass:: client.add_contact_gui.AddContactDialog
    :members:

del_contact_gui.py
~~~~~~~~~~~~~~~~~~

.. autoclass:: client.del_contact_gui.DelContactDialog
	:members:

main_window_gui.py
~~~~~~~~~~~~~~~~~~

.. autoclass:: client.main_window_gui.ClientMainWindow
	:members:

receiver.py
~~~~~~~~~~~

.. autoclass:: client.receiver.ClientReceiver
	:members:
