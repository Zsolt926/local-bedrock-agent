import json
from pathlib import Path
from app.core.config import get_settings
from app.infrastructure.bedrock_kb_repository import BedrockKnowledgeBaseRepository
from app.infrastructure.database import SessionLocal, IngestionRecord


class KnowledgeBaseService:
    def __init__(self):
        self.settings = get_settings()
        self.repository = BedrockKnowledgeBaseRepository()

    def create(self) -> dict:
        kb = self.repository.create_knowledge_base()
        ds = self.repository.create_s3_data_source(kb["knowledgeBaseId"])
        # Update the cached settings object too, so API callers can continue
        # with ingestion in the same process without restarting FastAPI.
        self.settings.bedrock_kb_id = kb["knowledgeBaseId"]
        self.settings.bedrock_data_source_id = ds["dataSourceId"]
        self._update_env({
            "BEDROCK_KB_ID": kb["knowledgeBaseId"],
            "BEDROCK_DATA_SOURCE_ID": ds["dataSourceId"],
        })
        return {"knowledge_base": kb, "data_source": ds}

    def start_ingestion(self, kb_id: str | None = None,
                        data_source_id: str | None = None) -> dict:
        kb_id = kb_id or self.settings.bedrock_kb_id
        data_source_id = data_source_id or self.settings.bedrock_data_source_id
        if not kb_id or not data_source_id:
            raise ValueError("Set BEDROCK_KB_ID and BEDROCK_DATA_SOURCE_ID or run create-kb.")
        job = self.repository.start_ingestion(kb_id, data_source_id)
        with SessionLocal() as db:
            db.add(IngestionRecord(
                job_id=job["ingestionJobId"],
                knowledge_base_id=kb_id,
                data_source_id=data_source_id,
                status=job.get("status", "STARTING"),
                raw_status=json.dumps(job, default=str),
            ))
            db.commit()
        return job

    def get_ingestion(self, job_id: str, kb_id: str | None = None,
                      data_source_id: str | None = None) -> dict:
        kb_id = kb_id or self.settings.bedrock_kb_id
        data_source_id = data_source_id or self.settings.bedrock_data_source_id
        if not kb_id or not data_source_id:
            raise ValueError("Knowledge Base and data source IDs are required.")
        job = self.repository.get_ingestion_job(kb_id, data_source_id, job_id)
        with SessionLocal() as db:
            record = db.query(IngestionRecord).filter_by(job_id=job_id).one_or_none()
            if record:
                record.status = job.get("status", record.status)
                record.raw_status = json.dumps(job, default=str)
                db.commit()
        return job

    def retrieve(self, query: str, kb_id: str | None = None,
                 number_of_results: int = 5) -> list[dict]:
        kb_id = kb_id or self.settings.bedrock_kb_id
        if not kb_id:
            raise ValueError("Set BEDROCK_KB_ID or run create-kb.")
        return self.repository.retrieve(kb_id, query, number_of_results)

    def retrieve_and_generate(self, query: str, kb_id: str | None = None,
                              model_arn: str | None = None) -> dict:
        kb_id = kb_id or self.settings.bedrock_kb_id
        if not kb_id:
            raise ValueError("Set BEDROCK_KB_ID or run create-kb.")
        model_arn = model_arn or self.settings.bedrock_foundation_model_arn
        return self.repository.retrieve_and_generate(kb_id, model_arn, query)

    @staticmethod
    def _update_env(values: dict[str, str]) -> None:
        env_path = Path(".env")
        if not env_path.exists():
            return
        lines = env_path.read_text(encoding="utf-8").splitlines()
        for key, value in values.items():
            prefix = key + "="
            for index, line in enumerate(lines):
                if line.startswith(prefix):
                    lines[index] = f"{key}={value}"
                    break
            else:
                lines.append(f"{key}={value}")
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        # Settings are cached; tell the user to restart the process after create-kb.
