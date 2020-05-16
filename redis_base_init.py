import dotenv
import redis

import logging
import os
import json
import random

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s  %(name)s  %(levelname)s  %(message)s', level=logging.DEBUG)

    dotenv.load_dotenv()
    redis_db_address = os.getenv('REDIS_DB_ADDRESS')
    redis_db_port = os.getenv('REDIS_DB_PORT')
    redis_db_password = os.getenv('REDIS_DB_PASSWORD')
    db_path = os.getenv('DB_PATH', default='data/questions.json')
    db_record_count = os.getenv('DB_RECORD_COUNT', default=100)
    redis_set_of_questions_name = os.getenv('REDIS_SET_OF_QUESTIONS_NAME', default='QuestionAnswerSet')
    redis_hash_of_questions_and_answers_name = os.getenv('REDIS_HASH_OF_QUESTIONS_AND_ANSWERS_NAME',
                                                         default='QuestionAnswerHash')

    logger.debug('.env was read')

    with open(db_path, encoding='utf-8') as f:
        data = json.load(f)
    data_keys = [int(num) for num in data.keys()]
    min_id = min(data_keys)
    max_id = max(data_keys)
    logger.debug(f'data was read. Min_id: {min_id}. Max_id: {max_id}')

    redis_db = redis.Redis(host=redis_db_address, port=redis_db_port, password=redis_db_password)

    new_data = False
    for i in range(db_record_count):
        q_num = str(random.randint(data['min_id'], data['max_id']))
        question = str(data['data'][q_num]['q']).encode('utf-8')
        answer = str(data['data'][q_num]['a']).encode('utf-8')
        if new_data:
            redis_db.hset(redis_hash_of_questions_and_answers_name, question, answer)
            redis_db.sadd(redis_set_of_questions_name, question)

    logger.debug(f'db size {redis_db.dbsize()}')
    redis_db.close()
