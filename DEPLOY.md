# Развертывание на Vercel

## Переменные окружения

В панели Vercel для проекта `septik-plus`:
1. Перейдите в **Settings** → **Environment Variables**
2. Добавьте переменные:

| Имя | Значение |
|-----|----------|
| `TG_BOT_TOKEN` | Токен Telegram бота (например: `8632041506:AAGLfnE...`) |
| `TG_CHAT_IDS` | ID чатов через запятую (например: `8029756633,7332528461`) |

## Структура проекта

```
septik-plus2/
├── index.html      # Главная страница
├── api/
│   └── send.js     # Serverless функция для отправки в Telegram
├── vercel.json     # Конфигурация Vercel
└── package.json    # Node.js dependencies
```

## Как работает:

1. Форма на сайте отправляет POST на `/api/send`
2. Vercel вызывает `api/send.js`
3. Функция читает `TG_BOT_TOKEN` и `TG_CHAT_IDS` из env
4. Отправляет сообщение во ВСЕ указанные чаты Telegram
5. Возвращает `{ ok: true }`

## Проверка после деплоя:

1. Откройте ваш сайт на Vercel
2. Заполните форму и отправьте
3. Проверьте Telegram — сообщение должно прийти во все чаты
