import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Токен бота
BOT_TOKEN = "8534805469:AAEUY93MrdpUNrfw85hHJsC4Js-EX1OpNKo"

# Если хочешь через .env, раскомментируй эти строки:
# BOT_TOKEN = os.getenv('BOT_TOKEN')
# if not BOT_TOKEN:
#     raise ValueError("Нет токена! Создайте .env файл с BOT_TOKEN")