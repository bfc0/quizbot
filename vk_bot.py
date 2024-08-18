from vkbottle.bot import Bot, BotLabeler, Message
from vkbottle import BaseStateGroup, Keyboard, Text
from environs import Env
import redis
import logging

from common import get_random_question


class QuizStates(BaseStateGroup):
    IDLE = "idle"
    AWAITING_ANSWER = "awaiting_answer"


def create_keyboard():
    keyboard = (
        Keyboard(one_time=True, inline=False)
        .add(Text("Новый вопрос"))
        .add(Text("Сдаться"))
        .row()
        .add(Text("Мой счёт"))
    ).get_json()
    return keyboard


async def start(message: Message, context: dict):
    await message.answer(
        "Я хочу сыграть с тобой в одну игру..", keyboard=create_keyboard()
    )
    await context["bot"].state_dispenser.set(message.peer_id, QuizStates.IDLE)


async def present_question(message: Message, context: dict):
    question = get_random_question(context["redis"])
    if not question:
        logging.error("no questions in database")
        await message.answer(f"Вопросы закончились")
        return

    await message.answer(question["question"], keyboard=create_keyboard())
    await context["bot"].state_dispenser.set(
        message.peer_id,
        QuizStates.AWAITING_ANSWER,
        payload=question,
    )


async def process_answer(message: Message, context: dict):

    question = message.state_peer.payload["payload"]  # type: ignore
    primary, secondary = question["primary_answer"], question.get(
        "secondary_answer")
    explanation = question.get("explanation")

    if message.text in (primary, secondary):
        await message.answer(f"Правильно!", keyboard=create_keyboard())
        await context["bot"].state_dispenser.set(
            message.peer_id, QuizStates.IDLE, payload={}
        )
    else:
        await message.answer(
            f"Неправильно. Попробуй еще.", keyboard=create_keyboard()
        )


async def give_up(message: Message, context: dict):

    question = message.state_peer.payload["payload"]  # type: ignore
    answer, explanation = question["primary_answer"], question.get(
        "explanation")

    await message.answer(f"Вот правильный ответ:\n{answer}", keyboard=create_keyboard())
    if explanation:
        await message.answer(explanation)
    await context["bot"].state_dispenser.set(message.peer_id, QuizStates.IDLE)


async def user_score(message: Message, context: dict):
    await message.answer("Не надо сюда жать", keyboard=create_keyboard())


async def any_message(message: Message, context: dict):
    await message.answer("Ничего не знаю", keyboard=create_keyboard())


def main():
    env = Env()
    env.read_env()

    labeler = BotLabeler()
    bot = Bot(env.str("VK_TOKEN"), labeler=labeler)
    ctx = {
        "redis": redis.Redis(host=env.str("REDIS_HOST", "redis")),
        "bot": bot,
    }

    labeler.message(state=None)(lambda message: start(message, context=ctx))
    labeler.message(text="Новый вопрос")(
        lambda message: present_question(message, context=ctx)
    )
    labeler.message(text="Сдаться", state=QuizStates.AWAITING_ANSWER)(
        lambda message: give_up(message, context=ctx)
    )
    labeler.message(state=QuizStates.AWAITING_ANSWER)(
        lambda message: process_answer(message, context=ctx)
    )
    labeler.message(text="Мой счёт")(
        lambda message: user_score(message, context=ctx))
    labeler.message()(lambda message: any_message(message, context=ctx))

    bot.run_forever()


if __name__ == "__main__":
    main()
