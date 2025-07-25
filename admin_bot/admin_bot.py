import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import sqlite3
import importlib.util
from .notifications import update_order_status, get_order_by_id

load_dotenv()
ADMIN_BOT_TOKEN = os.getenv('ADMIN_BOT_TOKEN')
DB_PATH = os.getenv('DB_PATH')

if not ADMIN_BOT_TOKEN:
    raise RuntimeError("ADMIN_BOT_TOKEN не найден в .env файле")

bot = Bot(token=ADMIN_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Загружаем материалы и услуги
def load_materials_and_extras():
    spec = importlib.util.spec_from_file_location('materials', 'bot/materials.py')
    materials_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(materials_mod)
    return materials_mod.MATERIALS, materials_mod.EXTRAS

# Главное меню
def get_main_menu():
    keyboard = [
        [KeyboardButton(text="📋 Все заявки")],
        [KeyboardButton(text="🔧 Заявки в работе")],
        [KeyboardButton(text="💰 Прайс материалов")],
        [KeyboardButton(text="🛠️ Прайс услуг")],
        [KeyboardButton(text="👥 Управление подрядчиками")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    print(f"Админ-бот получил команду /start от пользователя {message.from_user.id}")
    await message.answer(
        "👨‍💼 Админ-панель\n\nВыберите действие:",
        reply_markup=get_main_menu()
    )

@dp.message(F.text == "📋 Все заявки")
async def show_all_orders(message: types.Message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, phone, address, material, area, extras, date, time, price, status FROM orders ORDER BY id DESC')
    orders = c.fetchall()
    conn.close()
    
    if not orders:
        await message.answer("📭 Заявок пока нет")
        return
    
    text = "📋 Все заявки:\n\n"
    for order in orders[:10]:  # Показываем первые 10
        status_emoji = {
            'новая': '🆕',
            'в работе': '🔧',
            'завершенная': '✅'
        }.get(order[10], '❓')
        
        text += f"{status_emoji} <b>Заявка #{order[0]}</b>\n"
        text += f"👤 {order[1]}\n"
        text += f"📞 {order[2]}\n"
        text += f"📍 {order[3]}\n"
        text += f"🏗️ {order[4]} ({order[5]} м²)\n"
        text += f"💰 {order[9]} ₽\n"
        text += f"📅 {order[7]}\n"
        text += f"⏰ {order[8] if order[8] else '-'}\n"
        text += f"🔧 {order[6] if order[6] else 'нет'}\n"
        text += f"📊 Статус: {order[10]}\n"
        text += "─" * 30 + "\n"
    
    if len(orders) > 10:
        text += f"\n... и еще {len(orders) - 10} заявок"
    
    await message.answer(text, parse_mode='HTML')

@dp.message(F.text == "🔧 Заявки в работе")
async def show_orders_in_work(message: types.Message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, phone, address, material, area, extras, date, time, price FROM orders WHERE status = "в работе" ORDER BY id DESC')
    orders = c.fetchall()
    conn.close()
    
    if not orders:
        await message.answer("🔧 Заявок в работе нет")
        return
    
    # Отправляем каждую заявку отдельным сообщением с кнопкой
    for order in orders:
        text = f"🔧 <b>Заявка #{order[0]}</b>\n"
        text += f"👤 {order[1]}\n"
        text += f"📞 {order[2]}\n"
        text += f"📍 {order[3]}\n"
        text += f"🏗️ {order[4]} ({order[5]} м²)\n"
        text += f"💰 {order[9]} ₽\n"
        text += f"📅 {order[7]}\n"
        text += f"⏰ {order[8] if order[8] else '-'}\n"
        text += f"🔧 {order[6] if order[6] else 'нет'}\n"
        
        # Создаем кнопку "Завершить"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Завершить", callback_data=f"complete_{order[0]}")]
        ])
        
        await message.answer(text, parse_mode='HTML', reply_markup=keyboard)

@dp.message(F.text == "💰 Прайс материалов")
async def show_materials_price(message: types.Message):
    MATERIALS, _ = load_materials_and_extras()
    
    text = "💰 <b>Прайс материалов</b>\n\n"
    for material, price in MATERIALS.items():
        text += f"🏗️ <b>{material}</b>\n"
        text += f"💵 {price} ₽/м²\n"
        text += "─" * 20 + "\n"
    
    await message.answer(text, parse_mode='HTML')

@dp.message(F.text == "🛠️ Прайс услуг")
async def show_services_price(message: types.Message):
    _, EXTRAS = load_materials_and_extras()
    
    text = "🛠️ <b>Прайс услуг</b>\n\n"
    for service, price in EXTRAS.items():
        text += f"🔧 <b>{service}</b>\n"
        text += f"💵 {price} ₽\n"
        text += "─" * 20 + "\n"
    
    await message.answer(text, parse_mode='HTML')

@dp.message(F.text == "👥 Управление подрядчиками")
async def manage_contractors(message: types.Message):
    # Заглушка - показываем что функционал в разработке
    await message.answer(
        "👥 <b>Управление подрядчиками</b>\n\n"
        "🔧 Функционал в разработке\n"
        "Здесь будет возможность добавлять и удалять подрядчиков для пересылки заявок.",
        parse_mode='HTML'
    )

# Обработчик всех сообщений для отладки
@dp.message()
async def handle_all_messages(message: types.Message):
    print(f"📨 Получено сообщение от {message.from_user.id} в чате {message.chat.id}")
    print(f"📝 Текст: {message.text}")
    print(f"👤 Пользователь: {message.from_user.first_name} {message.from_user.last_name or ''}")
    print(f"🏷️ Тип чата: {message.chat.type}")
    print("─" * 50)

# Обработчики callback кнопок
@dp.callback_query(F.data.startswith("accept_"))
async def accept_order(callback: types.CallbackQuery):
    order_id = callback.data.split("_")[1]
    
    # Обновляем статус заявки
    await update_order_status(order_id, "в работе")
    
    # Получаем данные заявки для уведомления
    order = await get_order_by_id(order_id)
    
    await callback.answer("✅ Заявка принята в работу!")
    
    # Отправляем уведомление об изменении статуса
    if order:
        text = f"""
✅ <b>Заявка #{order_id} принята в работу</b>

👤 Клиент: {order['name']}
📞 Телефон: {order['phone']}
📍 Адрес: {order['address']}
💰 Стоимость: {order['price']} ₽
"""
        await callback.message.answer(text, parse_mode='HTML')
    
    # Удаляем кнопки из исходного сообщения
    await callback.message.edit_reply_markup(reply_markup=None)

@dp.callback_query(F.data.startswith("contract_"))
async def contract_order(callback: types.CallbackQuery):
    order_id = callback.data.split("_")[1]
    
    # Получаем данные заявки
    order = await get_order_by_id(order_id)
    
    await callback.answer("📤 Заявка передана на подряд!")
    
    # Отправляем заглушку о передаче на подряд
    if order:
        text = f"""
📤 <b>Заявка #{order_id} передана на подряд</b>

👤 Клиент: {order['name']}
📞 Телефон: {order['phone']}
📍 Адрес: {order['address']}
💰 Стоимость: {order['price']} ₽

🔧 <i>Функционал пересылки подрядчикам в разработке</i>
"""
        await callback.message.answer(text, parse_mode='HTML')
    
    # Удаляем кнопки из исходного сообщения
    await callback.message.edit_reply_markup(reply_markup=None)

@dp.callback_query(F.data.startswith("complete_"))
async def complete_order(callback: types.CallbackQuery):
    print(f"🔔 Получен callback: {callback.data}")
    order_id = callback.data.split("_")[1]
    print(f"📋 ID заявки: {order_id}")
    
    # Обновляем статус заявки
    print("🔄 Начинаем обновление статуса...")
    await update_order_status(order_id, "завершенная")
    print("✅ Статус обновлен")
    
    # Получаем данные заявки для уведомления
    order = await get_order_by_id(order_id)
    
    await callback.answer("✅ Заявка завершена!")
    
    # Отправляем уведомление об изменении статуса
    if order:
        text = f"""
✅ <b>Заявка #{order_id} завершена</b>

👤 Клиент: {order['name']}
📞 Телефон: {order['phone']}
📍 Адрес: {order['address']}
💰 Стоимость: {order['price']} ₽
"""
        await callback.message.answer(text, parse_mode='HTML')
    
    # Удаляем кнопку из исходного сообщения
    await callback.message.edit_reply_markup(reply_markup=None)
    print("🎯 Callback обработан успешно")

async def main():
    print("🚀 Админ-бот запускается...")
    print(f"🔑 Токен: {ADMIN_BOT_TOKEN[:10]}...")
    print(f"📁 База данных: {DB_PATH}")
    print("📡 Начинаем polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 