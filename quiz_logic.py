import json
import random
import sqlite3
from config import DATABASE_NAME


class QuizGame:
    def __init__(self, user_id, quiz_id):
        self.user_id = user_id
        self.quiz_id = quiz_id
        self.score = 0
        self.current_question_index = 0
        self.questions = []
        self.total_questions = 0
        self.correct_answers = 0  # СЧЕТЧИК ПРАВИЛЬНЫХ ОТВЕТОВ
        self.question_start_time = None  # Время начала вопроса
        self.timeout_seconds = 10  # 10 секунд на ответ
        self.load_questions()

    def load_questions(self):
        """Загружает вопросы для данного квиза"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT question_id, question_text, options, correct_answer, difficulty
            FROM questions WHERE quiz_id = ?
        ''', (self.quiz_id,))

        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.questions.append({
                'id': row[0],
                'question': row[1],
                'options': json.loads(row[2]),
                'correct_answer': row[3],
                'difficulty': row[4]
            })

        # Перемешиваем вопросы
        random.shuffle(self.questions)
        self.total_questions = len(self.questions)
        print(f"Загружено {self.total_questions} вопросов для квиза {self.quiz_id}")

    def get_current_question(self):
        """Возвращает текущий вопрос"""
        if self.current_question_index < self.total_questions:
            return self.questions[self.current_question_index]
        return None

    def check_answer(self, user_answer):
        """Проверяет ответ и возвращает результат"""
        if self.current_question_index >= self.total_questions:
            return False, 0

        current_q = self.questions[self.current_question_index]
        is_correct = (user_answer == current_q['correct_answer'])

        if is_correct:
            points = current_q['difficulty'] * 10
            self.score += points
            self.correct_answers += 1  # ИСПРАВЛЕНО

        self.current_question_index += 1
        return is_correct, self.score

    def is_finished(self):
        """Проверяет, завершен ли квиз"""
        return self.current_question_index >= self.total_questions

    def get_progress(self):
        """Возвращает прогресс в виде строки"""
        return f"Вопрос {self.current_question_index + 1} из {self.total_questions}"

    def get_results(self):
        """Возвращает результаты для отображения"""
        return {
            'score': self.score,
            'correct': self.correct_answers,
            'total': self.total_questions,
            'percentage': int(self.correct_answers / self.total_questions * 100) if self.total_questions > 0 else 0
        }

    def start_question_timer(self):
        """Засекает время начала вопроса"""
        import time
        self.question_start_time = time.time()

    def check_timeout(self):
        """Проверяет, не истекло ли время"""
        import time
        if self.question_start_time is None:
            return False
        elapsed = time.time() - self.question_start_time
        return elapsed > self.timeout_seconds

    def get_remaining_time(self):
        """Возвращает оставшееся время в секундах"""
        import time
        if self.question_start_time is None:
            return self.timeout_seconds
        elapsed = time.time() - self.question_start_time
        remaining = max(0, self.timeout_seconds - int(elapsed))
        return remaining