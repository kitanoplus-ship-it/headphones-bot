import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from handlers import start, search, compare, recommendations
from handlers import reviews

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def daily_refresh():
    """Ежедневное обновление кэша отзывов для популярных товаров."""
    from parsers.reviews_manager import collect_reviews
    popular = [
        "Sony WH-1000XM5",
        "Apple AirPods Pro 2",
        "Samsung Galaxy Buds2 Pro",
        "JBL Tune 720BT",
        "Xiaomi Redmi Buds 5 Pro",
    ]
    for name in popular:
        try:
            await collect_reviews(name, force=True)
            logger.info(f"Обновлены отзывы: {name}")
        except Exception as e:
            logger.error(f"Ошибка обновления отзывов [{name}]: {e}")


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не задан! Создай файл .env с BOT_TOKEN=...")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрируем роутеры
    dp.include_router(start.router)
    dp.include_router(search.router)
    dp.include_router(compare.router)
    dp.include_router(recommendations.router)
    dp.include_router(reviews.router)

    # Планировщик — обновление отзывов раз в сутки в 03:00
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(daily_refresh, "cron", hour=3, minute=0)
    scheduler.start()

    logger.info("🤖 Бот запущен!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
