import redis
import json


def get_random_question(r: redis.Redis) -> dict | None:
    question = r.get(r.randomkey())
    return json.loads(question) if question else None
