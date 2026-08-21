from pydantic import BaseModel, Field, HttpUrl


class AgentRunRequest(BaseModel):
    target_url: HttpUrl
    question: str = Field(min_length=5, max_length=500)