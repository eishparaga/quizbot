from flask import Flask, request, jsonify
from telebot import TeleBot, types
import sqlite3
import random

# Настройки бота
TOKEN = '7730389641:AAFeAaFanVRv6Vlv2lksJPjTcba_JcFy7UY'  # Замените на ваш токен
APP_URL = 'https://test23.pubns.ru/'  # Замените на ваш домен
WEBHOOK_URL = f'{APP_URL}webhook'

# Инициализация Flask и Telebot
app = Flask(__name__)
bot = TeleBot(TOKEN)

# Глобальный словарь для хранения состояния пользователей
user_states = {}

# Функция для подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect('quiz.db')
    conn.row_factory = sqlite3.Row
    return conn

# Создание таблицы questions (если её нет)
def init_database():
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

# Вызываем инициализацию базы данных при старте приложения
init_database()

# Функция для получения всех вопросов из базы данных
def get_all_questions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM questions')
    rows = cursor.fetchall()
    conn.close()
    questions = []
    for row in rows:
        question_id, question_text, options, correct_answer = row
        questions.append({
            "id": question_id,
            "question": question_text,
            "options": eval(options),  # Преобразуем строку в список
            "correct_answer": correct_answer
        })
    return questions

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

# Обработчик вебхука
@app.route('/webhook', methods=['POST'])
def webhook():
    update = types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200

# Начало квиза
@bot.message_handler(commands=['start'])
def start_quiz(message):
    user_id = message.from_user.id
    if user_id not in user_states:
        user_states[user_id] = {"step": "enter_name", "score": 0}

    bot.send_message(user_id, "Введите ваше имя:")

# Обработка состояний игры
@bot.message_handler(func=lambda message: True)
def handle_game_states(message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if not state:
        return

    step = state.get("step")

    if step == "enter_name":
        state["name"] = message.text.strip()
        state["step"] = "playing"
        send_next_question(user_id)
    elif step == "playing":
        questions = get_all_questions()
        if not questions:
            bot.send_message(user_id, "Вопросы отсутствуют. Используйте команду /add, чтобы добавить вопросы.")
            del user_states[user_id]
            return

        # Проверяем правильность ответа
        correct_answer = state.get("current_question_correct_answer")
        if message.text.strip() == correct_answer:
            state["score"] += 1
            bot.send_message(user_id, "Правильно! Следующий вопрос:")
            send_next_question(user_id)
        else:
            bot.send_message(user_id, f"Неправильно. Правильный ответ: {correct_answer}")
            bot.send_message(user_id, f"{state['name']}, игра окончена! Ваш результат: {state['score']} баллов.")
            del user_states[user_id]

# Отправка следующего вопроса
def send_next_question(user_id):
    questions = get_all_questions()
    if not questions:
        bot.send_message(user_id, "Вопросы отсутствуют. Используйте команду /add, чтобы добавить вопросы.")
        del user_states[user_id]
        return

    # Случайно выбираем вопрос
    question_data = random.choice(questions)
    question_text = question_data["question"]
    options = question_data["options"]
    correct_answer = question_data["correct_answer"]

    # Сохраняем правильный ответ для проверки
    user_states[user_id]["current_question_correct_answer"] = correct_answer

    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for option in options:
        keyboard.add(types.KeyboardButton(option))

    bot.send_message(user_id, question_text, reply_markup=keyboard)

# Команда для добавления вопроса
@bot.message_handler(commands=['add'])
def add_question_start(message):
    user_id = message.from_user.id
    user_states[user_id] = {"step": "enter_question"}
    bot.send_message(user_id, "Введите вопрос:")

# Обработка состояний добавления вопроса
@bot.message_handler(func=lambda message: True)
def handle_add_question_states(message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if not state or "step" not in state:
        return

    step = state.get("step")

    if step == "enter_question":
        state["question"] = message.text
        state["step"] = "enter_options"
        bot.send_message(user_id, "Введите 4 варианта ответов через запятую (например: Python,Java,JavaScript,C++):")
    elif step == "enter_options":
        options = [option.strip() for option in message.text.split(",")]
        if len(options) != 4:
            bot.send_message(user_id, "Пожалуйста, введите ровно 4 варианта ответов через запятую:")
            return
        state["options"] = options
        state["step"] = "enter_correct_answer"
        bot.send_message(user_id, "Какой вариант является правильным? Введите его текст:")
    elif step == "enter_correct_answer":
        correct_answer = message.text.strip()
        if correct_answer not in state["options"]:
            bot.send_message(user_id, "Правильный ответ должен быть одним из предложенных вариантов. Попробуйте снова:")
            return
        state["correct_answer"] = correct_answer

        # Сохраняем вопрос в базу данных
        add_question(state["question"], state["options"], state["correct_answer"])
        del user_states[user_id]
        bot.send_message(user_id, "Вопрос успешно добавлен!")

# Главная страница (для проверки работы сервера)
@app.route('/')
def index():
    return "Telegram Quiz Bot is running!", 200

# Запуск приложения
if __name__ == '__main__':
    # Удаление старого вебхука
    bot.remove_webhook()
    # Установка нового вебхука
    bot.set_webhook(url=WEBHOOK_URL)
    # Запуск Flask приложения
    app.run(host='0.0.0.0', port=5000)