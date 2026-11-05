from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import get_settings
from app.infrastructure.database import init_db
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=get_settings().app_name,
    version="0.1.0",
    description="FakeCloud Bedrock API tests and real Ollama-backed local RAG.",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "application": get_settings().app_name}
