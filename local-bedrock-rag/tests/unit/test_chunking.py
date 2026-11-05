import pytest
from app.services.local_rag_service import chunk_text


def test_chunk_text_returns_chunks_with_overlap():
    chunks = chunk_text("abcdefghij", chunk_size=6, overlap=2)
    assert chunks == ["abcdef", "efghij"]


def test_chunk_text_empty():
    assert chunk_text("   ", 10, 2) == []


def test_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        chunk_text("abc", 5, 5)
