import re

from rag.models import DocumentChunk


def split_document(
    source: str,
    content: str,
    *,
    chunk_size: int = 500,
    chunk_overlap: int = 80,
) -> list[DocumentChunk]:
    sections = re.split(r"(?m)(?=^##\s+)", content)
    chunks: list[DocumentChunk] = []
    chunk_index = 0

    for section_text in sections:
        section_text = section_text.strip()
        if not section_text:
            continue

        first_line, _, body = section_text.partition("\n")
        section_name = first_line.lstrip("# ").strip()
        body = body.strip() or section_text

        start = 0
        while start < len(body):
            end = min(start + chunk_size, len(body))
            chunk_text = body[start:end].strip()
            if chunk_text:
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{source}:{chunk_index}",
                        source=source,
                        content=chunk_text,
                        section=section_name,
                        chunk_index=chunk_index,
                        metadata={"char_start": start, "char_end": end},
                    )
                )
                chunk_index += 1

            if end >= len(body):
                break
            start = max(end - chunk_overlap, start + 1)

    return chunks


def split_documents(
    documents: list[tuple[str, str]],
    *,
    chunk_size: int = 500,
    chunk_overlap: int = 80,
) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for source, content in documents:
        chunks.extend(
            split_document(
                source,
                content,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        )
    return chunks