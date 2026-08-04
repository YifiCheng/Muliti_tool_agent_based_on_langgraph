import json

class MockLLMProvider:
    name = "mock"

    def chat(self, messages: list[dict], temperature: float = 0.2) -> str:
        last = messages[-1]["content"] if messages else ""
        return f"mock response: {last}"

    def chat_json(self, messages: list[dict], schema_name: str) -> dict:
        if schema_name == "plan":
            return {
                "tools": ["mock_search"],
                "reason": "mock plan for testing",
            }
        if schema_name == "reflection":
            return {
                "is_sufficient": True,
                "missing_info": [],
                "next_action": "answer",
                "reason": "mock evidence is sufficient",
            }
        return json.loads("{}")