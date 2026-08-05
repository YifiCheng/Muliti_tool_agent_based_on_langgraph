import ast
import operator
from typing import Any

from tools.base import BaseTool, Evidence, ToolRequest, ToolResult


class MockDocumentSearchTool(BaseTool):
    name = "mock_document_search"
    description = "Search mock enterprise policy documents."

    def run(self, request: ToolRequest) -> ToolResult:
        evidence = Evidence(
            source="mock_policy.md#section_1",
            content="报销金额超过 5000 元时，需要部门负责人和财务负责人审批。",
            score=0.95,
            metadata={"doc_type": "policy"},
        )
        return ToolResult(
            tool_name=self.name,
            success=True,
            content="找到 1 条报销审批相关制度。",
            evidence=[evidence],
            metadata={"query": request.query},
        )


class MockSQLTool(BaseTool):
    name = "mock_sql"
    description = "Run mock read-only business data queries."

    def run(self, request: ToolRequest) -> ToolResult:
        rows = [
            {"product": "智能客服套餐", "sales_amount": 128000},
            {"product": "数据分析套餐", "sales_amount": 96000},
        ]
        return ToolResult(
            tool_name=self.name,
            success=True,
            content="查询到 2 条销售数据，销售额最高的是智能客服套餐。",
            metadata={"rows": rows, "row_count": len(rows)},
        )


class MockCalculatorTool(BaseTool):
    name = "mock_calculator"
    description = "Evaluate simple arithmetic expressions for testing."

    def run(self, request: ToolRequest) -> ToolResult:
        expression = request.params.get("expression") or request.query
        value = _safe_eval_arithmetic(expression)
        return ToolResult(
            tool_name=self.name,
            success=True,
            content=str(value),
            metadata={"expression": expression, "value": value},
        )


def build_mock_registry():
    from tools.registry import ToolRegistry

    registry = ToolRegistry()
    registry.register(MockDocumentSearchTool())
    registry.register(MockSQLTool())
    registry.register(MockCalculatorTool())
    return registry


_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def _safe_eval_arithmetic(expression: str) -> int | float:
    node = ast.parse(expression, mode="eval")
    return _eval_node(node.body)


def _eval_node(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Only simple arithmetic expressions are allowed")