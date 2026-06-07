import json
from pathlib import Path
from typing import Any

from data_retrieval import CHUNKS_OUTPUT_PATH, OUTPUT_PATH, chunk_documents, dedupe_sentences, write_jsonl


HSA_TERMS = [
    "hsa",
    "health savings account",
    "health savings accounts",
    "high-deductible health plan",
    "high deductible health plan",
    "hdhp",
]

NON_HSA_SECTION_TERMS = [
    "archer msa",
    "dependent care",
    "fsa",
    "flexible spending",
    "health reimbursement",
    "hra",
    "medical savings account",
    "medical savings accounts",
    "medicare advantage msa",
    "msa",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {path}. Run data_retrieval.py once to create cleaned source documents."
        )

    records = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON on line {line_number} of {path}") from error

    return records


def is_hsa_related(record: dict[str, Any]) -> bool:
    title = record.get("title", "").lower()
    section = record.get("section", "").lower()
    text = record.get("text", "").lower()
    combined = f"{title} {section} {text}"

    if not any(term in combined for term in HSA_TERMS):
        return False

    if any(term in section for term in NON_HSA_SECTION_TERMS):
        return False

    return True


def filter_hsa_documents(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hsa_documents = []

    for document in documents:
        if not is_hsa_related(document):
            continue

        cleaned_document = dict(document)
        cleaned_document["text"] = dedupe_sentences(document["text"])
        hsa_documents.append(cleaned_document)

    return hsa_documents


def print_chunk_summary(chunks: list[dict[str, Any]]) -> None:
    if not chunks:
        print("No chunks were created.")
        return

    lengths = [len(chunk["text"]) for chunk in chunks]
    multi_chunk_documents = {
        chunk["document_id"]
        for chunk in chunks
        if chunk.get("chunk_count", 1) > 1
    }

    print(f"Wrote {len(chunks)} chunks to {CHUNKS_OUTPUT_PATH}")
    print(f"Chunk length range: {min(lengths)}-{max(lengths)} characters")
    print(f"Documents split into multiple chunks: {len(multi_chunk_documents)}")

    sample = max(chunks, key=lambda chunk: len(chunk["text"]))
    print("\n--- Sample chunk ---")
    print(f"Source: {sample.get('source_name')}")
    print(f"Title: {sample.get('title')}")
    print(f"Section: {sample.get('section')}")
    print(f"Chunk: {sample.get('chunk_index')} of {sample.get('chunk_count')}")
    print(f"Characters: {len(sample.get('text', ''))}")
    print(f"URL: {sample.get('url')}")
    print()
    print(sample.get("text", "")[:2000])
    print("--- End sample chunk ---")


def main() -> None:
    documents = read_jsonl(OUTPUT_PATH)
    hsa_documents = filter_hsa_documents(documents)
    chunks = chunk_documents(hsa_documents)
    write_jsonl(CHUNKS_OUTPUT_PATH, chunks)
    print(f"Read {len(documents)} cleaned documents from {OUTPUT_PATH}")
    print(f"Kept {len(hsa_documents)} HSA-related documents")
    print(f"Filtered out {len(documents) - len(hsa_documents)} non-HSA documents")
    print_chunk_summary(chunks)


if __name__ == "__main__":
    main()
