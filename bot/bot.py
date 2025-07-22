import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, FSInputFile
from aiogram.filters import Command
from dotenv import load_dotenv
from pathlib import Path

# Явно грузим .env из корня проекта
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

BOT_TOKEN = os.getenv('BOT_TOKEN')
print('DEBUG BOT_TOKEN:', BOT_TOKEN)
if not BOT_TOKEN or not BOT_TOKEN.startswith('7'):
    raise RuntimeError('BOT_TOKEN не найден или невалиден! Проверьте .env и перезапустите activate_bot.sh')

from .fsm_handlers import router as fsm_router

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(fsm_router)

@dp.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Примеры работ:')
    examples = [
        {'file': 'bot/photos/1.png', 'caption': 'Гостиная с многоуровневым потолком'},
        {'file': 'bot/photos/2.jpg', 'caption': 'Кухня с подсветкой'},
        {'file': 'bot/photos/3.jpg', 'caption': 'Спальня с фотопечатью'},
        {'file': 'bot/photos/4.jpg', 'caption': 'Классический белый потолок'},
        {'file': 'bot/photos/5.jpg', 'caption': 'Потолок с точечными светильниками'},
    ]
    for ex in examples:
        photo = FSInputFile(ex['file'])
        await message.answer_photo(photo, caption=ex['caption'])
    await message.answer(
        '👋 Добрый день!\nМеня зовут мастер Роман и я готов выполнить ваш заказ.\n\nПожалуйста, представьтесь (напишите Ваше имя).',
        reply_markup=ReplyKeyboardRemove()
    )
    from .states import OrderFSM
    await state.set_state(OrderFSM.name)

if __name__ == '__main__':
    import asyncio
    asyncio.run(dp.start_polling(bot)) 