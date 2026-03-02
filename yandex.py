import asyncio
import logging
from typing import Optional
from urllib.parse import quote_plus

from parsers.base import BaseReviewParser, Review
from parsers.browser import new_page

logger = logging.getLogger(__name__)


class YandexMarketParser(BaseReviewParser):
    SOURCE_NAME = "yandex"

    async def search_product_url(self, product_name: str) -> Optional[str]:
        search_url = f"https://market.yandex.ru/search?text={quote_plus(product_name)}&hid=90555"
        async with new_page(ua_index=0) as page:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(2)

            # Берём первый результат поиска
            link = await page.query_selector("a[data-auto='snippet-link']")
            if not link:
                link = await page.query_selector("article a[href*='/product--']")
            if link:
                href = await link.get_attribute("href")
                if href:
                    if href.startswith("/"):
                        href = "https://market.yandex.ru" + href
                    # Приводим к странице отзывов
                    base = href.split("?")[0].rstrip("/")
                    return base + "/reviews"
        return None

    async def fetch_reviews(self, product_url: str, limit: int = 5) -> list[Review]:
        reviews = []
        async with new_page(ua_index=0) as page:
            await page.goto(product_url, wait_until="domcontentloaded", timeout=25000)
            await asyncio.sleep(3)

            # Сортировка по полезности
            try:
                sort_btn = await page.query_selector("button[data-auto='sort-by-useful']")
                if sort_btn:
                    await sort_btn.click()
                    await asyncio.sleep(2)
            except Exception:
                pass

            items = await page.query_selector_all("[data-auto='review']")
            for item in items[:limit]:
                try:
                    author_el = await item.query_selector("[data-auto='author-name']")
                    rating_el = await item.query_selector("[data-auto='rating']")
                    title_el  = await item.query_selector("[data-auto='review-title']")
                    pros_el   = await item.query_selector("[data-auto='review-pros']")
                    cons_el   = await item.query_selector("[data-auto='review-cons']")
                    useful_el = await item.query_selector("[data-auto='useful-count']")

                    author  = (await author_el.inner_text()).strip() if author_el else "Аноним"
                    rating  = int((await rating_el.get_attribute("data-value") or "0"))
                    title   = (await title_el.inner_text()).strip() if title_el else ""
                    pros    = (await pros_el.inner_text()).strip() if pros_el else ""
                    cons    = (await cons_el.inner_text()).strip() if cons_el else ""
                    useful  = int((await useful_el.inner_text()).strip() or "0") if useful_el else 0

                    text = ""
                    if pros:
                        text += f"Плюсы: {pros}\n"
                    if cons:
                        text += f"Минусы: {cons}"

                    if text.strip():
                        reviews.append(Review(
                            source="Яндекс.Маркет",
                            author=author,
                            rating=rating,
                            title=title,
                            text=text.strip(),
                            useful_count=useful,
                            date="",
                        ))
                except Exception as e:
                    logger.debug(f"Ошибка парсинга отзыва YM: {e}")
                    continue

        return reviews
