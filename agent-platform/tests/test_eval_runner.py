from eval.runner import load_cases, load_dataset, run_eval


def test_load_cases():
    cases = load_cases("eval/cases/mvp_cases.yaml")
    assert len(cases) >= 6
    assert cases[0].case_id


def test_run_eval_returns_report():
    cases = load_cases("eval/cases/mvp_cases.yaml")[:2]
    report = run_eval(cases)

    assert report.total == 2
    assert len(report.results) == 2
    assert report.average_score >= 0

def test_load_dataset_metadata():
    metadata, cases = load_dataset("eval/cases/mvp_cases.yaml")

    assert metadata.name == "default"
    assert metadata.rag_docs_dir is None
    assert len(cases) >= 6