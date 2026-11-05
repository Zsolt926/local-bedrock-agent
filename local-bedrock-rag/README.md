# Local Bedrock RAG

A Windows-friendly learning project for:

- S3 bucket creation, document upload and Bedrock metadata sidecars.
- Bedrock Knowledge Base / S3 data-source API lifecycle through FakeCloud.
- Ingestion job start/status, Retrieve and RetrieveAndGenerate API calls.
- Pydantic AI tool calling and Pydantic structured output on both the Bedrock Converse and local Ollama paths.
- A separate, real local RAG path using Ollama embeddings + ChromaDB.
- FastAPI endpoints, SQLAlchemy/SQLite metadata persistence, CLI and tests.

## Important: what is emulated and what is real?

**FakeCloud** is an AWS API emulator. Its Bedrock Agent control plane supports Knowledge Base and data-source CRUD plus ingestion job lifecycle. Its Agent Runtime supports Retrieve and RetrieveAndGenerate with synthetic retrieval results. It does **not** execute embedding pipelines, index S3 documents, perform real vector search, or run model inference. Bedrock model responses are configurable/canned. See:

- https://fakecloud.dev/docs/guides/testing-bedrock/
- https://fakecloud.dev/docs/services/bedrock-agent/
- https://fakecloud.dev/docs/services/bedrock-agent-runtime/
- https://fakecloud.dev/docs/services/s3/

The **local RAG** path is real inference: it reads local `.txt`/`.md` files, calls Ollama `/api/embed`, stores vectors in ChromaDB, retrieves relevant chunks, and uses a Pydantic AI agent backed by Ollama's OpenAI-compatible chat endpoint. It is intentionally independent from Bedrock's managed Knowledge Base API.

This is a development scaffold, not a production-ready AWS provisioning system. The OpenSearch Serverless collection and IAM role in `.env` are placeholders. FakeCloud accepts/stores the API configuration for contract tests; real AWS requires a real execution role, S3 permissions, an embedding model enabled in the account/region, and an actual vector store.

## 1. Prerequisites

- Windows 10/11
- Python 3.11+
- `uv` (recommended) or pip
- Docker Desktop
- Ollama is run in Docker Compose here; alternatively install Ollama separately.

Install uv if needed:
```cmd
winget install --id= astral-sh.uv -e
```

## 2. Setup

From the project directory:

```cmd
uv venv
.venv\Scripts\activate
uv sync --extra dev
copy .env.example .env
```

Create local folders:
```cmd
mkdir data
mkdir documents
```

Start FakeCloud and Ollama:
```cmd
docker compose up -d
curl http://localhost:4566/_fakecloud/health
```

Pull the chat and embedding models:
```cmd
docker exec -it local-bedrock-ollama ollama pull qwen3.5:0.8b
docker exec -it local-bedrock-ollama ollama pull nomic-embed-text
```

If you already run Ollama on Windows rather than in Docker, change `OLLAMA_BASE_URL` in `.env` to `http://host.docker.internal:11434` only for containers calling the host; this Python app runs on Windows, so normally use `http://localhost:11434`.

## 3. Add sample documents

A few sample documents are included in `documents/`. You can add Markdown or TXT files there.

## 4. S3 + FakeCloud workflow

Create bucket and upload all documents:
```cmd
uv run python -m app.cli s3-init
uv run python -m app.cli upload --directory documents
uv run python -m app.cli s3-list
```

Each document is uploaded under `documents/`. If a matching `.metadata.json` file exists beside it, it is uploaded as `<object-key>.metadata.json`, the Bedrock S3 sidecar naming convention.

Example metadata sidecar:
```json
{
  "metadataAttributes": {
    "department": "engineering",
    "category": "architecture"
  }
}
```

## 5. Create the Bedrock Knowledge Base API resources

Set `.env` values if you want different names. The demo values for role ARN and OpenSearch collection ARN are placeholders.

```cmd
uv run python -m app.cli create-kb
```

The command:
1. Calls `bedrock-agent.CreateKnowledgeBase` with VECTOR configuration and OpenSearch Serverless storage configuration.
2. Persists the returned Knowledge Base ID in `.env`.
3. Calls `CreateDataSource` with S3 bucket ARN and `documents/` inclusion prefix.
4. Persists the returned data source ID in `.env`.

**FakeCloud mode:** this verifies API request/response plumbing and resource lifecycle. It does not create a real OpenSearch collection, assume an IAM role, or embed/index your uploaded documents.

## 6. Start and monitor ingestion

```cmd
uv run python -m app.cli ingest
uv run python -m app.cli ingestion-status --job-id YOUR_JOB_ID
```

The CLI prints the ingestion job ID. In FakeCloud, ingestion state transitions are simulated and no vectors are generated.

## 7. Exercise Knowledge Base retrieval APIs

```cmd
uv run python -m app.cli retrieve --query "What is our application architecture?"
uv run python -m app.cli retrieve-generate --query "Summarize our architecture."
```

These call the actual boto3 Bedrock Agent Runtime API operations against FakeCloud. Results are synthetic, intended for testing response handling and API contracts.

## 8. Run a real local RAG pipeline with Ollama

Index the local documents:
```cmd
uv run python -m app.cli rag-index --directory documents
```

Ask a question:
```cmd
uv run python -m app.cli rag-ask --query "What components make up our RAG architecture?"
```

This path performs real local embedding and vector retrieval with Ollama + ChromaDB, then calls a Pydantic AI agent with a `search_local_knowledge_base` tool and a Pydantic `RagAnswer` output schema.

## 9. Pydantic AI on Bedrock Converse (tools + structured output)

Set `BEDROCK_CHAT_MODEL` to a model ID supported by your Bedrock setup (FakeCloud uses canned/default responses for emulator tests). The agent registers a `search_knowledge_base` Python tool and declares `RagAnswer` as its structured output type:

```cmd
uv run python -m app.cli bedrock-ask --query "What does our security guidance say about retrieval?"
```

This verifies the Pydantic AI / Bedrock Converse integration path when run against FakeCloud. FakeCloud's model output is deterministic/canned unless configured through its documented response facilities; it does not run the model. The Python tool itself executes in this application and calls Bedrock Agent Runtime Retrieve.

## 10. Run FastAPI

```cmd
uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs

Endpoints:
- `GET /health`
- `POST /documents/upload` (multipart file upload)
- `POST /knowledge-base/create`
- `POST /knowledge-base/ingestion`
- `GET /knowledge-base/ingestion/{job_id}`
- `POST /knowledge-base/retrieve`
- `POST /knowledge-base/retrieve-and-generate`
- `POST /local-rag/index`
- `POST /local-rag/ask`
- `POST /bedrock-agent/ask` (Bedrock Converse + registered retrieval tool + Pydantic output schema)

## 11. Tests

Unit tests:
```cmd
uv run pytest tests/unit -v
```

FakeCloud integration tests (start Docker Compose first):
```cmd
uv run pytest tests/integration -v
```

Integration tests use boto3 and FakeCloud. They are API contract tests, not model-quality or semantic retrieval tests.

## Architecture

```text
                         FastAPI / CLI
                              |
                       Application services
                              |
            +-----------------+-------------------+
            |                 |                   |
         S3 Repo         Bedrock KB Repo     Local RAG Service
            |                 |                   |
         boto3 S3       boto3 bedrock-agent   Ollama /api/embed
            |           boto3 agent-runtime        |
         FakeCloud          FakeCloud            ChromaDB
            |                                      |
       S3 object store                        Pydantic AI
                                                  |
                                             Ollama chat

SQLAlchemy/SQLite stores application-side document and ingestion metadata.
```

## Notes / limitations

- FakeCloud S3 is useful for S3 API integration testing. FakeCloud Knowledge Base ingestion and retrieval are simulated.
- Real AWS Knowledge Bases need a valid service role and supported vector store. The example OpenSearch Serverless config is a starting template, not a deployed infrastructure definition.
- Local RAG indexes `.md` and `.txt` files only. Add a PDF/docx parser if you need those formats.
- The Pydantic AI local agent uses Ollama's OpenAI-compatible endpoint. Tool execution occurs in the Python application.
- Don't point `USE_FAKECLOUD=false` at a production AWS account until you have reviewed the IAM role, resource names, model access, and costs.

## Local Bedrock inference through FakeCloud → LiteLLM → Ollama

The Bedrock Runtime client used by `BedrockConverseModel` still points to FakeCloud (`http://localhost:4566`). FakeCloud's Bedrock upstream integration translates supported Bedrock-native runtime requests into the configured upstream protocol. In this project, the upstream is LiteLLM, and LiteLLM routes the `local-qwen` alias to Ollama.

```text
Pydantic AI (BedrockConverseModel)
  -> FakeCloud :4566 (Bedrock wire protocol)
  -> LiteLLM :4000/v1 (OpenAI-compatible upstream)
  -> Ollama :11434 (qwen3.5:0.8b)
```

This uses FakeCloud's built-in upstream integration; a separate Bedrock companion service is not required for this path. FakeCloud's other emulated AWS APIs, including S3 and Bedrock control-plane/Guardrails operations, remain available.

Start the stack:

```cmd
docker compose up -d --pull always
docker exec -it local-bedrock-ollama ollama pull qwen3.5:0.8b
```

Check the services:

```cmd
curl http://localhost:4566/_fakecloud/health
curl http://localhost:4000/health/liveliness
curl http://localhost:11434/api/tags
```

The Bedrock model ID configured in `.env` (`BEDROCK_CHAT_MODEL`) is mapped to the LiteLLM alias `local-qwen` by `FAKECLOUD_BEDROCK_UPSTREAM_MODEL_MAP`. The upstream model is configured in `litellm_config.yaml`.

For this local development stack, `sk-local-dev` is a placeholder key only. Do not reuse it outside a local isolated environment. Pin and review container versions before using the setup in shared environments.
