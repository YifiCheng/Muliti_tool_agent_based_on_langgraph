from rag.hybrid_retriever import HybridRetriever
from rag.query_translation import NoopQueryTranslator, QueryTranslator
from tools.base import BaseTool, Evidence, ToolRequest, ToolResult


class DocumentSearchTool(BaseTool):
    name = "document_search"
    description = "Search enterprise documents and return cited evidence."

    def __init__(
        self,
        retriever: HybridRetriever,
        translator: QueryTranslator | None = None,
    ) -> None:
        self.retriever = retriever
        self.translator = translator or NoopQueryTranslator()

    def run(self, request: ToolRequest) -> ToolResult:
        top_k = int(request.params.get("top_k", 5))
        translation = self.translator.translate(request.query)
        results = self.retriever.search(translation.search_query, top_k=top_k)

        evidence = [
            Evidence(
                source=f"{result.chunk.source}#{result.chunk.chunk_index}",
                content=result.chunk.content,
                score=result.score,
                metadata={
                    "section": result.chunk.section,
                    "retriever": result.retriever,
                    "original_query": translation.original_query,
                    "search_query": translation.search_query,
                    "query_translated": translation.translated,
                    "translation_strategy": translation.strategy,
                },
            )
            for result in results
        ]

        metadata = {
            "query": request.query,
            "search_query": translation.search_query,
            "query_translated": translation.translated,
            "translation_strategy": translation.strategy,
            "result_count": len(evidence),
        }

        if not evidence:
            return ToolResult(
                tool_name=self.name,
                success=True,
                content="没有找到相关文档证据。",
                evidence=[],
                metadata=metadata,
            )

        return ToolResult(
            tool_name=self.name,
            success=True,
            content=f"找到 {len(evidence)} 条相关文档证据。",
            evidence=evidence,
            metadata=metadata,
        )