import os
import psycopg2
import json
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL')


def get_connection():
    """Возвращает соединение с базой данных"""
    return psycopg2.connect(DATABASE_URL)


def init_database():
    """Создаёт все таблицы"""
    conn = get_connection()
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            level INTEGER DEFAULT 5,
            rating INTEGER DEFAULT 0,
            games_played INTEGER DEFAULT 0,
            correct_answers INTEGER DEFAULT 0,
            total_answers INTEGER DEFAULT 0
        )
    ''')

    # Таблица квизов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            quiz_id SERIAL PRIMARY KEY,
            creator_id BIGINT,
            quiz_name TEXT NOT NULL,
            description TEXT,
            code TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            plays_count INTEGER DEFAULT 0,
            FOREIGN KEY (creator_id) REFERENCES users (user_id)
        )
    ''')

    # Таблица вопросов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            question_id SERIAL PRIMARY KEY,
            quiz_id INTEGER,
            question_text TEXT NOT NULL,
            options TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            difficulty INTEGER DEFAULT 5,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (quiz_id)
        )
    ''')

    # Таблица результатов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            result_id SERIAL PRIMARY KEY,
            user_id BIGINT,
            quiz_id INTEGER,
            score INTEGER,
            total_questions INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (quiz_id) REFERENCES quizzes (quiz_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ База данных PostgreSQL инициализирована")


def create_user(user_id, username, first_name):
    """Создаёт нового пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, username, first_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING
    ''', (user_id, username, first_name))
    conn.commit()
    conn.close()


def get_user_stats(user_id):
    """Получает статистику пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT level, rating, games_played, correct_answers, total_answers 
        FROM users WHERE user_id = %s
    ''', (user_id,))
    stats = cursor.fetchone()
    conn.close()
    return stats


def create_quiz(creator_id, quiz_name, description):
    """Создаёт новый квиз"""
    import random
    import string
    conn = get_connection()
    cursor = conn.cursor()

    code = 'QUIZ_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    cursor.execute('''
        INSERT INTO quizzes (creator_id, quiz_name, description, code)
        VALUES (%s, %s, %s, %s) RETURNING quiz_id
    ''', (creator_id, quiz_name, description, code))

    quiz_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    return quiz_id, code


def add_question_to_quiz(quiz_id, question_text, options, correct_answer, difficulty=5):
    """Добавляет вопрос в квиз"""
    conn = get_connection()
    cursor = conn.cursor()

    options_json = json.dumps(options, ensure_ascii=False)

    cursor.execute('''
        INSERT INTO questions (quiz_id, question_text, options, correct_answer, difficulty)
        VALUES (%s, %s, %s, %s, %s)
    ''', (quiz_id, question_text, options_json, correct_answer, difficulty))

    conn.commit()
    conn.close()


def get_quiz_by_code(code):
    """Находит квиз по коду"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM quizzes WHERE code = %s', (code,))
    quiz = cursor.fetchone()
    conn.close()
    return quiz


def get_quiz_questions(quiz_id):
    """Получает все вопросы квиза"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM questions WHERE quiz_id = %s', (quiz_id,))
    questions = cursor.fetchall()
    conn.close()
    return questions


def save_quiz_result_with_details(user_id, quiz_id, score, total_questions, correct_answers):
    """Сохраняет результат с детальной статистикой"""
    conn = get_connection()
    cursor = conn.cursor()

    # Сохраняем результат
    cursor.execute('''
        INSERT INTO results (user_id, quiz_id, score, total_questions)
        VALUES (%s, %s, %s, %s)
    ''', (user_id, quiz_id, score, total_questions))

    # Обновляем статистику пользователя
    cursor.execute('''
        UPDATE users 
        SET rating = rating + %s,
            games_played = games_played + 1,
            correct_answers = correct_answers + %s,
            total_answers = total_answers + %s
        WHERE user_id = %s
    ''', (score, correct_answers, total_questions, user_id))

    conn.commit()
    conn.close()
    print(f"✅ Статистика обновлена: пользователь {user_id}, правильных {correct_answers}/{total_questions}")


def get_top_players(limit=10):
    """Возвращает топ игроков"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT first_name, username, rating, games_played 
        FROM users 
        WHERE rating > 0 
        ORDER BY rating DESC 
        LIMIT %s
    ''', (limit,))
    top = cursor.fetchall()
    conn.close()
    return top


def get_user_quizzes(user_id):
    """Получает все квизы пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM quizzes WHERE creator_id = %s ORDER BY created_at DESC
    ''', (user_id,))
    quizzes = cursor.fetchall()
    conn.close()
    return quizzes

def get_quiz_stats(quiz_id):
    """Получает статистику по квизу"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT AVG(score) as avg_score, COUNT(*) as plays
        FROM results WHERE quiz_id = %s
    ''', (quiz_id,))
    stats = cursor.fetchone()
    conn.close()
    return stats

def get_quiz_results(quiz_id):
    """Получает результаты прохождения квиза (топ игроков по этому квизу)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT users.first_name, users.username, results.score, results.date
        FROM results
        JOIN users ON results.user_id = users.user_id
        WHERE results.quiz_id = %s
        ORDER BY results.score DESC
        LIMIT 10
    ''', (quiz_id,))
    results = cursor.fetchall()
    conn.close()
    return results