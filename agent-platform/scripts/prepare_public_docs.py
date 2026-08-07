import argparse
import html
import re
from datetime import UTC, datetime
from pathlib import Path

import yaml


PROJECT_DIR = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_DIR / "data" / "source_manifest.yaml"
RAW_DIR = PROJECT_DIR / "data" / "public_docs" / "raw"
CLEAN_DIR = PROJECT_DIR / "data" / "public_docs" / "clean"
NOTICE_PATH = PROJECT_DIR / "data" / "public_docs" / "NOTICE.md"


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def strip_html(raw_html: str) -> str:
    text = re.sub(r"(?is)<script.*?</script>", " ", raw_html)
    text = re.sub(r"(?is)<style.*?</style>", " ", text)
    text = re.sub(r"(?i)</(h1|h2|h3)>", "\n\n", text)
    text = re.sub(r"(?i)<(h1|h2|h3)[^>]*>", "\n\n## ", text)
    text = re.sub(r"(?i)</p>", "\n\n", text)
    text = re.sub(r"(?i)<br\\s*/?>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    return html.unescape(text)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def raw_path_for(source: dict) -> Path:
    suffix = ".md" if source["fetch_type"] == "markdown" else ".html"
    return RAW_DIR / f"{source['id']}{suffix}"


def build_clean_document(source: dict, raw_text: str) -> str:
    if source["fetch_type"] == "html":
        body = normalize_text(strip_html(raw_text))
    elif source["fetch_type"] == "markdown":
        body = normalize_text(raw_text)
    else:
        raise ValueError(f"Unsupported fetch_type: {source['fetch_type']}")

    fetched_at = datetime.now(UTC).isoformat()
    topics = ", ".join(source.get("topics", []))

    front_matter = "\n".join(
        [
            "---",
            f"source_id: {source['id']}",
            f"title: {source['title']}",
            f"organization: {source['organization']}",
            f"source_url: {source['source_url']}",
            f"license: {source['license']}",
            f"license_url: {source['license_url']}",
            f"language: {source.get('language', 'unknown')}",
            f"topics: {topics}",
            f"fetched_at: {fetched_at}",
            "---",
            "",
        ]
    )
    return front_matter + f"# {source['title']}\n\n" + body + "\n"


def write_notice(manifest: dict) -> None:
    lines = [
        "# Public Document Sources Notice",
        "",
        "The clean RAG documents in `data/public_docs/clean/` are generated from public web sources.",
        "Verify each license before redistribution and keep attribution when using the content.",
        "",
        "## Sources",
        "",
    ]
    for source in manifest.get("sources", []):
        lines.extend(
            [
                f"### {source['title']}",
                "",
                f"- Organization: {source['organization']}",
                f"- Source: {source['source_url']}",
                f"- License: {source['license']}",
                f"- License URL: {source['license_url']}",
                "",
            ]
        )

    NOTICE_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTICE_PATH.write_text("\n".join(lines), encoding="utf-8")


def prepare_sources() -> list[Path]:
    manifest = load_manifest()
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for source in manifest.get("sources", []):
        raw_path = raw_path_for(source)
        if not raw_path.exists():
            raise FileNotFoundError(
                f"Missing raw document for {source['id']}: {raw_path}. "
                "Run scripts/fetch_public_docs.py first."
            )

        raw_text = raw_path.read_text(encoding="utf-8", errors="replace")
        clean_text = build_clean_document(source, raw_text)
        clean_path = CLEAN_DIR / f"{source['id']}.md"
        clean_path.write_text(clean_text, encoding="utf-8")
        written.append(clean_path)
        print(f"wrote {clean_path.relative_to(PROJECT_DIR)}")

    write_notice(manifest)
    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()

    written = prepare_sources()
    print(f"prepared_documents={len(written)}")
    print("prepare_public_docs=ready")


if __name__ == "__main__":
    main()