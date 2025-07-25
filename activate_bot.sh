#!/bin/bash

# Остановить все старые процессы бота и админки
pkill -f bot.bot 2>/dev/null
pkill -f web.app 2>/dev/null
pkill -f admin_bot.admin_bot 2>/dev/null
sleep 1

# Очистить переменные окружения, чтобы не мешали .env
unset BOT_TOKEN
unset ADMIN_BOT_TOKEN

# Резервное копирование базы данных
if [ -f database/bot.db ]; then
  cp database/bot.db database/bot.db.backup_$(date +%Y%m%d_%H%M%S)
fi

# Инициализация базы
python3 -m database.init_db

# Запуск основного Telegram-бота в фоне
nohup python3 -m bot.bot > bot.log 2>&1 &

# Запуск админ-бота в фоне
nohup python3 -m admin_bot.admin_bot > admin_bot.log 2>&1 &

# Освобождение порта 5001 для веб-админки
echo "Освобождаем порт 5001..."
lsof -ti:5001 | xargs kill -9 2>/dev/null || true
sleep 2

# Запуск веб-админки (Flask) в фоне
nohup python3 -m web.app > admin.log 2>&1 &

echo "Все сервисы запущены!"
echo "Веб-админка: http://127.0.0.1:5001"
echo "Админ-бот: запущен" 