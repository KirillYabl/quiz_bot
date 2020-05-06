def is_correct_answer(user_answer, correct_answer, limit):
    """Check if answer correct (more than :limit: of words is ok).

    :param user_answer: text of user answer
    :param correct_answer: text of correct answer
    :param limit: number between 0 and 1, this is percentage of correct answers
    :return: bool, correct or no
    """
    def prepare_answer(answer):
        """Do manipulations with answer for checking.

        1. Split by '.'. If answer have more than one sentence, only one sentence will check
        2. Take first.
        3. Split by '('. This symbol usually means explanations. We won't check explanations
        4. Take first.
        5. Make lower

        :param answer: str, text of answer
        :return: str, modified answer
        """
        first_sentence_of_answer = answer.split('.')[0]
        answer_without_explanation = first_sentence_of_answer.split('(')[0]

        return answer_without_explanation.lower()

    # prepare answers
    prepared_correct_answer = prepare_answer(correct_answer)
    prepared_user_answer = prepare_answer(user_answer)

    # sets of words
    words_of_correct_answer = set(prepared_correct_answer.split(' '))
    words_of_user_answer = set(prepared_user_answer.split(' '))

    # correct words - intersection of sets
    correct_words = words_of_correct_answer.intersection(words_of_user_answer)

    # calculate len of correct and len of user answer
    number_of_correct_words = len(correct_words)
    number_of_user_answer_words = len(words_of_user_answer)

    # calculate percentage of correct and compare with limit
    percentage_of_correct_words = number_of_correct_words / number_of_user_answer_words
    correct_words_more_or_equal_than_limit = percentage_of_correct_words >= limit

    if correct_words_more_or_equal_than_limit:
        return True
    return False
