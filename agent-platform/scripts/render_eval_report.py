import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    metadata = data.get("metadata", {})
    title = metadata.get("name", "MVP 自动化评测报告")

    lines = [
        f"# {title}",
        "",
        metadata.get("description", ""),
        "",
        f"- Total: {data['total']}",
        f"- Passed: {data['passed']}",
        f"- Pass Rate: {data['pass_rate']:.2%}",
        f"- Average Score: {data['average_score']:.2f}",
        f"- RAG Docs Dir: {metadata.get('rag_docs_dir', '')}",
        "",
        "## By Category",
        "",
    ]

    for category, item in data["by_category"].items():
        lines.extend(
            [
                f"### {category}",
                "",
                f"- Total: {item['total']}",
                f"- Passed: {item['passed']}",
                f"- Pass Rate: {item['pass_rate']:.2%}",
                f"- Average Score: {item['average_score']:.2f}",
                "",
            ]
        )

    lines.extend(["## Cases", ""])
    for result in data["results"]:
        status = "PASS" if result["passed"] else "FAIL"
        result_metadata = result.get("metadata", {})
        lines.extend(
            [
                f"### {result['case_id']} - {status}",
                "",
                f"- Category: {result['category']}",
                f"- Query: {result['query']}",
                f"- Score: {result['score']:.2f}",
                f"- Selected Tools: {result['selected_tools']}",
                f"- Errors: {result['errors']}",
                f"- Evidence Count: {result_metadata.get('evidence_count', 0)}",
                f"- Expected Sources: {result_metadata.get('expected_sources', [])}",
                f"- Actual Sources: {result_metadata.get('actual_sources', [])}",
                "",
            ]
        )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"markdown_report={output_path}")


if __name__ == "__main__":
    main()