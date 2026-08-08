import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eval.runner import load_dataset, run_eval


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--case-id", default="")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--allow-failures",
        action="store_true",
        help="Write the report even if some cases fail.",
    )
    args = parser.parse_args()

    metadata, cases = load_dataset(args.dataset)
    if args.case_id:
        cases = [case for case in cases if case.case_id == args.case_id]
        if not cases:
            raise SystemExit(f"case not found: {args.case_id}")
    if args.limit > 0:
        cases = cases[: args.limit]
    report = run_eval(cases, metadata=metadata)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"dataset={metadata.name}")
    print(f"total={report.total}")
    print(f"passed={report.passed}")
    print(f"pass_rate={report.pass_rate:.2f}")
    print(f"average_score={report.average_score:.2f}")
    print(f"output={output_path}")

    if report.passed != report.total and not args.allow_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()