import logging
from playwright.async_api import async_playwright, Page, Response as PlaywrightResponse
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio

from company_researcher.models import Response
from company_researcher.scrapers.parser import Parser

logger = logging.getLogger(__name__)


class ScraperException(Exception):
    """Custom exception for scraper failures"""

    pass


class Scraper:
    """Handles browser automation and content fetching"""

    def __init__(self, max_tabs: int = 5):
        self.max_tabs = max_tabs
        self.playwright = None
        self.browser = None
        self.page_pool: asyncio.Queue[Page] = asyncio.Queue()
        self.initialized = False
        self.parser = Parser()

    async def initialize(self):
        """Initialize browser and page pool"""
        if self.initialized:
            return

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        context = await self.browser.new_context()

        # Create pool of pages
        for _ in range(self.max_tabs):
            page = await context.new_page()
            await self.page_pool.put(page)

        self.initialized = True

    async def cleanup(self):
        """Cleanup browser and resources"""
        if self.browser:
            await self.browser.close()
            await self.playwright.stop()
            self.browser = None
            self.playwright = None
            self.initialized = False

    def after_retry_failed(retry_state):
        """Callback function that will be called when all retries failed"""
        exception = retry_state.outcome.exception()
        raise ScraperException(
            f"Failed to access URL after all retries. Original error: {str(exception)}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=15),
        reraise=False,
        retry_error_callback=after_retry_failed,
    )
    async def access_url(self, page: Page, url: str) -> PlaywrightResponse:
        response = await page.goto(url, wait_until="load", timeout=45_000)

        # wait until all frames are loaded
        await page.wait_for_timeout(3_000)
        return response

    async def scrape_url(self, url: str) -> Response:
        """Scrape a single URL using a page from the pool"""
        if not self.initialized:
            await self.initialize()

        page = await self.page_pool.get()
        try:
            pw_response = await self.access_url(page, url)
            content = await page.content()

            soup = self.parser.parse_content(content)

            # a lot of content can be inside the frames
            frames = page.frames
            for frame in frames:
                try:
                    frame_content = await frame.content()
                    self.parser.merge_frame_content(soup, frame_content)
                except Exception as e:
                    logger.warning(f"Error processing frame: {e}")
                    continue

            return Response(
                status_code=pw_response.status,
                html=content,
                text=self.parser.extract_text(soup),
                urls=self.parser.extract_urls(soup),
                title=self.parser.extract_title(soup),
                url=url,
            )
        finally:
            await self.page_pool.put(page)
