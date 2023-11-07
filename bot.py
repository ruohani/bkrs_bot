from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from AiogramStorages.storages import PGStorage

from config import TOKEN
from program import main


bot = Bot(token=TOKEN)
storage = PGStorage(username='postgres', password='root', db_name='bkrs_bot')
dp = Dispatcher(bot, storage=storage)
# storage = MemoryStorage()
# dp = Dispatcher(bot, storage=storage)


class Bot(StatesGroup):
    InputWord = State()


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_full_name = message.from_user.full_name

    await message.answer(
        f"Привет, {user_full_name}!\n\nЭто бот, который поможет находить переводы слов, для этого используются данные с сайта БКРС.\n\nДля начала использования, пожалуйста, введите слово на русском или китайском языке.\n\nПримечание: при нажатии на китайские иероглифы они копируются в буфер обмена.")
    await message.answer('Введите слово:')

    await Bot.InputWord.set()


@dp.message_handler(state=Bot.InputWord)
async def translate(message: types.Message):
    word = message.text
    print(f"Пользователь {message.from_user.full_name} ({message.from_user.id}) написал боту сообщение: {message.text}")
    
    await main(message, word)

if __name__ == '__main__':
    executor.start_polling(dp)
