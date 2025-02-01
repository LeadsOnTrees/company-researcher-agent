from pydantic import BaseModel


class Response(BaseModel):
    status_code: int
    html: str
    text: str
    urls: list[str]
    title: str | None
    url: str


class FundingData(BaseModel):
    company_name: str
    funding_amount: float
    funding_date: str
    funding_round: str | None
