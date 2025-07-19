#!/bin/bash

# Инициализация базы
python3 -m database.init_db

# Запуск Telegram-бота в фоне
nohup python3 -m bot.bot > bot.log 2>&1 &

# Запуск админки (Flask) в фоне
nohup python3 -m web.app > admin.log 2>&1 &

echo "Бот и админка запущены!"
echo "Админка: http://127.0.0.1:5000" 