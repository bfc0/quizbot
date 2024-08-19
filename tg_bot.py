import asyncio
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart
from environs import Env
import redis
import logging

from common import get_random_question, is_correct_answer_to


class QuizStates(StatesGroup):
    idle = State()
    awaiting_answer = State()


router = Router()


def create_buttons():
    buttons = [
        [
            types.KeyboardButton(text="Новый вопрос"),
            types.KeyboardButton(text="Сдаться"),
        ],
        [types.KeyboardButton(text="Мой счёт")],
    ]
    return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    await message.answer("Нажми на «Новый вопрос»", reply_markup=create_buttons())
    await state.set_state(QuizStates.idle)


@router.message(F.text.contains("Новый вопрос"), QuizStates.idle)
async def reply(message: types.Message, state: FSMContext, context: dict) -> None:

    question = get_random_question(context["redis"])
    await state.set_data({"current_question": question})

    if not question:
        logging.error("No questions in the storage")
        await message.answer("На сегодня вопросы закончились")
        return

    await message.answer(question["question"])
    await state.set_state(QuizStates.awaiting_answer)


@router.message(F.text.contains("Новый вопрос"), QuizStates.awaiting_answer)
async def reply_newquestion_wrongtime(message: types.Message, state: FSMContext, context: dict) -> None:
    await message.answer("Сначала нажми Сдаться")


@router.message(F.text.contains("Сдаться"), QuizStates.awaiting_answer)
async def give_up(message: types.Message, state: FSMContext) -> None:
    question = (await state.get_data())["current_question"]
    await message.answer(question["primary_answer"])
    if explanation := question.get("explanation"):
        await message.answer(explanation)
    await state.set_state(QuizStates.idle)


@router.message(QuizStates.awaiting_answer)
async def answer_question(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    question = data["current_question"]

    if is_correct_answer_to(question, message.text):
        await message.answer("Правильно", reply_markup=create_buttons())
        if explanation := question.get("explanation"):
            await message.answer(explanation)
        await state.set_state(QuizStates.idle)
    else:
        await message.answer(f"Неправильно. Попробуй ещё", reply_markup=create_buttons())


@router.message(QuizStates.idle)
async def reply_to_random_message(message: types.Message, state: FSMContext) -> None:
    await message.answer("Просто нажми кнопку", reply_markup=create_buttons())


async def main():
    env = Env()
    env.read_env()
    redis_host = env.str("REDIS_HOST", "redis")
    tg_token = env.str("TG_TOKEN", None)

    if not tg_token:
        logging.error("TG_TOKEN not set in .env")
        return

    context = {"redis": redis.Redis(host=redis_host)}

    logging.info("starting service")
    bot = Bot(token=tg_token)
    dp = Dispatcher(context=context)
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
