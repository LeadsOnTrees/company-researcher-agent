from pydantic import BaseModel, Field

from company_researcher.models import Response
from company_researcher.modules.ai.llm import AI


class JobDescription(BaseModel):
    title: str = Field(
        ...,
        description="The exact title of the job position as listed on the website",
    )
    location: str = Field(
        ...,
        description="The location where the job is based, including remote options if specified",
    )
    department: str = Field(
        ...,
        description="The department or team the role belongs to within the company",
    )
    short_description: str = Field(
        ...,
        description="A 2-3 sentence summary of the role, its purpose, and impact on the company",
    )
    skills: list[str] = Field(
        ...,
        description="List of specific technical skills, tools, and competencies required for the role",
    )
    responsibilities: list[str] = Field(
        ...,
        description="Key responsibilities and duties of the role, extracted from the job posting",
    )
    experience_level: str = Field(
        ...,
        description="Required years of experience or seniority level (e.g., 'Entry Level', '3-5 years', 'Senior')",
    )
    salary_range: str = Field(
        ...,
        description="Salary range if provided, or 'Not specified' if not mentioned",
    )


CAREER_ANALYSIS_PROMPT = {
    "system": """You are a career data extraction specialist. Analyze job postings and extract structured information about each position.
For each job posting, identify:
- Exact job title
- Location (including remote options)
- Department/team
- Role summary
- Required skills and competencies
- Key responsibilities
- Experience requirements
- Salary information (if available)

Provide accurate, specific information as listed in the job posting. Do not make assumptions about unlisted details.""",
    "user": """Extract job details from the following career page content:

{career_content}

Format each job posting as a structured object with the following fields:
- title
- location
- department
- short_description
- skills (as a list)
- responsibilities (as a list)
- experience_level
- salary_range

If any field is not specified in the posting, use "Not specified" for text fields or empty lists for list fields.""",
}


class CareersInfoGenerator:
    def __init__(self, responses: list[Response]) -> None:
        self.responses = responses

    async def parse_career(self, response: Response) -> JobDescription:
        """Parse a single career page"""
        career_ai = AI(
            response_model=JobDescription,
            prompts=[
                {"role": "system", "content": CAREER_ANALYSIS_PROMPT["system"]},
                {
                    "role": "user",
                    "content": CAREER_ANALYSIS_PROMPT["user"].format(
                        career_content=response.text
                    ),
                },
            ],
        )

        job_descriptions = await career_ai.query()
        return job_descriptions

    async def generate(self) -> list[JobDescription]:
        """Extract job descriptions from career pages"""
        if not self.responses:
            return []

        job_descriptions = []

        for response in self.responses:
            job_description = await self.parse_career(response)
            job_descriptions.append(job_description)

        return job_descriptions
