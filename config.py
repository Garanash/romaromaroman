import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', 'ВАШ_ТОКЕН_ТУТ')
ADMIN_USERS = os.getenv('ADMIN_USERS', 'admin').split(',')  # логины админов через запятую
ADMIN_PASSWORDS = os.getenv('ADMIN_PASSWORDS', 'admin').split(',')  # пароли админов через запятую
DB_PATH = os.getenv('DB_PATH', 'database/bot.db')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'database/uploads') 