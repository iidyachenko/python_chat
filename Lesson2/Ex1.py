import csv
import re
import os


def get_data():
    folder_path = os.path.join(os.curdir, 'csv')
    files_list = os.listdir(folder_path)
    main_data = [["Название ОС","Код продукта", "Изготовитель системы", "Тип системы"]]
    s_prod_list = []
    os_name_list = []
    os_code_list = []
    os_type_list = []
    for filename in files_list:
        file_name = os.path.join(folder_path, filename)
        with open(file_name, 'r', encoding='windows-1251') as file:
            for line in file:
                result = re.match(r'Изготовитель системы', line)
                if result:
                    s_prod_list.append(line[result.end()+1:].strip())
                result = re.match(r'Название ОС', line)
                if result:
                    os_name_list.append(line[result.end() + 1:].strip())
                result = re.match(r'Код продукта', line)
                if result:
                    os_code_list.append(line[result.end() + 1:].strip())
                result = re.match(r'Тип системы', line)
                if result:
                    os_type_list.append(line[result.end() + 1:].strip())
    for i in range(0, 3):
        main_data.append([])
        main_data[i + 1].append(os_name_list[i])
        main_data[ i + 1].append(os_code_list[i])
        main_data[i + 1].append(s_prod_list[i])
        main_data[i + 1].append(os_type_list[i])
    return main_data


def write_to_csv(filename):
    with open(filename, 'w') as f_n:
        f_n_writer = csv.writer(f_n)
        data = get_data()
        for row in data:
            f_n_writer.writerow(row)


write_to_csv('csv_ex1.csv')