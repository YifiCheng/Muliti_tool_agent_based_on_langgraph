from typing import Any


def build_plan_messages(
    query: str,
    available_tools: list[dict[str, str]],
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是企业 Agent 的任务规划器。"
                "请选择完成用户问题所需的工具，并只返回 JSON。"
                "JSON 字段为 tools 和 reason。"
                f"可用工具: {available_tools}"
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
