from pathlib import Path
from sqlalchemy import select
from app.infrastructure.database import SessionLocal, DocumentRecord
from app.infrastructure.s3_repository import S3Repository


class DocumentService:
    def __init__(self):
        self.s3 = S3Repository()

    def upload_directory(self, directory: str) -> list[dict]:
        root = Path(directory)
        if not root.exists():
            raise FileNotFoundError(root)
        uploaded = []
        with SessionLocal() as db:
            for path in sorted(root.iterdir()):
                if not path.is_file() or path.name.endswith(".metadata.json"):
                    continue
                result = self.s3.upload_file(path)
                record = db.scalar(
                    select(DocumentRecord).where(
                        DocumentRecord.object_key == result["key"]
                    )
                )
                if record is None:
                    record = DocumentRecord(
                        object_key=result["key"],
                        filename=path.name,
                        content_type=result["content_type"],
                        size_bytes=result["size_bytes"],
                    )
                    db.add(record)
                else:
                    record.size_bytes = result["size_bytes"]
                    record.content_type = result["content_type"]
                uploaded.append(result)
            db.commit()
        return uploaded

    def upload_bytes(self, filename: str, content: bytes, content_type: str,
                     metadata: dict | None = None) -> dict:
        result = self.s3.upload_bytes(filename, content, content_type, metadata)
        with SessionLocal() as db:
            record = db.scalar(
                select(DocumentRecord).where(
                    DocumentRecord.object_key == result["key"]
                )
            )
            if record is None:
                db.add(DocumentRecord(
                    object_key=result["key"],
                    filename=Path(filename).name,
                    content_type=content_type,
                    size_bytes=len(content),
                ))
            else:
                record.size_bytes = len(content)
            db.commit()
        return result
