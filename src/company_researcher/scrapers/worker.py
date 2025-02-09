import asyncio
import logging
from typing import Set
from company_researcher.scrapers.scraper import Scraper, ScraperException
from company_researcher.models import Response


logger = logging.getLogger(__name__)


class ScraperWorker:
    def __init__(
        self, max_depth: int = 2, max_concurrent: int = 5, max_results: int = 100
    ):
        self.max_depth = max_depth
        self.max_concurrent = max_concurrent
        self.max_results = max_results
        self.url_queue: asyncio.Queue[tuple[str, int]] = asyncio.Queue()
        self.seen_urls: Set[str] = set()
        self.results: list[Response] = []
        self.scraper = Scraper(max_tabs=max_concurrent)
        self.should_stop = asyncio.Event()
        self.active_workers = 0

    async def process_url(self, url: str, depth: int = 0) -> None:
        """Process a single URL and queue its links if within depth limit"""
        if depth >= self.max_depth or url in self.seen_urls:
            return

        self.seen_urls.add(url)
        logger.info(f"Scraping {url}")

        try:
            response = await self.scraper.scrape_url(url)
        except ScraperException as e:
            logger.warning(f"Error scraping {url}: {e}")
            return

        self.results.append(response)

        # Queue new URLs if we haven't reached max depth
        if depth < self.max_depth - 1:
            valid_urls = [
                normalized_url
                for found_url in response.urls
                if (normalized_url := self.scraper.parser.normalize_url(url, found_url))
                and normalized_url not in self.seen_urls
            ]
            for new_url in valid_urls:
                await self.url_queue.put((new_url, depth + 1))
        return

    async def worker(self) -> None:
        """Worker to process URLs from the queue"""
        while not self.should_stop.is_set():
            try:
                # Use get with timeout to check should_stop periodically
                try:
                    url, depth = await asyncio.wait_for(
                        self.url_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    # If queue is empty and no workers are processing URLs, we're done
                    if self.url_queue.empty() and self.active_workers == 0:
                        self.should_stop.set()
                    continue

                self.active_workers += 1
                try:
                    await self.process_url(url, depth)
                finally:
                    self.active_workers -= 1
                    self.url_queue.task_done()

                # Check if max results reached
                if len(self.results) >= self.max_results:
                    self.should_stop.set()

                    while not self.url_queue.empty():
                        try:
                            self.url_queue.get_nowait()
                            self.url_queue.task_done()
                        except asyncio.QueueEmpty:
                            break
                    break

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Worker error: {e}")

    async def scrape(self, start_url: str) -> list[Response]:
        """Main entry point to start scraping"""
        try:
            await self.scraper.initialize()

            await self.url_queue.put((start_url, 0))

            workers = [
                asyncio.create_task(self.worker()) for _ in range(self.max_concurrent)
            ]

            await asyncio.gather(*workers)

            return self.results[: self.max_results]
        finally:
            await self.scraper.cleanup()
