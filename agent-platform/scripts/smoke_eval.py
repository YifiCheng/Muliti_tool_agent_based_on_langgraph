import subprocess
import sys
from pathlib import Path


def main() -> None:
    project_dir = Path(__file__).resolve().parents[1]
    commands = [
        [
            sys.executable,
            "scripts/run_eval.py",
            "--dataset",
            "eval/cases/mvp_cases.yaml",
            "--output",
            "eval/reports/mvp_report.json",
        ],
        [
            sys.executable,
            "scripts/render_eval_report.py",
            "--input",
            "eval/reports/mvp_report.json",
            "--output",
            "eval/reports/mvp_report.md",
        ],
    ]

    for command in commands:
        print("running:", " ".join(command))
        completed = subprocess.run(command, cwd=project_dir, check=False)
        if completed.returncode != 0:
            raise SystemExit(completed.returncode)

    print("eval_smoke=passed")


if __name__ == "__main__":
    main()