import sqlite3
import json
from config import DATABASE_NAME
from datetime import datetime
import random
import string

def generate_room_code():
    """Генерирует уникальный код комнаты"""
    return 'ROOM_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def init_database():
    """Создает все таблицы в базе данных"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            level INTEGER DEFAULT 5,
            rating INTEGER DEFAULT 0,
            games_played INTEGER DEFAULT 0,
            correct_answers INTEGER DEFAULT 0,
            total_answers INTEGER DEFAULT 0
        )
    ''')

    # ТАБЛИЦА КВИЗОВ (пользовательские викторины)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER,
            quiz_name TEXT NOT NULL,
            description TEXT,
            code TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            plays_count INTEGER DEFAULT 0,
            FOREIGN KEY (creator_id) REFERENCES users (user_id)
        )
    ''')

    # ТАБЛИЦА ВОПРОСОВ (для каждого квиза)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            question_text TEXT NOT NULL,
            options TEXT NOT NULL,  -- JSON массив вариантов
            correct_answer TEXT NOT NULL,
            difficulty INTEGER DEFAULT 5,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (quiz_id)
        )
    ''')

    # ТАБЛИЦА РЕЗУЛЬТАТОВ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            quiz_id INTEGER,
            score INTEGER,
            total_questions INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (quiz_id) REFERENCES quizzes (quiz_id)
        )
    ''')
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                room_id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_code TEXT UNIQUE NOT NULL,
                creator_id INTEGER,
                quiz_id INTEGER,
                status TEXT DEFAULT 'waiting',  -- waiting, playing, finished
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                max_players INTEGER DEFAULT 10,
                current_players INTEGER DEFAULT 0,
                FOREIGN KEY (creator_id) REFERENCES users (user_id),
                FOREIGN KEY (quiz_id) REFERENCES quizzes (quiz_id)
            )
        ''')

    # НОВАЯ ТАБЛИЦА ИГРОКОВ В КОМНАТЕ
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS room_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER,
                user_id INTEGER,
                username TEXT,
                first_name TEXT,
                score INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms (room_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

    # НОВАЯ ТАБЛИЦА ОТВЕТОВ В КОМНАТЕ
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS room_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER,
                user_id INTEGER,
                question_index INTEGER,
                answer TEXT,
                is_correct BOOLEAN,
                answer_time REAL,  -- время ответа в секундах
                FOREIGN KEY (room_id) REFERENCES rooms (room_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

    conn.commit()
    conn.close()
    print("✅ База данных инициализирована (с поддержкой комнат)")


# ========== РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ==========

def get_user(user_id):
    """Получает информацию о пользователе"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def create_user(user_id, username, first_name):
    """Создает нового пользователя"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
    ''', (user_id, username, first_name))
    conn.commit()
    conn.close()


def update_user_stats(user_id, correct):
    """Обновляет статистику пользователя"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    if correct:
        cursor.execute('''
            UPDATE users 
            SET correct_answers = correct_answers + 1,
                total_answers = total_answers + 1
            WHERE user_id = ?
        ''', (user_id,))
    else:
        cursor.execute('''
            UPDATE users 
            SET total_answers = total_answers + 1
            WHERE user_id = ?
        ''', (user_id,))

    conn.commit()
    conn.close()


def get_user_stats(user_id):
    """Возвращает статистику пользователя"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT level, rating, games_played, correct_answers, total_answers 
        FROM users WHERE user_id = ?
    ''', (user_id,))

    stats = cursor.fetchone()
    conn.close()

    if stats:
        print(f"📊 Статистика из БД: {stats}")
        return stats
    else:
        print(f"⚠️ Пользователь {user_id} не найден в БД")
        return (5, 0, 0, 0, 0)


# ========== СОЗДАНИЕ КВИЗОВ ==========

def create_quiz(creator_id, quiz_name, description):
    """Создает новый квиз и возвращает код для приглашения друзей"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Генерируем уникальный код
    import random
    import string
    code = 'QUIZ_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    cursor.execute('''
        INSERT INTO quizzes (creator_id, quiz_name, description, code)
        VALUES (?, ?, ?, ?)
    ''', (creator_id, quiz_name, description, code))

    quiz_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return quiz_id, code


def add_question_to_quiz(quiz_id, question_text, options, correct_answer, difficulty=5):
    """Добавляет вопрос в квиз"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    options_json = json.dumps(options, ensure_ascii=False)

    # ИСПРАВЛЕНО: названия столбцов должны соответствовать CREATE TABLE
    cursor.execute('''
        INSERT INTO questions (quiz_id, question_text, options, correct_answer, difficulty)
        VALUES (?, ?, ?, ?, ?)
    ''', (quiz_id, question_text, options_json, correct_answer, difficulty))

    conn.commit()
    conn.close()


def get_quiz_by_code(code):
    """Находит квиз по коду приглашения"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM quizzes WHERE code = ?
    ''', (code,))

    quiz = cursor.fetchone()
    conn.close()
    return quiz


def get_quiz_questions(quiz_id):
    """Получает все вопросы квиза"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM questions WHERE quiz_id = ?
    ''', (quiz_id,))

    questions = cursor.fetchall()
    conn.close()
    return questions


def get_user_quizzes(user_id):
    """Получает все квизы, созданные пользователем"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM quizzes WHERE creator_id = ? ORDER BY created_at DESC
    ''', (user_id,))

    quizzes = cursor.fetchall()
    conn.close()
    return quizzes


def save_quiz_result_with_details(user_id, quiz_id, score, total_questions, correct_answers):
    """Сохраняет результат с детальной статистикой"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    print(
        f"💾 Сохраняем результат: user={user_id}, quiz={quiz_id}, score={score}, correct={correct_answers}/{total_questions}")

    # Сохраняем результат
    cursor.execute('''
        INSERT INTO results (user_id, quiz_id, score, total_questions)
        VALUES (?, ?, ?, ?)
    ''', (user_id, quiz_id, score, total_questions))

    # Обновляем счетчик прохождений квиза
    cursor.execute('''
        UPDATE quizzes SET plays_count = plays_count + 1 WHERE quiz_id = ?
    ''', (quiz_id,))

    # Обновляем статистику пользователя
    cursor.execute('''
        UPDATE users 
        SET rating = rating + ?,
            games_played = games_played + 1,
            correct_answers = correct_answers + ?,
            total_answers = total_answers + ?
        WHERE user_id = ?
    ''', (score, correct_answers, total_questions, user_id))

    conn.commit()

    # ПРОВЕРЯЕМ, ЧТО ПОЛЬЗОВАТЕЛЬ СУЩЕСТВУЕТ
    cursor.execute('''
        SELECT correct_answers, total_answers, games_played, rating 
        FROM users WHERE user_id = ?
    ''', (user_id,))

    new_stats = cursor.fetchone()

    # ЕСЛИ ПОЛЬЗОВАТЕЛЬ НЕ НАЙДЕН - СОЗДАЁМ ЕГО
    if new_stats is None:
        print(f"⚠️ Пользователь {user_id} не найден, создаём...")

        # Получаем информацию о пользователе (имя пока неизвестно)
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, level, rating, games_played, correct_answers, total_answers)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, "unknown", "User", 5, score, 1, correct_answers, total_questions))

        conn.commit()

        # Получаем обновленную статистику
        cursor.execute('''
            SELECT correct_answers, total_answers, games_played, rating 
            FROM users WHERE user_id = ?
        ''', (user_id,))

        new_stats = cursor.fetchone()

    # ТЕПЕРЬ new_stats точно не None
    if new_stats:
        print(
            f"📊 Новая статистика пользователя: правильных={new_stats[0]}, всего={new_stats[1]}, игр={new_stats[2]}, рейтинг={new_stats[3]}")
    else:
        print(f"❌ Не удалось получить статистику пользователя {user_id}")

    conn.close()
    return True


def get_top_players(limit=10):
    """Возвращает топ игроков по рейтингу (ИСПРАВЛЕНО)"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT first_name, username, rating, games_played 
        FROM users 
        WHERE rating > 0 
        ORDER BY rating DESC 
        LIMIT ?
    ''', (limit,))

    top = cursor.fetchall()
    conn.close()

    # Если топ пустой, возвращаем тестовые данные
    if not top:
        return [
            ("Илья", "ilya_quiz", 1500, 5),
            ("Анна", "anna_kviz", 1200, 4),
            ("Максим", "max_bot", 900, 3),
            ("Елена", "elena_quiz", 600, 2),
            ("Дмитрий", "dmitry", 300, 1)
        ]
    return top


def get_quiz_stats(quiz_id):
    """Получает статистику по квизу"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT AVG(score) as avg_score, COUNT(*) as plays
        FROM results WHERE quiz_id = ?
    ''', (quiz_id,))

    stats = cursor.fetchone()
    conn.close()
    return stats


def get_quiz_results(quiz_id):
    """Получает результаты прохождения квиза (для топа по квизу)"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT users.first_name, users.username, results.score, results.date
        FROM results
        JOIN users ON results.user_id = users.user_id
        WHERE results.quiz_id = ?
        ORDER BY results.score DESC
        LIMIT 10
    ''', (quiz_id,))

    results = cursor.fetchall()
    conn.close()
    return results


def create_room(creator_id, quiz_id):
    """Создает новую комнату"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    room_code = generate_room_code()

    cursor.execute('''
        INSERT INTO rooms (room_code, creator_id, quiz_id, status, current_players)
        VALUES (?, ?, ?, ?, ?)
    ''', (room_code, creator_id, quiz_id, 'waiting', 1))

    room_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return room_id, room_code


def get_room_by_code(room_code):
    """Получает информацию о комнате по коду"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM rooms WHERE room_code = ?
    ''', (room_code,))

    room = cursor.fetchone()
    conn.close()
    return room


def get_room_players(room_id):
    """Получает список игроков в комнате"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM room_players WHERE room_id = ? ORDER BY score DESC
    ''', (room_id,))

    players = cursor.fetchall()
    conn.close()
    return players


def update_room_players_count(room_id, count):
    """Обновляет количество игроков в комнате"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE rooms SET current_players = ? WHERE room_id = ?
    ''', (count, room_id))

    conn.commit()
    conn.close()