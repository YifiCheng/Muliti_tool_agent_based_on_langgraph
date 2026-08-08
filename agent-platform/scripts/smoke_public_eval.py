import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATASET = "eval/cases/public_docs_rag_cases.yaml"
JSON_REPORT = "eval/reports/public_docs_rag_report.json"
MD_REPORT = "eval/reports/public_docs_rag_report.md"


def run(command: list[str]) -> None:
    print("running:", " ".join(command))
    subprocess.run(command, cwd=PROJECT_DIR, check=True)


def main() -> None:
    clean_dir = PROJECT_DIR / "data" / "public_docs" / "clean"
    if not clean_dir.exists() or not list(clean_dir.glob("*.md")):
        raise FileNotFoundError(
            "Public clean docs not found. Run scripts/fetch_public_docs.py "
            "and scripts/prepare_public_docs.py first."
        )

    run(
        [
            sys.executable,
            "scripts/run_eval.py",
            "--dataset",
            DATASET,
            "--output",
            JSON_REPORT,
            "--allow-failures",
        ]
    )
    run(
        [
            sys.executable,
            "scripts/render_eval_report.py",
            "--input",
            JSON_REPORT,
            "--output",
            MD_REPORT,
        ]
    )
    print("smoke_public_eval=ready")


if __name__ == "__main__":
    main()