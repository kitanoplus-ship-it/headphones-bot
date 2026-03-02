import asyncio
import logging
from typing import Optional
from urllib.parse import quote_plus

from parsers.base import BaseReviewParser, Review
from parsers.browser import new_page

logger = logging.getLogger(__name__)


class DNSParser(BaseReviewParser):
    SOURCE_NAME = "dns"

    async def search_product_url(self, product_name: str) -> Optional[str]:
        search_url = f"https://www.dns-shop.ru/search/?q={quote_plus(product_name)}"
        async with new_page(ua_index=2) as page:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(2)

            link = await page.query_selector("a.catalog-product__name")
            if link:
                href = await link.get_attribute("href")
                if href:
                    if href.startswith("/"):
                        href = "https://www.dns-shop.ru" + href
                    return href
        return None

    async def fetch_reviews(self, product_url: str, limit: int = 5) -> list[Review]:
        reviews = []
        # DNS: отзывы на отдельной вкладке /отзывы/
        reviews_url = product_url.rstrip("/") + "/отзывы/"
        async with new_page(ua_index=2) as page:
            await page.goto(reviews_url, wait_until="domcontentloaded", timeout=25000)
            await asyncio.sleep(3)

            items = await page.query_selector_all(".ow-opinion")
            for item in items[:limit]:
                try:
                    author_el  = await item.query_selector(".ow-opinion__user-name")
                    rating_el  = await item.query_selector(".ow-opinion__rating")
                    pros_el    = await item.query_selector(".ow-opinion__advantages")
                    cons_el    = await item.query_selector(".ow-opinion__disadvantages")
                    useful_el  = await item.query_selector(".ow-opinion__likes-count")

                    author  = (await author_el.inner_text()).strip() if author_el else "Аноним"
                    useful  = 0
                    if useful_el:
                        try:
                            useful = int((await useful_el.inner_text()).strip())
                        except Exception:
                            pass

                    # Рейтинг через aria-label или считаем активные звёзды
                    rating = 0
                    if rating_el:
                        aria = await rating_el.get_attribute("aria-label")
                        if aria:
                            try:
                                rating = int("".join(filter(str.isdigit, aria.split("/")[0])))
                            except Exception:
                                pass

                    pros = (await pros_el.inner_text()).strip() if pros_el else ""
                    cons = (await cons_el.inner_text()).strip() if cons_el else ""

                    text = ""
                    if pros:
                        text += f"Плюсы: {pros}\n"
                    if cons:
                        text += f"Минусы: {cons}"

                    if text.strip():
                        reviews.append(Review(
                            source="DNS",
                            author=author,
                            rating=rating,
                            title="",
                            text=text.strip(),
                            useful_count=useful,
                            date="",
                        ))
                except Exception as e:
                    logger.debug(f"Ошибка парсинга отзыва DNS: {e}")
                    continue

        return reviews
