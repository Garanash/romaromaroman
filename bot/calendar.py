from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import calendar
import sqlite3
from config import DB_PATH

RU_MONTHS = [
    '', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
]
RU_WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

def get_weekends():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT date FROM weekends')
    weekends = set(row[0] for row in c.fetchall())
    conn.close()
    return weekends

def get_calendar(year=None, month=None):
    today = datetime.today().date()
    if year is None or month is None:
        year, month = today.year, today.month
    cal = calendar.monthcalendar(year, month)
    weekends = get_weekends()
    kb = []
    kb.append([InlineKeyboardButton(text=f'{RU_MONTHS[month]} {year}', callback_data='ignore')])
    kb.append([InlineKeyboardButton(text=wd, callback_data='ignore') for wd in RU_WEEKDAYS])
    for week in cal:
        row = []
        for i, day in enumerate(week):
            if day == 0:
                row.append(InlineKeyboardButton(text=' ', callback_data='ignore'))
            else:
                date_obj = datetime(year, month, day).date()
                date_str = date_obj.strftime('%Y-%m-%d')
                if date_obj < today or date_str in weekends:
                    row.append(InlineKeyboardButton(text='·', callback_data='ignore'))
                else:
                    row.append(InlineKeyboardButton(text=str(day), callback_data=f'date_{date_obj}'))
        kb.append(row)
    prev_month = (month - 1) or 12
    prev_year = year - 1 if month == 1 else year
    next_month = (month % 12) + 1
    next_year = year + 1 if month == 12 else year
    nav = [
        InlineKeyboardButton(text='◀️', callback_data=f'cal_{prev_year}_{prev_month}'),
        InlineKeyboardButton(text='Сегодня', callback_data=f'date_{today}'),
        InlineKeyboardButton(text='▶️', callback_data=f'cal_{next_year}_{next_month}')
    ]
    kb.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=kb) 