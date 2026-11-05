from pydantic import BaseModel, Field


class CreateKnowledgeBaseRequest(BaseModel):
    pass


class IngestionRequest(BaseModel):
    knowledge_base_id: str | None = None
    data_source_id: str | None = None


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1)
    knowledge_base_id: str | None = None
    number_of_results: int = Field(default=5, ge=1, le=100)


class RetrieveGenerateRequest(BaseModel):
    query: str = Field(min_length=1)
    knowledge_base_id: str | None = None
    model_arn: str | None = None


class LocalIndexRequest(BaseModel):
    directory: str = "documents"


class LocalAskRequest(BaseModel):
    question: str = Field(min_length=1)


class BedrockAskRequest(BaseModel):
    question: str = Field(min_length=1)
