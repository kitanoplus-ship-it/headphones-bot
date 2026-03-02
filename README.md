# 🎧 Headphones Bot

Telegram-бот для поиска, сравнения наушников и анализа отзывов из российского сегмента (Яндекс.Маркет, DNS, Citilink, Ozon, Wildberries).

## Возможности

- 🔍 **Поиск** — свободный ввод бренда или названия
- ⚖️ **Сравнение** до 3 моделей бок о бок
- 🏆 **Топ** по рейтингу, цене, отзывам
- 💡 **Подборки**: бюджетные, с ANC, флагманы и др.
- 📝 **Анализ отзывов** — DeepSeek собирает топ-20 отзывов с 4 маркетплейсов и выявляет плюсы/минусы

## Быстрый старт

### 1. Клонируй репозиторий
```bash
git clone https://github.com/YOUR_USERNAME/headphones-bot.git
cd headphones-bot
```

### 2. Установи зависимости
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 3. Создай `.env`
```bash
cp .env.example .env
# Вставь BOT_TOKEN и DEEPSEEK_API_KEY
```

### 4. Запусти
```bash
python bot.py
```

## Деплой через GitHub Actions

Добавь секреты в `Settings → Secrets`:
- `BOT_TOKEN`
- `DEEPSEEK_API_KEY`
- `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`

## Структура проекта

```
headphones-bot/
├── bot.py                    # точка входа + планировщик
├── config.py                 # настройки
├── db.py                     # JSON-база наушников
├── keyboards.py              # кнопки и меню
├── formatters.py             # форматирование карточек
├── deepseek_analyzer.py      # анализ отзывов через DeepSeek
├── handlers/
│   ├── start.py
│   ├── search.py             # свободный ввод бренда/названия
│   ├── compare.py
│   ├── recommendations.py
│   └── reviews.py            # сбор и анализ отзывов
├── parsers/
│   ├── base.py               # базовый класс
│   ├── browser.py            # Playwright + stealth
│   ├── reviews_manager.py    # параллельный сбор + кэш 24ч
│   ├── yandex.py
│   ├── ozon.py
│   ├── dns.py
│   └── wildberries.py        # использует публичное API WB
├── data/
│   ├── headphones.json
│   └── reviews/              # кэш отзывов (JSON, TTL 24ч)
└── .github/workflows/deploy.yml
```

## Как работает анализ отзывов

```
Пользователь вводит название
         ↓
Playwright параллельно парсит:
  Яндекс.Маркет / Ozon / DNS / Wildberries
         ↓
Топ-20 самых полезных отзывов
         ↓
DeepSeek анализирует → плюсы / минусы / вывод
         ↓
Кэш на 24 часа + ежесуточное обновление в 03:00
```
