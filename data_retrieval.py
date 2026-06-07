import hashlib
import html
import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


SOURCE_URLS = [
    "https://www.investopedia.com/terms/h/hsa.asp",
    "https://www.irs.gov/publications/p969",
    "https://www.healthcare.gov/high-deductible-health-plan/hdhp-hsa-information/",
    "https://www.fidelity.com/learning-center/personal-finance/spending-from-hsa",
    "https://www.fidelity.com/learning-center/personal-finance/hsa-what-to-look-for",
    "https://www.fidelity.com/learning-center/personal-finance/how-to-open-an-HSA",
    "https://www.optumbank.com/resources/library/money-management-hsa.html",
    "https://www.optumbank.com/health-savings-accounts/resources/managing-hsa.html",
    "https://www.hsabank.com/HSABank/Learning-Center/IRS-qualified-medical-expenses",
    "https://www.hsabank.com/Members/Members-FAQs.html",
]

OUTPUT_PATH = Path("documents/hsa_sources.jsonl")
CHUNKS_OUTPUT_PATH = Path("documents/hsa_chunks.jsonl")
CACHE_DIR = Path("documents/raw_cache")
REQUEST_DELAY_SECONDS = 1.0
CHUNK_SIZE_CHARS = 2000
CHUNK_OVERLAP_CHARS = 300

HEADERS = {
    "User-Agent": "ai201-hsa-rag-project/1.0 by student",
    "Accept": "text/html,application/json",
}

BOILERPLATE_PATTERNS = [
    r"^advertisement$",
    r"^close$",
    r"^continue reading$",
    r"^email this page$",
    r"^follow us$",
    r"^get (your|an) hsa\b.*",
    r"^image$",
    r"^learn more$",
    r"^learn more\b.*",
    r"^open (your|an) hsa\b.*",
    r"^more info$",
    r"^print$",
    r"^read more$",
    r"^related articles?$",
    r"^save image image$",
    r"^share$",
    r"^subscribe$",
    r"^table of contents$",
]

BOILERPLATE_TEXT_FRAGMENTS = [
    "accept cookies",
    "all rights reserved",
    "cookie policy",
    "do not sell",
    "getting answers to your tax questions",
    "getting tax forms",
    "external link",
    "how to get tax help",
    "ordering tax forms",
    "privacy policy",
    "publication 969 - main contents",
    "terms of use",
    "this website uses cookies",
    "we welcome your comments",
]

MIN_TEXT_LENGTH = 30
HEADING_TAGS = {"h2", "h3", "h4", "h5", "h6"}
INLINE_LABEL_HEADINGS = {"caution:", "note:", "tip:"}
STOP_SECTION_HEADINGS = {
    "additional material",
    "for more information",
    "how to get tax help",
    "index",
    "publication 969 - additional material",
    "related articles",
    "tax help",
}


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    scheme = "https"
    netloc = parsed.netloc.lower()
    path = parsed.path
    last_path_part = path.rsplit("/", 1)[-1]
    if "." not in last_path_part and not path.endswith("/"):
        path += "/"
    return urlunparse((scheme, netloc, path, "", "", ""))


def cache_path(url: str, suffix: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return CACHE_DIR / f"{digest}.{suffix}"


def fetch(url: str, suffix: str) -> str:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = cache_path(url, suffix)

    if path.exists():
        return path.read_text(encoding="utf-8")

    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    text = response.text
    path.write_text(text, encoding="utf-8")
    time.sleep(REQUEST_DELAY_SECONDS)
    return text


def clean_text(text: str) -> str:
    text = html.unescape(text)
    if "â" in text or "Â" in text:
        try:
            text = text.encode("latin1").decode("utf-8")
        except UnicodeError:
            pass
    replacements = {
        "â": "'",
        "â": "'",
        "â": '"',
        "â": '"',
        "â": "-",
        "â": "-",
        "\u00e2\u0080\u0099": "'",
        "\u00e2\u0080\u0098": "'",
        "\u00e2\u0080\u009c": '"',
        "\u00e2\u0080\u009d": '"',
        "\u00e2\u0080\u0093": "-",
        "\u00e2\u0080\u0094": "-",
        "Â": " ",
        "\u00c2": " ",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip()


def is_boilerplate_text(text: str) -> bool:
    normalized = clean_text(text).lower()
    if not normalized:
        return True

    if "➜" in normalized or "→" in normalized:
        return True

    if re.fullmatch(r"https?://\S+", normalized):
        return True

    if len(normalized) < MIN_TEXT_LENGTH and not normalized.endswith("?"):
        return True

    if any(re.fullmatch(pattern, normalized) for pattern in BOILERPLATE_PATTERNS):
        return True

    return any(fragment in normalized for fragment in BOILERPLATE_TEXT_FRAGMENTS)


def is_boilerplate_heading(text: str) -> bool:
    normalized = clean_text(text).lower()
    if not normalized:
        return True

    if "➜" in normalized or "→" in normalized:
        return True

    if re.fullmatch(r"https?://\S+", normalized):
        return True

    if any(re.fullmatch(pattern, normalized) for pattern in BOILERPLATE_PATTERNS):
        return True

    return any(fragment in normalized for fragment in BOILERPLATE_TEXT_FRAGMENTS)


def dedupe_parts(parts: list[str]) -> list[str]:
    seen = set()
    deduped = []

    for part in parts:
        normalized = clean_text(part).lower()
        normalized = re.sub(r"[^a-z0-9]+", " ", normalized).strip()
        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        deduped.append(part)

    return deduped


def dedupe_sentences(text: str) -> str:
    pieces = re.split(r"(?<=[.!?])\s+", clean_text(text))
    seen = set()
    deduped = []

    for piece in pieces:
        if is_boilerplate_text(piece):
            continue

        normalized = re.sub(r"[^a-z0-9]+", " ", piece.lower()).strip()
        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        deduped.append(piece)

    return " ".join(deduped)


def page_title(soup: BeautifulSoup, url: str) -> str:
    for selector in ["h1", "meta[property='og:title']", "title"]:
        node = soup.select_one(selector)
        if node is None:
            continue

        text = node.get("content") if node.name == "meta" else node.get_text(" ")
        text = clean_text(text or "")
        if text and not re.fullmatch(r"https?://\S+", text.lower()):
            return text

    return urlparse(normalize_url(url)).netloc.replace("www.", "")


def remove_boilerplate_elements(soup: BeautifulSoup) -> None:
    selectors = [
        "aside",
        "button",
        "footer",
        "form",
        "header",
        "iframe",
        "nav",
        "noscript",
        "script",
        "style",
        "svg",
        "[aria-label*=breadcrumb i]",
        "[aria-label*=share i]",
        "[class*=advert i]",
        "[class*=breadcrumb i]",
        "[class*=cookie i]",
        "[class*=modal i]",
        "[class*=newsletter i]",
        "[class*=promo i]",
        "[class*=share i]",
        "[class*=social i]",
        "[id*=advert i]",
        "[id*=cookie i]",
        "[id*=newsletter i]",
        "[id*=share i]",
        "[role=banner]",
        "[role=complementary]",
        "[role=contentinfo]",
        "[role=navigation]",
    ]

    for selector in selectors:
        for element in soup.select(selector):
            element.decompose()


def parse_web_page(url: str) -> list[dict[str, str]]:
    html = fetch(normalize_url(url), "html")
    soup = BeautifulSoup(html, "html.parser")

    remove_boilerplate_elements(soup)

    title = page_title(soup, url)
    article = soup.find("article") or soup.find("main") or soup.body
    if article is None:
        return []

    records = []
    current_heading = title
    current_parts = []

    for node in article.find_all(["h2", "h3", "h4", "h5", "h6", "p", "li"]):
        text = clean_text(node.get_text(" "))

        if node.name in HEADING_TAGS:
            normalized_heading = text.lower()
            if normalized_heading in STOP_SECTION_HEADINGS:
                break

            if normalized_heading in INLINE_LABEL_HEADINGS:
                continue

            if is_boilerplate_heading(text):
                continue
            if current_parts:
                records.append(make_article_record(url, title, current_heading, current_parts))
                current_parts = []
            current_heading = text
        else:
            if is_boilerplate_text(text):
                continue
            current_parts.append(text)

    if current_parts:
        records.append(make_article_record(url, title, current_heading, current_parts))

    return [record for record in records if should_keep_record(record)]


def make_article_record(url: str, title: str, heading: str, parts: list[str]) -> dict[str, str]:
    filtered_parts = dedupe_parts([part for part in parts if not is_boilerplate_text(part)])
    body = dedupe_sentences("\n".join(filtered_parts))
    body = re.sub(rf"^{re.escape(heading)}\s+", "", body).strip()
    text = f"{heading}\n\n{body}".strip()
    digest = hashlib.sha256(f"{url}:{heading}:{text[:100]}".encode("utf-8")).hexdigest()[:12]
    source_name = urlparse(normalize_url(url)).netloc.replace("www.", "")
    return {
        "id": f"web-{digest}",
        "source_type": "web_article_section",
        "source_name": source_name,
        "title": title,
        "section": heading,
        "url": normalize_url(url),
        "text": text,
    }


def should_keep_record(record: dict[str, str]) -> bool:
    if record["source_name"] == "irs.gov" and record["section"] == record["title"]:
        return False

    if is_boilerplate_text(record["text"]):
        return False

    return True


def retrieve_documents(urls: list[str]) -> list[dict[str, Any]]:
    documents = []

    for url in urls:
        documents.extend(parse_web_page(url))

    return [doc for doc in documents if len(doc.get("text", "")) >= MIN_TEXT_LENGTH]


def split_text_units(text: str) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if len(paragraphs) > 1:
        return paragraphs

    sentences = re.split(r"(?<=[.!?])\s+", clean_text(text))
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def trailing_overlap(text: str, overlap_chars: int = CHUNK_OVERLAP_CHARS) -> str:
    if overlap_chars <= 0:
        return ""

    if len(text) <= overlap_chars:
        return text

    overlap = text[-overlap_chars:]
    sentence_boundary = max(overlap.rfind(". "), overlap.rfind("? "), overlap.rfind("! "))
    if sentence_boundary > 0:
        return overlap[sentence_boundary + 2 :].strip()

    return overlap.strip()


def split_oversized_unit(unit: str, chunk_size: int = CHUNK_SIZE_CHARS) -> list[str]:
    pieces = []
    remaining = clean_text(unit)

    while len(remaining) > chunk_size:
        split_at = remaining.rfind(" ", 0, chunk_size)
        if split_at < chunk_size // 2:
            split_at = chunk_size
        pieces.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()

    if remaining:
        pieces.append(remaining)

    return pieces


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE_CHARS,
    overlap_chars: int = CHUNK_OVERLAP_CHARS,
) -> list[str]:
    text = clean_text(text)
    if len(text) <= chunk_size:
        return [text]

    units = split_text_units(text)
    chunks = []
    current_parts = []
    current_length = 0

    for unit in units:
        unit_pieces = split_oversized_unit(unit, chunk_size)

        for piece in unit_pieces:
            separator_length = 2 if current_parts else 0
            would_be_length = current_length + separator_length + len(piece)

            if current_parts and would_be_length > chunk_size:
                chunk = "\n\n".join(current_parts).strip()
                chunks.append(chunk)
                overlap = trailing_overlap(chunk, overlap_chars)
                max_overlap = max(0, chunk_size - len(piece) - 2)
                if len(overlap) > max_overlap:
                    overlap = trailing_overlap(overlap, max_overlap)
                current_parts = [overlap] if overlap else []
                current_length = len(overlap)

            current_parts.append(piece)
            current_length += (2 if current_length else 0) + len(piece)

    if current_parts:
        chunks.append("\n\n".join(current_parts).strip())

    return [chunk for chunk in chunks if len(chunk) >= MIN_TEXT_LENGTH]


def chunk_documents(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chunks = []

    for document in documents:
        document_chunks = chunk_text(document["text"])

        for index, chunk in enumerate(document_chunks, start=1):
            chunk_id = f"{document['id']}-chunk-{index}"
            chunks.append(
                {
                    "id": chunk_id,
                    "document_id": document["id"],
                    "chunk_index": index,
                    "chunk_count": len(document_chunks),
                    "source_type": document["source_type"],
                    "source_name": document["source_name"],
                    "title": document["title"],
                    "section": document["section"],
                    "url": document["url"],
                    "text": chunk,
                }
            )

    return chunks


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def print_sample_document(records: list[dict[str, Any]]) -> None:
    if not records:
        print("No documents were retrieved.")
        return

    sample = max(records, key=lambda record: len(record.get("text", "")))
    print("\n--- Sample cleaned document ---")
    print(f"Source: {sample.get('source_name')}")
    print(f"Title: {sample.get('title')}")
    print(f"Section: {sample.get('section')}")
    print(f"URL: {sample.get('url')}")
    print()
    print(sample.get("text", "")[:2000])
    print("--- End sample ---\n")


def print_sample_chunk(records: list[dict[str, Any]]) -> None:
    if not records:
        print("No chunks were created.")
        return

    sample = max(records, key=lambda record: len(record.get("text", "")))
    print("\n--- Sample chunk ---")
    print(f"Source: {sample.get('source_name')}")
    print(f"Title: {sample.get('title')}")
    print(f"Section: {sample.get('section')}")
    print(f"Chunk: {sample.get('chunk_index')} of {sample.get('chunk_count')}")
    print(f"Characters: {len(sample.get('text', ''))}")
    print(f"URL: {sample.get('url')}")
    print()
    print(sample.get("text", "")[:2000])
    print("--- End sample chunk ---\n")


def main() -> None:
    try:
        documents = retrieve_documents(SOURCE_URLS)
    except RuntimeError as error:
        raise SystemExit(f"Data retrieval failed: {error}") from None

    chunks = chunk_documents(documents)
    write_jsonl(OUTPUT_PATH, documents)
    write_jsonl(CHUNKS_OUTPUT_PATH, chunks)
    print(f"Wrote {len(documents)} documents to {OUTPUT_PATH}")
    print(f"Wrote {len(chunks)} chunks to {CHUNKS_OUTPUT_PATH}")
    print_sample_document(documents)
    print_sample_chunk(chunks)


if __name__ == "__main__":
    main()
