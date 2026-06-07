import json
from pathlib import Path
from typing import Any


CHUNKS_PATH = Path("documents/hsa_chunks.jsonl")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Could not find {path}. Run chunk_documents.py first.")

    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def representative_chunks(chunks: list[dict[str, Any]], count: int = 5) -> list[dict[str, Any]]:
    if len(chunks) <= count:
        return chunks

    sorted_chunks = sorted(chunks, key=lambda chunk: (chunk["source_name"], chunk["title"], chunk["section"]))
    indexes = [0, len(sorted_chunks) // 4, len(sorted_chunks) // 2, (len(sorted_chunks) * 3) // 4, len(sorted_chunks) - 1]
    return [sorted_chunks[index] for index in indexes]


def print_chunk(chunk: dict[str, Any], number: int) -> None:
    text = chunk["text"]
    print(f"\n=== Chunk {number} ===")
    print(f"Source: {chunk['source_name']}")
    print(f"Title: {chunk['title']}")
    print(f"Section: {chunk['section']}")
    print(f"Chunk: {chunk['chunk_index']} of {chunk['chunk_count']}")
    print(f"Characters: {len(text)}")
    print(f"URL: {chunk['url']}")
    print("\nText:")
    print(text)
    print("\nInspection questions:")
    print("- Does this make sense on its own?")
    print("- Could someone answer a question from this chunk alone, without reading before or after?")


def main() -> None:
    chunks = read_jsonl(CHUNKS_PATH)
    for number, chunk in enumerate(representative_chunks(chunks), start=1):
        print_chunk(chunk, number)


if __name__ == "__main__":
    main()
