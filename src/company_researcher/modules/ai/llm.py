import instructor
import openai
from pydantic import BaseModel

from company_researcher.config import config


class AI:
    def __init__(
        self, response_model: BaseModel, prompts: list[dict[str, str]]
    ) -> None:
        kwargs = {}
        deepseek_api_key = config.DEEPSEEK_API_KEY
        openai_api_key = config.OPENAI_API_KEY
        if deepseek_api_key and not openai_api_key:
            kwargs["base_url"] = "https://api.deepseek.com"

        api_key = openai_api_key or deepseek_api_key

        self.client = instructor.from_openai(
            openai.AsyncOpenAI(
                api_key=api_key,
                **kwargs,
            )
        )
        self.response_model = response_model
        self.prompts = prompts

    async def query(self) -> BaseModel:
        return await self.client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=self.prompts,
            response_model=self.response_model,
        )
