from pydantic import BaseModel


class Response(BaseModel):
    status_code: int
    html: str
    text: str
    urls: list[str]
    title: str | None
    url: str
