import argparse
import json
from pathlib import Path
from app.infrastructure.database import init_db
from app.infrastructure.s3_repository import S3Repository
from app.services.document_service import DocumentService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.local_rag_service import LocalRagService
from app.agents.local_rag_agent import ask_local_rag
from app.agents.bedrock_kb_agent import ask_bedrock_knowledge_base


def _print(value):
    print(json.dumps(value, indent=2, default=str, ensure_ascii=False))


def main():
    init_db()
    parser = argparse.ArgumentParser(prog="local-bedrock")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("s3-init")
    upload = sub.add_parser("upload")
    upload.add_argument("--directory", default="documents")
    sub.add_parser("s3-list")

    sub.add_parser("create-kb")
    sub.add_parser("ingest")
    status = sub.add_parser("ingestion-status")
    status.add_argument("--job-id", required=True)

    retrieve = sub.add_parser("retrieve")
    retrieve.add_argument("--query", required=True)
    retrieve.add_argument("--top-k", type=int, default=5)

    generate = sub.add_parser("retrieve-generate")
    generate.add_argument("--query", required=True)

    index = sub.add_parser("rag-index")
    index.add_argument("--directory", default="documents")

    ask = sub.add_parser("rag-ask")
    ask.add_argument("--query", required=True)

    bedrock_ask = sub.add_parser("bedrock-ask")
    bedrock_ask.add_argument("--query", required=True)

    args = parser.parse_args()

    if args.command == "s3-init":
        S3Repository().ensure_bucket()
        print("S3 bucket is ready.")
    elif args.command == "upload":
        _print(DocumentService().upload_directory(args.directory))
    elif args.command == "s3-list":
        _print(S3Repository().list_objects())
    elif args.command == "create-kb":
        _print(KnowledgeBaseService().create())
        print("\nIDs were written to .env. Restart the command for cached settings to reload.")
    elif args.command == "ingest":
        _print(KnowledgeBaseService().start_ingestion())
    elif args.command == "ingestion-status":
        _print(KnowledgeBaseService().get_ingestion(args.job_id))
    elif args.command == "retrieve":
        _print(KnowledgeBaseService().retrieve(args.query, number_of_results=args.top_k))
    elif args.command == "retrieve-generate":
        _print(KnowledgeBaseService().retrieve_and_generate(args.query))
    elif args.command == "rag-index":
        _print(LocalRagService().index_directory(args.directory))
    elif args.command == "rag-ask":
        _print(ask_local_rag(args.query).model_dump())
    elif args.command == "bedrock-ask":
        _print(ask_bedrock_knowledge_base(args.query).model_dump())


if __name__ == "__main__":
    main()
