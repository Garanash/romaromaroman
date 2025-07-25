# 🚀 Быстрый запуск

## Для macOS/Linux

1. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Настройте переменные окружения:**
   ```bash
   cp env.example .env
   # Отредактируйте .env файл, добавив ваши токены
   ```

3. **Запустите систему:**
   ```bash
   chmod +x activate_bot.sh
   ./activate_bot.sh
   ```

## Для Windows

1. **Установите зависимости:**
   ```cmd
   pip install -r requirements.txt
   ```

2. **Настройте переменные окружения:**
   ```cmd
   copy env.example .env
   # Отредактируйте .env файл, добавив ваши токены
   ```

3. **Запустите систему:**
   ```cmd
   activate_bot_win.bat
   ```

## Что нужно настроить в .env

```env
# Основной бот (получить у @BotFather)
BOT_TOKEN=your_main_bot_token_here

# Админ-бот (создать отдельного бота у @BotFather)
ADMIN_BOT_TOKEN=your_admin_bot_token_here

# Ваш Chat ID (отправить сообщение админ-боту)
ADMIN_CHAT_ID=your_personal_chat_id_here
```

## Доступ к системе

- **Веб-админка**: http://127.0.0.1:5001
- **Логин**: admin
- **Пароль**: admin

## Остановка системы

**macOS/Linux:**
```bash
pkill -f python3
```

**Windows:**
```cmd
taskkill /f /im python.exe
```

## Логи

- `bot.log` - основной бот
- `admin_bot.log` - админ-бот
- `admin.log` - веб-админка 