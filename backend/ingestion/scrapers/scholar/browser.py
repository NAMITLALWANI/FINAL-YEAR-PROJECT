import asyncio
from playwright.async_api import async_playwright, Browser, Playwright
from log_config import get_logger

logger = get_logger(__name__)

class BrowserManager:
    """
    Singleton manager for Playwright browser.
    Ensures only one browser instance runs and limits concurrent scraping.
    """
    _instance = None

    def __init__(self):
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        # Semaphore to ensure only ONE scholar scrape happens at a time to prevent IP bans
        self.semaphore = asyncio.Semaphore(1)
        self.is_running = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start(self):
        if self.is_running:
            return
        logger.info("Starting global Playwright browser instance...")
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )
            self.is_running = True
            logger.info("Global Playwright browser started successfully.")
        except Exception as e:
            logger.error(f"Failed to start Playwright browser: {e}")

    async def stop(self):
        if not self.is_running:
            return
        logger.info("Stopping global Playwright browser instance...")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.is_running = False
        logger.info("Global Playwright browser stopped.")

    async def get_browser(self) -> Browser | None:
        if not self.is_running:
            await self.start()
        return self.browser
