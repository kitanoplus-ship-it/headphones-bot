"""
Сборщик отзывов со всех маркетплейсов.
Запускает парсеры параллельно, кэширует результат в JSON на 24 часа.
"""
import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from dataclasses import asdict

from config import REVIEWS_DIR, REVIEWS_TTL_HOURS, REVIEWS_PER_SOURCE
from parsers.base import Review
from parsers.yandex import YandexMarketParser
from parsers.ozon import OzonParser
from parsers.dns import DNSParser
from parsers.wildberries import WildberriesParser

logger = logging.getLogger(__name__)

os.makedirs(REVIEWS_DIR, exist_ok=True)

PARSERS = {
    "yandex":      YandexMarketParser,
    "ozon":        OzonParser,
    "dns":         DNSParser,
    "wildberries": WildberriesParser,
}


def _cache_path(product_name: str) -> str:
    safe = product_name.lower().replace(" ", "_")[:60]
    return os.path.join(REVIEWS_DIR, f"{safe}.json")


def _load_cache(product_name: str) -> dict | None:
    path = _cache_path(product_name)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cached_at = datetime.fromisoformat(data.get("cached_at", "2000-01-01"))
    if datetime.now() - cached_at > timedelta(hours=REVIEWS_TTL_HOURS):
        return None
    return data


def _save_cache(product_name: str, data: dict):
    path = _cache_path(product_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def _parse_one(source: str, product_name: str) -> list[dict]:
    cls = PARSERS.get(source)
    if not cls:
        return []
    parser = cls()
    reviews: list[Review] = await parser.get_reviews(product_name, limit=REVIEWS_PER_SOURCE)
    return [asdict(r) for r in reviews]


async def collect_reviews(product_name: str, force: bool = False) -> dict:
    """
    Возвращает словарь:
    {
        "product": "...",
        "cached_at": "...",
        "reviews": { "yandex": [...], "ozon": [...], ... },
        "all_reviews": [...]   # все отзывы в одном списке
    }
    """
    if not force:
        cached = _load_cache(product_name)
        if cached:
            logger.info(f"Отзывы для '{product_name}' взяты из кэша")
            return cached

    logger.info(f"Парсим отзывы для '{product_name}' со всех маркетплейсов...")

    tasks = {
        source: asyncio.create_task(_parse_one(source, product_name))
        for source in PARSERS
    }
    results = {}
    for source, task in tasks.items():
        try:
            results[source] = await task
        except Exception as e:
            logger.error(f"Ошибка сбора отзывов [{source}]: {e}")
            results[source] = []

    all_reviews = []
    for lst in results.values():
        all_reviews.extend(lst)

    # Сортируем все по useful_count
    all_reviews.sort(key=lambda r: r.get("useful_count", 0), reverse=True)

    data = {
        "product": product_name,
        "cached_at": datetime.now().isoformat(),
        "reviews": results,
        "all_reviews": all_reviews[:20],   # топ-20 полезных
    }
    _save_cache(product_name, data)
    return data
