from rag.hybrid_retriever import HybridRetriever
from tools.base import BaseTool, Evidence, ToolRequest, ToolResult


class DocumentSearchTool(BaseTool):
    name = "document_search"
    description = "Search enterprise documents and return cited evidence."

    def __init__(self, retriever: HybridRetriever) -> None:
        self.retriever = retriever

    def run(self, request: ToolRequest) -> ToolResult:
        top_k = int(request.params.get("top_k", 5))
        results = self.retriever.search(request.query, top_k=top_k)

        evidence = [
            Evidence(
                source=f"{result.chunk.source}#{result.chunk.chunk_index}",
                content=result.chunk.content,
                score=result.score,
                metadata={
                    "section": result.chunk.section,
                    "retriever": result.retriever,
                },
            )
            for result in results
        ]

        if not evidence:
            return ToolResult(
                tool_name=self.name,
                success=True,
                content="没有找到相关文档证据。",
                evidence=[],
                metadata={"query": request.query, "result_count": 0},
            )

        return ToolResult(
            tool_name=self.name,
            success=True,
            content=f"找到 {len(evidence)} 条相关文档证据。",
            evidence=evidence,
            metadata={"query": request.query, "result_count": len(evidence)},
        )