from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.providers.bedrock import BedrockProvider

from app.core.config import get_settings
from app.infrastructure.aws_clients import bedrock_runtime_client
from app.models.rag import RagAnswer
from app.services.knowledge_base_service import KnowledgeBaseService


def build_bedrock_kb_agent() -> Agent:
    settings = get_settings()
    model = BedrockConverseModel(
        settings.bedrock_chat_model,
        provider=BedrockProvider(bedrock_client=bedrock_runtime_client()),
    )
    agent = Agent(
        model,
        output_type=RagAnswer,
        system_prompt=(
            "You are a knowledge assistant. Use the search_knowledge_base tool "
            "before answering questions about indexed knowledge. Ground answers "
            "in retrieved passages. If the evidence is insufficient, say so."
        ),
    )

    @agent.tool_plain
    def search_knowledge_base(query: str) -> list[dict]:
        """Retrieve relevant passages from the configured Bedrock Knowledge Base."""
        return KnowledgeBaseService().retrieve(query)

    return agent


def ask_bedrock_knowledge_base(question: str) -> RagAnswer:
    return build_bedrock_kb_agent().run_sync(question).output
