import asyncio
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart
from environs import Env
import logging


class QuizStates(StatesGroup):
    idle = State()
    awaiting_answer = State()


dp = Dispatcher()
router = Router()


def question_buttons():
    buttons = [
        [
            types.KeyboardButton(text="Next Question"),
            types.KeyboardButton(text="Give Up"),
        ],
        [types.KeyboardButton(text="Cancel")],
    ]
    return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    await state.set_state(QuizStates.idle)
    await message.answer("Hello", reply_markup=question_buttons())


@router.message(F.text.contains("Next Question"), QuizStates.idle)
async def reply(message: types.Message, state: FSMContext) -> None:
    await state.set_data({"answer": "123"})
    await message.answer("Here is a question for you:")
    await state.set_state(QuizStates.awaiting_answer)


@router.message(QuizStates.awaiting_answer)
async def reply2(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    if message.text == data["answer"]:
        await message.answer("Correct")
    else:
        await message.answer("Nopers")

    await state.set_state(QuizStates.idle)


@router.message(QuizStates.idle)
async def reply_to_random_message(message: types.Message, state: FSMContext) -> None:
    await message.answer("Just press the button")


async def main():
    env = Env()
    env.read_env()
    tg_token = env.str("TG_TOKEN", None)
    if not tg_token:
        logging.error("TG_TOKEN not set in .env")
        return

    print("starting service")
    bot = Bot(token=tg_token)
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
