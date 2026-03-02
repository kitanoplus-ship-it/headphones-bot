import asyncio
import logging
from typing import Optional
from urllib.parse import quote_plus
import aiohttp

from parsers.base import BaseReviewParser, Review
from parsers.browser import new_page

logger = logging.getLogger(__name__)


class WildberriesParser(BaseReviewParser):
    SOURCE_NAME = "wildberries"

    async def search_product_url(self, product_name: str) -> Optional[str]:
        """WB: ищем через поиск, возвращаем nmId товара для API отзывов."""
        search_url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={quote_plus(product_name)}"
        async with new_page(ua_index=0) as page:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(3)

            # Берём первый артикул из data-nm-id
            card = await page.query_selector("[data-nm-id]")
            if card:
                nm_id = await card.get_attribute("data-nm-id")
                if nm_id:
                    return nm_id  # Возвращаем nmId, не URL
        return None

    async def fetch_reviews(self, nm_id: str, limit: int = 5) -> list[Review]:
        """WB отдаёт отзывы через публичное API — не нужен браузер."""
        reviews = []
        try:
            # Определяем shard по nmId
            n = int(nm_id)
            vol = n // 100000
            part = n // 1000
            basket = self._get_basket(vol)
            api_url = (
                f"https://basket-{basket:02d}.wbbasket.ru/vol{vol}/part{part}/{nm_id}/info/ru/feedbacks.json"
            )

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        logger.warning(f"WB feedbacks API вернул {resp.status} для nmId={nm_id}")
                        return []
                    data = await resp.json(content_type=None)

            feedbacks = data.get("feedbacks", [])
            # Сортируем по полезности (votes)
            feedbacks.sort(key=lambda x: x.get("votes", 0), reverse=True)

            for fb in feedbacks[:limit]:
                text_parts = []
                pros = fb.get("pros", "").strip()
                cons = fb.get("cons", "").strip()
                comment = fb.get("text", "").strip()

                if pros:
                    text_parts.append(f"Плюсы: {pros}")
                if cons:
                    text_parts.append(f"Минусы: {cons}")
                if comment:
                    text_parts.append(comment)

                text = "\n".join(text_parts)
                if text:
                    reviews.append(Review(
                        source="Wildberries",
                        author=fb.get("wbUserDetails", {}).get("name", "Аноним"),
                        rating=fb.get("productValuation", 0),
                        title="",
                        text=text,
                        useful_count=fb.get("votes", 0),
                        date=fb.get("createdDate", "")[:10],
                    ))
        except Exception as e:
            logger.error(f"Ошибка парсинга WB отзывов nmId={nm_id}: {e}")

        return reviews

    @staticmethod
    def _get_basket(vol: int) -> int:
        """Определяем номер basket-сервера по объёму артикула."""
        if vol <= 143:     return 1
        if vol <= 287:     return 2
        if vol <= 431:     return 3
        if vol <= 719:     return 4
        if vol <= 1007:    return 5
        if vol <= 1061:    return 6
        if vol <= 1115:    return 7
        if vol <= 1169:    return 8
        if vol <= 1313:    return 9
        if vol <= 1601:    return 10
        if vol <= 1655:    return 11
        if vol <= 1919:    return 12
        return 13
