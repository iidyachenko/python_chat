import yaml

dict_to_file = {'my_list': ['Moscow', 'London', 'Paris'],
                'my_number': 41,
                'my_dict': {1: '1$',
                            2: '2€'
                            }
                }

with open('data.yaml', 'w') as f_n:
    yaml.dump(dict_to_file, f_n, allow_unicode=True, default_flow_style=False)

with open('data.yaml') as f_n:
    f_n_content = yaml.load(f_n, Loader=yaml.FullLoader)
print(f_n_content)
print(dict_to_file == f_n_content)