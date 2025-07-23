#!/bin/bash

# Остановить все старые процессы бота и админки
pkill -f bot.bot 2>/dev/null
pkill -f web.app 2>/dev/null
sleep 1

# Очистить переменную окружения BOT_TOKEN, чтобы не мешала .env
unset BOT_TOKEN

# Резервное копирование базы данных
if [ -f database/bot.db ]; then
  cp database/bot.db database/bot.db.backup_$(date +%Y%m%d_%H%M%S)
fi

# Инициализация базы
python3 -m database.init_db

# Запуск Telegram-бота в фоне
nohup python3 -m bot.bot > bot.log 2>&1 &

# Запуск админки (Flask) в фоне
nohup python3 -m web.app > admin.log 2>&1 &

echo "Бот и админка запущены!"
echo "Админка: http://127.0.0.1:5000" 