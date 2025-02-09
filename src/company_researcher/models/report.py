from pydantic import BaseModel

from company_researcher.models.models import FundingData
from company_researcher.modules.prompts.career_generator import JobDescription
from company_researcher.modules.prompts.company_description import CompanyDescription


class Report(BaseModel):
    title: str
    company_description: CompanyDescription
    careers_info: list[JobDescription]
    funding_data: list[FundingData]
