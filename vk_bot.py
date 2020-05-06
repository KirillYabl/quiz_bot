import random
import logging
import os

import dotenv
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import redis

from common_functions import is_correct_answer

logger = logging.getLogger(__name__)


class VkSessionUsersCondition:
    """Custom user db. It only works in one session, after that clear because is MVP."""

    def __init__(self):
        # Template of info about new user
        self.new_user_template = {
            'got_q': False,  # Is user got question
            'q': '',  # text of question
            'a': ''  # text of answer
        }
        self.db = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug('Initialize class params')

    def add_or_update_user(self, user_id):
        """Add new user or update existing user if he got answer.

        :param user_id: id of user in VK
        """
        self.db[user_id] = self.new_user_template.copy()
        self.logger.debug(f'User created user_id={user_id}')

    def is_user_in_db(self, user_id):
        """Check user in db.

        :param user_id: id of user in VK
        :return: bool, True if user found
        """
        if user_id in self.db:
            return True
        return False

    def is_user_got_question(self, user_id):
        """Check status of user question.

        :param user_id: id of user in VK
        :return: bool, True if user got question
        """
        if not self.is_user_in_db(user_id):
            self.add_or_update_user(user_id)
            return False
        return self.db[user_id]['got_q']

    def get_user_correct_answer(self, user_id):
        """Get user correct answer.
        If this method gave answer, user will update.
        If this method didn't know user, user will initialize. And method will return 'None' for the next handling.
        If user didn't get question, method will return 'None' for the next handling.

        :param user_id: id of user in VK
        :return: answer or None (don't know user or user didn't get question)
        """
        if not self.is_user_in_db(user_id):
            self.add_or_update_user(user_id)
            return None

        if self.db[user_id]['got_q']:
            answer = self.db[user_id]['a']
            self.add_or_update_user(user_id)
            return answer
        return None

    def add_answer_to_user(self, user_id, q, a):
        """Update user with new answer.

        :param user_id: id of user in VK
        :param q: str, user question
        :param a: str, correct answer
        """
        if not self.is_user_in_db(user_id):
            self.add_or_update_user(user_id)

        self.db[user_id]['got_q'] = True
        self.db[user_id]['q'] = q
        self.db[user_id]['a'] = a
        self.logger.debug(f'User got answer. user_id={user_id}')


def run_bot_logic(event, vk_api):
    """Logic of bot.

    :param event: event which discribe message
    :param vk_api: authorized session in vk
    """
    first_time = False
    got_question = True
    msg = ''
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        logger.debug(f'Starting work. user_id={event.user_id}')
        # in start we will get future question and answer if didn't get early
        if not VK_DB.is_user_in_db(event.user_id):
            VK_DB.add_or_update_user(event.user_id)
            first_time = True
            msg += 'Рады приветствовать вас в нашей викторине!\n'
            logger.debug('User play first time.')

        if not VK_DB.is_user_got_question(event.user_id):
            got_question = False
            logger.debug('User didn\'t get question.')

        if event.text == "Сдаться":
            logger.debug('User gave up')
            answer = VK_DB.get_user_correct_answer(event.user_id)

            if answer is None:
                msg += 'Еще не получили вопрос, а уже сдаетесь? Попробуйте сыграть в викторину.\n'
                msg += 'Нажмите на кнопку "Новый вопрос".'
                vk_api.messages.send(
                    user_id=event.user_id,
                    message=msg,
                    random_id=random.randint(1, 1000),
                    keyboard=init_keyboard().get_keyboard()
                )
                logger.debug('"give up without question" message sent')
                return

            msg = f'Жаль, правильный ответ:\n{answer}'
            vk_api.messages.send(
                user_id=event.user_id,
                message=msg,
                random_id=random.randint(1, 1000),
                keyboard=init_keyboard().get_keyboard()
            )
            logger.debug('"give up" message sent')
        elif event.text == "Новый вопрос":
            logger.debug('User is getting new question')
            if got_question and not first_time:
                answer = VK_DB.get_user_correct_answer(event.user_id)
                msg += f'А как же предыдущий вопрос?\nПравильный ответ:\n{answer}'
                vk_api.messages.send(
                    user_id=event.user_id,
                    message=msg,
                    random_id=random.randint(1, 1000),
                    keyboard=init_keyboard().get_keyboard()
                )
                logger.debug('"answer to question with new question request" message sent')
                q = DB.randomkey().decode('utf-8')
                answer = DB.get(q).decode('utf-8')
                VK_DB.add_answer_to_user(event.user_id, q, answer)
                msg = f'Ваш новый вопрос:\n{q}'
                vk_api.messages.send(
                    user_id=event.user_id,
                    message=msg,
                    random_id=random.randint(1, 1000),
                    keyboard=init_keyboard().get_keyboard()
                )
                logger.debug('"new question with new question request" message sent')
                return

            q = DB.randomkey().decode('utf-8')
            answer = DB.get(q).decode('utf-8')
            VK_DB.add_answer_to_user(event.user_id, q, answer)
            msg += q
            vk_api.messages.send(
                user_id=event.user_id,
                message=msg,
                random_id=random.randint(1, 1000),
                keyboard=init_keyboard().get_keyboard()
            )
            logger.debug('"new question" message sent')
        else:
            if got_question:
                correct_answer = VK_DB.get_user_correct_answer(event.user_id)
                if is_correct_answer(event.text, correct_answer, limit=0.5):
                    msg = f'Правильно! Полный ответ:\n{correct_answer}\nХотите новый вопрос? Выберите в меню.'
                    logger.debug('"correct answer" message sent')
                else:
                    msg = f'К сожалению нет! Полный ответ:\n{correct_answer}\nХотите новый вопрос? Выберите в меню.'
                    logger.debug('"incorrect answer" message sent')
                vk_api.messages.send(
                    user_id=event.user_id,
                    message=msg,
                    random_id=random.randint(1, 1000),
                    keyboard=init_keyboard().get_keyboard()
                )
                return

            msg += 'Нажмите на кнопку "Новый вопрос" для получения вопроса.'
            vk_api.messages.send(
                user_id=event.user_id,
                message=msg,
                random_id=random.randint(1, 1000),
                keyboard=init_keyboard().get_keyboard()
            )
            logger.debug('"press new question" message sent')


def init_keyboard():
    """Initialize keyboard.

    :return: keyboard object
    """
    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    keyboard.add_line()  # Переход на вторую строку
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.PRIMARY)

    logger.debug('Keyboard initialized')
    return keyboard


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s  %(name)s  %(levelname)s  %(message)s', level=logging.DEBUG)

    dotenv.load_dotenv()
    VK_APP_TOKEN = os.getenv('VK_APP_TOKEN')
    REDIS_DB_ADDRESS = os.getenv('REDIS_DB_ADDRESS')
    REDIS_DB_PORT = os.getenv('REDIS_DB_PORT')
    REDIS_DB_PASSWORD = os.getenv('REDIS_DB_PASSWORD')
    logger.debug('.env was read')

    DB = redis.Redis(host=REDIS_DB_ADDRESS, port=REDIS_DB_PORT, password=REDIS_DB_PASSWORD)
    logger.debug('Got DB connection')
    VK_DB = VkSessionUsersCondition()

    while True:
        try:
            vk_session = vk.VkApi(token=VK_APP_TOKEN)
            logger.debug('Got VK API connection')
            vk_api = vk_session.get_api()
            longpoll = VkLongPoll(vk_session)
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    run_bot_logic(event, vk_api)
        except Exception:
            logger.exception('Critical error in ')
