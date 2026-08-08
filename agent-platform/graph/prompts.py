from typing import Any


def infer_tools_from_query(query: str, available_tools: list[dict[str, str]]) -> list[str]:
    tool_names = {item["name"] for item in available_tools}
    lowered = query.lower()

    document_terms = [
        "handbook",
        "document",
        "doc",
        "文档",
        "手册",
        "制度",
        "政策",
        "沟通",
        "工程",
        "产品",
        "values",
        "employee",
        "people",
        "团队",
        "报销",
        "审批",
    ]
    sql_terms = [
        "sql",
        "数据库",
        "数据",
        "销售",
        "订单",
        "商品",
        "客户",
        "查询",
        "统计",
        "最高",
        "最大",
        "金额",
        "营收",
        "收入",
    ]

    selected: list[str] = []
    if "document_search" in tool_names and any(term in lowered for term in document_terms):
        selected.append("document_search")
    if "sql_query" in tool_names and any(term in lowered for term in sql_terms):
        selected.append("sql_query")

    return list(dict.fromkeys(selected))


def build_plan_messages(
    query: str,
    available_tools: list[dict[str, str]],
) -> list[dict[str, str]]:
    tool_names = [item["name"] for item in available_tools]
    return [
        {
            "role": "system",
            "content": (
                "你是企业 Agent 的任务规划器。"
                "只能从给定的工具名中选择，且至少选择 1 个。"
                "只返回 JSON，tools 必须是字符串数组。"
                "不要返回工具对象，不要返回 description，不要返回空数组。"
                f"可选工具名: {tool_names}"
            ),
        },
        {
            "role": "user",
            "content": f"用户问题: {query}",
        },
    ]


def build_reflection_messages(
    query: str,
    tool_results: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是 Agent 的证据充分性校验器。"
                "请判断当前信息是否足以回答原始问题，并只返回 JSON。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"原始问题: {query}\n"
                f"工具结果: {tool_results}\n"
                f"证据: {evidence}"
            ),
        },
    ]


def build_answer_messages(
    query: str,
    tool_results: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是企业业务助手。"
                "只能根据工具结果和证据回答。"
                "如果信息不足，需要明确说明，不要编造。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"原始问题: {query}\n"
                f"累计工具结果: {tool_results}\n"
                f"累计证据: {evidence}\n"
                f"执行错误: {errors}"
            ),
        },
    ]
