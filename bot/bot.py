import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, FSInputFile, InputMediaPhoto
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
    # Сначала отправляем калаж с фото
    examples = [
        {'file': 'bot/photos/1.png', 'caption': 'Гостиная с многоуровневым потолком'},
        {'file': 'bot/photos/2.jpg', 'caption': 'Кухня с подсветкой'},
        {'file': 'bot/photos/3.jpg', 'caption': 'Спальня с фотопечатью'},
        {'file': 'bot/photos/4.jpg', 'caption': 'Классический белый потолок'},
        {'file': 'bot/photos/5.jpg', 'caption': 'Потолок с точечными светильниками'},
    ]
    media = [InputMediaPhoto(media=FSInputFile(ex['file']), caption=('Примеры работ' if i == 0 else '')) for i, ex in enumerate(examples[1:])]
    await message.answer_media_group(media)
    # Далее логика приветствия/запроса имени
    user = message.from_user
    full_name = (user.first_name or '') + (' ' + user.last_name if user.last_name else '')
    phone = None
    if full_name.strip():
        await state.update_data(name=full_name.strip())
        greet = f'👋 Привет, {full_name.strip()}!\nМеня зовут мастер Роман и я делаю потолки уже много лет, могу исполнить заказы любой сложности.'
        await message.answer(greet, reply_markup=ReplyKeyboardRemove())
        await message.answer('Пожалуйста, введите номер телефона (в любом формате):')
        from .states import OrderFSM
        await state.set_state(OrderFSM.phone)
    else:
        await message.answer(
            '👋 Добрый день!\nМеня зовут мастер Роман и я делаю потолки уже много лет, могу исполнить заказы любой сложности.\n\nПожалуйста, для оформления заявки представьтесь (напишите Ваше имя).',
            reply_markup=ReplyKeyboardRemove()
        )
        from .states import OrderFSM
        await state.set_state(OrderFSM.name)

if __name__ == '__main__':
    import asyncio
    asyncio.run(dp.start_polling(bot)) 