import argparse
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml


PROJECT_DIR = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_DIR / "data" / "source_manifest.yaml"
RAW_DIR = PROJECT_DIR / "data" / "public_docs" / "raw"


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def extension_for(fetch_type: str) -> str:
    if fetch_type == "markdown":
        return ".md"
    if fetch_type == "html":
        return ".html"
    raise ValueError(f"Unsupported fetch_type: {fetch_type}")


def fetch_url(url: str, *, timeout: int = 30) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "business-multi-tool-agent-rag-demo/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def fetch_sources(*, limit: int | None = None) -> list[Path]:
    manifest = load_manifest()
    sources = manifest.get("sources", [])
    if limit is not None:
        sources = sources[:limit]

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for source in sources:
        source_id = source["id"]
        fetch_type = source["fetch_type"]
        target = RAW_DIR / f"{source_id}{extension_for(fetch_type)}"
        print(f"fetching {source_id}: {source['fetch_url']}")

        try:
            content = fetch_url(source["fetch_url"])
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Failed to fetch {source_id} from {source['fetch_url']}: {exc}"
            ) from exc

        target.write_text(content, encoding="utf-8")
        written.append(target)
        print(f"wrote {target.relative_to(PROJECT_DIR)}")

    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Fetch only the first N sources for a quick smoke test.",
    )
    args = parser.parse_args()

    written = fetch_sources(limit=args.limit)
    print(f"fetched_documents={len(written)}")
    print("fetch_public_docs=ready")


if __name__ == "__main__":
    sys.path.insert(0, str(PROJECT_DIR))
    main()