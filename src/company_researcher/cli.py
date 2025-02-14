import asyncio
import typer
from company_researcher.main import CompanyResearcher

app = typer.Typer(pretty_exceptions_enable=False)


@app.command()
def research(
    url: str = typer.Argument(..., help="URL to start research"),
    max_depth: int = typer.Option(5, help="Maximum depth to follow links"),
    max_concurrent: int = typer.Option(8, help="Maximum number of concurrent requests"),
    max_results: int = typer.Option(100, help="Maximum number of results"),
):
    """
    Perform research on a company website.

    Provide a URL to start research. Should be a main page of the company.

    The more depth and the more max results, the more pages will be crawled and more data will be collected.
    """

    async def main():
        researcher = CompanyResearcher(
            url=url,
            max_depth=max_depth,
            max_concurrent=max_concurrent,
            max_results=max_results,
        )
        await researcher.research()

    asyncio.run(main())


if __name__ == "__main__":
    app()
