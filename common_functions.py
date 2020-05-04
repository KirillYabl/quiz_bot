def is_correct_answer(user_answer, correct_answer, limit):
    """Check if answer correct (more than :limit: of words is ok).

    :param user_answer: text of user answer
    :param correct_answer: text of correct answer
    :param limit: number between 0 and 1, this is percentage of correct answers
    :return: bool, correct or no
    """
    # 1. Split by '.'. 2. Take first. 3. Split by '('. 4. Take first. 5. Make lower
    # '.' - If answer have more than one sentence, only one sentence will check
    # '(' - This symbol usually means explanations. We won't check explanations
    correct_answer = correct_answer.split('.')[0].split('(')[0].lower()
    user_answer = user_answer.split('.')[0].split('(')[0].lower()
    correct = 0
    words = user_answer.split(' ')
    for word in words:
        if word in correct_answer:
            correct += 1

    # I think half correct words is OK
    if (correct / len(words)) >= limit:
        return True
    return False
