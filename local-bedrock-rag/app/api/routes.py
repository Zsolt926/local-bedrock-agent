from fastapi import APIRouter, UploadFile, File, HTTPException
from app.api.schemas import (
    IngestionRequest, RetrieveRequest, RetrieveGenerateRequest,
    LocalIndexRequest, LocalAskRequest, BedrockAskRequest,
)
from app.services.document_service import DocumentService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.local_rag_service import LocalRagService
from app.agents.local_rag_agent import ask_local_rag
from app.agents.bedrock_kb_agent import ask_bedrock_knowledge_base

router = APIRouter()


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return DocumentService().upload_bytes(
            file.filename or "upload.bin",
            content,
            file.content_type or "application/octet-stream",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/knowledge-base/create")
def create_knowledge_base():
    try:
        return KnowledgeBaseService().create()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/knowledge-base/ingestion")
def start_ingestion(request: IngestionRequest):
    try:
        return KnowledgeBaseService().start_ingestion(
            request.knowledge_base_id, request.data_source_id
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/knowledge-base/ingestion/{job_id}")
def get_ingestion(job_id: str):
    try:
        return KnowledgeBaseService().get_ingestion(job_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/knowledge-base/retrieve")
def retrieve(request: RetrieveRequest):
    try:
        return {"results": KnowledgeBaseService().retrieve(
            request.query, request.knowledge_base_id, request.number_of_results
        )}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/knowledge-base/retrieve-and-generate")
def retrieve_and_generate(request: RetrieveGenerateRequest):
    try:
        return KnowledgeBaseService().retrieve_and_generate(
            request.query, request.knowledge_base_id, request.model_arn
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/local-rag/index")
def index_local_documents(request: LocalIndexRequest):
    try:
        return LocalRagService().index_directory(request.directory)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/local-rag/ask")
def ask_local_documents(request: LocalAskRequest):
    try:
        return ask_local_rag(request.question).model_dump()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/bedrock-agent/ask")
def ask_bedrock_agent(request: BedrockAskRequest):
    try:
        return ask_bedrock_knowledge_base(request.question).model_dump()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
