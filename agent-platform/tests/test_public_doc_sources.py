from pathlib import Path

import yaml

from scripts.prepare_public_docs import (
    build_clean_document,
    normalize_text,
    strip_html,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = PROJECT_DIR.parent
MANIFEST_PATH = PROJECT_DIR / "data" / "source_manifest.yaml"


def load_manifest() -> dict:
    return yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_source_manifest_exists_and_has_real_sources() -> None:
    manifest = load_manifest()
    sources = manifest["sources"]

    assert len(sources) >= 5
    assert {source["organization"] for source in sources} >= {
        "GitLab",
        "Mattermost",
        "Clef",
    }


def test_source_manifest_has_license_and_urls() -> None:
    manifest = load_manifest()

    for source in manifest["sources"]:
        assert source["id"]
        assert source["title"]
        assert source["source_url"].startswith("https://")
        assert source["fetch_url"].startswith("https://")
        assert source["license"]
        assert source["license_url"].startswith("https://")
        assert source["fetch_type"] in {"html", "markdown"}


def test_html_stripping_keeps_visible_text() -> None:
    raw = """
    <html>
      <head><style>.x { color: red; }</style></head>
      <body>
        <h1>Handbook</h1>
        <script>alert("x")</script>
        <p>Communication guidelines for distributed teams.</p>
      </body>
    </html>
    """

    text = normalize_text(strip_html(raw))

    assert "Handbook" in text
    assert "Communication guidelines" in text
    assert "alert" not in text
    assert "color: red" not in text


def test_build_clean_document_adds_attribution_metadata() -> None:
    source = {
        "id": "demo",
        "title": "Demo Handbook",
        "organization": "Demo Org",
        "source_url": "https://example.com/handbook",
        "fetch_type": "markdown",
        "license": "CC0-1.0",
        "license_url": "https://example.com/license",
        "language": "en",
        "topics": ["communication", "process"],
    }

    text = build_clean_document(
        source,
        "# Demo\n\nCommunication guidelines for teams.",
    )

    assert "source_id: demo" in text
    assert "organization: Demo Org" in text
    assert "license: CC0-1.0" in text
    assert "Communication guidelines" in text


def test_gitignore_allows_manifest_and_notice() -> None:
    gitignore = (ROOT_DIR / ".gitignore").read_text(encoding="utf-8")

    assert "!agent-platform/data/source_manifest.yaml" in gitignore
    assert "!agent-platform/data/public_docs/" in gitignore
    assert "!agent-platform/data/public_docs/NOTICE.md" in gitignore