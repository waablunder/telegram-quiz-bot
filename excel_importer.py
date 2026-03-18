import pandas as pd
import sqlite3
import json
import os
from config import DATABASE_NAME


class ExcelImporter:
    """Класс для импорта вопросов из Excel"""

    def __init__(self):
        self.errors = []
        self.success_count = 0

    def validate_question(self, row, row_num):
        """Проверяет корректность строки с вопросом"""
        errors = []

        # Проверяем наличие обязательных полей
        if pd.isna(row.get('Вопрос', '')):
            errors.append(f"Строка {row_num}: отсутствует текст вопроса")

        # Проверяем варианты ответов
        options = []
        for i in range(1, 5):
            opt_col = f'Вариант{i}'
            if not pd.isna(row.get(opt_col, '')):
                options.append(str(row[opt_col]))

        if len(options) < 2:
            errors.append(f"Строка {row_num}: нужно минимум 2 варианта ответа")

        # Проверяем правильный ответ
        if pd.isna(row.get('Правильный ответ', '')):
            errors.append(f"Строка {row_num}: не указан правильный ответ")
        else:
            correct = str(row['Правильный ответ'])
            if correct not in options:
                errors.append(f"Строка {row_num}: правильный ответ должен быть одним из вариантов")

        # Проверяем сложность
        if pd.isna(row.get('Сложность', '')):
            errors.append(f"Строка {row_num}: не указана сложность")
        else:
            try:
                diff = int(row['Сложность'])
                if diff < 1 or diff > 10:
                    errors.append(f"Строка {row_num}: сложность должна быть от 1 до 10")
            except:
                errors.append(f"Строка {row_num}: сложность должна быть числом")

        return errors

    def import_from_excel(self, file_path, user_id, quiz_name=None, quiz_description=None):
        """Импортирует вопросы из Excel файла"""
        self.errors = []
        self.success_count = 0

        try:
            # Читаем Excel файл
            df = pd.read_excel(file_path)

            # Проверяем наличие необходимых колонок
            required_columns = ['Вопрос', 'Вариант1', 'Вариант2', 'Вариант3', 'Вариант4', 'Правильный ответ',
                                'Сложность']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                self.errors.append(f"Отсутствуют колонки: {', '.join(missing_columns)}")
                return None, self.errors

            # Если не указано название квиза, берем из имени файла
            if not quiz_name:
                quiz_name = os.path.splitext(os.path.basename(file_path))[0]

            if not quiz_description:
                quiz_description = f"Импортировано из файла {os.path.basename(file_path)}"

            # Создаем квиз в базе данных
            from database import create_quiz
            quiz_id, quiz_code = create_quiz(user_id, quiz_name, quiz_description)

            # Обрабатываем каждую строку
            for index, row in df.iterrows():
                row_num = index + 2  # +2 потому что Excel считает с 1 и первая строка заголовки

                # Валидация
                validation_errors = self.validate_question(row, row_num)
                if validation_errors:
                    self.errors.extend(validation_errors)
                    continue

                # Собираем варианты ответов
                options = []
                for i in range(1, 5):
                    opt_col = f'Вариант{i}'
                    if not pd.isna(row[opt_col]):
                        options.append(str(row[opt_col]))

                # Добавляем вопрос
                from database import add_question_to_quiz
                add_question_to_quiz(
                    quiz_id,
                    str(row['Вопрос']),
                    options,
                    str(row['Правильный ответ']),
                    int(row['Сложность'])
                )

                self.success_count += 1

            if self.success_count == 0:
                # Если ни один вопрос не добавлен, удаляем квиз
                conn = sqlite3.connect(DATABASE_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM quizzes WHERE quiz_id = ?", (quiz_id,))
                conn.commit()
                conn.close()
                return None, self.errors

            return {"quiz_id": quiz_id, "quiz_code": quiz_code, "count": self.success_count}, self.errors

        except Exception as e:
            self.errors.append(f"Ошибка чтения файла: {str(e)}")
            return None, self.errors


def create_sample_excel_template():
    """Создает шаблон Excel файла"""
    import pandas as pd

    data = {
        'Вопрос': ['Столица Франции?', 'Сколько планет в солнечной системе?'],
        'Вариант1': ['Париж', '7'],
        'Вариант2': ['Лондон', '8'],
        'Вариант3': ['Берлин', '9'],
        'Вариант4': ['Мадрид', '10'],
        'Правильный ответ': ['Париж', '8'],
        'Сложность': [1, 2]
    }

    df = pd.DataFrame(data)
    df.to_excel('template_questions.xlsx', index=False)
    print("✅ Шаблон создан: template_questions.xlsx")