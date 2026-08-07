import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eval.runner import load_cases, run_eval


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    cases = load_cases(args.dataset)
    report = run_eval(cases)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"total={report.total}")
    print(f"passed={report.passed}")
    print(f"pass_rate={report.pass_rate:.2f}")
    print(f"average_score={report.average_score:.2f}")
    print(f"output={output_path}")

    if report.passed != report.total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()