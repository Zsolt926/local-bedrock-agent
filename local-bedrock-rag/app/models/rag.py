from pydantic import BaseModel, Field


class RagAnswer(BaseModel):
    answer: str = Field(description="Answer grounded only in retrieved passages.")
    sources: list[str] = Field(description="Unique source filenames used.")
    insufficient_information: bool = Field(
        description="True when retrieved passages do not support an answer."
    )
