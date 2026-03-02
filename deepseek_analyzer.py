"""
Анализ отзывов через DeepSeek API.
Выявляет сильные и слабые стороны товара на основе реальных отзывов.
"""
import logging
from openai import AsyncOpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
)

SYSTEM_PROMPT = """Ты — эксперт по анализу потребительских отзывов на электронику.
Тебе дают отзывы на наушники с разных маркетплейсов (Яндекс.Маркет, Ozon, DNS, Wildberries).
Твоя задача — выявить реальные плюсы и минусы товара на основе того, что пишут покупатели.

Правила:
- Анализируй только то, что написано в отзывах — не придумывай
- Выделяй конкретные, повторяющиеся наблюдения
- Используй живой, понятный язык
- Если отзывов мало — честно скажи об этом
- Отвечай строго по структуре ниже"""

USER_TEMPLATE = """Товар: {product_name}
Всего отзывов: {total} (из {sources})

Тексты отзывов:
{reviews_text}

Дай анализ строго в формате:

✅ СИЛЬНЫЕ СТОРОНЫ (топ-5):
1. ...
2. ...
3. ...
4. ...
5. ...

❌ СЛАБЫЕ СТОРОНЫ (топ-5):
1. ...
2. ...
3. ...
4. ...
5. ...

📊 ВЫВОД (2-3 предложения):
...

🎯 КОМУ ПОДОЙДУТ:
...

🚫 КОМУ НЕ ПОДОЙДУТ:
..."""


async def analyze_reviews(product_name: str, reviews: list[dict]) -> str:
    """
    Отправляет отзывы в DeepSeek, возвращает готовый анализ плюсов/минусов.
    """
    if not reviews:
        return "😕 Недостаточно отзывов для анализа."

    if not DEEPSEEK_API_KEY:
        return "⚠️ DeepSeek API ключ не настроен."

    # Формируем текст отзывов для промпта
    reviews_lines = []
    sources_seen = set()
    for i, r in enumerate(reviews[:20], 1):
        source = r.get("source", "?")
        sources_seen.add(source)
        rating = r.get("rating", "?")
        text = r.get("text", "").strip()
        if text:
            reviews_lines.append(f"[{i}] {source} ★{rating}: {text}")

    if not reviews_lines:
        return "😕 Отзывы не содержат текста для анализа."

    reviews_text = "\n\n".join(reviews_lines)
    sources_str = ", ".join(sorted(sources_seen))

    prompt = USER_TEMPLATE.format(
        product_name=product_name,
        total=len(reviews_lines),
        sources=sources_str,
        reviews_text=reviews_text,
    )

    try:
        logger.info(f"Отправляем {len(reviews_lines)} отзывов в DeepSeek для '{product_name}'")
        response = await client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=1500,
            temperature=0.3,
        )
        result = response.choices[0].message.content.strip()
        logger.info(f"DeepSeek анализ получен для '{product_name}'")
        return result

    except Exception as e:
        logger.error(f"Ошибка DeepSeek API: {e}")
        return f"⚠️ Ошибка анализа: {e}"
