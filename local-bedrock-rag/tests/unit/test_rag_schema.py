from app.models.rag import RagAnswer


def test_rag_answer_schema():
    result = RagAnswer(
        answer="The application uses retrieval augmented generation.",
        sources=["architecture.md"],
        insufficient_information=False,
    )
    assert result.sources == ["architecture.md"]
