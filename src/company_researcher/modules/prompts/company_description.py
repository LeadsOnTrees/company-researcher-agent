import asyncio
import logging
from pydantic import BaseModel, Field
from typing import List
import textwrap

from company_researcher.models import Response
from company_researcher.modules.ai.llm import AI
from company_researcher.modules.prompts.career_generator import JobDescription


class PurchaseNeeds(BaseModel):
    technology_needs: list[str] = Field(
        ...,
        description="""List specific tools, platforms, and software the company likely needs based on:
        - Current tech stack gaps
        - Infrastructure scaling requirements
        - Development workflow improvements
        - Integration requirements""",
    )

    service_needs: list[str] = Field(
        ...,
        description="""List professional services and consulting needs based on:
        - Technical implementation challenges
        - Expertise gaps
        - Training requirements
        - Process improvement needs""",
    )

    infrastructure_needs: list[str] = Field(
        ...,
        description="""List infrastructure and operational needs based on:
        - Cloud/hardware requirements
        - Security and compliance needs
        - Monitoring and observability gaps
        - Scaling requirements""",
    )

    talent_needs: list[str] = Field(
        ...,
        description="""List talent acquisition and development needs based on:
        - Critical skill gaps
        - Hard-to-fill positions
        - Training requirements
        - Team scaling needs""",
    )


class CompanyDescription(BaseModel):
    short_overview_headline: str = Field(
        ...,
        description="A concise, one-sentence summary of what the company does, its main product/service, and target market. Should be clear and jargon-free, similar to a headline.",
    )

    detailed_overview_paragraph: str = Field(
        ...,
        description="A comprehensive 3-4 sentence explanation of the company's business model, main products/services, target customers, and unique value proposition. Include any significant technological advantages or innovations mentioned on the website.",
    )

    growth_possibility_summary: str = Field(
        ...,
        description="Based on the website content, summarize in 2-3 sentences how the company could grow in the future. Consider factors like market expansion plans, new product developments, hiring indicators, and industry trends mentioned.",
    )

    possible_risks: list[str] = Field(
        ...,
        description="Identify 3-5 potential business risks or challenges the company might face, based on their business model and market position. Look for hints in their product descriptions, target market, and competitive landscape. Each risk should be a clear, specific statement.",
    )

    possible_opportunities: list[str] = Field(
        ...,
        description="List 3-5 specific growth opportunities or potential advantages the company could leverage, based on their current position and website content. Consider market trends, technology capabilities, and customer needs mentioned. Each opportunity should be concrete and actionable.",
    )

    technologies_used: list[str] = Field(
        ...,
        description="List the technologies the company uses, based on the job descriptions",
    )

    team_structure: list[str] = Field(
        ...,
        description="List the team structure of the company, based on the job descriptions",
    )

    technical_challenges: list[str] = Field(
        ...,
        description="Technical challenges and areas of complexity the company is addressing, based on job requirements and responsibilities",
    )

    purchase_insights: PurchaseNeeds = Field(
        ...,
        description="Detailed analysis of company's potential purchase needs across different categories",
    )

    growth_trajectory: str = Field(
        ...,
        description="A brief, data-driven statement about the company's growth potential based on current indicators. Should be a single sentence focusing on growth metrics, hiring patterns, or expansion signals.",
    )

    market_opportunity: str = Field(
        ...,
        description="A concise assessment of the company's market position and immediate opportunities. Should be a single sentence highlighting their strongest market advantage or opportunity.",
    )


CHUNK_ANALYSIS_PROMPT = {
    "system": """You are a business analyst specializing in technology companies. Analyze this website content section and extract key information about the company. 

    Focus on these key areas:

    1. Business Overview:
    - Core products/services
    - Main value proposition
    - Target market and customers
    - Unique selling points
    - Technology foundations

    2. Market Position:
    - Competitive advantages
    - Market differentiation
    - Industry positioning
    - Key partnerships or integrations
    - Customer segments served

    3. Growth and Development:
    - Expansion indicators
    - Product development plans
    - Market expansion signals
    - Innovation focus areas
    - Investment priorities

    4. Technical Capabilities:
    - Core technology platforms
    - Infrastructure mentions
    - Technical innovations
    - Integration capabilities
    - Platform scalability

    5. Challenges and Risks:
    - Market challenges
    - Technical hurdles
    - Competitive pressures
    - Industry constraints
    - Regulatory considerations

    6. Business Opportunities:
    - Market gaps addressed
    - Innovation potential
    - Expansion possibilities
    - Partnership opportunities
    - Technology advancement areas

    7. Purchase Indicators:
    - Technology needs
    - Infrastructure requirements
    - Scaling necessities
    - Integration requirements
    - Service needs

    Provide a structured summary highlighting the most relevant information found in this section. Focus on concrete details and specific mentions rather than general statements.""",
    "user": """Analyze this website content section, focusing on the areas outlined above:

    {content_chunk}

    Provide specific, factual information found in the text, avoiding speculation or unsupported conclusions.""",
}

FINAL_COMBINATION_PROMPT = {
    "system": """You are a technology business analyst tasked with creating a comprehensive company analysis. 
You will receive two types of information:
1. Website content summaries analyzing their public presence
2. Detailed job descriptions showing their internal needs and growth

Your task is to synthesize this information into a structured analysis that reveals both their current position and future direction.""",
    "user": """Analyze the following information:

WEBSITE CONTENT SUMMARIES:
{combined_summaries}

CAREER LISTINGS:
{careers_info}

Create a comprehensive company analysis with these components:

1. Tech Stack and Infrastructure:
   - Current technology stack from job requirements
   - Infrastructure patterns and preferences
   - Development practices and methodologies
   - Technical priorities and standards

2. Business Overview:
   short_overview_headline:
   - Company's core focus and scale
   - Main product/service offering
   - Target market and positioning
   
   detailed_overview_paragraph:
   - Business model and value proposition
   - Technical capabilities and innovations
   - Team structure and organization
   - Development culture and practices

3. Growth and Scaling:
   growth_possibility_summary:
   - Business expansion indicators
   - Team growth patterns
   - Technology investment areas
   - Market expansion signals
   
   scaling_initiatives:
   - Infrastructure scaling plans
   - Team scaling strategies
   - Product development directions
   - Technical capability expansion

4. Engineering Culture:
   development_culture:
   - Engineering practices and standards
   - Team collaboration patterns
   - Technical priorities
   - Knowledge sharing approach

5. Challenges and Opportunities:
   technical_challenges:
   - Current technical hurdles
   - Scaling challenges
   - Integration complexities
   - Infrastructure needs
   
   possible_risks:
   - Technology adoption risks
   - Talent acquisition challenges
   - Market position threats
   - Technical debt indicators
   
   possible_opportunities:
   - Technology advantage areas
   - Market positioning opportunities
   - Innovation potential
   - Team capability leverage

6. Purchase Intelligence:
   purchase_insights:
   Technology_Needs:
   - Tools and platforms needed
   - Missing infrastructure pieces
   - Scaling requirements
   
   Service_Needs:
   - Professional services required
   - Consulting needs
   - Training requirements
   
   Infrastructure_Needs:
   - Hardware/cloud requirements
   - Security/compliance needs
   - Monitoring/observability needs
   
   Talent_Needs:
   - Skills gaps to fill
   - Expertise requirements
   - Training needs

   growth_trajectory:
   - Growth potential based on current indicators
   - Hiring patterns or expansion signals
   - Market expansion or innovation potential

   market_opportunity:
   - Current market position
   - Immediate opportunities or competitive advantage
   - Potential for growth or market expansion

Base all insights on concrete evidence from either the website content or job descriptions. Prioritize specific, actionable insights over general observations.""",
}


logger = logging.getLogger(__name__)


class CompanyDescriptionGenerator:
    def __init__(
        self,
        responses: list[Response],
        careers_info: list[JobDescription],
        max_chunk_size: int = 20_000,
        max_concurrent_tasks: int = 10,
    ) -> None:
        self.website_content = "\n".join(
            [response.text for response in responses if response.text]
        )
        logger.info(f"Website content: {len(self.website_content)} characters")

        self.max_chunk_size = max_chunk_size
        self.chunks = self._split_content()
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.careers_info = [career.model_dump_json() for career in careers_info]

        self.MAX_SUMMARY_LENGTH = 50_000

    def _split_content(self) -> List[str]:
        """Split content into chunks of approximately max_chunk_size characters"""
        return textwrap.wrap(
            self.website_content,
            width=self.max_chunk_size,
            break_long_words=False,
            break_on_hyphens=False,
        )

    async def _analyze_chunk(self, chunk: str) -> str:
        """Analyze a single chunk of content"""
        chunk_ai = AI(
            response_model=str,  # Just get raw text response for summaries
            prompts=[
                {"role": "system", "content": CHUNK_ANALYSIS_PROMPT["system"]},
                {
                    "role": "user",
                    "content": CHUNK_ANALYSIS_PROMPT["user"].format(
                        content_chunk=chunk
                    ),
                },
            ],
        )
        return await chunk_ai.query()

    async def _analyze_chunks_parallel(self) -> list[str]:
        """Process all chunks in parallel with rate limiting"""
        logger.info(f"Starting parallel analysis of {len(self.chunks)} chunks")

        async def process_chunk(index: int, chunk: str) -> tuple[int, str]:
            """Process a single chunk with its index"""
            async with self.semaphore:
                logger.info(f"Processing chunk {index + 1}/{len(self.chunks)}")
                try:
                    summary = await asyncio.wait_for(
                        self._analyze_chunk(chunk), timeout=30
                    )
                    return index, summary
                except Exception as e:
                    logger.warning(f"Error processing chunk {index + 1}: {e}")
                    return index, ""

        tasks = [
            asyncio.create_task(process_chunk(i, chunk))
            for i, chunk in enumerate(self.chunks)
        ]

        results = await asyncio.gather(*tasks)

        valid_results = [
            summary for _, summary in sorted(results) if summary and len(summary) > 0
        ]

        # Check total size and trim if needed
        summaries = []
        total_length = 0
        for summary in valid_results:
            new_length = total_length + len(summary)
            if new_length > self.MAX_SUMMARY_LENGTH:
                logger.info("Reached size limit, truncating results")
                break
            summaries.append(summary)
            total_length = new_length

        logger.info(f"Successfully processed {len(summaries)} chunks")
        return summaries

    async def generate(self) -> CompanyDescription:
        chunk_summaries = await self._analyze_chunks_parallel()

        logger.info(
            f"Analyzed {len(chunk_summaries)} chunks - final chunk {len(str(chunk_summaries))}"
        )

        combined_ai = AI(
            response_model=CompanyDescription,
            prompts=[
                {"role": "system", "content": FINAL_COMBINATION_PROMPT["system"]},
                {
                    "role": "user",
                    "content": FINAL_COMBINATION_PROMPT["user"].format(
                        combined_summaries="\n\n---\n\n".join(chunk_summaries),
                        careers_info="\n\n---\n\n".join(self.careers_info),
                    ),
                },
            ],
        )

        return await combined_ai.query()
