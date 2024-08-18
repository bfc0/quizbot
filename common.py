import redis
import json


def get_random_question(r: redis.Redis) -> dict | None:
    question = r.get(r.randomkey())
    return json.loads(question) if question else None


def is_correct_answer_to(question: dict[str, str], answer: str) -> bool:
    primary = question.get("primary_answer")
    if not primary:  # something wrong with the question
        return False

    if answer == primary.split(".")[0]:
        return True

    secondary = question.get("secondary_answer")
    if not secondary:
        return False

    if answer == secondary.split(".")[0]:
        return True

    return False
