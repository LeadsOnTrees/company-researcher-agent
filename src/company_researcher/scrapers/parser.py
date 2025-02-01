from bs4 import BeautifulSoup
from typing import Optional
from urllib.parse import urljoin, urlparse

from company_researcher.modules.prompts.page_type import PageTypeRecognizer


class Parser:
    """Handles all HTML parsing and URL extraction/normalization logic"""

    @staticmethod
    def extract_urls(soup: BeautifulSoup) -> list[str]:
        """Extract all URLs from a BeautifulSoup object"""
        return list(
            set(
                [
                    a.get("href")
                    for a in soup.find_all("a", href=True)
                    if a.get("href").startswith(("http", "/"))
                ]
            )
        )

    @staticmethod
    def normalize_url(base_url: str, url: str) -> Optional[str]:
        """Normalize URL and filter out URLs that are not part of the same domain"""
        if not url:
            return None

        full_url = urljoin(base_url, url)
        parsed_url = urlparse(full_url)
        parsed_base = urlparse(base_url)

        base_domain = ".".join(parsed_base.netloc.split(".")[-2:])
        url_domain = ".".join(parsed_url.netloc.split(".")[-2:])

        if url_domain != base_domain:
            return None

        # documentation pages bring little value
        if any(
            pattern in full_url
            for pattern in ["docs", "documentation", "community", "status"]
        ):
            return None

        # make urls all the same
        full_url = full_url.replace("www.", "").replace("http://", "https://")

        full_url = full_url[:-1] if full_url.endswith("/") else full_url

        return full_url

    @staticmethod
    async def determine_page_type(
        url: str, text_content: str, page_title: str, status_code: int
    ) -> str | None:
        """Determine the type of page based on URL and content"""
        if status_code not in [200, 201]:
            return None

        return await PageTypeRecognizer(url, page_title, text_content).recognize()

    @staticmethod
    def parse_content(content: str) -> BeautifulSoup:
        """Parse HTML content into BeautifulSoup object"""
        return BeautifulSoup(content, "html.parser")

    @staticmethod
    def merge_frame_content(main_soup: BeautifulSoup, frame_content: str) -> None:
        """Merge frame content into the main soup object"""
        frame_soup = BeautifulSoup(frame_content, "html.parser")
        if frame_soup.body:
            main_soup.body.extend(frame_soup.body.contents)

    @staticmethod
    def extract_text(soup: BeautifulSoup) -> str:
        """Extract clean text from BeautifulSoup object"""
        return soup.get_text(separator=" ", strip=True)

    @staticmethod
    def extract_title(soup: BeautifulSoup) -> str:
        """Extract title from BeautifulSoup object"""
        return soup.title.string if soup.title else ""
