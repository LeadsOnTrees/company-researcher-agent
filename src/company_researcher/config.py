from typing import Literal
from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str | None = None
    DEEPSEEK_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    LEADSONTREES_API_KEY: str | None = None

    LLM_MODEL: str = "models/gemini-2.0-flash"
    LLM_PROVIDER: Literal["openai", "deepseek", "google"] = "google"

    @model_validator(mode="after")
    def validate_llm_api_keys(self):
        """Validate that either OpenAI or Deepseek API key is present"""
        if (
            not self.OPENAI_API_KEY
            and not self.DEEPSEEK_API_KEY
            and not self.GEMINI_API_KEY
        ):
            raise ValueError(
                "Either OPENAI_API_KEY or DEEPSEEK_API_KEY or GEMINI_API_KEY must be provided"
            )
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


config = Settings()
