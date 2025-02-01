from datetime import datetime
import logging
import httpx

from company_researcher.models.models import FundingData
from company_researcher.config import config

logger = logging.getLogger(__name__)


class LeadsOnTreesClient:
    def __init__(self):
        self.api_key = config.LEADSONTREES_API_KEY
        self.api_url = "https://leadsontrees.com/api/v1/funding?website={website}"

    def parse_funding_data(self, response: httpx.Response) -> list[FundingData]:
        response_json = response.json()
        fundings = response_json["response"]["data"]

        return [
            FundingData(
                company_name=funding["company_name"],
                funding_amount=funding["funding_amount"],
                funding_date=datetime.fromisoformat(funding["date_seen"]).strftime(
                    "%Y-%m-%d"
                ),
                funding_round=funding["round_type"],
            )
            for funding in fundings
        ]

    async def get_funding_data(self, website: str) -> list[FundingData]:
        if not self.api_key:
            logger.warning(
                "No LeadsOnTrees.com API key provided, skipping funding data"
            )
            return []

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.api_url.format(website=website),
                follow_redirects=True,
                timeout=30,
                headers={"x-lot-api-key": self.api_key},
            )
            return self.parse_funding_data(response)
