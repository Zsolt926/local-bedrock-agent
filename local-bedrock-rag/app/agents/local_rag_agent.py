from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from app.core.config import get_settings
from app.models.rag import RagAnswer
from app.services.local_rag_service import LocalRagService


def build_local_rag_agent() -> Agent:
    settings = get_settings()
    model = OpenAIChatModel(
        settings.ollama_chat_model,
        provider=OpenAIProvider(
            base_url=f"{settings.ollama_base_url.rstrip('/')}/v1",
            api_key="ollama",
        ),
    )
    agent = Agent(
        model,
        output_type=RagAnswer,
        system_prompt=(
            "You are a retrieval-grounded assistant. Always call "
            "search_local_knowledge_base before answering. Use only retrieved passages. "
            "If the passages do not contain the answer, say so and set "
            "insufficient_information=true. Include source filenames."
        ),
    )

    @agent.tool_plain
    def search_local_knowledge_base(query: str) -> list[dict]:
        """Search indexed local documents and return relevant passages."""
        return LocalRagService().search(query)

    return agent


def ask_local_rag(question: str) -> RagAnswer:
    result = build_local_rag_agent().run_sync(question)
    return result.output
