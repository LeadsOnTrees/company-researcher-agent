from pydantic import BaseModel


class FundingData(BaseModel):
    company_name: str
    funding_amount: float
    funding_date: str
    funding_round: str | None
