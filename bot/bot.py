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
    # Сначала отправляем подпись
    await message.answer('Примеры работ')
    # Получаем все фото из папки bot/photos
    photos_dir = os.path.join(os.path.dirname(__file__), 'photos')
    photo_files = sorted([f for f in os.listdir(photos_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    # Отправляем калажами по 10 фото
    batch_size = 10
    for i in range(0, len(photo_files), batch_size):
        batch = photo_files[i:i+batch_size]
        media = []
        for fname in batch:
            path = os.path.join(photos_dir, fname)
            media.append(InputMediaPhoto(media=FSInputFile(path)))
        await message.answer_media_group(media)
    # Далее логика приветствия/запроса имени
    user = message.from_user
    full_name = (user.first_name or '') + (' ' + user.last_name if user.last_name else '')
    phone = None
    if full_name.strip():
        await state.update_data(name=full_name.strip())
        greet = f'👋 Привет, {full_name.strip()}!\nМеня зовут мастер Роман и я делаю потолки уже много лет, могу исполнить заказы любой сложности.'
        await message.answer(greet, reply_markup=ReplyKeyboardRemove())
        await message.answer('Для оформления заявки на замер пожалуйста, введите номер телефона (в любом формате):')
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