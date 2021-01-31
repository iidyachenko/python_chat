"""
 Определить, какие из слов «attribute», «класс», «функция», «type» невозможно записать в байтовом типе.
"""
try:
    b_attribute = b'attribute'
except Exception as exc:
    print("Не удалось записать в байтовом виде", b_attribute)

try:
    b_class = b'класс'
except Exception as exc:
    print("Не удалось записать в байтовом виде", b_attribute)

try:
    b_func = b'функция'
except Exception as exc:
    print("Не удалось записать в байтовом виде", b_attribute)

try:
    b_type = b'type'
except Exception as exc:
    print("Не удалось записать в байтовом виде", b_attribute)

# Невозможно представить в байтовом виде слова написанные на кириллице: "класс" и "функция"
