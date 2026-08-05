from langgraph.graph import END

from graph.state import AgentState


def route_after_reflect(state: AgentState) -> str:
    reflection = state.get("reflection", {})
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 3)

    if iteration >= max_iterations:
        return "answer"

    if reflection.get("next_action") == "retrieve_more":
        return "plan"

    return "answer"