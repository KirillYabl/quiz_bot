def normalize_answer(answer):
    """Do manipulations with answer for checking.

    :param answer: str, text of answer
    :return: str, modified answer
    """
    first_sentence_of_answer = answer.split('.')[0]
    answer_without_explanation = first_sentence_of_answer.split('(')[0]

    return answer_without_explanation.lower()


def is_correct_answer(user_answer, correct_answer, limit, answer_handler=None):
    """Check if answer correct (more than :limit: of words is ok).

    :param user_answer: text of user answer
    :param correct_answer: text of correct answer
    :param limit: number between 0 and 1, this is percentage of correct answers
    :param answer_handler: functions, this functions should do manipulations with answers to normalize them.
    If you don't need to normalize answer, you will set this param 'None'
    :return: bool, correct or no
    """

    # prepare answers
    prepared_correct_answer = correct_answer
    prepared_user_answer = user_answer
    if answer_handler is not None:
        prepared_correct_answer = answer_handler(correct_answer)
        prepared_user_answer = answer_handler(user_answer)

    # sets of words
    words_of_correct_answer = set(prepared_correct_answer.split())
    words_of_user_answer = set(prepared_user_answer.split())

    # correct words - intersection of sets
    correct_words = words_of_correct_answer.intersection(words_of_user_answer)

    # calculate len of correct and len of user answer
    number_of_correct_words = len(correct_words)
    number_of_user_answer_words = len(words_of_user_answer)

    # calculate percentage of correct and compare with limit
    percentage_of_correct_words = number_of_correct_words / number_of_user_answer_words
    correct_words_more_or_equal_than_limit = percentage_of_correct_words >= limit

    return correct_words_more_or_equal_than_limit
