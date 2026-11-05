from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Local Bedrock RAG"
    database_url: str = "sqlite:///./data/app.db"

    use_fakecloud: bool = True
    fakecloud_endpoint_url: str = "http://localhost:4566"
    aws_region: str = "us-east-1"
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"

    s3_bucket: str = "local-bedrock-kb-documents"
    s3_document_prefix: str = "documents/"
    s3_addressing_style: str = "path"

    bedrock_chat_model: str = "anthropic.claude-3-haiku-20240307-v1:0"
    bedrock_kb_id: str = ""
    bedrock_data_source_id: str = ""
    bedrock_kb_name: str = "local-demo-kb"
    bedrock_data_source_name: str = "local-s3-source"
    bedrock_foundation_model_arn: str = (
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
    )
    bedrock_kb_role_arn: str = (
        "arn:aws:iam::000000000000:role/LocalBedrockKnowledgeBaseRole"
    )
    opensearch_collection_arn: str = (
        "arn:aws:aoss:us-east-1:000000000000:collection/localcollection"
    )
    opensearch_vector_index: str = "bedrock-knowledge-base-index"

    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen2.5:7b"
    ollama_embed_model: str = "nomic-embed-text"
    chroma_path: str = "./data/chroma"
    chroma_collection: str = "local-knowledge"
    chunk_size: int = 900
    chunk_overlap: int = 120
    top_k: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()
