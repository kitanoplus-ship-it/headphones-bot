"""
Общий headless-браузер на Playwright с anti-bot настройками.
Используется всеми парсерами.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

_browser: Optional[Browser] = None
_lock = asyncio.Lock()

STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-infobars",
    "--window-size=1920,1080",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]


async def get_browser() -> Browser:
    global _browser
    async with _lock:
        if _browser is None or not _browser.is_connected():
            pw = await async_playwright().start()
            _browser = await pw.chromium.launch(
                headless=True,
                args=STEALTH_ARGS,
            )
            logger.info("Playwright browser запущен")
    return _browser


@asynccontextmanager
async def new_page(ua_index: int = 0):
    """Контекстный менеджер — создаёт страницу с нужным UA и закрывает после."""
    browser = await get_browser()
    ua = USER_AGENTS[ua_index % len(USER_AGENTS)]
    context: BrowserContext = await browser.new_context(
        user_agent=ua,
        viewport={"width": 1920, "height": 1080},
        locale="ru-RU",
        timezone_id="Europe/Moscow",
        java_script_enabled=True,
    )
    # Скрываем webdriver-флаги
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
    """)
    page: Page = await context.new_page()
    try:
        yield page
    finally:
        await context.close()


async def close_browser():
    global _browser
    if _browser:
        await _browser.close()
        _browser = None
        logger.info("Playwright browser закрыт")
