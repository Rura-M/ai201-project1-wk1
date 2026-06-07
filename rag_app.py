import argparse
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from retrieval import DEFAULT_TOP_K, retrieve


DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an HSA assistant for a retrieval-augmented generation system.

Grounding rules:
- Answer only using the retrieved context provided by the system.
- Do not use outside knowledge, even if you think you know the answer.
- If the context does not contain enough information to answer, say exactly: "I don't have enough information on that."
- Do not invent facts, contribution limits, penalties, dates, or eligibility rules.
- Keep the answer concise and beginner-friendly.
- You may refer to sources by their source labels like [S1] or [S2] when useful.
"""


def groq_client() -> Groq:
    load_dotenv(dotenv_path=".env")
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("Missing GROQ_API_KEY. Add it to your .env file before running generation.")
    return Groq()


def format_context(results: list[dict[str, Any]]) -> str:
    context_blocks = []

    for index, result in enumerate(results, start=1):
        metadata = result["metadata"]
        context_blocks.append(
            "\n".join(
                [
                    f"[S{index}]",
                    f"Source: {metadata['source_name']}",
                    f"Title: {metadata['title']}",
                    f"Section: {metadata['section']}",
                    f"URL: {metadata['url']}",
                    "Text:",
                    result["text"],
                ]
            )
        )

    return "\n\n---\n\n".join(context_blocks)


def source_key(result: dict[str, Any]) -> tuple[str, str, str]:
    metadata = result["metadata"]
    return (metadata["source_name"], metadata["title"], metadata["url"])


def format_source_list(results: list[dict[str, Any]]) -> str:
    seen = set()
    lines = []

    for result in results:
        metadata = result["metadata"]
        key = source_key(result)
        if key in seen:
            continue

        seen.add(key)
        lines.append(
            f"- {metadata['source_name']} - {metadata['title']} ({metadata['section']}): {metadata['url']}"
        )

    return "\n".join(lines)


def generate_answer(question: str, retrieved_chunks: list[dict[str, Any]]) -> str:
    model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
    context = format_context(retrieved_chunks)
    user_prompt = f"""Question:
{question}

Retrieved context:
{context}

Answer the question using only the retrieved context."""

    response = groq_client().chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=600,
    )

    return response.choices[0].message.content.strip()


def answer_question(question: str, top_k: int = DEFAULT_TOP_K) -> str:
    result = ask(question, top_k=top_k)
    return f"{result['answer']}\n\n## Sources\n{result['sources']}"


def ask(question: str, top_k: int = DEFAULT_TOP_K) -> dict[str, str]:
    question = question.strip()
    if not question:
        return {"answer": "Please enter a question.", "sources": ""}

    retrieved_chunks = retrieve(question, top_k=top_k)
    answer = generate_answer(question, retrieved_chunks)
    if answer.strip() == "I don't have enough information on that.":
        sources = "No retrieved source contained enough information to answer this question."
    else:
        sources = format_source_list(retrieved_chunks)

    return {"answer": answer, "sources": sources}


def handle_query(question: str, top_k: int = DEFAULT_TOP_K) -> tuple[str, str, str]:
    result = ask(question, top_k=top_k)
    retrieved = retrieved_context_preview(question, top_k=top_k) if question.strip() else ""
    return result["answer"], result["sources"], retrieved


def retrieved_context_preview(question: str, top_k: int = DEFAULT_TOP_K) -> str:
    retrieved_chunks = retrieve(question, top_k=top_k)
    previews = []

    for index, result in enumerate(retrieved_chunks, start=1):
        metadata = result["metadata"]
        previews.append(
            "\n".join(
                [
                    f"### Retrieved Chunk {index}",
                    f"Distance: {result['distance']:.4f}",
                    f"Source: {metadata['source_name']}",
                    f"Title: {metadata['title']}",
                    f"Section: {metadata['section']}",
                    f"URL: {metadata['url']}",
                    "",
                    result["text"][:1200],
                ]
            )
        )

    return "\n\n".join(previews)


def build_gradio_app():
    try:
        import gradio as gr
    except ImportError as error:
        raise RuntimeError("Gradio is not installed. Run: python3 -m pip install -r requirements.txt") from error

    def answer_and_sources(question: str) -> tuple[str, str]:
        ans, srcs, _ = handle_query(question, top_k=DEFAULT_TOP_K)
        return ans, srcs

    with gr.Blocks(title="HSA RAG Assistant") as demo:
        gr.Markdown("# HSA RAG Assistant")
        question = gr.Textbox(label="Question", placeholder="Ask about HSAs, eligibility, tax benefits, or qualified expenses.")
        submit = gr.Button("Answer", variant="primary")
        answer = gr.Textbox(label="Answer", lines=8)
        sources = gr.Textbox(label="Retrieved from", lines=5)

        submit.click(answer_and_sources, inputs=[question], outputs=[answer, sources])
        question.submit(answer_and_sources, inputs=[question], outputs=[answer, sources])

    return demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the HSA Groq RAG assistant.")
    parser.add_argument("--question", help="Ask a single question from the command line.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="Number of chunks to retrieve.")
    parser.add_argument("--share", action="store_true", help="Create a public Gradio share link.")
    parser.add_argument("--server-port", type=int, default=8060, help="Local port for the Gradio app.")
    args = parser.parse_args()

    if args.question:
        print(answer_question(args.question, top_k=args.top_k))
        return

    demo = build_gradio_app()
    demo.launch(share=args.share, server_port=args.server_port)


if __name__ == "__main__":
    main()
