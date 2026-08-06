import json


class MockLLMProvider:
    name = "mock"

    def chat(self, messages: list[dict], temperature: float = 0.2) -> str:
        last = messages[-1]["content"] if messages else ""
        return f"mock response: {last}"

    def chat_json(self, messages: list[dict], schema_name: str) -> dict:
        last = messages[-1]["content"] if messages else ""

        if schema_name == "plan":
            if any(token in last for token in ["销售", "订单", "商品"]):
                return {
                    "tools": ["sql_query"],
                    "reason": "mock plan selected SQL tool",
                }
            if any(token in last for token in ["计算", "+", "-", "*", "/"]):
                return {
                    "tools": ["mock_calculator"],
                    "reason": "mock plan selected calculator tool",
                }
            return {
                "tools": ["document_search"],
                "reason": "mock plan selected document search tool",
            }

        if schema_name == "reflection":
            if "需要补充" in last:
                return {
                    "is_sufficient": False,
                    "missing_info": ["mock missing evidence"],
                    "next_action": "retrieve_more",
                    "replan_query": "补充检索报销审批规则",
                    "reason": "mock reflection asks for another retrieval",
                }
            return {
                "is_sufficient": True,
                "missing_info": [],
                "next_action": "answer",
                "reason": "mock evidence is sufficient",
            }

        return json.loads("{}")