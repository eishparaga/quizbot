import sqlite3

# Функция для подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect('quiz.db')
    conn.row_factory = sqlite3.Row
    return conn

# Функция для добавления вопроса в базу данных
def add_question(question, options, correct_answer):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO questions (question, options, correct_answer)
    VALUES (?, ?, ?)
    ''', (question, str(options), correct_answer))
    conn.commit()
    conn.close()

# Функция для проверки существования таблицы questions
def check_table_exists():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT name FROM sqlite_master WHERE type='table' AND name='questions'
    ''')
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

# Функция для создания таблицы questions, если её нет
def create_questions_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        options TEXT NOT NULL,
        correct_answer TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

# Основная функция для добавления вопросов
def main():
    # Проверяем, существует ли таблица questions
    if not check_table_exists():
        print("Таблица 'questions' не найдена. Создание таблицы...")
        create_questions_table()

    print("Добавление вопросов в базу данных.")
    while True:
        try:
            # Ввод вопроса
            question = input("Введите вопрос (или 'exit' для выхода): ").strip()
            if question.lower() == 'exit':
                break

            # Ввод вариантов ответов
            options_input = input("Введите 4 варианта ответов через запятую: ").strip()
            options = [option.strip() for option in options_input.split(",")]
            if len(options) != 4:
                print("Ошибка: необходимо ввести ровно 4 варианта ответов.")
                continue

            # Ввод правильного ответа
            correct_answer = input("Какой вариант является правильным? Введите его текст: ").strip()
            if correct_answer not in options:
                print(f"Ошибка: '{correct_answer}' не является одним из предложенных вариантов.")
                continue

            # Добавляем вопрос в базу данных
            add_question(question, options, correct_answer)
            print("Вопрос успешно добавлен!\n")
        except Exception as e:
            print(f"Произошла ошибка: {e}")

    print("Завершение работы.")

if __name__ == '__main__':
    main()