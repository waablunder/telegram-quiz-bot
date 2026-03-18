from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


def get_main_keyboard():
    """Главная клавиатура бота"""
    keyboard = [
        ['🎮 Играть', '📚 Школьные квизы'],
        ['➕ Создать квиз', '📊 Импорт из Excel'],  # Новая кнопка
        ['🏆 Топ игроков', '❓ Помощь']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_answer_keyboard(options, quiz_code=None):
    """Создает клавиатуру с вариантами ответов и кнопкой остановки"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = []

    # Добавляем варианты ответов
    for i, option in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{i + 1}. {option}", callback_data=f"answer_{i}")])

    # Добавляем кнопку остановки
    keyboard.append([InlineKeyboardButton("⏹ ОСТАНОВИТЬ ТЕСТ", callback_data="stop_quiz")])

    return InlineKeyboardMarkup(keyboard)


def get_quiz_action_keyboard(quiz_code):
    """Клавиатура для действий с квизом"""
    keyboard = [
        [InlineKeyboardButton("▶ Начать квиз", callback_data=f"start_quiz_{quiz_code}")],
        [InlineKeyboardButton("📊 Статистика квиза", callback_data=f"quiz_stats_{quiz_code}")],
        [InlineKeyboardButton("🔗 Поделиться", callback_data=f"share_{quiz_code}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_share_keyboard(quiz_code):
    """Клавиатура для шаринга квиза"""
    keyboard = [
        [InlineKeyboardButton("📤 Отправить другу", switch_inline_query=f"Пройди мой квиз! Код: {quiz_code}")],
        [InlineKeyboardButton("📋 Скопировать код", callback_data=f"copy_{quiz_code}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_my_quizzes_keyboard(quizzes):
    """Клавиатура со списком квизов пользователя"""
    keyboard = []
    for quiz in quizzes:
        # quiz: (id, creator_id, name, description, code, created_at, plays)
        button_text = f"📌 {quiz[2]} (игр: {quiz[6]})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"myquiz_{quiz[0]}")])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)


def get_room_keyboard(room_code):
    """Клавиатура для комнаты"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = [
        [InlineKeyboardButton("🚪 Войти в комнату", callback_data=f"join_room_{room_code}")],
        [InlineKeyboardButton("▶ Начать игру (только создатель)", callback_data=f"start_room_{room_code}")],
        [InlineKeyboardButton("👥 Игроки в комнате", callback_data=f"room_players_{room_code}")],
        [InlineKeyboardButton("🚫 Закрыть комнату", callback_data=f"close_room_{room_code}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_room_answer_keyboard(options, question_index, room_code):
    """Создает клавиатуру для ответов в комнате с кнопкой выхода"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = []

    # Добавляем варианты ответов
    for i, option in enumerate(options):
        keyboard.append([InlineKeyboardButton(
            f"{i + 1}. {option}",
            callback_data=f"room_answer_{question_index}_{i}_{room_code}"
        )])

    # Добавляем кнопку выхода из комнаты
    keyboard.append([InlineKeyboardButton("🚪 Выйти из комнаты", callback_data=f"room_leave_{room_code}")])

    return InlineKeyboardMarkup(keyboard)