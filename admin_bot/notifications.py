import os
from aiogram import Bot, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import sqlite3

load_dotenv()
ADMIN_BOT_TOKEN = os.getenv('ADMIN_BOT_TOKEN')
DB_PATH = os.getenv('DB_PATH')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', '1904520384')  # ID чата для уведомлений

async def send_new_order_notification(order_data):
    """Отправляет уведомление о новой заявке с кнопками действий"""
    if not ADMIN_BOT_TOKEN:
        return
    
    admin_bot = Bot(token=ADMIN_BOT_TOKEN)
    
    # Создаем кнопки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять в работу", callback_data=f"accept_{order_data.get('id')}"),
            InlineKeyboardButton(text="📤 Отдать на подряд", callback_data=f"contract_{order_data.get('id')}")
        ]
    ])
    
    # Формируем текст уведомления
    extras = ', '.join(order_data.get('extras', [])) if order_data.get('extras') else 'нет'
    text = f"""
🆕 <b>Новая заявка #{order_data.get('id')}</b>

👤 <b>Клиент:</b> {order_data.get('name')}
📞 <b>Телефон:</b> {order_data.get('phone')}
📍 <b>Адрес:</b> {order_data.get('address')}

🏗️ <b>Работа:</b>
• Материал: {order_data.get('material')}
• Площадь: {order_data.get('area')} м²
• Доп. работы: {extras}

💰 <b>Стоимость:</b> {order_data.get('price')} ₽

📅 <b>Дата замера:</b> {order_data.get('date')}
⏰ <b>Время:</b> {order_data.get('time') if order_data.get('time') else '-'}

📸 <b>Фото:</b> {'есть' if order_data.get('photos') else 'нет'}
"""
    
    try:
        print(f"Отправляем уведомление в чат {ADMIN_CHAT_ID}")
        await admin_bot.send_message(
            chat_id=int(ADMIN_CHAT_ID),  # ID админ-чата
            text=text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        print("Уведомление отправлено успешно")
        
        # Отправляем фото если есть
        photos = order_data.get('photos', [])
        for photo in photos:
            try:
                with open(f'database/uploads/{photo}', 'rb') as f:
                    await admin_bot.send_photo(int(ADMIN_CHAT_ID), f)
            except Exception as e:
                print(f"Ошибка отправки фото: {e}")
                
    except Exception as e:
        print(f"Ошибка отправки уведомления: {e}")
        print(f"Токен админ-бота: {ADMIN_BOT_TOKEN[:10]}...")
        print(f"ID чата: {ADMIN_CHAT_ID}")
    finally:
        await admin_bot.session.close()

async def update_order_status(order_id, new_status):
    """Обновляет статус заявки в базе данных"""
    print(f"🔄 Обновляем статус заявки {order_id} на '{new_status}'")
    print(f"📁 Путь к БД: {DB_PATH}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Проверяем текущий статус
        c.execute('SELECT status FROM orders WHERE id = ?', (order_id,))
        current_status = c.fetchone()
        print(f"📋 Текущий статус: {current_status[0] if current_status else 'не найден'}")
        
        # Обновляем статус
        c.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
        rows_affected = c.rowcount
        print(f"📊 Затронуто строк: {rows_affected}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Статус успешно обновлен на '{new_status}'")
        
    except Exception as e:
        print(f"❌ Ошибка обновления статуса: {e}")
        if 'conn' in locals():
            conn.close()

async def get_order_by_id(order_id):
    """Получает заявку по ID"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, phone, address, material, area, extras, photos, date, time, price, status FROM orders WHERE id = ?', (order_id,))
    order = c.fetchone()
    conn.close()
    
    if order:
        return {
            'id': order[0],
            'name': order[1],
            'phone': order[2],
            'address': order[3],
            'material': order[4],
            'area': order[5],
            'extras': order[6].split(', ') if order[6] else [],
            'photos': order[7].split(', ') if order[7] else [],
            'date': order[8],
            'time': order[9],
            'price': order[10],
            'status': order[11]
        }
    return None 