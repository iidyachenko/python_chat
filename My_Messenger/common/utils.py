import json


def get_data_from_message(response):
    response_str = response.decode('utf-8')
    return json.loads(response_str)


def send_message(socket, data_dict):
    data = json.dumps(data_dict)
    socket.send(bytes(data, encoding="utf-8"))


