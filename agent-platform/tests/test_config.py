from config.settings import load_settings


def test_load_settings():
    settings = load_settings()
    assert settings.app.name == "business-multi-tool-agent-test"
    assert settings.llm.provider == "mock"
    assert settings.agent.max_iterations >= 1