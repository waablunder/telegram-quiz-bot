import sqlite3
import json
from config import DATABASE_NAME

# ========== СИСТЕМНЫЕ КВИЗЫ ПО ШКОЛЬНОЙ ПРОГРАММЕ ==========

SCHOOL_QUIZZES = {
    "history": {
        "name": "📜 История России",
        "description": "Проверь свои знания по истории России от древних времен до современности",
        "category": "История",
        "questions": [
            {
                "question": "В каком году было Крещение Руси?",
                "options": ["988 г.", "862 г.", "1054 г.", "1240 г."],
                "correct": "988 г.",
                "difficulty": 3
            },
            {
                "question": "Кто был первым русским царём?",
                "options": ["Иван Грозный", "Петр I", "Рюрик", "Александр Невский"],
                "correct": "Иван Грозный",
                "difficulty": 4
            },
            {
                "question": "В каком году была Куликовская битва?",
                "options": ["1380 г.", "1242 г.", "1480 г.", "1223 г."],
                "correct": "1380 г.",
                "difficulty": 5
            },
            {
                "question": "Кто основал Санкт-Петербург?",
                "options": ["Петр I", "Екатерина II", "Александр I", "Николай II"],
                "correct": "Петр I",
                "difficulty": 2
            },
            {
                "question": "Какое событие произошло в 1812 году?",
                "options": ["Отечественная война", "Восстание декабристов", "Отмена крепостного права",
                            "Крымская война"],
                "correct": "Отечественная война",
                "difficulty": 4
            },
            {
                "question": "Кто был последним российским императором?",
                "options": ["Николай II", "Александр III", "Николай I", "Александр II"],
                "correct": "Николай II",
                "difficulty": 3
            },
            {
                "question": "В каком году состоялся первый полет человека в космос?",
                "options": ["1961 г.", "1957 г.", "1965 г.", "1975 г."],
                "correct": "1961 г.",
                "difficulty": 2
            },
            {
                "question": "Кто написал 'Повесть временных лет'?",
                "options": ["Нестор Летописец", "Кирилл и Мефодий", "Ярослав Мудрый", "Владимир Мономах"],
                "correct": "Нестор Летописец",
                "difficulty": 6
            },
            {
                "question": "Как называлась первая русская династия князей?",
                "options": ["Рюриковичи", "Романовы", "Гедиминовичи", "Ольговичи"],
                "correct": "Рюриковичи",
                "difficulty": 4
            },
            {
                "question": "В каком году отменили крепостное право?",
                "options": ["1861 г.", "1825 г.", "1905 г.", "1917 г."],
                "correct": "1861 г.",
                "difficulty": 5
            }
        ]
    },

    "sport": {
        "name": "⚽ Спорт",
        "description": "Вопросы о спорте: от футбола до шахмат",
        "category": "Спорт",
        "questions": [
            {
                "question": "Сколько игроков в футбольной команде на поле?",
                "options": ["11", "10", "12", "9"],
                "correct": "11",
                "difficulty": 1
            },
            {
                "question": "Какая страна выиграла ЧМ по футболу в 2018?",
                "options": ["Франция", "Хорватия", "Бразилия", "Германия"],
                "correct": "Франция",
                "difficulty": 2
            },
            {
                "question": "Какой вид спорта называют 'королевой спорта'?",
                "options": ["Легкая атлетика", "Фигурное катание", "Гимнастика", "Плавание"],
                "correct": "Легкая атлетика",
                "difficulty": 3
            },
            {
                "question": "Сколько колец на олимпийском флаге?",
                "options": ["5", "6", "4", "7"],
                "correct": "5",
                "difficulty": 1
            },
            {
                "question": "В каком году прошли первые Олимпийские игры в России?",
                "options": ["1980", "2000", "2014", "1976"],
                "correct": "1980",
                "difficulty": 4
            },
            {
                "question": "Какой хоккейный клуб самый титулованный в России?",
                "options": ["ЦСКА", "Ак Барс", "Салават Юлаев", "Динамо"],
                "correct": "ЦСКА",
                "difficulty": 5
            },
            {
                "question": "Кто самый титулованный шахматист в истории?",
                "options": ["Гарри Каспаров", "Магнус Карлсен", "Бобби Фишер", "Анатолий Карпов"],
                "correct": "Гарри Каспаров",
                "difficulty": 5
            },
            {
                "question": "Сколько весит баскетбольный мяч?",
                "options": ["600-650 г", "500-550 г", "700-750 г", "400-450 г"],
                "correct": "600-650 г",
                "difficulty": 6
            },
            {
                "question": "Какая страна является родиной футбола?",
                "options": ["Англия", "Бразилия", "Италия", "Испания"],
                "correct": "Англия",
                "difficulty": 2
            },
            {
                "question": "Какой вид спорта был единственным на первых Олимпийских играх?",
                "options": ["Бег", "Борьба", "Метание диска", "Прыжки в длину"],
                "correct": "Бег",
                "difficulty": 6
            }
        ]
    },

    "math": {
        "name": "➕ Математика",
        "description": "Задачи и вопросы по математике для всех уровней",
        "category": "Математика",
        "questions": [
            {
                "question": "Сколько будет 7 × 8?",
                "options": ["56", "48", "64", "54"],
                "correct": "56",
                "difficulty": 1
            },
            {
                "question": "Чему равен квадрат гипотенузы?",
                "options": ["Сумме квадратов катетов", "Сумме катетов", "Произведению катетов", "Разности катетов"],
                "correct": "Сумме квадратов катетов",
                "difficulty": 3
            },
            {
                "question": "Сколько градусов в прямом угле?",
                "options": ["90°", "180°", "360°", "45°"],
                "correct": "90°",
                "difficulty": 1
            },
            {
                "question": "Чему равно число Пи (π) с точностью до сотых?",
                "options": ["3,14", "3,15", "3,13", "3,16"],
                "correct": "3,14",
                "difficulty": 2
            },
            {
                "question": "Как найти площадь круга?",
                "options": ["πR²", "2πR", "πD", "R²"],
                "correct": "πR²",
                "difficulty": 4
            },
            {
                "question": "Сколько будет 15% от 200?",
                "options": ["30", "20", "25", "35"],
                "correct": "30",
                "difficulty": 3
            },
            {
                "question": "Чему равен корень из 144?",
                "options": ["12", "14", "16", "18"],
                "correct": "12",
                "difficulty": 2
            },
            {
                "question": "Какое число является простым?",
                "options": ["17", "21", "27", "33"],
                "correct": "17",
                "difficulty": 4
            },
            {
                "question": "Сколько будет 2 в 5 степени?",
                "options": ["32", "16", "64", "128"],
                "correct": "32",
                "difficulty": 3
            },
            {
                "question": "Чему равна производная от x²?",
                "options": ["2x", "x", "2", "x²"],
                "correct": "2x",
                "difficulty": 7
            }
        ]
    },

    "literature": {
        "name": "📚 Литература",
        "description": "Классическая и современная литература",
        "category": "Литература",
        "questions": [
            {
                "question": "Кто написал 'Войну и мир'?",
                "options": ["Лев Толстой", "Федор Достоевский", "Александр Пушкин", "Антон Чехов"],
                "correct": "Лев Толстой",
                "difficulty": 2
            },
            {
                "question": "Какое стихотворение написано А.С. Пушкиным?",
                "options": ["Я помню чудное мгновенье", "Парус", "Бородино", "К Чаадаеву"],
                "correct": "Я помню чудное мгновенье",
                "difficulty": 3
            },
            {
                "question": "Кто автор 'Преступления и наказания'?",
                "options": ["Достоевский", "Тургенев", "Гоголь", "Лермонтов"],
                "correct": "Достоевский",
                "difficulty": 2
            },
            {
                "question": "Как звали главного героя романа 'Евгений Онегин'?",
                "options": ["Евгений Онегин", "Владимир Ленский", "Петр Гринев", "Алексей Вронский"],
                "correct": "Евгений Онегин",
                "difficulty": 1
            },
            {
                "question": "Кто написал 'Ревизора'?",
                "options": ["Гоголь", "Чехов", "Грибоедов", "Островский"],
                "correct": "Гоголь",
                "difficulty": 3
            },
            {
                "question": "Какое произведение написал Михаил Булгаков?",
                "options": ["Мастер и Маргарита", "Доктор Живаго", "Тихий Дон", "Собачье сердце"],
                "correct": "Мастер и Маргарита",
                "difficulty": 4
            },
            {
                "question": "Кто автор 'Горя от ума'?",
                "options": ["Грибоедов", "Фонвизин", "Радищев", "Крылов"],
                "correct": "Грибоедов",
                "difficulty": 5
            },
            {
                "question": "Сколько томов в 'Войне и мире'?",
                "options": ["4", "3", "5", "6"],
                "correct": "4",
                "difficulty": 3
            },
            {
                "question": "Кто написал 'Мертвые души'?",
                "options": ["Гоголь", "Салтыков-Щедрин", "Тургенев", "Гончаров"],
                "correct": "Гоголь",
                "difficulty": 2
            },
            {
                "question": "Какое стихотворение принадлежит Лермонтову?",
                "options": ["Бородино", "Узник", "Анчар", "Деревня"],
                "correct": "Бородино",
                "difficulty": 3
            }
        ]
    },

    "geography": {
        "name": "🌍 География",
        "description": "Столицы, страны, реки и горы мира",
        "category": "География",
        "questions": [
            {
                "question": "Какая самая длинная река в мире?",
                "options": ["Амазонка", "Нил", "Волга", "Миссисипи"],
                "correct": "Амазонка",
                "difficulty": 4
            },
            {
                "question": "Столица Франции?",
                "options": ["Париж", "Лондон", "Берлин", "Рим"],
                "correct": "Париж",
                "difficulty": 1
            },
            {
                "question": "Самая высокая гора в мире?",
                "options": ["Эверест", "Эльбрус", "Килиманджаро", "Монблан"],
                "correct": "Эверест",
                "difficulty": 2
            },
            {
                "question": "Самое глубокое озеро в мире?",
                "options": ["Байкал", "Танганьика", "Виктория", "Каспийское море"],
                "correct": "Байкал",
                "difficulty": 3
            },
            {
                "question": "Сколько океанов на Земле?",
                "options": ["5", "4", "6", "3"],
                "correct": "5",
                "difficulty": 2
            },
            {
                "question": "Столица Австралии?",
                "options": ["Канберра", "Сидней", "Мельбурн", "Брисбен"],
                "correct": "Канберра",
                "difficulty": 5
            },
            {
                "question": "Какая пустыня самая большая в мире?",
                "options": ["Сахара", "Гоби", "Калахари", "Атакама"],
                "correct": "Сахара",
                "difficulty": 3
            },
            {
                "question": "В какой стране находится статуя Христа-Искупителя?",
                "options": ["Бразилия", "Аргентина", "Чили", "Перу"],
                "correct": "Бразилия",
                "difficulty": 4
            },
            {
                "question": "Самое маленькое государство в мире?",
                "options": ["Ватикан", "Монако", "Сан-Марино", "Лихтенштейн"],
                "correct": "Ватикан",
                "difficulty": 4
            },
            {
                "question": "Столица Японии?",
                "options": ["Токио", "Киото", "Осака", "Нагоя"],
                "correct": "Токио",
                "difficulty": 1
            }
        ]
    },

    "physics": {
        "name": "⚡ Физика",
        "description": "Законы физики, формулы и открытия",
        "category": "Физика",
        "questions": [
            {
                "question": "Какой ученый открыл закон всемирного тяготения?",
                "options": ["Ньютон", "Эйнштейн", "Галилей", "Тесла"],
                "correct": "Ньютон",
                "difficulty": 2
            },
            {
                "question": "В чем измеряется сила тока?",
                "options": ["Амперы", "Вольты", "Ватты", "Омы"],
                "correct": "Амперы",
                "difficulty": 2
            },
            {
                "question": "Какая частица имеет положительный заряд?",
                "options": ["Протон", "Электрон", "Нейтрон", "Фотон"],
                "correct": "Протон",
                "difficulty": 3
            },
            {
                "question": "Скорость света в вакууме?",
                "options": ["300 000 км/с", "150 000 км/с", "1 млн км/с", "3 млн км/с"],
                "correct": "300 000 км/с",
                "difficulty": 4
            },
            {
                "question": "Какой закон гласит, что энергия не исчезает?",
                "options": ["Закон сохранения энергии", "Закон Ньютона", "Закон Ома", "Закон Архимеда"],
                "correct": "Закон сохранения энергии",
                "difficulty": 3
            },
            {
                "question": "Кто изобрел радио?",
                "options": ["Попов", "Маркони", "Тесла", "Эдисон"],
                "correct": "Попов",
                "difficulty": 4
            },
            {
                "question": "В чем измеряется давление?",
                "options": ["Паскали", "Ньютоны", "Джоули", "Ватты"],
                "correct": "Паскали",
                "difficulty": 3
            },
            {
                "question": "Какое агрегатное состояние воды при 0°C?",
                "options": ["Лед", "Вода", "Пар", "Туман"],
                "correct": "Лед",
                "difficulty": 1
            },
            {
                "question": "Какой металл самый легкий?",
                "options": ["Литий", "Алюминий", "Магний", "Титан"],
                "correct": "Литий",
                "difficulty": 7
            },
            {
                "question": "Кто создал теорию относительности?",
                "options": ["Эйнштейн", "Ньютон", "Галилей", "Бор"],
                "correct": "Эйнштейн",
                "difficulty": 4
            }
        ]
    }
}


def add_school_quizzes():
    """Добавляет системные квизы в базу данных"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Проверяем, есть ли уже системные квизы
    cursor.execute("SELECT COUNT(*) FROM quizzes WHERE creator_id = 0")
    count = cursor.fetchone()[0]

    if count == 0:
        print("📚 Добавляем системные квизы по школьной программе...")

        for quiz_id, quiz_data in SCHOOL_QUIZZES.items():
            # Добавляем квиз (creator_id = 0 означает системный квиз)
            cursor.execute('''
                INSERT INTO quizzes (creator_id, quiz_name, description, code)
                VALUES (?, ?, ?, ?)
            ''', (0, quiz_data["name"], quiz_data["description"], f"SCHOOL_{quiz_id.upper()}"))

            quiz_db_id = cursor.lastrowid

            # Добавляем вопросы
            for q in quiz_data["questions"]:
                options_json = json.dumps(q["options"], ensure_ascii=False)
                cursor.execute('''
                    INSERT INTO questions (quiz_id, question_text, options, correct_answer, difficulty)
                    VALUES (?, ?, ?, ?, ?)
                ''', (quiz_db_id, q["question"], options_json, q["correct"], q["difficulty"]))

            print(f"  + Добавлен квиз: {quiz_data['name']} ({len(quiz_data['questions'])} вопросов)")

        conn.commit()
        print("✅ Системные квизы успешно добавлены!")
    else:
        print("📚 Системные квизы уже существуют в базе")

    conn.close()


def get_school_quizzes_list():
    """Возвращает список системных квизов"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT quiz_id, quiz_name, description, code, plays_count 
        FROM quizzes 
        WHERE creator_id = 0
        ORDER BY quiz_name
    ''')

    quizzes = cursor.fetchall()
    conn.close()
    return quizzes


def get_quiz_by_category(category_name):
    """Возвращает квиз по названию категории"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT quiz_id, quiz_name, description, code, plays_count 
        FROM quizzes 
        WHERE creator_id = 0 AND quiz_name LIKE ?
        ORDER BY quiz_name
    ''', (f'%{category_name}%',))

    quizzes = cursor.fetchall()
    conn.close()
    return quizzes