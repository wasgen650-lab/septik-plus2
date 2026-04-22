# Развертывание на Vercel

## Шаг 1: Установка переменных окружения

В панели Vercel для проекта `septik-plus`:
1. Перейдите в **Settings** → **Environment Variables**
2. Добавьте две переменные:

```
TG_BOT_TOKEN = 8632041506:AAGLfnE--AoAwsHM6wBra-rQt5p3Txzil98
TG_CHAT_IDS = 8029756633,7332528461
```

## Шаг 2: Push изменений в GitHub

```bash
git add .
git commit -m "Fix: Migrate PHP API to Node.js for Vercel"
git push origin main
```

## Что было исправлено:

✅ **api/send.js** - новая Node.js serverless функция (вместо send.php)
✅ **index.html** - обновлен путь API: `/api/send` (вместо `api/send.php`)
✅ **package.json** - конфигурация Node.js
✅ **vercel.json** - маршруты для Vercel

## Как это работает:

1. Когда вы отправляете форму, она делает POST запрос к `/api/send`
2. Vercel перенаправляет это на `api/send.js`
3. Функция берет `TG_BOT_TOKEN` и `TG_CHAT_IDS` из переменных окружения
4. Отправляет сообщение в оба чата Telegram
5. Возвращает `{ ok: true }` при успехе

## Проверка:

После push'а:
- Vercel автоматически пересоберет проект
- Проверьте вкладку **Deployments** на vercel.com
- Откройте сайт и попробуйте отправить форму
- Сообщение должно прийти в оба чата Telegram

## Безопасность:

⚠️ **Важно:** Токен бота и chat ID-ы теперь хранятся в переменных окружения Vercel (защищенное хранилище), а не в коде.
