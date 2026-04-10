import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import create_quiz, add_question_to_quiz, get_user_quizzes, get_quiz_questions, get_quiz_stats

# Состояния для диалога создания квиза
(NAME, DESCRIPTION, QUESTION, OPTIONS, CORRECT_ANSWER, DIFFICULTY, CONFIRM) = range(7)

# Состояния для редактирования квиза
(EDIT_MENU, EDIT_SELECT_QUESTION, EDIT_QUESTION_TEXT, EDIT_OPTIONS, EDIT_CORRECT, EDIT_DIFFICULTY, EDIT_CONFIRM_DELETE) = range(7, 14)

# Состояния для добавления вопроса в существующий квиз
(ADD_QUESTION_DIFF, ADD_QUESTION_TEXT, ADD_QUESTION_OPTIONS, ADD_QUESTION_CORRECT) = range(14, 18)


class QuizCreator:
    """Класс для создания пользовательских квизов"""

    def __init__(self, user_id):
        self.user_id = user_id
        self.quiz_id = None
        self.quiz_name = ""
        self.description = ""
        self.questions = []
        self.current_question = {}

    def start_creation(self, quiz_name, description):
        """Начинает создание нового квиза"""
        self.quiz_name = quiz_name
        self.description = description
        self.questions = []

    def add_question(self, question_text, options, correct_answer, difficulty):
        """Добавляет вопрос в текущий квиз"""
        self.questions.append({
            'text': question_text,
            'options': options,
            'correct': correct_answer,
            'difficulty': difficulty
        })

    def save_to_database(self, creator_id):
        """Сохраняет квиз в базу данных"""
        # Создаем квиз
        quiz_id, code = create_quiz(creator_id, self.quiz_name, self.description)
        self.quiz_id = quiz_id

        # Добавляем все вопросы
        for q in self.questions:
            add_question_to_quiz(
                quiz_id,
                q['text'],
                q['options'],
                q['correct'],
                q['difficulty']
            )

        return code


# ========== ОБРАБОТЧИКИ ДЛЯ СОЗДАНИЯ КВИЗА ==========

async def create_quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс создания квиза"""
    # Устанавливаем флаг, что пользователь начал создание квиза
    context.user_data['creating_quiz'] = True

    await update.message.reply_text(
        "📝 **Создание нового квиза**\n\n"
        "Придумай название для своего квиза (например: 'Викторина о фильмах', 'География для друзей'):",
        parse_mode='Markdown'
    )
    return NAME


async def create_quiz_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает название квиза"""
    print(f"🔍 create_quiz_name вызвана, текст: {update.message.text}")  # отладка
    context.user_data['quiz_name'] = update.message.text
    await update.message.reply_text(
        "📝 Теперь напиши описание квиза (о чем он, для кого, какие темы):"
    )
    return DESCRIPTION


async def add_question_to_quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает добавление вопроса в существующий квиз"""
    query = update.callback_query
    await query.answer()

    quiz_id = int(query.data.replace('add_question_', ''))
    context.user_data['editing_quiz_id'] = quiz_id

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = [
        [InlineKeyboardButton("⭐ Легкий (1-3)", callback_data="add_q_diff_3")],
        [InlineKeyboardButton("⭐⭐ Средний (4-7)", callback_data="add_q_diff_6")],
        [InlineKeyboardButton("⭐⭐⭐ Сложный (8-10)", callback_data="add_q_diff_9")],
        [InlineKeyboardButton("🔙 Отмена", callback_data=f"edit_quiz_{quiz_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "➕ Добавление вопроса\n\nВыбери сложность вопроса:",
        reply_markup=reply_markup
    )
    return ADD_QUESTION_DIFF


async def add_question_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет сложность и запрашивает текст вопроса"""
    query = update.callback_query
    await query.answer()

    difficulty_map = {
        'add_q_diff_3': 3,
        'add_q_diff_6': 6,
        'add_q_diff_9': 9
    }

    context.user_data['new_question_diff'] = difficulty_map.get(query.data, 5)

    await query.edit_message_text(
        "❓ Напиши текст вопроса:"
    )
    return ADD_QUESTION_TEXT


async def add_question_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает текст вопроса"""
    context.user_data['new_question_text'] = update.message.text

    await update.message.reply_text(
        "📋 Напиши варианты ответов через запятую\n"
        "Например: Москва, Санкт-Петербург, Казань, Новосибирск"
    )
    return ADD_QUESTION_OPTIONS


async def add_question_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает варианты ответов"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    options_text = update.message.text
    options = [opt.strip() for opt in options_text.split(',')]

    if len(options) < 2:
        await update.message.reply_text("❌ Нужно минимум 2 варианта! Попробуй еще раз:")
        return ADD_QUESTION_OPTIONS

    context.user_data['new_question_options'] = options

    keyboard = []
    for i, opt in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{i + 1}. {opt}", callback_data=f"add_q_correct_{i}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✅ Выбери правильный ответ:",
        reply_markup=reply_markup
    )
    return ADD_QUESTION_CORRECT


async def add_question_correct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет правильный ответ и добавляет вопрос в БД"""
    import sqlite3
    import json
    from config import DATABASE_NAME

    query = update.callback_query
    await query.answer()

    answer_index = int(query.data.replace('add_q_correct_', ''))
    options = context.user_data['new_question_options']
    correct = options[answer_index]

    quiz_id = context.user_data.get('editing_quiz_id')

    if not quiz_id:
        await query.edit_message_text("❌ Ошибка: не найден ID квиза")
        return

    # Добавляем вопрос в базу данных
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    options_json = json.dumps(options, ensure_ascii=False)

    cursor.execute('''
        INSERT INTO questions (quiz_id, question_text, options, correct_answer, difficulty)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        quiz_id,
        context.user_data['new_question_text'],
        options_json,
        correct,
        context.user_data['new_question_diff']
    ))

    conn.commit()
    conn.close()

    await query.edit_message_text("✅ Вопрос успешно добавлен!")

    # Очищаем временные данные
    context.user_data.pop('new_question_text', None)
    context.user_data.pop('new_question_options', None)
    context.user_data.pop('new_question_diff', None)

    # Возвращаемся к редактированию квиза
    from main import edit_quiz_handler
    fake_update = type('obj', (object,), {
        'callback_query': type('obj', (object,), {
            'data': f"edit_quiz_{quiz_id}",
            'answer': lambda: None,
            'from_user': query.from_user,
            'message': query.message,
            'edit_message_text': query.edit_message_text
        })
    })
    await edit_quiz_handler(fake_update, context)
    return ConversationHandler.END

async def create_quiz_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает описание квиза"""
    context.user_data['quiz_description'] = update.message.text
    context.user_data['questions'] = []

    # Создаем клавиатуру для выбора сложности первого вопроса
    keyboard = [
        [InlineKeyboardButton("⭐ Легкий (1-3)", callback_data="diff_easy")],
        [InlineKeyboardButton("⭐⭐ Средний (4-7)", callback_data="diff_medium")],
        [InlineKeyboardButton("⭐⭐⭐ Сложный (8-10)", callback_data="diff_hard")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "❓ **Добавление первого вопроса**\n\n"
        "Выбери сложность вопроса:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return DIFFICULTY


async def create_question_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор сложности вопроса"""
    query = update.callback_query
    await query.answer()

    difficulty_map = {
        'diff_easy': 3,
        'diff_medium': 6,
        'diff_hard': 9
    }

    context.user_data['current_difficulty'] = difficulty_map.get(query.data, 5)

    await query.edit_message_text(
        "❓ Напиши текст вопроса:"
    )
    return QUESTION


async def create_question_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает текст вопроса"""
    context.user_data['current_question'] = update.message.text

    await update.message.reply_text(
        "📋 Напиши варианты ответов через запятую\n"
        "Например: Москва, Санкт-Петербург, Казань, Новосибирск\n\n"
        "❗ Минимум 2 варианта, максимум 6"
    )
    return OPTIONS


async def create_question_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает варианты ответов"""
    options_text = update.message.text
    options = [opt.strip() for opt in options_text.split(',')]

    if len(options) < 2:
        await update.message.reply_text("❌ Нужно минимум 2 варианта! Попробуй еще раз:")
        return OPTIONS

    if len(options) > 6:
        await update.message.reply_text("❌ Максимум 6 вариантов! Попробуй еще раз:")
        return OPTIONS

    context.user_data['current_options'] = options

    # Показываем варианты для выбора правильного ответа
    keyboard = []
    for i, opt in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{i + 1}. {opt}", callback_data=f"correct_{i}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✅ Выбери **правильный ответ**:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return CORRECT_ANSWER


async def create_correct_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор правильного ответа"""
    query = update.callback_query
    await query.answer()

    # Получаем индекс правильного ответа
    answer_index = int(query.data.replace('correct_', ''))
    options = context.user_data['current_options']
    correct = options[answer_index]

    # Сохраняем вопрос
    question = {
        'text': context.user_data['current_question'],
        'options': options,
        'correct': correct,
        'difficulty': context.user_data['current_difficulty']
    }

    context.user_data['questions'].append(question)

    # Спрашиваем, добавить еще вопрос или завершить
    keyboard = [
        [InlineKeyboardButton("➕ Добавить еще вопрос", callback_data="add_more")],
        [InlineKeyboardButton("✅ Завершить создание", callback_data="finish_quiz")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"✅ Вопрос сохранен!\n"
        f"Всего вопросов: {len(context.user_data['questions'])}\n\n"
        f"Что делаем дальше?",
        reply_markup=reply_markup
    )
    return CONFIRM


async def add_more_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавляет еще один вопрос"""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("⭐ Легкий (1-3)", callback_data="diff_easy")],
        [InlineKeyboardButton("⭐⭐ Средний (4-7)", callback_data="diff_medium")],
        [InlineKeyboardButton("⭐⭐⭐ Сложный (8-10)", callback_data="diff_hard")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"❓ **Вопрос #{len(context.user_data['questions']) + 1}**\n\n"
        f"Выбери сложность:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return DIFFICULTY


async def finish_quiz_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает создание квиза и сохраняет в БД"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    quiz_name = context.user_data['quiz_name']
    description = context.user_data['quiz_description']
    questions = context.user_data['questions']

    # Создаем квиз в базе данных
    creator = QuizCreator(user_id)
    creator.start_creation(quiz_name, description)

    for q in questions:
        creator.add_question(q['text'], q['options'], q['correct'], q['difficulty'])

    code = creator.save_to_database(user_id)

    # Формируем сообщение с результатом
    result_text = (
        f"🎉 **Квиз успешно создан!**\n\n"
        f"📌 Название: {quiz_name}\n"
        f"📝 Описание: {description}\n"
        f"❓ Вопросов: {len(questions)}\n\n"
        f"🔑 **Код для друзей:** `{code}`\n\n"
        f"Отправь этот код друзьям, чтобы они могли пройти твой квиз!\n"
        f"Команда: `/play {code}`"
    )

    await query.edit_message_text(
        result_text,
        parse_mode='Markdown'
    )

    # Очищаем все данные пользователя (включая флаг создания)
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет создание квиза"""
    await update.message.reply_text(
        "❌ Создание квиза отменено. Можешь начать заново командой /create"
    )
    context.user_data.clear()  # Очищаем все данные
    return ConversationHandler.END


