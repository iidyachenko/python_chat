import json


def write_order_to_json(item, quantity, price, buyer, date):
    dict_to_file = {"item": item,
                    "quantity": quantity,
                    "price": price,
                    "buyer": buyer,
                    "date": date
                    }

    with open('orders.json', 'r') as j_file:
        file_orders = json.load(j_file)

    if 'orders' in file_orders:
        file_orders['orders'].append(dict_to_file)
    else:
        file_orders['orders'] = []
        file_orders['orders'].append(dict_to_file)

    with open('orders.json', 'w') as j_file:
        json.dump(file_orders, j_file, indent=4)


write_order_to_json('Ball', "100", "25.5", "Mike", "01.01.2021")
