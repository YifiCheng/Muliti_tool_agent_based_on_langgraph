import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATASET = "eval/cases/public_docs_rag_cases.yaml"
JSON_REPORT = "eval/reports/public_docs_rag_report.json"
MD_REPORT = "eval/reports/public_docs_rag_report.md"


def run(command: list[str], timeout_seconds: int) -> None:
    print("running:", " ".join(command), flush=True)
    subprocess.run(
        command,
        cwd=PROJECT_DIR,
        check=True,
        timeout=timeout_seconds,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id", default="")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    args = parser.parse_args()

    clean_dir = PROJECT_DIR / "data" / "public_docs" / "clean"
    if not clean_dir.exists() or not list(clean_dir.glob("*.md")):
        raise FileNotFoundError(
            "Public clean docs not found. Run scripts/fetch_public_docs.py "
            "and scripts/prepare_public_docs.py first."
        )

    eval_command = [
        sys.executable,
        "scripts/run_eval.py",
        "--dataset",
        DATASET,
        "--output",
        JSON_REPORT,
        "--allow-failures",
    ]
    if args.case_id:
        eval_command.extend(["--case-id", args.case_id])
    if args.limit > 0:
        eval_command.extend(["--limit", str(args.limit)])

    run(eval_command, timeout_seconds=args.timeout_seconds)
    run(
        [
            sys.executable,
            "scripts/render_eval_report.py",
            "--input",
            JSON_REPORT,
            "--output",
            MD_REPORT,
        ],
        timeout_seconds=60,
    )
    print("smoke_public_eval=ready")


if __name__ == "__main__":
    main()