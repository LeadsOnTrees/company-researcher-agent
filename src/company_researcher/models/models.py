from pydantic import BaseModel

from company_researcher.modules.prompts.career_generator import JobDescription
from company_researcher.modules.prompts.company_description import CompanyDescription


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


class Report(BaseModel):
    title: str
    company_description: CompanyDescription
    careers_info: list[JobDescription]
    funding_data: list[FundingData]
