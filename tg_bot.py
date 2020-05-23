from telegram.ext import ConversationHandler, CommandHandler, Filters, Updater, MessageHandler
from telegram import ReplyKeyboardMarkup
import dotenv
import redis

import logging
import os
from enum import IntEnum, unique
from functools import partial

from common_functions import is_correct_answer, normalize_answer

logger = logging.getLogger(__name__)


@unique
class Buttons(IntEnum):
    MENU = 0
    QUESTION = 1
    ANSWER = 2


def greet_user(bot, update):
    """Just hello message for /start command.

    :param bot: tg bot object
    :param update: event with update tg object
    :return: number of next action for conversation handler
    """
    custom_keyboard = [
        ['Новый вопрос', 'Сдаться'],
        ['Мой счёт']
    ]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    msg = 'Добро пожаловать в историческую викторину. Выберите действие!'
    bot.send_message(chat_id=update.message.chat_id, text=msg, reply_markup=reply_markup)
    logger.debug('"Greeting" message was sent')

    return Buttons.MENU


def manage_menu_logic(bot, update, user_data):
    """Manage menu logic.

    :param bot: tg bot object
    :param update: event with update tg object
    :param user_data: users data which tg must remember. Dict-like interface
    :return: number of next action for conversation handler
    """
    if update.message.text == 'Новый вопрос':
        logger.debug('User pressed new question')
        return Buttons.QUESTION

    if update.message.text == 'Сдаться':
        logger.debug('User pressed gave up')
        return Buttons.MENU


def give_question(bot, update, user_data, redis_db, redis_set_name, redis_hash_name):
    """Send any question.

    :param bot: tg bot object
    :param update: event with update tg object
    :param user_data: users data which tg must remember. Dict-like interface
    :param redis_db: redis database object
    :param redis_set_name: name of set in Redis
    :param redis_hash_name: name of hash in redis
    :return: number of next action for conversation handler
    """
    question = redis_db.srandmember(redis_set_name, 1)[0].decode('utf-8')
    bot.send_message(chat_id=update.message.chat_id, text=question)
    logger.debug('Question was sent')

    answer = redis_db.hget(redis_hash_name, question).decode('utf-8')
    user_data['answer'] = answer
    logger.debug('Answer was wrote')

    return Buttons.ANSWER


def check_answer(bot, update, user_data):
    """Check user answer.

    :param bot: tg bot object
    :param update: event with update tg object
    :param user_data: users data which tg must remember. Dict-like interface
    :return: number of next action for conversation handler
    """
    answer = user_data['answer']

    user_answer = update.message.text

    # half correct words is OK
    if is_correct_answer(user_answer, answer, limit=0.5, answer_handler=normalize_answer):
        msg = 'Правильно! Полный ответ:\n{}\nХотите новый вопрос? Выберите в меню.'.format(user_data['answer'])
        bot.send_message(chat_id=update.message.chat_id, text=msg)
        logger.debug('"Correct answer" message was sent')
        return Buttons.QUESTION

    if update.message.text == 'Сдаться':
        msg = 'Жаль... Правильный ответ:\n{}\nХотите новый вопрос? Выберите в меню.'.format(user_data['answer'])
        bot.send_message(chat_id=update.message.chat_id, text=msg)
        logger.debug('"Gave up" message was sent')
        return Buttons.QUESTION

    msg = 'К сожалению нет! Правильный ответ:\n{}\nХотите новый вопрос? Выберите в меню.'.format(user_data['answer'])
    bot.send_message(chat_id=update.message.chat_id, text=msg)
    logger.debug('"Mistake" message was sent')
    return Buttons.QUESTION


def stop_quiz(bot, update):
    """Action which executes if user stop quiz.

    :param bot: tg bot object
    :param update: event with update tg object
    :return: number of next action for conversation handler
    """
    bot.send_message(chat_id=update.message.chat_id, text='Викторина остановлена.')
    logger.debug('"Stop" message was sent')

    return Buttons.MENU


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s  %(name)s  %(levelname)s  %(message)s', level=logging.DEBUG)

    dotenv.load_dotenv()
    tg_bot_token = os.getenv('TG_BOT_TOKEN')
    proxy = os.getenv('PROXY')  # Fill in .env if you are from mother Russia
    redis_db_address = os.getenv('REDIS_DB_ADDRESS')
    redis_db_port = os.getenv('REDIS_DB_PORT')
    redis_db_password = os.getenv('REDIS_DB_PASSWORD')
    redis_set_of_questions_name = os.getenv('REDIS_SET_OF_QUESTIONS_NAME', default='QuestionAnswerSet')
    redis_hash_of_questions_and_answers_name = os.getenv('REDIS_HASH_OF_QUESTIONS_AND_ANSWERS_NAME',
                                                         default='QuestionAnswerHash')
    logger.debug('.env was read')

    redis_db = redis.Redis(host=redis_db_address, port=redis_db_port, password=redis_db_password)
    logger.debug('Got DB connection')

    # handler of bot's states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', greet_user)],
        states={
            Buttons.MENU: [MessageHandler(Filters.text, manage_menu_logic, pass_user_data=True)],
            Buttons.QUESTION: [
                MessageHandler(Filters.text, partial(give_question, redis_db=redis_db), pass_user_data=True)],
            Buttons.ANSWER: [MessageHandler(Filters.text, check_answer, pass_user_data=True)],
        },
        fallbacks=[CommandHandler('stop', stop_quiz)]
    )
    logger.debug('Conversation handler was initialized')

    request_kwargs = None
    if proxy:
        request_kwargs = {'proxy_url': proxy}
        logger.debug(f'Using proxy - {proxy}')
    updater = Updater(token=tg_bot_token, request_kwargs=request_kwargs)
    logger.debug('Connection with TG was established')

    # add handlers
    updater.dispatcher.add_handler(conv_handler)
    logger.debug('Conversation handler was added to updater')

    # If your error handling consists in writing errors to the log,
    # then you don't need to write a some error handler,
    # telegram updater logger will write them instead you
    # and the application will start working again
    updater.start_polling()
