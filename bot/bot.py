import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from config import BOT_TOKEN
from .fsm_handlers import router as fsm_router

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(fsm_router)

@dp.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        '👋 Добрый день!\nМеня зовут мастер Роман и я готов выполнить ваш заказ.\n\nПожалуйста, представьтесь (напишите Ваше имя).',
        reply_markup=ReplyKeyboardRemove()
    )
    from .states import OrderFSM
    await state.set_state(OrderFSM.name)

if __name__ == '__main__':
    import asyncio
    asyncio.run(dp.start_polling(bot)) 