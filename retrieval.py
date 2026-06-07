import argparse
import json
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer


CHUNKS_PATH = Path("documents/hsa_chunks.jsonl")
CHROMA_PATH = Path("chroma_db")
COLLECTION_NAME = "hsa_chunks"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_TOP_K = 4


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Could not find {path}. Run chunk_documents.py first.")

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


def chunk_metadata(chunk: dict[str, Any]) -> dict[str, str | int]:
    return {
        "document_id": chunk["document_id"],
        "chunk_index": int(chunk["chunk_index"]),
        "chunk_count": int(chunk["chunk_count"]),
        "source_type": chunk["source_type"],
        "source_name": chunk["source_name"],
        "title": chunk["title"],
        "section": chunk["section"],
        "url": chunk["url"],
    }


def load_embedding_model() -> SentenceTransformer:
    try:
        return SentenceTransformer(EMBEDDING_MODEL_NAME, local_files_only=True)
    except Exception:
        return SentenceTransformer(EMBEDDING_MODEL_NAME)


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"embedding_model": EMBEDDING_MODEL_NAME},
    )


def recreate_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"embedding_model": EMBEDDING_MODEL_NAME},
    )


def build_vector_store(chunks_path: Path = CHUNKS_PATH) -> None:
    chunks = read_jsonl(chunks_path)
    if not chunks:
        raise ValueError(f"No chunks found in {chunks_path}")

    model = load_embedding_model()
    collection = recreate_collection()

    ids = [chunk["id"] for chunk in chunks]
    texts = [chunk["text"] for chunk in chunks]
    metadatas = [chunk_metadata(chunk) for chunk in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True).tolist()

    collection.upsert(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    print(f"Indexed {len(chunks)} chunks into ChromaDB collection '{COLLECTION_NAME}'.")
    print(f"Vector store path: {CHROMA_PATH}")


def retrieve(query: str, top_k: int = DEFAULT_TOP_K) -> list[dict[str, Any]]:
    model = load_embedding_model()
    collection = get_collection()

    query_embedding = model.encode([query], normalize_embeddings=True).tolist()[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []
    for index, chunk_id in enumerate(results["ids"][0]):
        retrieved.append(
            {
                "id": chunk_id,
                "text": results["documents"][0][index],
                "metadata": results["metadatas"][0][index],
                "distance": results["distances"][0][index],
            }
        )

    return retrieved


def print_results(results: list[dict[str, Any]]) -> None:
    for rank, result in enumerate(results, start=1):
        metadata = result["metadata"]
        print(f"\n=== Result {rank} ===")
        print(f"Distance: {result['distance']:.4f}")
        print(f"Source: {metadata['source_name']}")
        print(f"Title: {metadata['title']}")
        print(f"Section: {metadata['section']}")
        print(f"URL: {metadata['url']}")
        print()
        print(result["text"][:1200])


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and query the HSA ChromaDB vector store.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("build", help="Embed chunks and store them in ChromaDB.")

    query_parser = subparsers.add_parser("query", help="Retrieve the top matching chunks for a question.")
    query_parser.add_argument("question", help="Question to retrieve context for.")
    query_parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="Number of chunks to retrieve.")

    args = parser.parse_args()

    if args.command == "build":
        build_vector_store()
    elif args.command == "query":
        print_results(retrieve(args.question, top_k=args.top_k))


if __name__ == "__main__":
    main()
