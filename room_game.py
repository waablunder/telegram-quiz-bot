import random
import string
import time

# Активные комнаты (храним в памяти)
active_rooms = {}


def generate_room_code():
    """Генерирует простой код комнаты"""
    return 'ROOM_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))


class SimpleRoom:
    """Очень простая комната"""

    def __init__(self, room_code, creator_id, quiz_id, quiz_name):
        self.room_code = room_code
        self.creator_id = creator_id
        self.quiz_id = quiz_id
        self.quiz_name = quiz_name
        self.players = {}  # user_id: {"name": имя, "score": 0, "correct": 0}
        self.answered = set()  # Множество ID пользователей, кто ответил на текущий вопрос
        self.status = "waiting"  # waiting, playing, finished
        self.questions = []
        self.current_question = 0
        self.total_questions = 0

    def add_player(self, user_id, name):
        """Добавляет игрока"""
        if user_id not in self.players and len(self.players) < 10:
            self.players[user_id] = {
                "name": name,
                "score": 0,
                "correct": 0
            }
            return True
        return False

    def remove_player(self, user_id):
        """Удаляет игрока"""
        if user_id in self.players:
            del self.players[user_id]
            if user_id in self.answered:
                self.answered.remove(user_id)
            return True
        return False

    def load_questions(self, questions):
        """Загружает вопросы"""
        self.questions = questions
        self.total_questions = len(questions)
        random.shuffle(self.questions)

    def start_game(self):
        """Начинает игру"""
        if self.status == "waiting" and len(self.players) > 0:
            self.status = "playing"
            self.current_question = 0
            self.answered = set()
            return True
        return False

    def get_current_question(self):
        """Возвращает текущий вопрос"""
        if self.current_question < self.total_questions:
            return self.questions[self.current_question]
        return None

    def submit_answer(self, user_id, answer_index):
        """Принимает ответ"""
        if user_id not in self.players:
            return False, "Ты не в комнате"

        if self.status != "playing":
            return False, "Игра не началась"

        # Проверяем, не отвечал ли уже
        if user_id in self.answered:
            return False, "Ты уже ответил на этот вопрос"

        question = self.questions[self.current_question]
        options = question['options']

        if answer_index >= len(options):
            return False, "Неверный ответ"

        user_answer = options[answer_index]
        is_correct = (user_answer == question['correct_answer'])

        # Отмечаем, что пользователь ответил
        self.answered.add(user_id)

        if is_correct:
            points = question['difficulty'] * 10
            self.players[user_id]['score'] += points
            self.players[user_id]['correct'] += 1
            return True, {
                "correct": True,
                "points": points,
                "correct_answer": question['correct_answer']
            }
        else:
            return True, {
                "correct": False,
                "points": 0,
                "correct_answer": question['correct_answer']
            }

    def all_answered(self):
        """Проверяет, все ли ответили на текущий вопрос"""
        return len(self.answered) == len(self.players)

    def next_question(self):
        """Переходит к следующему вопросу"""
        self.current_question += 1
        self.answered = set()  # Очищаем множество ответивших для нового вопроса

        if self.current_question >= self.total_questions:
            self.status = "finished"
            return False
        return True

    def get_leaderboard(self):
        """Возвращает таблицу лидеров"""
        sorted_players = sorted(
            self.players.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        result = []
        for user_id, data in sorted_players:
            result.append({
                "name": data['name'],
                "score": data['score'],
                "correct": data['correct']
            })
        return result