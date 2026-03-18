import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import create_quiz, add_question_to_quiz, get_user_quizzes, get_quiz_questions, get_quiz_stats

# Состояния для импорта Excel
(IMPORT_WAIT_FILE, IMPORT_CONFIRM) = range(14, 16)

# Состояния для диалога создания квиза
(NAME, DESCRIPTION, QUESTION, OPTIONS, CORRECT_ANSWER, DIFFICULTY, CONFIRM) = range(7)

# Состояния для редактирования квиза
(EDIT_MENU, EDIT_SELECT_QUESTION, EDIT_QUESTION_TEXT, EDIT_OPTIONS, EDIT_CORRECT, EDIT_DIFFICULTY, EDIT_CONFIRM_DELETE) = range(7, 14)


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
    context.user_data['quiz_name'] = update.message.text

    await update.message.reply_text(
        "📝 Теперь напиши описание квиза (о чем он, для кого, какие темы):"
    )
    return DESCRIPTION


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


async def import_excel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс импорта из Excel"""
    await update.message.reply_text(
        "📊 **Импорт вопросов из Excel**\n\n"
        "Отправь мне Excel файл с вопросами.\n\n"
        "Файл должен содержать колонки:\n"
        "• Вопрос\n"
        "• Вариант1, Вариант2, Вариант3, Вариант4\n"
        "• Правильный ответ\n"
        "• Сложность (от 1 до 10)\n\n"
        "Пример файла можно скачать командой /template",
        parse_mode='Markdown'
    )
    return IMPORT_WAIT_FILE


async def handle_excel_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает загруженный Excel файл"""
    from excel_importer import ExcelImporter

    # Получаем файл
    file = await update.message.document.get_file()

    # Создаем временное имя файла
    import os
    import time
    temp_filename = f"temp_import_{update.effective_user.id}_{int(time.time())}.xlsx"

    # Скачиваем файл
    await file.download_to_drive(temp_filename)

    # Спрашиваем название квиза
    context.user_data['import_file'] = temp_filename
    context.user_data['import_step'] = 'waiting_name'

    await update.message.reply_text(
        "📝 Придумай название для квиза (или отправь 'пропустить' для имени по умолчанию):"
    )
    return IMPORT_CONFIRM


async def process_import_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает название квиза и запускает импорт"""
    from excel_importer import ExcelImporter
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    text = update.message.text
    temp_filename = context.user_data.get('import_file')

    quiz_name = None
    if text.lower() != 'пропустить':
        quiz_name = text

    # Отправляем сообщение о начале импорта
    status_msg = await update.message.reply_text("⏳ Идет импорт вопросов...")

    # Запускаем импорт
    importer = ExcelImporter()
    result, errors = importer.import_from_excel(
        temp_filename,
        update.effective_user.id,
        quiz_name
    )

    # Удаляем временный файл
    import os
    try:
        os.remove(temp_filename)
    except:
        pass

    # Очищаем данные
    context.user_data.pop('import_file', None)
    context.user_data.pop('import_step', None)

    if result:
        # Успешный импорт
        success_text = (
            f"✅ **Импорт завершен!**\n\n"
            f"📌 Квиз: {result['count']} вопросов\n"
            f"🔑 Код: `{result['quiz_code']}`\n\n"
            f"Можешь поделиться кодом с друзьями!"
        )

        keyboard = [[InlineKeyboardButton("▶ Начать квиз", callback_data=f"start_quiz_{result['quiz_code']}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await status_msg.delete()
        await update.message.reply_text(
            success_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        # Если были ошибки, показываем их
        if errors:
            error_text = "⚠️ **Ошибки в некоторых строках:**\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                error_text += f"\n...и еще {len(errors) - 5} ошибок"
            await update.message.reply_text(error_text, parse_mode='Markdown')

    else:
        # Ошибка импорта
        error_text = "❌ **Ошибка импорта:**\n" + "\n".join(errors[:10])
        await status_msg.delete()
        await update.message.reply_text(error_text, parse_mode='Markdown')

    return ConversationHandler.END


async def send_template(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет шаблон Excel файла"""
    from excel_importer import create_sample_excel_template
    import os

    create_sample_excel_template()

    if os.path.exists('template_questions.xlsx'):
        await update.message.reply_document(
            document=open('template_questions.xlsx', 'rb'),
            filename='template_questions.xlsx',
            caption="📊 Шаблон для импорта вопросов\nЗаполни его и отправь мне!"
        )
    else:
        await update.message.reply_text("❌ Не удалось создать шаблон")