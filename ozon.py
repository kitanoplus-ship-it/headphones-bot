import asyncio
import logging
from typing import Optional
from urllib.parse import quote_plus

from parsers.base import BaseReviewParser, Review
from parsers.browser import new_page

logger = logging.getLogger(__name__)


class OzonParser(BaseReviewParser):
    SOURCE_NAME = "ozon"

    async def search_product_url(self, product_name: str) -> Optional[str]:
        search_url = f"https://www.ozon.ru/search/?text={quote_plus(product_name)}&category=15722"
        async with new_page(ua_index=1) as page:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(3)

            link = await page.query_selector("a.tile-hover-target")
            if not link:
                link = await page.query_selector("[data-widget='searchResultsV2'] a")
            if link:
                href = await link.get_attribute("href")
                if href:
                    if href.startswith("/"):
                        href = "https://www.ozon.ru" + href
                    base = href.split("/?")[0].rstrip("/")
                    return base + "/reviews/"
        return None

    async def fetch_reviews(self, product_url: str, limit: int = 5) -> list[Review]:
        reviews = []
        async with new_page(ua_index=1) as page:
            await page.goto(product_url, wait_until="domcontentloaded", timeout=25000)
            await asyncio.sleep(3)

            # Сортировка по полезности
            try:
                sort_btns = await page.query_selector_all("button")
                for btn in sort_btns:
                    txt = (await btn.inner_text()).lower()
                    if "полезн" in txt:
                        await btn.click()
                        await asyncio.sleep(2)
                        break
            except Exception:
                pass

            items = await page.query_selector_all("[data-widget='webReviewItem']")
            if not items:
                items = await page.query_selector_all("div.y8o_23")

            for item in items[:limit]:
                try:
                    author_el  = await item.query_selector("span.tsBody500Medium")
                    rating_el  = await item.query_selector("div[data-rating]")
                    text_el    = await item.query_selector("span.tsBody400Small")
                    useful_el  = await item.query_selector("span.tsBodyControl400Small")

                    author  = (await author_el.inner_text()).strip() if author_el else "Аноним"
                    rating  = int((await rating_el.get_attribute("data-rating") or "0")) if rating_el else 0
                    text    = (await text_el.inner_text()).strip() if text_el else ""
                    useful  = 0
                    if useful_el:
                        try:
                            useful = int((await useful_el.inner_text()).strip())
                        except Exception:
                            pass

                    if text:
                        reviews.append(Review(
                            source="Ozon",
                            author=author,
                            rating=rating,
                            title="",
                            text=text,
                            useful_count=useful,
                            date="",
                        ))
                except Exception as e:
                    logger.debug(f"Ошибка парсинга отзыва Ozon: {e}")
                    continue

        return reviews
