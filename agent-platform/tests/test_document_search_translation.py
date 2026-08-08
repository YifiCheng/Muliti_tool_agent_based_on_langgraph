from rag.bm25_store import BM25Store
from rag.hybrid_retriever import HybridRetriever
from rag.models import DocumentChunk
from rag.query_translation import RuleBasedQueryTranslator
from rag.vector_store import VectorStore
from tests.fakes import FakeEmbedder
from tools.base import ToolRequest
from tools.document_search import DocumentSearchTool


def test_document_search_uses_translated_query_metadata() -> None:
    chunks = [
        DocumentChunk(
            chunk_id="gitlab-communication-0",
            source="gitlab_handbook_communication.md",
            content="GitLab handbook communication guidelines for async work.",
        )
    ]
    embedder = FakeEmbedder(
        {
            chunks[0].content: [1.0, 0.0, 0.0],
            "GitLab communication handbook": [1.0, 0.0, 0.0],
        }
    )
    retriever = HybridRetriever(
        BM25Store(chunks),
        VectorStore(chunks, embedder),
    )
    tool = DocumentSearchTool(
        retriever,
        translator=RuleBasedQueryTranslator(),
    )

    result = tool.run(
        ToolRequest(
            query="GitLab handbook 中如何描述沟通方式？",
            session_id="s1",
        )
    )

    assert result.success is True
    assert result.evidence
    assert result.metadata["query_translated"] is True
    assert "communication" in result.metadata["search_query"]
    assert result.evidence[0].metadata["original_query"] == (
        "GitLab handbook 中如何描述沟通方式？"
    )
    assert result.evidence[0].metadata["query_translated"] is True