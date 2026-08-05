from pathlib import Path

from config.settings import Settings, load_settings
from rag.bm25_store import BM25Store
from rag.embeddings import build_embedder
from rag.hybrid_retriever import HybridRetriever
from rag.loader import load_documents
from rag.splitter import split_documents
from rag.vector_store import VectorStore


def build_retriever(settings: Settings | None = None) -> HybridRetriever:
    settings = settings or load_settings()
    documents = load_documents(settings.rag.docs_dir)
    chunks = split_documents(
        documents,
        chunk_size=settings.rag.chunk_size,
        chunk_overlap=settings.rag.chunk_overlap,
    )
    if not chunks:
        raise ValueError("No document chunks were created")

    bm25_store = BM25Store(chunks)
    vector_store = VectorStore(chunks, build_embedder("hash"))
    return HybridRetriever(bm25_store, vector_store)


def main() -> None:
    settings = load_settings()
    documents = load_documents(settings.rag.docs_dir)
    chunks = split_documents(
        documents,
        chunk_size=settings.rag.chunk_size,
        chunk_overlap=settings.rag.chunk_overlap,
    )
    retriever = build_retriever(settings)

    Path(settings.rag.index_dir).mkdir(parents=True, exist_ok=True)
    print(f"loaded_documents={len(documents)}")
    print(f"created_chunks={len(chunks)}")
    print(f"bm25_index={retriever.bm25_store.__class__.__name__}")
    print(f"vector_index={retriever.vector_store.__class__.__name__}")
    print("hybrid_retriever=ready")


if __name__ == "__main__":
    main()