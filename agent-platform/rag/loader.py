from pathlib import Path


def load_documents(docs_dir: str | Path) -> list[tuple[str, str]]:
    root = Path(docs_dir)
    if not root.exists():
        raise FileNotFoundError(f"Document directory not found: {root}")

    documents: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        content = path.read_text(encoding="utf-8")
        if content.strip():
            documents.append((path.name, content))

    return documents