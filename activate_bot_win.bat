@echo off
chcp 65001 >nul
echo ========================================
echo Telegram Bot для заявок на установку потолков
echo Скрипт запуска для Windows
echo ========================================
echo.

echo Останавливаем старые процессы...
taskkill /f /im python.exe 2>nul
taskkill /f /im python3.exe 2>nul
timeout /t 2 /nobreak >nul

echo Очищаем переменные окружения...
set BOT_TOKEN=
set ADMIN_BOT_TOKEN=

echo Создаем резервную копию базы данных...
if exist database\bot.db (
    for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
    set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
    set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
    set "datestamp=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"
    copy database\bot.db database\bot.db.backup_%datestamp%
    echo Резервная копия создана: database\bot.db.backup_%datestamp%
)

echo Инициализируем базу данных...
python -m database.init_db
if %errorlevel% neq 0 (
    echo Ошибка инициализации базы данных!
    pause
    exit /b 1
)

echo Освобождаем порт 5001...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5001') do (
    taskkill /f /pid %%a 2>nul
)
timeout /t 2 /nobreak >nul

echo Запускаем основной Telegram-бот...
start /b python -m bot.bot > bot.log 2>&1

echo Запускаем админ-бот...
start /b python -m admin_bot.admin_bot > admin_bot.log 2>&1

echo Запускаем веб-админку...
start /b python -m web.app > admin.log 2>&1

echo.
echo ========================================
echo Все сервисы запущены!
echo ========================================
echo.
echo Веб-админка: http://127.0.0.1:5001
echo Логин: admin
echo Пароль: admin
echo.
echo Админ-бот: запущен
echo Основной бот: запущен
echo.
echo Логи:
echo - Основной бот: bot.log
echo - Админ-бот: admin_bot.log
echo - Веб-админка: admin.log
echo.
echo Для остановки всех процессов выполните:
echo taskkill /f /im python.exe
echo.
pause 