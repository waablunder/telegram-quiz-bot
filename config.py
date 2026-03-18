import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Проверка, что токен загружен
if not BOT_TOKEN:
    raise ValueError("Нет токена! Создайте .env файл с BOT_TOKEN")

# Настройки базы данных
DATABASE_NAME = 'quiz_bot.db'

# Настройки квиза
QUESTIONS_PER_QUIZ = 10  # Количество вопросов за игру
TIME_PER_QUESTION = 30    # Секунд на ответ