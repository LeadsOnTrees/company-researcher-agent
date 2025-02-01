from collections import defaultdict
from company_researcher.models.models import Response
from company_researcher.modules.apis.lot_funding import LeadsOnTreesClient
from company_researcher.modules.prompts.career_generator import CareersInfoGenerator
from company_researcher.modules.prompts.company_description import (
    CompanyDescriptionGenerator,
)
from company_researcher.modules.prompts.page_type import PageTypeRecognizer
from company_researcher.reports.pdf_generator import PDFReport
from company_researcher.scrapers.worker import ScraperWorker
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class CompanyResearcher:
    def __init__(
        self,
        url: str,
        max_depth: int = 5,
        max_concurrent: int = 8,
        max_results: int = 100,
    ) -> None:
        self.url = url
        self.max_depth = max_depth
        self.max_concurrent = max_concurrent
        self.max_results = max_results

    async def deep_crawl(self, url: str) -> list[Response]:
        worker = ScraperWorker(
            max_depth=self.max_depth,
            max_concurrent=self.max_concurrent,
            max_results=self.max_results,
        )
        results = []
        try:
            results = await worker.scrape(url)
            logger.info("Scraped %d pages", len(results))
        finally:
            await worker.scraper.cleanup()

        return results

    async def load_page_types_to_responses(
        self, responses: list[Response]
    ) -> dict[str, list[Response]]:
        """Determine the type of each page and load them into a dictionary"""
        page_types = defaultdict(list)
        for response in responses:
            page_type_recognizer = PageTypeRecognizer(
                response.title, response.text, response.url
            )
            page_type = await page_type_recognizer.generate()
            page_types[page_type].append(response)
        return page_types

    async def research(self) -> None:
        logger.info("Starting deep crawl for URL: %s", self.url)
        responses = await self.deep_crawl(self.url)
        logger.info("Found %d responses", len(responses))

        # Determine the report title from the main page title.
        main_page_title = [
            response.title for response in responses if response.url == self.url
        ]
        report_title = main_page_title[0] if main_page_title else self.url
        logger.info("Report title determined: %s", report_title)

        # Load page types mapped to responses.
        logger.info("Loading page types to responses")
        page_type_to_responses = await self.load_page_types_to_responses(responses)
        logger.info("Loaded %d page types", len(page_type_to_responses))

        # Generate careers info.
        logger.info("Generating careers info")
        careers = CareersInfoGenerator(
            responses=page_type_to_responses.get("career", [])
        )
        careers_info = await careers.generate()
        logger.info("Extracted %d job descriptions", len(careers_info))

        # Retrieve funding data.
        logger.info("Searching for funding data")
        funding_data = await LeadsOnTreesClient().get_funding_data(self.url)
        logger.info("Found %d funding data entries", len(funding_data))

        # Generate company description.
        logger.info("Generating company description")
        company_description_generator = CompanyDescriptionGenerator(
            responses=responses, careers_info=careers_info
        )
        company_description = await company_description_generator.generate()
        logger.info("Generated company description")

        # Generate PDF report.
        logger.info("Generating PDF report")
        pdf_generator = PDFReport(
            report_title, company_description, careers_info, funding_data
        )
        pdf_path = await pdf_generator.generate()
        logger.info("PDF report generated: %s", pdf_path)

        # Open the generated PDF report.
        logger.info("Opening PDF report")
        pdf_generator.open()
