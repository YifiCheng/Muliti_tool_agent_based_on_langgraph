from pathlib import Path

from eval.metrics import evidence_source_match
from eval.runner import load_dataset, settings_for_dataset


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATASET = PROJECT_DIR / "eval" / "cases" / "public_docs_rag_cases.yaml"


def test_public_docs_eval_dataset_loads() -> None:
    metadata, cases = load_dataset(DATASET)

    assert metadata.name == "Public Docs RAG Evaluation"
    assert metadata.rag_docs_dir == "data/public_docs/clean"
    assert len(cases) >= 9
    assert any(case.query_language == "zh" for case in cases)
    assert all("document_search" in case.expected_tools for case in cases)


def test_public_docs_eval_cases_have_expected_sources() -> None:
    _, cases = load_dataset(DATASET)

    for case in cases:
        assert case.expected_sources, case.case_id
        assert case.min_evidence_count >= 1
        assert case.require_evidence is True


def test_settings_for_dataset_overrides_rag_docs_dir() -> None:
    metadata, _ = load_dataset(DATASET)
    settings = settings_for_dataset(metadata)

    assert settings.rag.docs_dir == "data/public_docs/clean"


def test_evidence_source_match_uses_partial_source_names() -> None:
    state = {
        "evidence": [
            {"source": "gitlab_handbook_communication.md#3"},
            {"source": "mattermost_handbook_product.md#1"},
        ]
    }

    assert evidence_source_match(
        state,
        ["gitlab_handbook_communication.md"],
    )
    assert not evidence_source_match(
        state,
        ["clef_handbook.md"],
    )