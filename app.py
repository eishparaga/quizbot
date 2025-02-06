from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random

# Настройки бота
TOKEN = '7730389641:AAFeAaFanVRv6Vlv2lksJPjTcba_JcFy7UY'  # Замените на токен вашего бота
APP_URL = f'http://test23.pubns.ru/'  # Замените YOUR_DOMAIN на ваш домен или IP адрес
WEBHOOK_URL = f'{APP_URL}webhook'

# Инициализация Flask и Telebot
app = Flask(__name__)
bot = telebot.TeleBot(TOKEN)

# Вопросы для квиза (можно расширить)
quiz_questions = [
    {
        "question": "Какой язык программирования используется для этого бота?",
        "options": ["Python", "JavaScript", "Java"],
        "correct_answer": "Python"
    },
    {
        "question": "Какой фреймворк используется для веб-сервера?",
        "options": ["Flask", "Django", "FastAPI"],
        "correct_answer": "Flask"
    },
    {
        "question": "Какой метод HTTP используется для обработки вебхуков?",
        "options": ["GET", "POST", "PUT"],
        "correct_answer": "POST"
    }
]

# Глобальный словарь для хранения состояния пользователей
user_states = {}

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200

@bot.message_handler(commands=['start'])
def start_quiz(message):
    user_id = message.from_user.id
    user_states[user_id] = {"current_question": 0, "score": 0}
    send_next_question(user_id)

def send_next_question(user_id):
    state = user_states.get(user_id)
    if not state or state["current_question"] >= len(quiz_questions):
        bot.send_message(user_id, f"Квиз завершён! Ваш результат: {state['score']} из {len(quiz_questions)}")
        del user_states[user_id]
        return

    question_data = quiz_questions[state["current_question"]]
    question_text = question_data["question"]
    options = question_data["options"]

    keyboard = InlineKeyboardMarkup()
    for option in options:
        keyboard.add(InlineKeyboardButton(option, callback_data=option))

    bot.send_message(user_id, question_text, reply_markup=keyboard)
    state["current_question"] += 1

@bot.callback_query_handler(func=lambda call: True)
def handle_answer(call):
    user_id = call.from_user.id
    state = user_states.get(user_id)
    if not state:
        bot.answer_callback_query(call.id, "Квиз уже завершён.")
        return

    current_question_index = state["current_question"] - 1
    correct_answer = quiz_questions[current_question_index]["correct_answer"]
    user_answer = call.data

    if user_answer == correct_answer:
        state["score"] += 1
        bot.answer_callback_query(call.id, "Правильно!")
    else:
        bot.answer_callback_query(call.id, f"Неправильно. Правильный ответ: {correct_answer}")

    send_next_question(user_id)

@app.route('/')
def index():
    return "Telegram Quiz Bot is running!", 200

if __name__ == '__main__':
    # Установка вебхука
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    app.run(host='0.0.0.0', port=5000)