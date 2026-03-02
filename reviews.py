import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from parsers.reviews_manager import collect_reviews
from deepseek_analyzer import analyze_reviews

logger = logging.getLogger(__name__)
router = Router()


class ReviewState(StatesGroup):
    waiting_name = State()
    analyzing = State()


def source_stats_text(reviews_data: dict) -> str:
    """Краткая статистика по маркетплейсам."""
    lines = []
    source_map = {
        "yandex":      "Яндекс.Маркет",
        "ozon":        "Ozon",
        "dns":         "DNS",
        "wildberries": "Wildberries",
    }
    for key, label in source_map.items():
        count = len(reviews_data.get("reviews", {}).get(key, []))
        icon = "✅" if count > 0 else "❌"
        lines.append(f"{icon} {label}: {count} отз.")
    return "\n".join(lines)


def refresh_kb(product_name: str) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🔄 Обновить отзывы",
        callback_data=f"refresh_reviews:{product_name[:50]}"
    ))
    return builder.as_markup()


@router.message(F.text == "📝 Анализ отзывов")
async def reviews_start(message: Message, state: FSMContext):
    await state.set_state(ReviewState.waiting_name)
    await message.answer(
        "📝 *Анализ отзывов по маркетплейсам*\n\n"
        "Введи название или бренд наушников, например:\n"
        "• `Sony WH-1000XM5`\n"
        "• `Apple AirPods Pro`\n"
        "• `JBL Tune 720BT`\n\n"
        "Соберу топ-20 отзывов с Яндекс.Маркета, Ozon, DNS и Wildberries,\n"
        "затем DeepSeek найдёт сильные и слабые стороны 🔍",
        parse_mode="Markdown"
    )


@router.message(ReviewState.waiting_name)
async def reviews_search(message: Message, state: FSMContext):
    product_name = message.text.strip()
    if len(product_name) < 3:
        await message.answer("⚠️ Слишком короткий запрос. Введи полное название или бренд.")
        return

    await state.set_state(ReviewState.analyzing)
    status_msg = await message.answer(
        f"🔍 Ищу отзывы на *{product_name}*...\n\n"
        "⏳ Это занимает 30-60 секунд — парсю все маркетплейсы параллельно",
        parse_mode="Markdown"
    )

    try:
        # 1. Сбор отзывов
        reviews_data = await collect_reviews(product_name)
        all_reviews = reviews_data.get("all_reviews", [])
        stats = source_stats_text(reviews_data)

        await status_msg.edit_text(
            f"✅ Отзывы собраны!\n\n{stats}\n\n"
            f"🤖 Передаю в DeepSeek для анализа...",
            parse_mode="Markdown"
        )

        if not all_reviews:
            await status_msg.edit_text(
                f"😕 Не удалось найти отзывы на *{product_name}*.\n\n"
                "Попробуй уточнить название, например: `Sony WH-1000XM5`",
                parse_mode="Markdown"
            )
            await state.clear()
            return

        # 2. Анализ DeepSeek
        analysis = await analyze_reviews(product_name, all_reviews)

        await status_msg.delete()
        await message.answer(
            f"🎧 *{product_name}*\n"
            f"_{stats}_\n\n"
            f"{analysis}",
            parse_mode="Markdown",
            reply_markup=refresh_kb(product_name)
        )

    except Exception as e:
        logger.error(f"Ошибка анализа отзывов: {e}")
        await status_msg.edit_text(
            f"⚠️ Ошибка при сборе отзывов: {e}\nПопробуй ещё раз."
        )
    finally:
        await state.clear()


@router.callback_query(F.data.startswith("refresh_reviews:"))
async def refresh_reviews(callback: CallbackQuery, state: FSMContext):
    product_name = callback.data.split(":", 1)[1]
    await callback.answer("🔄 Обновляю отзывы...")

    status_msg = await callback.message.answer(
        f"🔄 Обновляю отзывы на *{product_name}*...",
        parse_mode="Markdown"
    )

    try:
        reviews_data = await collect_reviews(product_name, force=True)
        all_reviews = reviews_data.get("all_reviews", [])
        stats = source_stats_text(reviews_data)

        await status_msg.edit_text("🤖 Анализирую через DeepSeek...")

        analysis = await analyze_reviews(product_name, all_reviews)

        await status_msg.delete()
        await callback.message.answer(
            f"🎧 *{product_name}* _(обновлено)_\n"
            f"_{stats}_\n\n"
            f"{analysis}",
            parse_mode="Markdown",
            reply_markup=refresh_kb(product_name)
        )
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Ошибка: {e}")
