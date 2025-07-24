import re
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from .materials import MATERIALS, EXTRAS
from .states import OrderFSM
import os
from datetime import datetime
from .calendar import get_calendar
import sqlite3
from dotenv import load_dotenv
import importlib.util
load_dotenv()
DB_PATH = os.getenv('DB_PATH')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')

router = Router()

# Валидация имени
@router.message(OrderFSM.name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not re.match(r'^[А-Яа-яA-Za-z]{2,}$', name):
        await message.answer('Имя должно содержать минимум 2 буквы. Попробуйте ещё раз.')
        return
    await state.update_data(name=name)
    await message.answer('Введите номер телефона (в любом формате):', reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='Отмена')]], resize_keyboard=True))
    await state.set_state(OrderFSM.phone)

# Валидация телефона
@router.message(OrderFSM.phone)
async def process_phone(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text.lower() == 'отмена':
        await state.clear()
        await message.answer('Заявка отменена.', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Создать новую заявку')]], resize_keyboard=True))
        return
    # Простейшая нормализация
    digits = re.sub(r'\D', '', text)
    if digits.startswith('8'):
        digits = '7' + digits[1:]
    if len(digits) == 11 and digits.startswith('7'):
        phone = f'+{digits}'
        await state.update_data(phone=phone)
        await message.answer('Введите адрес для вызова замерщика:', reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='Назад'), KeyboardButton(text='Отмена')]], resize_keyboard=True))
        await state.set_state(OrderFSM.address)
    else:
        await message.answer('Не удалось распознать номер. Введите в формате +7XXXXXXXXXX или 8XXXXXXXXXX.')

# Ввод адреса (кнопки материалов)
@router.message(OrderFSM.address)
async def process_address(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text.lower() == 'отмена':
        await state.clear()
        await message.answer('Заявка отменена.', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Создать новую заявку')]], resize_keyboard=True))
        return
    if text.lower() == 'назад':
        await message.answer('Введите номер телефона:', reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='Отмена')]], resize_keyboard=True))
        await state.set_state(OrderFSM.phone)
        return
    if len(text) < 5:
        await message.answer('Адрес слишком короткий. Введите подробнее.')
        return
    await state.update_data(address=text)
    # Динамически загружаем материалы
    spec = importlib.util.spec_from_file_location('materials', 'bot/materials.py')
    materials_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(materials_mod)
    MATERIALS = materials_mod.MATERIALS
    buttons = [[KeyboardButton(text=f'{m} ({MATERIALS[m]}₽/м²)')] for m in MATERIALS.keys()]
    buttons.append([KeyboardButton(text='Назад'), KeyboardButton(text='Отмена')])
    await message.answer('Выберите материал потолка:', reply_markup=ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True))
    await state.set_state(OrderFSM.material)

# Выбор материала (кнопки материалов)
@router.message(OrderFSM.material)
async def process_material(message: types.Message, state: FSMContext):
    text = message.text.strip()
    # Динамически загружаем материалы
    spec = importlib.util.spec_from_file_location('materials', 'bot/materials.py')
    materials_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(materials_mod)
    MATERIALS = materials_mod.MATERIALS
    # Если кнопка содержит цену, извлекаем только название
    if ' (' in text and '₽/м²' in text:
        text = text[:text.rfind(' (')]
    if text.lower() == 'отмена':
        await state.clear()
        await message.answer('Заявка отменена.', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Создать новую заявку')]], resize_keyboard=True))
        return
    if text.lower() == 'назад':
        buttons = [[KeyboardButton(text=f'{m} ({MATERIALS[m]}₽/м²)')] for m in MATERIALS.keys()]
        buttons.append([KeyboardButton(text='Назад'), KeyboardButton(text='Отмена')])
        await message.answer('Выберите материал потолка:', reply_markup=ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True))
        await state.set_state(OrderFSM.address)
        return
    if text not in MATERIALS:
        await message.answer('Пожалуйста, выберите материал из списка кнопок.')
        return
    await state.update_data(material=text)
    await message.answer('Введите площадь потолка (м²):', reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='Назад'), KeyboardButton(text='Отмена')]], resize_keyboard=True))
    await state.set_state(OrderFSM.area)

# Ввод площади (кнопки доп. услуг)
@router.message(OrderFSM.area)
async def process_area(message: types.Message, state: FSMContext):
    text = message.text.strip().replace(',', '.')
    if text.lower() == 'отмена':
        await state.clear()
        await message.answer('Заявка отменена.', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Создать новую заявку')]], resize_keyboard=True))
        return
    if text.lower() == 'назад':
        # Динамически загружаем материалы
        spec = importlib.util.spec_from_file_location('materials', 'bot/materials.py')
        materials_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(materials_mod)
        MATERIALS = materials_mod.MATERIALS
        buttons = [[KeyboardButton(text=f'{m} ({MATERIALS[m]}₽/м²)')] for m in MATERIALS.keys()]
        buttons.append([KeyboardButton(text='Назад'), KeyboardButton(text='Отмена')])
        await message.answer('Выберите материал потолка:', reply_markup=ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True))
        await state.set_state(OrderFSM.material)
        return
    try:
        area = float(text)
        if not (1 <= area <= 1000):
            raise ValueError
    except ValueError:
        await message.answer('Введите корректную площадь (от 1 до 1000 м²) если нужно больше введите 999.')
        return
    await state.update_data(area=area)
    # Динамически загружаем доп. услуги
    spec = importlib.util.spec_from_file_location('materials', 'bot/materials.py')
    materials_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(materials_mod)
    EXTRAS = dict(materials_mod.EXTRAS)
    buttons = [[KeyboardButton(text=f'{extra} ({EXTRAS[extra]}₽)')] for extra in EXTRAS.keys()]
    buttons.append([KeyboardButton(text='Далее'), KeyboardButton(text='Назад'), KeyboardButton(text='Отмена')])
    await message.answer('Выберите дополнительные работы (можно несколько, затем "Далее"):', reply_markup=ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True))
    await state.set_state(OrderFSM.extras)

# Выбор доп. работ (динамическая проверка)
@router.message(OrderFSM.extras)
async def process_extras(message: types.Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    selected = data.get('extras', [])
    # Динамически загружаем доп. услуги
    spec = importlib.util.spec_from_file_location('materials', 'bot/materials.py')
    materials_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(materials_mod)
    EXTRAS = dict(materials_mod.EXTRAS)
    if text.lower() == 'отмена':
        await state.clear()
        await message.answer('Заявка отменена.', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Создать новую заявку')]], resize_keyboard=True))
        return
    if text.lower() == 'назад':
        await message.answer('Введите площадь потолка (м²):', reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='Назад'), KeyboardButton(text='Отмена')]], resize_keyboard=True))
        await state.set_state(OrderFSM.area)
        return
    if text.lower() == 'далее':
        await state.update_data(extras=selected)
        await message.answer('Пожалуйста, отправьте фото помещения (можно несколько, затем "Далее") или просто далее:', reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='Далее'), KeyboardButton(text='Назад'), KeyboardButton(text='Отмена')]], resize_keyboard=True))
        await state.set_state(OrderFSM.photos)
        return
    # Проверяем по кнопке с ценой
    chosen = None
    for extra in EXTRAS.keys():
        if text.startswith(extra):
            chosen = extra
            break
    if chosen:
        if chosen not in selected:
            selected.append(chosen)
        await state.update_data(extras=selected)
        # Пересобираем кнопки без выбранных опций
        remaining = [e for e in EXTRAS.keys() if e not in selected]
        buttons = [[KeyboardButton(text=f'{e} ({EXTRAS[e]}₽)')] for e in remaining]
        buttons.append([KeyboardButton(text='Далее'), KeyboardButton(text='Назад'), KeyboardButton(text='Отмена')])
        await message.answer(f'Добавлено: {chosen}. Можно выбрать ещё или нажать "Далее".', reply_markup=ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True))
        return
    await message.answer('Пожалуйста, выберите опцию из списка или нажмите "Далее".')

# Загрузка фото
@router.message(OrderFSM.photos, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])
    file_id = message.photo[-1].file_id
    file = await message.bot.get_file(file_id)
    file_path = file.file_path
    file_name = f'{message.from_user.id}_{file_id}.jpg'
    dest = os.path.join(UPLOAD_FOLDER, file_name)
    await message.bot.download(file, dest)
    photos.append(file_name)
    await state.update_data(photos=photos)
    await message.answer('Фото добавлено. Можно отправить ещё или нажать "Далее".')

@router.message(OrderFSM.photos)
async def process_photos_control(message: types.Message, state: FSMContext):
    text = message.text.strip().lower()
    data = await state.get_data()
    if text == 'отмена':
        await state.clear()
        await message.answer('Заявка отменена.', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Создать новую заявку')]], resize_keyboard=True))
        return
    if text == 'назад':
        buttons = [[KeyboardButton(text=extra)] for extra in EXTRAS.keys()]
        buttons.append([KeyboardButton(text='Далее'), KeyboardButton(text='Назад'), KeyboardButton(text='Отмена')])
        await message.answer('Выберите дополнительные работы (можно несколько, затем "Далее"):', reply_markup=ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True))
        await state.set_state(OrderFSM.extras)
        return
    if text == 'далее':
        await state.update_data(photos=data.get('photos', []))
        await state.set_state(OrderFSM.date)
        await show_calendar(message, state)
        return
    await message.answer('Пожалуйста, отправьте фото или нажмите "Далее".')

# Показ календаря для выбора даты
@router.message(OrderFSM.date)
async def show_calendar(message: types.Message, state: FSMContext):
    from .calendar import get_calendar
    await message.answer('Выберите дату замера:', reply_markup=get_calendar())

@router.callback_query(F.data.startswith('cal_'), OrderFSM.date)
async def process_calendar_month(callback: types.CallbackQuery, state: FSMContext):
    from .calendar import get_calendar
    _, year, month = callback.data.split('_')
    year, month = int(year), int(month)
    await callback.message.edit_reply_markup(reply_markup=get_calendar(year, month))
    await callback.answer()

@router.callback_query(F.data.startswith('date_'), OrderFSM.date)
async def process_date_callback(callback: types.CallbackQuery, state: FSMContext):
    from datetime import datetime
    date_str = callback.data[5:]
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if date < datetime.today().date():
            await callback.answer('Нельзя выбрать прошедшую дату.', show_alert=True)
            return
        await state.update_data(date=str(date))
        await callback.message.edit_text(f'Дата замера выбрана: {date.strftime("%d.%m.%Y")}', reply_markup=None)
        # Переход к выбору времени
        await show_time_picker(callback.message, state)
        await state.set_state(OrderFSM.time)
    except Exception:
        await callback.answer('Ошибка выбора даты.', show_alert=True)

# Показываем выбор времени (инлайн-кнопки)
async def show_time_picker(message, state):
    import sqlite3
    import os
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
    DB_PATH = os.getenv('DB_PATH')
    data = await state.get_data()
    date = data.get('date')
    times = [f'{h:02d}:00' for h in range(9, 22)]
    # Получаем занятые времена на эту дату
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT time FROM orders WHERE date=? AND status IN ('новая', 'в работе')", (date,))
    busy_times = set(row[0] for row in c.fetchall())
    conn.close()
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=(t if t not in busy_times else '-'),
                    callback_data=(f'time_{t}' if t not in busy_times else 'ignore')
                ) for t in times[i:i+4]
            ]
            for i in range(0, len(times), 4)
        ]
    )
    await message.answer('Выберите время замера:', reply_markup=kb)

@router.callback_query(F.data == 'ignore', OrderFSM.time)
async def ignore_time_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer('Это время уже занято.', show_alert=True)

@router.callback_query(F.data.startswith('time_'), OrderFSM.time)
async def process_time_callback(callback: types.CallbackQuery, state: FSMContext):
    time_str = callback.data[5:]
    await state.update_data(time=time_str)
    await callback.message.edit_text(f'Время замера выбрано: {time_str}', reply_markup=None)
    # Переход к подтверждению заявки
    await show_order_summary(callback.message, state)
    from .states import OrderFSM
    await state.set_state(OrderFSM.confirm)

# Функция для показа сводки заказа и подтверждения
async def show_order_summary(message, state):
    data = await state.get_data()
    # Динамически загружаем материалы и услуги
    spec = importlib.util.spec_from_file_location('materials', 'bot/materials.py')
    materials_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(materials_mod)
    MATERIALS = materials_mod.MATERIALS
    EXTRAS = dict(materials_mod.EXTRAS)
    extras = data.get('extras', [])
    area = data.get('area', 0)
    material = data.get('material', '')
    # Цена материала
    price = MATERIALS.get(material, 0) * area
    # Цена монтажа (всегда включается)
    price_montage = 450 * area
    # Цена доп. услуг
    extras_price = sum(EXTRAS.get(e, 0) for e in extras)
    total = price + price_montage + extras_price
    summary = f"""
<b>Проверьте заявку:</b>
Имя: {data.get('name')}
Телефон: {data.get('phone')}
Адрес: {data.get('address')}
Материал: {material}
Площадь: {area} м²
Доп. работы: Монтаж потолка (450₽/м²){', ' + ', '.join(extras) if extras else ''}
Дата замера: {data.get('date')}
Время замера: {data.get('time') if data.get('time') else '-'}
Фото: {'есть' if data.get('photos') else 'нет'}

<b>приблизительная стоимость по заявке: {total} ₽</b>
"""
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Подтвердить'), KeyboardButton(text='Отмена')]], resize_keyboard=True)
    await message.answer(summary, reply_markup=kb, parse_mode='HTML')
    await state.update_data(price=total)

@router.message(OrderFSM.confirm)
async def process_confirm(message: types.Message, state: FSMContext):
    text = message.text.strip().lower()
    if text == 'отмена':
        await state.clear()
        await message.answer('Заявка отменена.', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Создать новую заявку')]], resize_keyboard=True))
        return
    if text == 'подтвердить':
        data = await state.get_data()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT INTO orders (name, phone, address, material, area, extras, photos, date, time, price, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            data.get('name'),
            data.get('phone'),
            data.get('address'),
            data.get('material'),
            data.get('area'),
            ', '.join(data.get('extras', [])),
            ', '.join(data.get('photos', [])),
            data.get('date'),
            data.get('time'),
            data.get('price'),
            'новая',
        ))
        conn.commit()
        conn.close()
        # Уведомление мастеру
        await notify_master(message.bot, data)
        await state.clear()
        await message.answer('Ваша заявка принята! Мы свяжемся с вами в ближайшее время.', reply_markup=ReplyKeyboardRemove())
        return
    await message.answer('Пожалуйста, подтвердите или отмените заявку.')

# Уведомление мастеру в Telegram
async def notify_master(bot, data):
    master_id = 5137827921
    extras = ', '.join(data.get('extras', [])) if data.get('extras') else 'нет'
    photos = data.get('photos', [])
    text = f"""
<b>Новая заявка!</b>
Имя: {data.get('name')}
Телефон: {data.get('phone')}
Адрес: {data.get('address')}
Материал: {data.get('material')}
Площадь: {data.get('area')} м²
Доп. работы: {extras}
Дата замера: {data.get('date')}
Время замера: {data.get('time')}
Цена: {data.get('price')} ₽
"""
    await bot.send_message(master_id, text, parse_mode='HTML')
    # Отправка фото (если есть)
    for photo in photos:
        try:
            with open(f'database/uploads/{photo}', 'rb') as f:
                await bot.send_photo(master_id, f)
        except Exception:
            pass 

# Хендлер для кнопки 'Создать новую заявку'
@router.message(lambda m: m.text and m.text.lower() == 'создать новую заявку')
async def restart_order(message: types.Message, state: FSMContext):
    await state.clear()
    from .bot import cmd_start
    await cmd_start(message, state)

# Везде, где заявка отменена:
# await state.clear()
# await message.answer('Заявка отменена.', reply_markup=ReplyKeyboardRemove())
# заменить на:
# await state.clear()
# await message.answer('Заявка отменена.', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Создать новую заявку')]], resize_keyboard=True))

# Везде, где эти кнопки используются (OrderFSM.extras, OrderFSM.photos -> назад и т.д.) 