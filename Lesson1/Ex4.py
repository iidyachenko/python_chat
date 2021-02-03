"""
4. Преобразовать слова «разработка», «администрирование», «protocol», «standard» из строкового представления в байтовое
и выполнить обратное преобразование (используя методы encode и decode).
"""

str_words = ['разработка', 'администрирование', 'protocol', 'standard']
byte_worlds = []
for word in str_words:
    b_word = word.encode('utf-8')
    print(f'Слово {word} преобразуется в байты UTF-8 как {b_word}')
    byte_worlds.append(b_word)

for word in byte_worlds:
    str_word = word.decode('utf-8')
    print(f'Слово {word} преобразуется обратно в строку как {str_word}')
