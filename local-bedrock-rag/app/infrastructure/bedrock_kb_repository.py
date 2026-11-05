from app.core.config import get_settings
from app.infrastructure.aws_clients import (
    bedrock_agent_client,
    bedrock_agent_runtime_client,
)


class BedrockKnowledgeBaseRepository:
    def __init__(self):
        self.settings = get_settings()
        self.control = bedrock_agent_client()
        self.runtime = bedrock_agent_runtime_client()

    def create_knowledge_base(self) -> dict:
        response = self.control.create_knowledge_base(
            name=self.settings.bedrock_kb_name,
            description="Local development Knowledge Base backed by S3.",
            roleArn=self.settings.bedrock_kb_role_arn,
            knowledgeBaseConfiguration={
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": self.settings.bedrock_foundation_model_arn,
                },
            },
            storageConfiguration={
                "type": "OPENSEARCH_SERVERLESS",
                "opensearchServerlessConfiguration": {
                    "collectionArn": self.settings.opensearch_collection_arn,
                    "vectorIndexName": self.settings.opensearch_vector_index,
                    "fieldMapping": {
                        "vectorField": "bedrock-knowledge-base-default-vector",
                        "textField": "AMAZON_BEDROCK_TEXT_CHUNK",
                        "metadataField": "AMAZON_BEDROCK_METADATA",
                    },
                },
            },
        )
        return response["knowledgeBase"]

    def create_s3_data_source(self, knowledge_base_id: str) -> dict:
        response = self.control.create_data_source(
            knowledgeBaseId=knowledge_base_id,
            name=self.settings.bedrock_data_source_name,
            description="S3 documents uploaded by the local application.",
            dataSourceConfiguration={
                "type": "S3",
                "s3Configuration": {
                    "bucketArn": f"arn:aws:s3:::{self.settings.s3_bucket}",
                    "inclusionPrefixes": [self.settings.s3_document_prefix],
                },
            },
        )
        return response["dataSource"]

    def start_ingestion(self, knowledge_base_id: str, data_source_id: str) -> dict:
        response = self.control.start_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id,
            description="Local development ingestion run",
        )
        return response["ingestionJob"]

    def get_ingestion_job(
        self, knowledge_base_id: str, data_source_id: str, job_id: str
    ) -> dict:
        response = self.control.get_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id,
            ingestionJobId=job_id,
        )
        return response["ingestionJob"]

    def retrieve(
        self, knowledge_base_id: str, query: str, number_of_results: int = 5
    ) -> list[dict]:
        response = self.runtime.retrieve(
            knowledgeBaseId=knowledge_base_id,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": number_of_results,
                }
            },
        )
        return response.get("retrievalResults", [])

    def retrieve_and_generate(
        self, knowledge_base_id: str, model_arn: str, query: str
    ) -> dict:
        response = self.runtime.retrieve_and_generate(
            input={"text": query},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": knowledge_base_id,
                    "modelArn": model_arn,
                },
            },
        )
        return response

    def list_knowledge_bases(self) -> dict:
        return self.control.list_knowledge_bases()
