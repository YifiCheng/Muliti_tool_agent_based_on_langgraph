from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_project_docs_exist():
    required = [
        ROOT / "README.md",
        ROOT / "docs" / "architecture.md",
        ROOT / "docs" / "api.md",
        ROOT / "docs" / "demo_script.md",
        ROOT / "docs" / "interview_notes.md",
    ]

    missing = [str(path) for path in required if not path.exists()]
    assert missing == []


def test_readme_mentions_implemented_features():
    text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "LangGraph" in text
    assert "FastAPI" in text
    assert "Reflection" in text
    assert "SQL" in text
    assert "Trace" in text


def test_demo_script_mentions_approval_flow():
    text = (ROOT / "docs" / "demo_script.md").read_text(encoding="utf-8")

    assert "批准" in text
    assert "拒绝" in text
    assert "Trace" in text