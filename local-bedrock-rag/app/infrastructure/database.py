from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine, String, DateTime, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


class DocumentRecord(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    object_key: Mapped[str] = mapped_column(String(1024), unique=True, index=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(255), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class IngestionRecord(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    knowledge_base_id: Mapped[str] = mapped_column(String(255))
    data_source_id: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(80), default="STARTING")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    raw_status: Mapped[str | None] = mapped_column(Text, nullable=True)


_settings = get_settings()
if _settings.database_url.startswith("sqlite:///./"):
    Path(_settings.database_url.removeprefix("sqlite:///./")).parent.mkdir(parents=True, exist_ok=True)
_engine = create_engine(
    _settings.database_url,
    connect_args={"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)


def init_db():
    Base.metadata.create_all(_engine)
