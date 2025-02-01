from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright
import webbrowser

from pathlib import Path

from company_researcher.models.models import FundingData
from company_researcher.modules.prompts.career_generator import JobDescription
from company_researcher.modules.prompts.company_description import CompanyDescription


class PDFReport:
    def __init__(
        self,
        title: str,
        company_description: CompanyDescription,
        careers: list[JobDescription],
        funding_data: list[FundingData],
        filename=None,
    ):
        base_filename = (
            filename or f"company_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.title = title
        self.html_path = str(Path.cwd() / "reports" / f"{base_filename}.html")
        self.pdf_path = str(Path.cwd() / "reports" / f"{base_filename}.pdf")
        self.company_description = company_description
        self.careers = careers
        self.funding_data = funding_data

    def _generate_html(self):
        """Generate HTML report using Jinja2 template"""
        Path(self.html_path).parent.mkdir(parents=True, exist_ok=True)

        jinja_env = Environment(
            loader=FileSystemLoader("src/company_researcher/reports/templates"),
            autoescape=True,
        )
        template = jinja_env.get_template("report.html")
        html_content = template.render(
            title=self.title,
            company=self.company_description,
            careers=self.careers,
            funding_data=self.funding_data,
        )

        with open(self.html_path, "w") as f:
            f.write(html_content)

        return self.html_path

    async def generate(self):
        """Generate HTML and convert to PDF using Playwright"""
        html_path = self._generate_html()

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            await page.goto(
                f"file://{Path(html_path).absolute()}", wait_until="networkidle"
            )

            await page.pdf(
                path=self.pdf_path,
                format="A4",
                print_background=True,
                margin={"top": "1cm", "right": "1cm", "bottom": "1cm", "left": "1cm"},
            )

            await browser.close()

        return self.pdf_path

    def open(self):
        """Open the generated PDF"""
        webbrowser.open(self.pdf_path)
