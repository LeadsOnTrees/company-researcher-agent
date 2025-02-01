from typing import Literal
from pydantic import BaseModel

from company_researcher.modules.ai.llm import AI


class PageType(BaseModel):
    type_: Literal["home", "blog", "contact", "about", "career", None]


PAGE_TYPE_PROMPT = {
    "system": """You are a web page classifier. Your task is to analyze the content and URL of web pages and determine their type. Available page types are: "home", "blog", "contact", "about", "career".
    Base your decision on both the URL structure and page content.""",
    "user": """Determine the page type for the following content:
                URL: {url}
                Title: {title}
                Content: {text}""",
}


class PageTypeRecognizer:
    def __init__(self, title: str, text: str, url: str) -> None:
        self.title = title
        self.text = text
        self.url = url

        self.ai = AI(
            response_model=PageType,
            prompts=[
                {
                    "role": "system",
                    "content": PAGE_TYPE_PROMPT["system"],
                },
                {
                    "role": "user",
                    "content": PAGE_TYPE_PROMPT["user"].format(
                        url=self.url, title=self.title, text=self.text
                    ),
                },
            ],
        )

    async def generate(self) -> str | None:
        response_model = await self.ai.query()
        return response_model.type_
