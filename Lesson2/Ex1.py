import csv
import re
import os


def get_data():
    folder_path = os.path.join(os.curdir, 'csv')
    files_list = os.listdir(folder_path)
    main_data = [["Имя файла", "Название ОС","Код продукта", "Изготовитель системы", "Тип системы"]]

    for filename in files_list:
        file_name = os.path.join(folder_path, filename)
        value_list = [filename]
        with open(file_name, 'r', encoding='windows-1251') as file:
            for line in file:
                result = re.match(r'Изготовитель системы|Название ОС|Код продукта|Тип системы', line)
                if result:
                    value_list.append(line[result.end()+1:].strip())
        main_data.append(value_list)
    return main_data


def write_to_csv(filename):
    with open(filename, 'w') as f_n:
        f_n_writer = csv.writer(f_n)
        data = get_data()
        for row in data:
            f_n_writer.writerow(row)


write_to_csv('csv_ex1.csv')