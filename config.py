import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
HEADPHONES_FILE = os.path.join(DATA_DIR, "headphones.json")
REVIEWS_DIR = os.path.join(DATA_DIR, "reviews")
CACHE_TTL_HOURS = 6
REVIEWS_TTL_HOURS = 24

HEADPHONE_TYPES = {
    "in_ear": "Вкладыши (TWS/проводные)",
    "on_ear": "Накладные",
    "over_ear": "Полноразмерные",
}

COMPARE_FIELDS = [
    ("name", "📱 Название"),
    ("price", "💰 Цена"),
    ("type", "🎧 Тип"),
    ("anc", "🔇 Шумоподавление"),
    ("battery_hours", "🔋 Батарея (ч)"),
    ("rating", "⭐ Рейтинг"),
    ("reviews_count", "💬 Отзывы"),
    ("shop", "🏪 Магазин"),
]

# Маркетплейсы для парсинга отзывов
REVIEW_SOURCES = ["yandex", "ozon", "dns", "wildberries"]
REVIEWS_PER_SOURCE = 5   # 5 с каждого = 20 итого (топ-полезные)

DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
