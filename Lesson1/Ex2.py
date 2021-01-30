"""
 Каждое из слов «class», «function», «method» записать в байтовом типе без преобразования в последовательность кодов
 (не используя методы encode и decode) и определить тип, содержимое и длину соответствующих переменных.
"""

b_class = b'class'
b_function = b'function'
b_method = b'method'
print(f"Тип поля: {type(b_class)}, значение поля: {b_class}, длина поля: {len(b_class)}")
print(f"Тип поля: {type(b_function)}, значение поля: {b_function}, длина поля: {len(b_function)}")
print(f"Тип поля: {type(b_method)}, значение поля: {b_method}, длина поля: {len(b_method)}")