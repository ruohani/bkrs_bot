from aiogram import types
import requests
from bs4 import BeautifulSoup
import re
from langid import classify


# Удаление пустых строк
def remove_empty_lines(block_content):
    # Создаем переменную, которая делит block_content на отдельные линии
    lines = block_content.splitlines()
    # Создаем массив из строк
    useful_lines = []
    # Перебираем каждую строку и ищем пустую. Если строка не равна пустоте, то добавляем в массив
    for line in lines:
        if line != ' ' and line != '':
            useful_lines += [line]
    # Объединяем массив в строки и делаем перенос строки между ними
    block_content = '\n'.join(useful_lines)
    return block_content


# Удаляем ненужные гиперссылки
def remove_href_lines(block_content):
    # Создаем переменную, которая делит block_content на отдельные линии
    lines = block_content.splitlines()
    # Создаем массив из строк
    useful_lines = []
    # Перебираем каждую строку и ищем ту, что начинается с тире. Если строка не начинается с тире, то добавляем в массив
    for line in lines:
        if line[0] != '-':
            useful_lines += [line]
    # Объединяем массив в строки и делаем перенос строки между ними
    block_content = '\n'.join(useful_lines)
    return block_content


# Делаем китайские иероглифы копирующимися
def highlight_chinese_characters(block_content):
    # Создаем массив, который содержит китайские иероглифы из block_content
    imposters = set(re.findall(r'[\u4e00-\u9fff]+', block_content))
    # Выделяем китайские иероглифы особым знаком(`) для вывода копируемого текста с помощью языка разметки Markdown
    for imposter in imposters:
        # Заменяем только первый найденный элемент
        block_content = re.sub(fr"\b{imposter}\b", f"`{imposter}`", block_content, flags=re.IGNORECASE)
    return block_content


async def split_roman_numbers(text, message):
    patterns = r'[IVXLCM]+'
    symbols = re.findall(patterns, text)

    roman_blocks = []

    if len(symbols) == 0:
        roman_blocks = None
        await split_too_much_symbols(roman_blocks, message, str(text))
        return
    else:

        roman_symbols_indexes = []
        for symbol in symbols:
            roman_symbols_indexes += [text.index(str(symbol))]

        symbol_index_last = int()
        roman_symbols_indexes[0] = 0
        for symbol_index_start, symbol_index_end in zip(roman_symbols_indexes[0:], roman_symbols_indexes[1:]):
            roman_blocks.append(text[symbol_index_start:symbol_index_end])
            symbol_index_last = symbol_index_end

        roman_blocks.append(text[symbol_index_last:])

    await split_too_much_symbols(roman_blocks, message, text)


async def split_too_much_symbols(roman_blocks, message, text):
    """
    Данная функция нужна для разделения слишком длинного сообщения (недопустимого) на маленькие (допустимые)

    :param roman_blocks: массив с блоками текста, которые начинаются на римские цифры
    :param message: передаем информацию о сообщении пользователя боту
    :param text: исходный текст на случай если нет блоков с римскими цифрами
    """
    if roman_blocks:
        for text in roman_blocks:
            if len(text) > 4096:
                while len(text) > 4096:

                    # Ищем позицию при учете выделения китайских иероглифов
                    if text[:4096].count('`') % 2:
                        position = text[:4096].rfind('`')
                    else:
                        position = int(4096)

                    await message.reply(text[:position], parse_mode="MARKDOWN")
                    text = text[position:]
            else:
                await message.reply(text, parse_mode="MARKDOWN")
    else:
        await message.reply(text, parse_mode="MARKDOWN")


async def translate_to_chinese(message: types.Message, word):
    """
    Данная функция выполняет перевод строки с русского на китайский

    :param message: передаем информацию о сообщении пользователя боту
    :param word: слово, вводимое пользователем
    """
    url = f"http://bkrs.info/slovo.php?ch={word}"
    # Отправка GET-запроса, по итогу которого мы получаем объект с кодом ответа (200 или 404) и контент страницы
    response = requests.get(url)
    # Проверка статуса ответа
    if response.status_code == 200:
        # Создаем переменную с контентом страницы
        html = BeautifulSoup(response.text, "html.parser")
        # Если нет точного перевода слова, которое ввел пользователь, то выводится блок "в других китайских словах:"
        if html.find("div", {"id": "no-such-word"}):
            try:
                in_ch_words_block = html.find("div", {"id": "xinsheng_fullsearch"})
                in_ch_words_block_content = re.sub(' +', ' ',
                                                   (in_ch_words_block.get_text().replace("•", "").replace("-", "")))
            except:
                await message.reply("Ошибка! Слово не найдено.")
            else:
                await message.reply(in_ch_words_block_content)
        else:
            # Находим нужный блок по классу
            block = html.find(class_="ch_ru")
            # Заменяем знаки, удаляем пустые строки после гиперссылок
            block_content = re.sub(' +', ' ', (block.get_text().replace("•", "")))
            # Удаляем пустые строки
            block_content = remove_empty_lines(block_content)
            # Удаление ненужных гиперссылок
            block_content = remove_href_lines(block_content)
            # Делаем китайские символы копирующимися
            block_content = highlight_chinese_characters(block_content)
            # Делим на разные сообщения
            await split_roman_numbers(block_content, message)

    else:
        await message.reply("Произошла ошибка при запросе.")


async def translate_to_russian(message: types.Message, word):
    """
    Данная функция выполняет перевод строки с китайского на русский

    :param message: передаем информацию о сообщении пользователя боту
    :param word: слово, вводимое пользователем
    """
    url = f"http://bkrs.info/slovo.php?ch={word}"
    # Отправка GET-запроса, по итогу которого мы получаем объект с кодом ответа (200 или 404) и контент страницы
    response = requests.get(url)
    if response.status_code == 200:
        # Создаем переменную с контентом страницы
        html = BeautifulSoup(response.text, "html.parser")
        blocks = html.find_all(class_=["ru", "py"])
        block_content = str()

        # Счетчик для первой уникальной итерации
        counter = True
        for block in blocks:
            block_content += block.get_text().replace("•", "").replace("*", "")
            # Удаляем пустые строки
            block_content = remove_empty_lines(block_content)
            # Удаление ненужных гиперссылок
            block_content = remove_href_lines(block_content)
            # Делаем китайские символы копирующимися
            block_content = highlight_chinese_characters(block_content)
            # Выделяем первый блок (пиньинь) жирным шрифтом и делаем дополнительный перенос строки
            if counter:
                block_content = block_content.replace(block_content, f'*{block_content}*') + '\n \n'
                counter = False
        # Делим на разные сообщения
        await split_roman_numbers(block_content, message)
    else:
        await message.reply("Произошла ошибка при запросе.")


async def main(message: types.Message, word):
    """
    Данная функция определяет язык введенного пользователем слова и вызывает функцию для его перевода

    :param message: передаем информацию о сообщении пользователя боту
    :param word: введенное пользователем слово для перевода
    """

    # Создаем переменную для определения языка введенного слова
    detect_language = classify(word)[0]

    # Делаем так, что бы определялось только между китайским или русским языками
    if detect_language != 'zh':
        detect_language = 'ru'

    # В соответствии с определенным языком, вызывается нужная функция для перевода слова
    if detect_language == 'ru':
        await translate_to_chinese(message, word)
    elif detect_language == 'zh':
        await translate_to_russian(message, word)
    else:
        await message.reply('Пожалуйста, введите слово на китайском или русском языке.')
