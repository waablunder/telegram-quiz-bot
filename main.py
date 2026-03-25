import logging
import asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes,
    ConversationHandler
)
from config import BOT_TOKEN
from database import (
    init_database, get_user, create_user, get_user_stats,
    get_top_players, get_quiz_by_code, get_quiz_questions,
    get_quiz_stats, get_quiz_results, get_user_quizzes,
    save_quiz_result_with_details
)
from keyboards import (
    get_main_keyboard, get_answer_keyboard, get_quiz_action_keyboard,
    get_share_keyboard, get_my_quizzes_keyboard, get_room_answer_keyboard
)
from quiz_logic import QuizGame
from school_quizzes import add_school_quizzes, get_school_quizzes_list

# ИМПОРТЫ ИЗ QUIZ_CREATOR
from quiz_creator import (
    create_quiz_start, create_quiz_name, create_quiz_description,
    create_question_difficulty, create_question_text,
    create_question_options, create_correct_answer,
    add_more_question, finish_quiz_creation, cancel_creation,
    NAME, DESCRIPTION, DIFFICULTY, QUESTION, OPTIONS,
    CORRECT_ANSWER, CONFIRM
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Хранилище активных игр
active_games = {}
active_timers = {}


# ========== ОСНОВНЫЕ КОМАНДЫ ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user

    # Регистрируем пользователя
    create_user(user.id, user.username, user.first_name)

    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        f"🎯 Что я умею:\n"
        f"• Проходить готовые квизы\n"
        f"• СОЗДАВАТЬ СВОИ КВИЗЫ и делиться с друзьями\n"
        f"• Соревноваться в рейтинге\n\n"
        f"📌 Как создать свой квиз:\n"
        f"1. Нажми /create или кнопку '➕ Создать квиз'\n"
        f"2. Придумай название и описание\n"
        f"3. Добавь вопросы (минимум 3)\n"
        f"4. Получи код и отправь друзьям\n\n"
        f"📌 Как играть с друзьями:\n"
        f"• Введи код квиза: /play КОД\n"
        f"• Например: /play QUIZ_ABC123"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""

    # Создаем клавиатуру для помощи
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = [
        [InlineKeyboardButton("📚 Школьные квизы", callback_data="help_school_quizzes")],
        [InlineKeyboardButton("🎯 Комнатная игра", callback_data="help_room_game")],  # НОВАЯ КНОПКА
        [InlineKeyboardButton("📋 Мои квизы", callback_data="help_my_quizzes")],
        [InlineKeyboardButton("🎮 Как играть", callback_data="help_how_to_play")],
        [InlineKeyboardButton("➕ Как создать квиз", callback_data="help_create_quiz")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    help_text = (
        "❓ Помощь по боту\n\n"
        "Выбери что тебя интересует:"
    )

    await update.message.reply_text(help_text, reply_markup=reply_markup)


async def help_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки в разделе помощи"""
    query = update.callback_query
    await query.answer()

    if query.data == "help_school_quizzes":
        # Перенаправляем на школьные квизы с кнопками
        from school_quizzes import get_school_quizzes_list
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        quizzes = get_school_quizzes_list()

        if not quizzes:
            await query.edit_message_text(
                "📚 Школьные квизы еще не загружены.\n"
                "Попробуй позже или создай свой квиз!"
            )
            return

        # Создаем кнопки для каждого квиза
        keyboard = []
        for quiz in quizzes:
            quiz_id, name, desc, code, plays = quiz
            # Убираем эмодзи из callback_data, но в тексте кнопки оставляем
            keyboard.append([InlineKeyboardButton(f"{name} (👥 {plays})", callback_data=f"play_school_{code}")])

        # Добавляем кнопку "Назад в помощь"
        keyboard.append([InlineKeyboardButton("🔙 Назад в помощь", callback_data="back_to_help")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "📚 **Выбери школьный квиз:**\n\nНажми на кнопку с нужным предметом, чтобы начать игру!",
            reply_markup=reply_markup
        )


    elif query.data == "help_my_quizzes":

        # Перенаправляем на мои квизы

        user_id = query.from_user.id

        from database import get_user_quizzes

        quizzes = get_user_quizzes(user_id)

        if not quizzes:
            await query.edit_message_text(

                "📋 У тебя пока нет созданных квизов.\n"

                "Создай первый с помощью /create или кнопки '➕ Создать квиз' в главном меню!"

            )

            return

        # Создаем кнопки для каждого квиза

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = []

        for quiz in quizzes:
            quiz_id, creator_id, name, desc, code, created, plays = quiz

            # ИСПРАВЛЕНО: используем view_quiz_ вместо myquiz_

            keyboard.append([InlineKeyboardButton(

                f"📌 {name} (👥 {plays})",

                callback_data=f"view_quiz_{quiz_id}"  # БЫЛО: myquiz_{quiz_id}

            )])

        # Добавляем кнопку "Назад в помощь"

        keyboard.append([InlineKeyboardButton("🔙 Назад в помощь", callback_data="back_to_help")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(

            "📋 **Твои квизы:**\n\nВыбери квиз для просмотра:",

            reply_markup=reply_markup,

            parse_mode='Markdown'

        )

    elif query.data == "help_how_to_play":
        text = (
            "🎮 **Как играть:**\n\n"
            "1️⃣ Нажми кнопку '🎮 Играть' или отправь /play\n"
            "2️⃣ Введи код квиза (например: SCHOOL_HISTORY)\n"
            "3️⃣ Отвечай на вопросы, нажимая на кнопки\n"
            "4️⃣ За правильные ответы получаешь очки\n"
            "5️⃣ В конце узнаешь свой результат\n\n"
            "📚 Чтобы посмотреть все школьные квизы, нажми кнопку '📚 Школьные квизы' в главном меню"
        )

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [[InlineKeyboardButton("🔙 Назад в помощь", callback_data="back_to_help")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text, reply_markup=reply_markup)

    elif query.data == "help_create_quiz":
        text = (
            "➕ **Как создать свой квиз:**\n\n"
            "1️⃣ Нажми кнопку '➕ Создать квиз' или отправь /create\n"
            "2️⃣ Придумай название квиза\n"
            "3️⃣ Напиши описание\n"
            "4️⃣ Добавляй вопросы (минимум 3)\n"
            "5️⃣ Для каждого вопроса выбери сложность\n"
            "6️⃣ В конце получишь уникальный код\n\n"
            "🎉 После этого отправь код друзьям, и они смогут пройти твой квиз!"
        )

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [[InlineKeyboardButton("🔙 Назад в помощь", callback_data="back_to_help")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text, reply_markup=reply_markup)

    elif query.data == "help_room_game":
        # Показываем информацию о комнатной игре
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        text = (
            "🎯 **Комнатная игра**\n\n"
            "Это режим, в котором ты можешь играть с друзьями одновременно!\n\n"
            "**Как играть:**\n"
            "1️⃣ Создай комнату командой /room\n"
            "2️⃣ Выбери квиз (свой или школьный)\n"
            "3️⃣ Отправь друзьям код комнаты\n"
            "4️⃣ Друзья заходят командой /join КОД\n"
            "5️⃣ Когда все собрались, создатель нажимает 'Начать'\n"
            "6️⃣ Все отвечают на вопросы одновременно\n"
            "7️⃣ Побеждает тот, кто набрал больше очков!\n\n"
            "**Преимущества:**\n"
            "• Видно, кто быстрее ответил\n"
            "• Бонусные очки за скорость\n"
            "• Общий рейтинг в комнате\n"
            "• До 10 игроков в одной комнате"
        )

        keyboard = [
            [InlineKeyboardButton("🎯 Создать комнату", callback_data="create_room_from_help")],
            [InlineKeyboardButton("🔙 Назад в помощь", callback_data="back_to_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


    elif query.data == "create_room_from_help":
        await query.answer()
        # Получаем ID пользователя
        user_id = query.from_user.id
        # Отправляем команду /room в личку
        await context.bot.send_message(
            chat_id=user_id,
            text="/room"
        )
        # Изменяем текущее сообщение
        await query.edit_message_text(
            "✅ Команда /room отправлена!\n"
            "Нажми на неё, чтобы создать комнату."
        )


    elif query.data == "back_to_help":
        # Возвращаемся в главное меню помощи
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = [
            [InlineKeyboardButton("📚 Школьные квизы", callback_data="help_school_quizzes")],
            [InlineKeyboardButton("🎯 Комнатная игра", callback_data="help_room_game")],  # ДОБАВЛЕНО
            [InlineKeyboardButton("📋 Мои квизы", callback_data="help_my_quizzes")],
            [InlineKeyboardButton("🎮 Как играть", callback_data="help_how_to_play")],
            [InlineKeyboardButton("➕ Как создать квиз", callback_data="help_create_quiz")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "❓ Помощь по боту\n\nВыбери что тебя интересует:",
            reply_markup=reply_markup
        )

# ========== РАБОТА С КВИЗАМИ ==========

async def play_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает квиз по коду"""
    user_id = update.effective_user.id

    # Получаем код из сообщения
    text = update.message.text
    parts = text.split()

    if len(parts) < 2:
        await update.message.reply_text(
            "❌ Укажи код квиза!\n"
            "Пример: /play QUIZ_ABC123"
        )
        return

    code = parts[1].strip().upper()

    # Ищем квиз в базе
    quiz = get_quiz_by_code(code)

    if not quiz:
        await update.message.reply_text(
            "❌ Квиз с таким кодом не найден!\n"
            "Проверь код или создай свой квиз: /create"
        )
        return

    # Сохраняем код квиза в контексте
    context.user_data['current_quiz_code'] = code
    context.user_data['current_quiz_id'] = quiz[0]
    context.user_data['quiz_name'] = quiz[2]

    # Показываем информацию о квизе
    questions = get_quiz_questions(quiz[0])
    stats = get_quiz_stats(quiz[0])

    info_text = (
        f"📌 **{quiz[2]}**\n"
        f"📝 {quiz[3]}\n\n"
        f"👤 Создатель: {quiz[1]}\n"
        f"❓ Вопросов: {len(questions)}\n"
        f"👥 Прохождений: {quiz[6]}\n"
    )

    if stats and stats[0]:
        info_text += f"⭐ Средний счет: {stats[0]:.1f}"

    await update.message.reply_text(
        info_text,
        reply_markup=get_quiz_action_keyboard(code),
        parse_mode='Markdown'
    )


async def start_quiz_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает игру по выбранному квизу"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    code = query.data.replace('start_quiz_', '')

    quiz = get_quiz_by_code(code)
    if not quiz:
        await query.edit_message_text("❌ Квиз не найден!")
        return

    game = QuizGame(user_id, quiz[0])

    if game.total_questions == 0:
        await query.edit_message_text("❌ В этом квизе нет вопросов!")
        return

    active_games[user_id] = game
    question = game.get_current_question()
    game.start_question_timer()

    question_text = (
        f"🎯 {game.get_progress()}\n"
        f"📚 {quiz[2]}\n"
        f"⏱ Осталось: {game.timeout_seconds} сек\n"
        f"Сложность: {'⭐' * question['difficulty']}\n\n"
        f"{question['question']}"
    )

    # ПЕРЕДАЕМ КОД КВИЗА В ФУНКЦИЮ get_answer_keyboard
    await query.edit_message_text(
        question_text,
        reply_markup=get_answer_keyboard(question['options'], code)
    )

    asyncio.create_task(check_timer(user_id, context, game))


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответ на вопрос"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # ЕСЛИ НАЖАЛИ СТОП
    if query.data == "stop_quiz":
        # Останавливаем таймер
        if user_id in active_timers:
            active_timers[user_id].cancel()
            del active_timers[user_id]

        # Удаляем игру
        if user_id in active_games:
            del active_games[user_id]

        # Отправляем сообщение
        await context.bot.send_message(
            chat_id=user_id,
            text="⏹ Тест остановлен.\nМожешь начать новый в любое время!",
            reply_markup=get_main_keyboard()
        )

        # Удаляем сообщение с вопросами
        await query.message.delete()
        return

    # ЕСЛИ ОТВЕТ НА ВОПРОС
    if user_id not in active_games:
        await query.edit_message_text("❌ Игра не найдена!")
        return

    game = active_games[user_id]

    # Отменяем таймер
    if user_id in active_timers:
        active_timers[user_id].cancel()
        del active_timers[user_id]

    # Получаем индекс ответа
    answer_index = int(query.data.replace('answer_', ''))
    options = game.questions[game.current_question_index]['options']
    user_answer = options[answer_index]

    # Проверяем ответ
    is_correct, score = game.check_answer(user_answer)
    current_q = game.questions[game.current_question_index - 1]

    # Показываем результат
    if is_correct:
        result_text = f"✅ Правильно! +{current_q['difficulty'] * 10} очков"
    else:
        result_text = f"❌ Неправильно! Правильный ответ: {current_q['correct_answer']}"

    await query.edit_message_text(result_text)

    # Следующий вопрос или завершение
    if game.is_finished():
        # Получаем результаты
        results = game.get_results()

        # Сохраняем результат
        save_quiz_result_with_details(
            user_id,
            game.quiz_id,
            results['score'],
            results['total'],
            results['correct']
        )

        # КРАСИВЫЙ ВЫВОД РЕЗУЛЬТАТОВ (как было раньше)
        final_text = (
            f"🎉 Квиз завершен!\n\n"
            f"📊 Твой результат:\n"
            f"• Очки: {results['score']}\n"
            f"• Правильных ответов: {results['correct']} из {results['total']}\n"
            f"• Точность: {results['percentage']}%\n\n"
            f"✅ Результат сохранен!"
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=final_text,
            reply_markup=get_main_keyboard()
        )

        del active_games[user_id]
    else:
        # Следующий вопрос
        next_q = game.get_current_question()
        game.start_question_timer()

        question_text = (
            f"🎯 {game.get_progress()}\n"
            f"⏱ Осталось: {game.timeout_seconds} сек\n"
            f"Сложность: {'⭐' * next_q['difficulty']}\n\n"
            f"{next_q['question']}"
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=question_text,
            reply_markup=get_answer_keyboard(next_q['options'])
        )

        # Новый таймер
        task = asyncio.create_task(simple_timer(user_id, context, game))
        active_timers[user_id] = task


async def simple_timer(user_id: int, context: ContextTypes.DEFAULT_TYPE, game):
    """Простой таймер"""
    try:
        await asyncio.sleep(game.timeout_seconds)

        # Проверяем, активна ли еще игра
        if user_id not in active_games:
            return

        if active_games[user_id] != game:
            return

        if game.current_question_index >= len(game.questions):
            return

        # Время вышло
        current_q = game.questions[game.current_question_index]
        await context.bot.send_message(
            user_id,
            f"⏱ Время вышло!\nПравильный ответ: {current_q['correct_answer']}"
        )

        game.current_question_index += 1

        if game.is_finished():
            results = game.get_results()
            save_quiz_result_with_details(
                user_id, game.quiz_id, results['score'],
                results['total'], results['correct']
            )

            final_text = (
                f"🎉 Квиз завершен!\n\n"
                f"📊 Твой результат:\n"
                f"• Очки: {results['score']}\n"
                f"• Правильных ответов: {results['correct']} из {results['total']}\n"
                f"• Точность: {results['percentage']}%\n\n"
                f"✅ Результат сохранен!"
            )

            await context.bot.send_message(
                user_id,
                final_text,
                reply_markup=get_main_keyboard()
            )
            del active_games[user_id]
            if user_id in active_timers:
                del active_timers[user_id]
        else:
            next_q = game.get_current_question()
            game.start_question_timer()

            question_text = (
                f"🎯 {game.get_progress()}\n"
                f"⏱ Осталось: {game.timeout_seconds} сек\n"
                f"Сложность: {'⭐' * next_q['difficulty']}\n\n"
                f"{next_q['question']}"
            )

            await context.bot.send_message(
                user_id,
                question_text,
                reply_markup=get_answer_keyboard(next_q['options'])
            )

            task = asyncio.create_task(simple_timer(user_id, context, game))
            active_timers[user_id] = task

    except asyncio.CancelledError:
        # Таймер отменен - ничего не делаем
        pass
    except Exception as e:
        print(f"Ошибка в таймере: {e}")

def get_quiz_by_code_from_id(quiz_id):
    """Получает код квиза по его ID"""
    import sqlite3
    from config import DATABASE_NAME

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM quizzes WHERE quiz_id = ?", (quiz_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    return None
# ========== СТАТИСТИКА И РЕЙТИНГ ==========

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику пользователя"""
    user_id = update.effective_user.id
    stats = get_user_stats(user_id)

    if stats:
        level, rating, games, correct, total = stats
        accuracy = int(correct / total * 100) if total > 0 else 0

        stats_text = (
            f"📊 **Твоя статистика:**\n\n"
            f"🎮 Сыграно игр: {games}\n"
            f"✅ Правильных ответов: {correct}\n"
            f"❌ Неправильных: {total - correct}\n"
            f"📈 Точность: {accuracy}%\n"
            f"🏆 Рейтинг: {rating}\n"
            f"🎯 Твой уровень: {level}"
        )
    else:
        stats_text = "📊 У тебя пока нет статистики. Сыграй первую игру!"

    await update.message.reply_text(stats_text)


async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает топ игроков"""
    top_players = get_top_players()

    if top_players:
        top_text = "🏆 **Топ игроков:**\n\n"
        for i, (name, username, rating, games) in enumerate(top_players, 1):
            name_display = name or (username or "Аноним")
            top_text += f"{i}. {name_display} — {rating} очков ({games} игр)\n"
    else:
        top_text = "🏆 Пока нет игроков в топе. Стань первым!"

    await update.message.reply_text(top_text, parse_mode='Markdown')


async def school_quizzes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список системных квизов с кнопками для выбора"""
    from school_quizzes import get_school_quizzes_list
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    quizzes = get_school_quizzes_list()

    if not quizzes:
        await update.message.reply_text(
            "📚 Системные квизы еще не загружены.\n"
            "Напиши администратору или попробуй позже."
        )
        return

    # Создаем кнопки для каждого квиза
    keyboard = []
    for quiz in quizzes:
        quiz_id, name, desc, code, plays = quiz
        # Убираем эмодзи из названия для кнопки
        clean_name = name.replace("📜 ", "").replace("⚽ ", "").replace("➕ ", "").replace("📚 ", "").replace("🌍 ",
                                                                                                          "").replace(
            "⚡ ", "")
        keyboard.append([InlineKeyboardButton(f"{name} (👥 {plays})", callback_data=f"play_school_{code}")])

    # Добавляем кнопку закрытия
    keyboard.append([InlineKeyboardButton("❌ Закрыть", callback_data="close_school_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "📚 **Выбери школьный квиз:**\n\n"
        "Нажми на кнопку с нужным предметом, чтобы начать игру!"
    )

    await update.message.reply_text(text, reply_markup=reply_markup)


async def play_school_quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запускает школьный квиз по нажатию кнопки"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    code = query.data.replace('play_school_', '')

    quiz = get_quiz_by_code(code)
    if not quiz:
        await query.edit_message_text("❌ Квиз не найден!")
        return

    game = QuizGame(user_id, quiz[0])
    if game.total_questions == 0:
        await query.edit_message_text("❌ В этом квизе нет вопросов!")
        return

    active_games[user_id] = game
    question = game.get_current_question()
    game.start_question_timer()

    question_text = (
        f"🎯 {game.get_progress()}\n"
        f"⏱ Осталось: {game.timeout_seconds} сек\n"
        f"Сложность: {'⭐' * question['difficulty']}\n\n"
        f"{question['question']}"
    )

    await query.edit_message_text(
        question_text,
        reply_markup=get_answer_keyboard(question['options'])
    )

    # Запускаем таймер
    task = asyncio.create_task(simple_timer(user_id, context, game))
    active_timers[user_id] = task


async def check_timer(user_id: int, context: ContextTypes.DEFAULT_TYPE, game):
    """Проверяет таймер и завершает вопрос при истечении времени"""
    try:
        # Ждем указанное количество секунд
        await asyncio.sleep(game.timeout_seconds)

        # ПРОВЕРЯЕМ, АКТИВНА ЛИ ЕЩЕ ИГРА (МОГЛИ ОСТАНОВИТЬ)
        if user_id not in active_games:
            return

        # Получаем актуальную игру
        current_game = active_games.get(user_id)
        if current_game != game:
            return

        # Проверяем, не ответил ли пользователь уже
        if game.current_question_index >= len(game.questions):
            return

        # Получаем текущий вопрос
        current_q = game.questions[game.current_question_index]

        # Отправляем сообщение о таймауте
        await context.bot.send_message(
            chat_id=user_id,
            text=f"⏱ Время вышло!\nПравильный ответ: {current_q['correct_answer']}"
        )

        # Увеличиваем индекс вопроса
        game.current_question_index += 1

        # Проверяем, завершена ли игра
        if game.is_finished():
            # Завершаем игру
            results = game.get_results()

            save_quiz_result_with_details(
                user_id,
                game.quiz_id,
                results['score'],
                results['total'],
                results['correct']
            )

            final_text = (
                f"🎉 Квиз завершен!\n\n"
                f"📊 Твой результат:\n"
                f"• Очки: {results['score']}\n"
                f"• Правильных ответов: {results['correct']} из {results['total']}\n"
                f"• Точность: {results['percentage']}%\n\n"
                f"✅ Результат сохранен!"
            )

            await context.bot.send_message(
                chat_id=user_id,
                text=final_text,
                reply_markup=get_main_keyboard()
            )

            del active_games[user_id]
            if user_id in active_timers:
                del active_timers[user_id]
        else:
            # Следующий вопрос
            next_q = game.get_current_question()
            game.start_question_timer()

            # Получаем код квиза
            quiz_code = None
            try:
                conn = sqlite3.connect('quiz_bot.db')
                cursor = conn.cursor()
                cursor.execute("SELECT code FROM quizzes WHERE quiz_id = ?", (game.quiz_id,))
                result = cursor.fetchone()
                conn.close()
                if result:
                    quiz_code = result[0]
            except:
                pass

            question_text = (
                f"🎯 {game.get_progress()}\n"
                f"⏱ Осталось: {game.timeout_seconds} сек\n"
                f"Сложность: {'⭐' * next_q['difficulty']}\n\n"
                f"{next_q['question']}"
            )

            await context.bot.send_message(
                chat_id=user_id,
                text=question_text,
                reply_markup=get_answer_keyboard(next_q['options'], quiz_code)
            )

            # Запускаем новый таймер
            if user_id in active_timers:
                del active_timers[user_id]
            new_task = asyncio.create_task(check_timer(user_id, context, game))
            active_timers[user_id] = new_task

    except asyncio.CancelledError:
        print(f"Таймер для пользователя {user_id} отменен")
    except Exception as e:
        print(f"Ошибка в таймере: {e}")

async def close_school_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Закрывает меню школьных квизов"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📚 Меню школьных квизов закрыто.\n"
        "Чтобы открыть снова, нажми '📚 Школьные квизы' в меню снизу."
    )


async def add_question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает добавление вопроса"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    query = update.callback_query
    await query.answer()

    quiz_id = int(query.data.replace('add_question_', ''))
    context.user_data['adding_to_quiz'] = quiz_id

    keyboard = [
        [InlineKeyboardButton("⭐ Легкий", callback_data="set_diff_3")],
        [InlineKeyboardButton("⭐⭐ Средний", callback_data="set_diff_6")],
        [InlineKeyboardButton("⭐⭐⭐ Сложный", callback_data="set_diff_9")],
        [InlineKeyboardButton("🔙 Отмена", callback_data=f"edit_quiz_{quiz_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "➕ Добавление вопроса\n\n"
        "Сначала выбери сложность:",
        reply_markup=reply_markup
    )


async def set_difficulty_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет сложность"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    query = update.callback_query
    await query.answer()

    difficulty_map = {
        'set_diff_3': 3,
        'set_diff_6': 6,
        'set_diff_9': 9
    }

    context.user_data['new_question_diff'] = difficulty_map.get(query.data, 5)

    await query.edit_message_text(
        "❓ Напиши текст вопроса:"
    )
    # Здесь мы не возвращаем состояние, просто ждем следующее сообщение


async def get_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает варианты ответов"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    options_text = update.message.text
    options = [opt.strip() for opt in options_text.split(',')]

    if len(options) < 2:
        await update.message.reply_text("❌ Нужно минимум 2 варианта! Попробуй еще раз:")
        return

    context.user_data['new_question_options'] = options

    keyboard = []
    for i, opt in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{i + 1}. {opt}", callback_data=f"select_correct_{i}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✅ Выбери правильный ответ:",
        reply_markup=reply_markup
    )


async def get_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает варианты ответов"""
    options_text = update.message.text
    options = [opt.strip() for opt in options_text.split(',')]

    if len(options) < 2:
        await update.message.reply_text("❌ Нужно минимум 2 варианта! Попробуй еще раз:")
        return "WAITING_OPTIONS"

    context.user_data['new_question_options'] = options

    # Показываем варианты для выбора правильного ответа
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = []
    for i, opt in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{i + 1}. {opt}", callback_data=f"select_correct_{i}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✅ Выбери правильный ответ:",
        reply_markup=reply_markup
    )
    return "WAITING_CORRECT"


async def select_correct_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет правильный ответ"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    query = update.callback_query
    await query.answer()

    answer_index = int(query.data.replace('select_correct_', ''))
    options = context.user_data['new_question_options']
    correct = options[answer_index]

    quiz_id = context.user_data.get('adding_to_quiz')

    if not quiz_id:
        await query.edit_message_text("❌ Ошибка: не найден ID квиза")
        return

    # Добавляем вопрос в базу данных
    import json
    conn = sqlite3.connect('quiz_bot.db')
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

    # Очищаем данные
    context.user_data.pop('new_question_text', None)
    context.user_data.pop('new_question_options', None)
    context.user_data.pop('new_question_diff', None)
    context.user_data.pop('adding_to_quiz', None)

    # Возвращаемся к редактированию
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


async def delete_question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет вопрос"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    query = update.callback_query
    await query.answer()

    question_id = int(query.data.replace('delete_question_', ''))

    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT quiz_id FROM questions WHERE question_id = ?", (question_id,))
    result = cursor.fetchone()

    if not result:
        await query.edit_message_text("❌ Вопрос не найден!")
        return

    quiz_id = result[0]

    cursor.execute("DELETE FROM questions WHERE question_id = ?", (question_id,))
    conn.commit()
    conn.close()

    await query.edit_message_text("✅ Вопрос удален!")

    # Возвращаемся к редактированию
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


async def edit_quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню редактирования квиза"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    query = update.callback_query
    await query.answer()

    quiz_id = int(query.data.replace('edit_quiz_', ''))
    context.user_data['editing_quiz_id'] = quiz_id

    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT quiz_name FROM quizzes WHERE quiz_id = ?", (quiz_id,))
    result = cursor.fetchone()

    if not result:
        await query.edit_message_text("❌ Квиз не найден!")
        return

    quiz_name = result[0]

    cursor.execute("SELECT question_id, question_text FROM questions WHERE quiz_id = ?", (quiz_id,))
    questions = cursor.fetchall()
    conn.close()

    # УБИРАЕМ МАРКДАУН
    text = f"✏️ Редактирование квиза: {quiz_name}\n\n"

    keyboard = [
        [InlineKeyboardButton("➕ Добавить вопрос", callback_data=f"add_question_{quiz_id}")],
    ]

    if questions:
        text += "Вопросы:\n"
        for i, q in enumerate(questions, 1):
            text += f"{i}. {q[1][:40]}...\n"
            keyboard.append([InlineKeyboardButton(
                f"❌ Удалить вопрос {i}",
                callback_data=f"delete_question_{q[0]}"
            )])
    else:
        text += "В этом квизе пока нет вопросов.\n"

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"view_quiz_{quiz_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    # УБИРАЕМ parse_mode='Markdown'
    await query.edit_message_text(
        text,
        reply_markup=reply_markup
    )


async def view_quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает детали квиза"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    query = update.callback_query
    await query.answer()

    quiz_id = int(query.data.replace('view_quiz_', ''))

    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT quiz_name, description, code, plays_count FROM quizzes WHERE quiz_id = ?", (quiz_id,))
    quiz_info = cursor.fetchone()

    cursor.execute("SELECT question_id, question_text, difficulty FROM questions WHERE quiz_id = ?", (quiz_id,))
    questions = cursor.fetchall()
    conn.close()

    if not quiz_info:
        await query.edit_message_text("❌ Квиз не найден!")
        return

    quiz_name, description, code, plays = quiz_info

    # УБИРАЕМ ВСЕ МАРКДАУН - используем обычный текст
    text = (
        f"📌 {quiz_name}\n"
        f"📝 {description}\n"
        f"🔑 Код: {code}\n"
        f"👥 Сыграно: {plays} раз\n"
        f"❓ Вопросов: {len(questions)}\n\n"
    )

    if questions:
        text += "Вопросы:\n"
        for i, q in enumerate(questions, 1):
            text += f"{i}. {q[1][:50]}... (сложность: {q[2]})\n"

    keyboard = [
        [InlineKeyboardButton("✏️ Редактировать этот квиз", callback_data=f"edit_quiz_{quiz_id}")],
        [InlineKeyboardButton("🔙 Назад к списку", callback_data="back_to_myquizzes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # УБИРАЕМ parse_mode='Markdown'
    await query.edit_message_text(
        text,
        reply_markup=reply_markup
    )

# ========== УПРАВЛЕНИЕ КВИЗАМИ ПОЛЬЗОВАТЕЛЯ ==========

async def my_quizzes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает квизы, созданные пользователем"""
    user_id = update.effective_user.id
    quizzes = get_user_quizzes(user_id)

    if not quizzes:
        await update.message.reply_text(
            "📋 У тебя пока нет созданных квизов.\n"
            "Создай первый: /create"
        )
        return

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = []
    for quiz in quizzes:
        quiz_id, creator_id, name, desc, code, created, plays = quiz
        # Кнопка для просмотра
        keyboard.append([InlineKeyboardButton(
            f"📌 {name} (👥 {plays})",
            callback_data=f"view_quiz_{quiz_id}"
        )])
        # Кнопка для редактирования
        keyboard.append([InlineKeyboardButton(
            f"✏️ Редактировать {name}",
            callback_data=f"edit_quiz_{quiz_id}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📋 Твои квизы:\n\nНажми на квиз для просмотра или на ✏️ для редактирования:",
        reply_markup=reply_markup
    )


async def share_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает информацию для шаринга квиза"""
    query = update.callback_query
    await query.answer()

    code = query.data.replace('share_', '')

    share_text = (
        f"🔗 **Поделись квизом с друзьями!**\n\n"
        f"📌 Код квиза: `{code}`\n\n"
        f"Отправь друзьям этот код, они смогут пройти квиз командой:\n"
        f"`/play {code}`"
    )

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=f"myquiz_{context.user_data.get('last_quiz_id', 0)}")]]

    await query.edit_message_text(
        share_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def copy_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка копирования кода"""
    query = update.callback_query
    await query.answer()

    code = query.data.replace('copy_', '')
    await query.edit_message_text(
        f"📋 Код скопирован: `{code}`\n\nОтправь его друзьям!",
        parse_mode='Markdown'
    )


async def back_to_myquizzes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к списку квизов"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    quizzes = get_user_quizzes(user_id)

    keyboard = []
    for quiz in quizzes:
        quiz_id, creator_id, name, desc, code, created, plays = quiz
        keyboard.append([InlineKeyboardButton(
            f"📌 {name} (👥 {plays})",
            callback_data=f"view_quiz_{quiz_id}"
        )])
        keyboard.append([InlineKeyboardButton(
            f"✏️ Редактировать {name}",
            callback_data=f"edit_quiz_{quiz_id}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "📋 Твои квизы:",
        reply_markup=reply_markup
    )


# ========== ОБРАБОТКА СООБЩЕНИЙ ==========

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик обычных сообщений"""
    if 'import_questions' in context.user_data:
        # Если данные есть, но пользователь не в процессе импорта (не ждёт название)
        if context.user_data.get('import_step') != 'waiting_name':
            context.user_data.pop('import_questions', None)
            context.user_data.pop('import_step', None)

    if context.user_data and 'creating_quiz' in context.user_data:
        # Если пользователь в процессе создания, но нажал другую кнопку - отменяем создание
        text = update.message.text

        # Список кнопок главного меню
        menu_buttons = ["🎮 Играть", "➕ Создать квиз", "📋 Мои квизы", "📚 Школьные квизы",
                        "📊 Статистика", "🏆 Топ игроков", "❓ Помощь", "📝 Импорт из файла"]

        if text in menu_buttons:
            # Очищаем данные создания квиза
            context.user_data.clear()
            await update.message.reply_text(
                "❌ Создание квиза отменено.",
                reply_markup=get_main_keyboard()
            )

            # Перенаправляем на выбранную кнопку
            if text == "🎮 Играть":
                await update.message.reply_text(
                    "Введи код квиза командой:\n/play КОД\n\nНапример: /play QUIZ_ABC123"
                )
            elif text == "➕ Создать квиз":
                await create_quiz_start(update, context)
            elif text == "📋 Мои квизы":
                await my_quizzes_command(update, context)
            elif text == "📚 Школьные квизы":
                await school_quizzes_command(update, context)
            elif text == "📊 Статистика":
                await stats_command(update, context)
            elif text == "🏆 Топ игроков":
                await top_command(update, context)
            elif text == "❓ Помощь":
                await help_command(update, context)
            elif text == "📝 Импорт из файла":
                await import_file_start(update, context)
            return

    # ДАЛЬШЕ ИДЕТ ОБЫЧНАЯ ОБРАБОТКА СООБЩЕНИЙ
    text = update.message.text

    if text == "🎮 Играть":
        await update.message.reply_text(
            "Введи код квиза командой:\n/play КОД\n\n"
            "Например: /play QUIZ_ABC123"
        )
    elif text == "➕ Создать квиз":
        await create_quiz_start(update, context)
    elif text == "📋 Мои квизы":
        await my_quizzes_command(update, context)
    elif text == "📚 Школьные квизы":
        await school_quizzes_command(update, context)
    elif text == "📊 Статистика":
        await stats_command(update, context)
    elif text == "🏆 Топ игроков":
        await top_command(update, context)
    elif text == "❓ Помощь":
        await help_command(update, context)
    elif text == "📝 Импорт из файла":
        await import_file_start(update, context)
    else:
        # Не выводим никаких сообщений
        pass


async def simple_create_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Очень простая функция создания комнаты"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Игрок"

    # Показываем школьные квизы для выбора
    from school_quizzes import get_school_quizzes_list
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    quizzes = get_school_quizzes_list()

    if not quizzes:
        await update.message.reply_text("❌ Нет доступных квизов!")
        return

    keyboard = []
    for quiz in quizzes:
        quiz_id, name, desc, code, plays = quiz
        # Очищаем название от эмодзи для красоты
        clean_name = name.replace("📜 ", "").replace("⚽ ", "").replace("➕ ", "").replace("📚 ", "").replace("🌍 ",
                                                                                                          "").replace(
            "⚡ ", "")
        keyboard.append([InlineKeyboardButton(f"📌 {clean_name}", callback_data=f"simple_select_{quiz_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎮 **Выбери квиз для комнаты:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def simple_select_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выбирает квиз и создает комнату"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        user_name = query.from_user.first_name or "Игрок"
        quiz_id = int(query.data.replace('simple_select_', ''))

        # Получаем информацию о квизе
        import sqlite3
        conn = sqlite3.connect('quiz_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT quiz_name FROM quizzes WHERE quiz_id = ?", (quiz_id,))
        quiz_name = cursor.fetchone()[0]

        # Получаем вопросы
        cursor.execute(
            "SELECT question_id, question_text, options, correct_answer, difficulty FROM questions WHERE quiz_id = ?",
            (quiz_id,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            await query.edit_message_text("❌ В этом квизе нет вопросов!")
            return

        # Создаем комнату
        from room_game import generate_room_code, SimpleRoom, active_rooms

        room_code = generate_room_code()
        room = SimpleRoom(room_code, user_id, quiz_id, quiz_name)

        # Загружаем вопросы
        questions = []
        for row in rows:
            import json
            questions.append({
                'id': row[0],
                'question': row[1],
                'options': json.loads(row[2]),
                'correct_answer': row[3],
                'difficulty': row[4]
            })

        room.load_questions(questions)
        room.add_player(user_id, user_name)

        # Сохраняем комнату
        active_rooms[room_code] = room

        await query.edit_message_text(
            f"✅ **Комната создана!**\n\n"
            f"📌 Квиз: {quiz_name}\n"
            f"🔑 Код комнаты: `{room_code}`\n"
            f"👥 Игроков: 1\n\n"
            f"Отправь код друзьям. Они могут войти командой:\n"
            f"`/join {room_code}`\n\n"
            f"Когда все соберутся, нажми кнопку ниже:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("▶ НАЧАТЬ ИГРУ", callback_data=f"simple_start_{room_code}")
            ]]),
            parse_mode='Markdown'
        )


async def simple_start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает игру в комнате"""
    query = update.callback_query
    await query.answer()

    room_code = query.data.replace('simple_start_', '')

    from room_game import active_rooms

    if room_code not in active_rooms:
        await query.edit_message_text("❌ Комната не найдена!")
        return

    room = active_rooms[room_code]

    if query.from_user.id != room.creator_id:
        await query.edit_message_text("❌ Только создатель может начать игру!")
        return

    if len(room.players) == 0:
        await query.edit_message_text("❌ В комнате нет игроков!")
        return

    room.start_game()

    # Удаляем сообщение с кнопкой "Начать игру"
    await query.message.delete()

    # Отправляем первый вопрос
    await send_simple_question(context, room_code)

    # Уведомляем создателя
    await context.bot.send_message(
        chat_id=room.creator_id,
        text="🎮 **Игра началась!**\n\nВопросы отправлены всем игрокам. Когда все ответят, следующий вопрос появится автоматически."
    )


async def send_simple_question(context, room_code):
    """Отправляет вопрос всем игрокам в комнате"""
    from room_game import active_rooms
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    if room_code not in active_rooms:
        return

    room = active_rooms[room_code]
    question = room.get_current_question()

    if not question:
        return

    # Клавиатура для ответов
    keyboard = []
    for i, option in enumerate(question['options']):
        keyboard.append([InlineKeyboardButton(
            f"{i + 1}. {option}",
            callback_data=f"simple_answer_{room_code}_{room.current_question}_{i}"
        )])

    # Кнопка выхода
    keyboard.append([InlineKeyboardButton("🚪 Выйти из комнаты", callback_data=f"simple_leave_{room_code}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    question_text = (
        f"❓ **Вопрос {room.current_question + 1} из {room.total_questions}**\n"
        f"Сложность: {'⭐' * question['difficulty']}\n\n"
        f"{question['question']}"
    )

    # Отправляем вопрос всем игрокам
    for player_id in room.players.keys():
        try:
            await context.bot.send_message(
                chat_id=player_id,
                text=question_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Ошибка отправки игроку {player_id}: {e}")


async def simple_answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответы в комнате - с автоматическим переходом"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    # Парсим данные
    if not data.startswith('simple_answer_'):
        return

    rest = data.replace('simple_answer_', '')
    parts = rest.rsplit('_', 2)

    if len(parts) != 3:
        await query.edit_message_text("❌ Ошибка формата ответа")
        return

    room_code = parts[0]

    try:
        question_index = int(parts[1])
        answer_index = int(parts[2])
    except ValueError:
        await query.edit_message_text("❌ Ошибка формата ответа")
        return

    from room_game import active_rooms

    if room_code not in active_rooms:
        await query.edit_message_text("❌ Комната не найдена!")
        return

    room = active_rooms[room_code]

    if room.status != "playing":
        await query.edit_message_text("❌ Игра не активна!")
        return

    if room.current_question != question_index:
        await query.edit_message_text("❌ Вопрос устарел!")
        return

    if user_id not in room.players:
        await query.edit_message_text("❌ Ты не в этой комнате!")
        return

    question = room.questions[question_index]
    options = question['options']

    if answer_index >= len(options):
        await query.edit_message_text("❌ Неверный ответ!")
        return

    # Принимаем ответ
    success, result = room.submit_answer(user_id, answer_index)

    if not success:
        await query.edit_message_text(f"❌ {result}")
        return

    # Показываем результат
    if result['correct']:
        await query.edit_message_text(f"✅ Правильно! +{result['points']} очков")
    else:
        await query.edit_message_text(f"❌ Неправильно! Правильный ответ: {result['correct_answer']}")

    # Проверяем, все ли ответили
    if room.all_answered():
        # Уведомляем всех, что все ответили
        for player_id in room.players.keys():
            try:
                await context.bot.send_message(
                    chat_id=player_id,
                    text="✅ Все ответили! Переходим к следующему вопросу..."
                )
            except:
                pass

        # Ждем 2 секунды
        await asyncio.sleep(2)

        # Переходим к следующему вопросу
        if room.next_question():
            # Отправляем следующий вопрос
            await send_simple_question(context, room_code)
        else:
            # Игра завершена
            await finish_simple_game(context, room_code)


async def simple_leave_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выход из комнаты"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    room_code = query.data.replace('simple_leave_', '')

    from room_game import active_rooms

    if room_code in active_rooms:
        room = active_rooms[room_code]

        if user_id in room.players:
            room.remove_player(user_id)
            await query.edit_message_text(
                "✅ Ты покинул комнату.",
                reply_markup=get_main_keyboard()
            )

            # Если комната пуста - удаляем
            if len(room.players) == 0:
                del active_rooms[room_code]
            else:
                # Уведомляем остальных
                for pid in room.players.keys():
                    try:
                        await context.bot.send_message(
                            chat_id=pid,
                            text=f"👋 Игрок покинул комнату. Осталось: {len(room.players)}"
                        )
                    except:
                        pass
        else:
            await query.edit_message_text("❌ Ты не в комнате!")
    else:
        await query.edit_message_text("❌ Комната не найдена!")


async def simple_join_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Присоединяется к комнате"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Игрок"

    # Получаем код
    text = update.message.text
    parts = text.split()

    if len(parts) < 2:
        await update.message.reply_text("❌ Укажи код комнаты! Пример: /join ROOM_ABCD")
        return

    room_code = parts[1].strip().upper()

    from room_game import active_rooms

    if room_code not in active_rooms:
        await update.message.reply_text("❌ Комната не найдена!")
        return

    room = active_rooms[room_code]

    if room.status != "waiting":
        await update.message.reply_text("❌ Игра в этой комнате уже началась!")
        return

    if len(room.players) >= 10:
        await update.message.reply_text("❌ Комната заполнена!")
        return

    if room.add_player(user_id, user_name):
        await update.message.reply_text(
            f"✅ Ты присоединился к комнате!\n"
            f"📌 Квиз: {room.quiz_name}\n"
            f"👥 Игроков: {len(room.players)}/10\n\n"
            f"Жди, когда создатель начнет игру."
        )

        # Уведомляем создателя
        try:
            await context.bot.send_message(
                chat_id=room.creator_id,
                text=f"👋 Новый игрок: {user_name}\n👥 Всего: {len(room.players)}/10"
            )
        except:
            pass
    else:
        await update.message.reply_text("❌ Не удалось присоединиться к комнате!")



async def finish_simple_game(context, room_code):
    """Завершает игру и показывает результаты"""
    from room_game import active_rooms
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    if room_code not in active_rooms:
        return

    room = active_rooms[room_code]

    # Формируем результаты
    results_text = "🏆 **Игра завершена!**\n\n**Результаты:**\n"

    # Сортируем игроков по очкам
    sorted_players = sorted(
        room.players.items(),
        key=lambda x: x[1]['score'],
        reverse=True
    )

    for i, (player_id, data) in enumerate(sorted_players, 1):
        results_text += f"{i}. {data['name']}: {data['score']} очков (✓{data['correct']})\n"

    # Отправляем результаты всем игрокам
    for player_id in room.players.keys():
        try:
            await context.bot.send_message(
                chat_id=player_id,
                text=results_text,
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )
        except:
            pass

    # Удаляем комнату
    del active_rooms[room_code]


# ========== ИМПОРТ ИЗ ТЕКСТОВОГО ФАЙЛА ==========

async def import_file_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс импорта из текстового файла"""

    await update.message.reply_text(
        "📝 **Импорт вопросов из текстового файла**\n\n"
        "Отправь мне текстовый файл (.txt) с вопросами.\n\n"
        "**Формат файла:**\n"
        "```\n"
        "Вопрос: текст вопроса\n"
        "Вариант1: ответ1\n"
        "Вариант2: ответ2\n"
        "Вариант3: ответ3\n"
        "Вариант4: ответ4\n"
        "Правильный ответ: ответ1\n"
        "Сложность: 1\n"
        "---\n"
        "Вопрос: следующий вопрос...\n"
        "```\n\n"
        "Разделитель между вопросами: `---` (три дефиса)",
        parse_mode='Markdown'
    )


async def handle_text_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает загруженный текстовый файл"""


    import os
    import time
    # ... остальной код ...
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    # Получаем файл
    file = await update.message.document.get_file()

    # Создаем временное имя файла
    temp_filename = f"temp_import_{update.effective_user.id}_{int(time.time())}.txt"

    # Скачиваем файл
    await file.download_to_drive(temp_filename)

    # Читаем файл
    with open(temp_filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Удаляем временный файл
    os.remove(temp_filename)

    # Парсим вопросы
    questions = parse_questions_from_text(content)

    if not questions:
        await update.message.reply_text(
            "❌ Не удалось найти вопросы в файле.\n"
            "Проверь формат: каждый вопрос начинается с 'Вопрос:',\n"
            "варианты с 'Вариант1:', 'Вариант2:', ...\n"
            "В конце каждого вопроса ставь '---'"
        )
        return

    # Сохраняем вопросы в контекст
    context.user_data['import_questions'] = questions
    context.user_data['import_step'] = 'waiting_name'

    # ОТЛАДКА: выводим количество найденных вопросов
    print(f"Найдено вопросов: {len(questions)}")
    for i, q in enumerate(questions):
        print(f"Вопрос {i + 1}: {q['question'][:50]}...")
        print(f"  Варианты: {q['options']}")
        print(f"  Правильный: {q['correct']}")
        print(f"  Сложность: {q['difficulty']}")

    # Спрашиваем название квиза
    await update.message.reply_text(
        f"✅ Найдено {len(questions)} вопросов.\n\n"
        "📝 Придумай название для квиза (или отправь 'пропустить'):"
    )


def parse_questions_from_text(content):
    """Парсит вопросы из текстового файла"""
    questions = []
    blocks = content.split('---')

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        question_data = {}
        options = []

        lines = block.split('\n')

        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                if key == 'Вопрос':
                    question_data['question'] = value
                elif key.startswith('Вариант'):
                    options.append(value)
                elif key == 'Правильный ответ':
                    question_data['correct'] = value
                elif key == 'Сложность':
                    try:
                        question_data['difficulty'] = int(value)
                    except:
                        question_data['difficulty'] = 5

        question_data['options'] = options

        # Проверяем, что все поля есть
        if 'question' in question_data and 'options' in question_data and 'correct' in question_data and 'difficulty' in question_data:
            if len(question_data['options']) >= 2:
                questions.append(question_data)
            else:
                print(f"Ошибка: недостаточно вариантов для вопроса: {question_data.get('question', '???')}")
        else:
            print(f"Ошибка: не все поля заполнены для вопроса: {question_data}")

    return questions


async def process_import_name_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создает квиз из импортированных вопросов"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from database import create_quiz, add_question_to_quiz

    # Проверяем, есть ли вопросы для импорта
    questions = context.user_data.get('import_questions', [])

    if not questions:
        await update.message.reply_text(
            "❌ Нет вопросов для импорта.\n"
            "Сначала отправь файл с вопросами: /importfile"
        )
        return

    text = update.message.text
    quiz_name = None
    if text.lower() != 'пропустить':
        quiz_name = text

    try:
        # Создаем квиз
        quiz_id, quiz_code = create_quiz(
            update.effective_user.id,
            quiz_name or "Импортированный квиз",
            f"Импортировано из текстового файла"
        )

        # Добавляем вопросы
        for q in questions:
            add_question_to_quiz(
                quiz_id,
                q['question'],
                q['options'],
                q['correct'],
                q['difficulty']
            )

        # ОЧИЩАЕМ ДАННЫЕ ТОЛЬКО ПОСЛЕ УСПЕШНОГО СОЗДАНИЯ
        context.user_data.clear()

        # Результат
        keyboard = [[InlineKeyboardButton("▶ Начать квиз", callback_data=f"start_quiz_{quiz_code}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ **Импорт завершен!**\n\n"
            f"📌 Название: {quiz_name or 'Импортированный квиз'}\n"
            f"❓ Вопросов: {len(questions)}\n"
            f"🔑 Код: `{quiz_code}`\n\n"
            f"Можешь поделиться кодом с друзьями или нажать кнопку, чтобы начать!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при создании квиза: {e}")

def main():
    """Главная функция запуска бота"""
    # Инициализируем базу данных
    init_database()

    # Добавляем системные квизы
    add_school_quizzes()

    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # ===== ОБЫЧНЫЕ КОМАНДЫ =====
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("play", play_quiz))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("top", top_command))
    application.add_handler(CommandHandler("myquizzes", my_quizzes_command))
    application.add_handler(CommandHandler("school", school_quizzes_command))
    application.add_handler(CommandHandler("room", simple_create_room))
    application.add_handler(CommandHandler("join", simple_join_command))
    # Команды для импорта
    application.add_handler(CommandHandler("importfile", import_file_start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_text_file))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_import_name_file))


    # ===== ДИАЛОГ СОЗДАНИЯ КВИЗА =====
    from quiz_creator import (
        create_quiz_start, create_quiz_name, create_quiz_description,
        create_question_difficulty, create_question_text,
        create_question_options, create_correct_answer,
        add_more_question, finish_quiz_creation, cancel_creation,
        NAME, DESCRIPTION, DIFFICULTY, QUESTION, OPTIONS,
        CORRECT_ANSWER, CONFIRM,
        IMPORT_WAIT_FILE, IMPORT_CONFIRM
    )

    # ===== ДИАЛОГ СОЗДАНИЯ КВИЗА =====
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("create", create_quiz_start),  # Вот здесь уже есть create_quiz_start
            MessageHandler(filters.Regex('^➕ Создать квиз$'), create_quiz_start)
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_quiz_name)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_quiz_description)],
            DIFFICULTY: [CallbackQueryHandler(create_question_difficulty, pattern='^diff_')],
            QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_question_text)],
            OPTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_question_options)],
            CORRECT_ANSWER: [CallbackQueryHandler(create_correct_answer, pattern='^correct_')],
            CONFIRM: [
                CallbackQueryHandler(add_more_question, pattern='^add_more$'),
                CallbackQueryHandler(finish_quiz_creation, pattern='^finish_quiz$')
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_creation)],
    )
    application.add_handler(conv_handler)

    # ===== CALLBACK-ОБРАБОТЧИКИ =====
    application.add_handler(CallbackQueryHandler(start_quiz_game, pattern='^start_quiz_'))
    application.add_handler(CallbackQueryHandler(play_school_quiz_handler, pattern='^play_school_'))
    application.add_handler(CallbackQueryHandler(close_school_menu_handler, pattern='^close_school_menu$'))
    application.add_handler(CallbackQueryHandler(share_quiz, pattern='^share_'))
    application.add_handler(CallbackQueryHandler(copy_code, pattern='^copy_'))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern='^stop_quiz$'))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern='^answer_'))
    application.add_handler(CallbackQueryHandler(help_callback_handler, pattern='^help_|^back_to_help$'))
    application.add_handler(CallbackQueryHandler(view_quiz_handler, pattern='^view_quiz_'))
    application.add_handler(CallbackQueryHandler(edit_quiz_handler, pattern='^edit_quiz_'))
    application.add_handler(CallbackQueryHandler(add_question_handler, pattern='^add_question_'))
    application.add_handler(CallbackQueryHandler(set_difficulty_handler, pattern='^set_diff_'))
    application.add_handler(CallbackQueryHandler(select_correct_handler, pattern='^select_correct_'))
    application.add_handler(CallbackQueryHandler(delete_question_handler, pattern='^delete_question_'))
    application.add_handler(CallbackQueryHandler(back_to_myquizzes, pattern='^back_to_myquizzes$'))
    application.add_handler(CallbackQueryHandler(simple_select_quiz, pattern='^simple_select_'))
    application.add_handler(CallbackQueryHandler(simple_start_game, pattern='^simple_start_'))
    application.add_handler(CallbackQueryHandler(simple_leave_handler, pattern='^simple_leave_'))
    application.add_handler(CallbackQueryHandler(simple_answer_handler, pattern='^simple_answer_'))
    

    # ===== ОБРАБОТЧИК СООБЩЕНИЙ =====
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    print("🚀 Бот запущен! Нажми Ctrl+C для остановки.")
    application.run_polling()


if __name__ == '__main__':
    # Импортируем sqlite3 для использования в функциях
    import sqlite3

    main()