import pytest

from rag.bm25_store import BM25Store
from rag.hybrid_retriever import HybridRetriever
from rag.loader import load_documents
from rag.models import DocumentChunk
from rag.splitter import split_document
from rag.vector_store import VectorStore
from tests.fakes import FakeEmbedder
from tools.base import ToolRequest
from tools.document_search import DocumentSearchTool


def make_chunks():
    return [
        DocumentChunk(
            chunk_id="policy-0",
            source="reimbursement_policy.md",
            content="报销金额超过 5000 元时，需要部门负责人审批。",
            section="报销审批",
        ),
        DocumentChunk(
            chunk_id="sales-0",
            source="sales_policy.md",
            content="销售折扣超过 10% 时，需要销售总监审批。",
            section="折扣审批",
        ),
    ]


def make_embedder(chunks, query_vector):
    return FakeEmbedder(
        {
            chunks[0].content: [1.0, 0.0, 0.0],
            chunks[1].content: [0.0, 1.0, 0.0],
            "报销审批": query_vector,
            "报销规则": [0.9, 0.1, 0.0],
            "unrelated": [0.0, 0.0, 1.0],
        }
    )


def test_load_documents():
    documents = load_documents("data/docs")
    assert len(documents) >= 3


def test_split_document():
    chunks = split_document(
        "demo.md",
        "# Demo\n\n## Section\n\n报销审批规则。" * 3,
        chunk_size=20,
        chunk_overlap=5,
    )
    assert chunks
    assert all(chunk.source == "demo.md" for chunk in chunks)
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)


def test_load_documents_missing_directory(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_documents(tmp_path / "missing")


def test_bm25_returns_relevant_document():
    store = BM25Store(make_chunks())
    results = store.search("报销审批", top_k=1)
    assert results
    assert results[0].chunk.source == "reimbursement_policy.md"


def test_bm25_empty_query():
    store = BM25Store(make_chunks())
    assert store.search("", top_k=3) == []


def test_vector_store_returns_similar_chunk():
    chunks = [
        DocumentChunk(chunk_id="a", source="a.md", content="报销审批"),
        DocumentChunk(chunk_id="b", source="b.md", content="产品套餐"),
    ]
    embedder = FakeEmbedder(
        {
            "报销审批": [1.0, 0.0, 0.0],
            "产品套餐": [0.0, 1.0, 0.0],
            "报销规则": [0.9, 0.1, 0.0],
        }
    )
    results = VectorStore(chunks, embedder).search("报销规则", top_k=1)
    assert len(results) == 1
    assert results[0].chunk.chunk_id == "a"


def test_hybrid_deduplicates_chunks():
    chunks = make_chunks()
    retriever = HybridRetriever(
        BM25Store(chunks),
        VectorStore(chunks, make_embedder(chunks, [1.0, 0.0, 0.0])),
    )
    results = retriever.search("报销审批", top_k=5)
    chunk_ids = [result.chunk.chunk_id for result in results]
    assert len(chunk_ids) == len(set(chunk_ids))
    assert all(result.retriever == "hybrid" for result in results)


def test_document_search_returns_evidence():
    chunks = make_chunks()
    retriever = HybridRetriever(
        BM25Store(chunks),
        VectorStore(chunks, make_embedder(chunks, [1.0, 0.0, 0.0])),
    )
    result = DocumentSearchTool(retriever).run(
        ToolRequest(query="报销审批", session_id="s1")
    )
    assert result.success is True
    assert result.evidence
    assert result.evidence[0].source
    assert result.evidence[0].content


def test_document_search_no_match_returns_empty_evidence():
    chunks = make_chunks()
    retriever = HybridRetriever(
        BM25Store(chunks),
        VectorStore(chunks, make_embedder(chunks, [0.0, 0.0, 1.0])),
    )
    result = DocumentSearchTool(retriever).run(
        ToolRequest(query="unrelated", session_id="s1")
    )
    assert result.success is True
    assert result.evidence == []