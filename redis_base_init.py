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
    db_path = os.getenv('DB_PATH')
    db_record_count = os.getenv('DB_RECORD_COUNT')

    # default values
    if db_path is None:
        db_path = 'data/questions.json'
    if db_record_count is None:
        db_record_count = 100

    logger.debug('.env were read')

    with open(db_path, encoding='utf-8') as f:
        data = json.load(f)
    data_keys = [int(num) for num in data.keys()]
    min_id = min(data_keys)
    max_id = max(data_keys)
    logger.debug(f'data were read. Min_id: {min_id}. Max_id: {max_id}')

    redis_db = redis.Redis(host=redis_db_address, port=redis_db_port, password=redis_db_password)

    new_data = False
    for i in range(db_record_count):
        q_num = str(random.randint(data['min_id'], data['max_id']))
        question = u'{}'.format(data['data'][q_num]['q'])
        answer = u'{}'.format(data['data'][q_num]['a'])
        if new_data:
            redis_db.hset('QuestionAnswerHash', question, answer)
            redis_db.sadd('QuestionAnswerSet', question)
    logger.debug(f'db size {redis_db.dbsize()}')
    redis_db.close()
