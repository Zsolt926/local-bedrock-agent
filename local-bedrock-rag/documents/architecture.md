# Local RAG application architecture

The sample application separates AWS API integration tests from local inference.

The AWS integration path uses S3 for document object storage and the Amazon Bedrock
Agent and Agent Runtime APIs for Knowledge Base lifecycle and retrieval requests.

The local RAG path uses Ollama to generate embeddings, ChromaDB to store vectors,
and Pydantic AI to orchestrate retrieval tools and produce validated structured output.

FakeCloud is used for deterministic AWS API integration tests. It does not execute
real document embedding or vector retrieval.
