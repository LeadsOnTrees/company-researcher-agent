from enum import Enum
from typing import Any
import instructor
import openai
from pydantic import BaseModel
import google.generativeai as genai

from company_researcher.config import config


class LLMProvider(str, Enum):
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    GOOGLE = "google"


class LLMConfig:
    """Configuration for different LLM providers"""

    PROVIDERS = {
        LLMProvider.DEEPSEEK: {
            "api_key": config.DEEPSEEK_API_KEY,
            "base_url": "https://api.deepseek.com",
            "model": config.LLM_MODEL,
        },
        LLMProvider.OPENAI: {
            "api_key": config.OPENAI_API_KEY,
            "model": config.LLM_MODEL,
        },
        LLMProvider.GOOGLE: {
            "api_key": config.GEMINI_API_KEY,
            "model": config.LLM_MODEL,
        },
    }


class AI:
    def __init__(
        self, response_model: type[BaseModel], prompts: list[dict[str, str]]
    ) -> None:
        self.provider = self._determine_provider()
        self.client = self._initialize_client()
        self.response_model = response_model
        self.prompts = prompts

    def _determine_provider(self) -> LLMProvider:
        """Determine which LLM provider to use based on available API keys"""
        if config.LLM_PROVIDER:
            return LLMProvider(config.LLM_PROVIDER)

        for provider, _config in LLMConfig.PROVIDERS.items():
            if _config["api_key"]:
                return provider
        raise ValueError("No API key provided for any LLM provider")

    def _initialize_client(self) -> instructor.Instructor:
        provider_config = LLMConfig.PROVIDERS[self.provider]

        match self.provider:
            case LLMProvider.DEEPSEEK:
                return instructor.from_openai(
                    openai.AsyncOpenAI(
                        api_key=provider_config["api_key"],
                        base_url=provider_config["base_url"],
                    )
                )

            case LLMProvider.OPENAI:
                return instructor.from_openai(
                    openai.AsyncOpenAI(
                        api_key=provider_config["api_key"],
                    )
                )

            case LLMProvider.GOOGLE:
                genai.configure(api_key=provider_config["api_key"])
                return instructor.from_gemini(
                    client=genai.GenerativeModel(provider_config["model"]),
                    mode=instructor.Mode.GEMINI_JSON,
                )

            case _:
                raise ValueError(f"Unsupported provider: {self.provider}")

    def _get_completion_kwargs(self) -> dict[str, Any]:
        if self.provider == LLMProvider.GOOGLE:
            return {}
        return {"model": LLMConfig.PROVIDERS[self.provider]["model"]}

    async def query(self) -> BaseModel:
        kwargs = self._get_completion_kwargs()

        return self.client.chat.completions.create(
            **kwargs,
            messages=self.prompts,
            response_model=self.response_model,
        )
