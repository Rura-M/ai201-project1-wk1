# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

This domain is a beginner’s guide to Health Savings Accounts (HSAs) that explains how to save, spend, and grow your money tax-free. This information is hard to find because official documents are usually full of confusing legal jargon that doesn't answer basic, real-world questions. By using sources like Reddit and personal blogs, this guide provides the simple, "human" explanations and reassurance that official bank websites often ignore.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Reddit| This informs the user of what HSA accounts are | https://www.reddit.com/r/personalfinance/comments/1tn70nh/hsa_explained_for_dummies/ |
| 2 | Investopedia| This describes HSA terms and gives a basic introduction|  https://www.investopedia.com/terms/h/hsa.asp |
| 3 | Reddit | This further gives more details on how HSA  works | http://reddit.com/r/explainlikeimfive/comments/1opcu1s/eli5how_do_hsas_work_they_seem_too_good_to_be_true/|
| 4 | Reddit| This explains how HSA works | https://www.reddit.com/r/FinancialPlanning/comments/17mv9nz/how_do_hsa_and_fsa_work/|
| 5 | Reddit| This exaplains how to use funds in the HSA account| https://www.reddit.com/r/personalfinance/comments/1t6q205/should_you_use_your_hsa_money/|
| 6 | Reddit| This exaplains whether the user can spend HSA funds on non-medial issues| https://www.reddit.com/r/fidelityinvestments/comments/1myepym/should_i_actually_be_using_hsa_for_health/|
| 7 | Reddit | Exaplains what happens to your HDHP when you no longer need it | https://www.reddit.com/r/personalfinance/comments/1nq9h30/what_happens_with_your_invested_hsa_funds_when/ |
| 8 | Reddit| Discusses what happens when you ises HSA for non-medical issues | https://www.reddit.com/r/personalfinance/comments/1mk0z2l/accidentally_used_hsa_on_non_medical_items/|
| 9 | Reddit | Exaplains what happens when users exceed their contributions to the HSA aaccounts | https://www.reddit.com/r/tax/comments/1q1mh67/hsa_excess_contribution_what_do/|
| 10 | Reddit| Discuss HSA investment strategy | https://www.reddit.com/r/personalfinance/comments/1q7vs35/hsa_investment_strategy/| 

---
## Chunking Strategy

Use a hybrid chunking strategy. Keep short Reddit posts/comments as individual chunks, and split longer Reddit posts or web page sections into smaller chunks based on paragraphs or headings.

**Chunk size:**

Reddit: 300–500 tokens
Web page: 500–800 tokens

**Overlap:**

Reddit: 50 tokens
Web page: 100 tokens

**Reasoning:**
Reddit content is usually short and opinion-based, so keeping posts/comments together preserves the full user experience. The web page is more structured and likely contains longer explanations, so larger chunks help keep related information together. The overlap helps prevent important details from being lost when information spans two adjacent chunks.
---

## Retrieval Approach

**Embedding model:**
I will use all-MiniLM-L6-v2 through the sentence-transformers library. This model is lightweight, fast, and commonly used for simple RAG systems. It is a good fit for this project because the corpus is small and mostly made up of Reddit comments and one web page.

**Top-k:**
I will retrieve the top 3 chunks for each query. This gives the system enough context to answer the question while reducing the chance of including unrelated or noisy chunks
**Production tradeoff reflection:**
If this system were being deployed for real users and cost was not a constraint, I would consider using a more accurate embedding model with stronger semantic understanding and a larger context length. I would weigh tradeoffs such as retrieval accuracy, latency, multilingual support, and how well the model understands HSA-related terminology. A larger or more domain-specific model may improve answer quality, but it could also increase cost and slow down retrieval.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What is an HSA? | An HSA is mainly used to save money for qualified medical expenses, usually alongside a high-deductible health plan.|
| 2 | What are the benefits of an HSA account| | They can act as both a medical savings account and a long-term investment tool.
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

1. Noisy or inconsistent Reddit data:
Reddit posts and comments may include personal opinions, incomplete explanations, slang, or conflicting advice. This could make it harder for the system to separate accurate HSA information from individual experiences.

2. Off-topic or weak retrieval:
Because the corpus includes informal Reddit content, some retrieved chunks may only loosely match the user’s question. For example, a query about HSA tax benefits could retrieve a personal finance opinion instead of a clear explanation of tax rules.

3. Chunk boundary issues:
Important information may be split across two chunks, especially in the longer web page. The overlap helps reduce this risk, but poor chunking could still cause the system to miss context needed for a complete answer.

---

## Architecture

A[Document Ingestion<br>Reddit posts/comments + web page] --> B[Chunking<br>Hybrid strategy: Reddit comments kept together, web page split by headings/paragraphs]
    B --> C[Embedding + Vector Store<br>sentence-transformers all-MiniLM-L6-v2 + FAISS/Chroma]
    C --> D[Retrieval<br>Top-k = 3 most relevant chunks]
    D --> E[Generation<br>LLM answers using retrieved context]
---

## AI Tool Plan

## AI Tool Plan

For **document ingestion**, I will use ChatGPT to help design the loading process for my Reddit data and web page source. I will give it my project requirements, source types, and Architecture section. I expect it to produce Python code that loads Reddit posts/comments and extracts readable text from the web page. I will verify the output by checking that the documents are loaded correctly, that the text is not empty, and that each document keeps useful metadata such as source type, title, and URL.

For **chunking**, I will use ChatGPT or GitHub Copilot to implement the `chunk_text()` function. I will give it my Chunking Strategy section, including my chunk sizes of 300–500 tokens for Reddit, 500–800 tokens for the web page, and overlaps of 50 and 100 tokens. I expect it to produce code that keeps short Reddit comments intact while splitting longer text with overlap. I will verify this by printing sample chunks, checking their approximate token lengths, and making sure key information is not cut off awkwardly.

For **embedding and vector storage**, I will use ChatGPT to help set up `sentence-transformers` with the `all-MiniLM-L6-v2` embedding model and connect it to a vector store such as FAISS or Chroma. I will give it my Retrieval Approach section and Architecture diagram. I expect it to produce code that embeds each chunk, stores the embeddings, and saves metadata with each chunk. I will verify this by checking that the number of embeddings matches the number of chunks and that similarity search returns relevant results.

For **retrieval**, I will use ChatGPT or Copilot to implement the retrieval function using top-k = 3. I will give it my Retrieval Approach section and Evaluation Plan. I expect it to produce a function that takes a user question, embeds it, retrieves the top 3 most relevant chunks, and returns those chunks with source information. I will verify this by running my five test questions and checking whether the retrieved chunks contain the expected answer.

For **generation and evaluation**, I will use ChatGPT to help write the prompt that instructs the language model to answer only using retrieved context. I will give it my Evaluation Plan and Anticipated Challenges section. I expect it to produce a prompt template that encourages accurate, grounded answers and source attribution. I will verify the output by comparing the generated answers to my expected answers and checking that the model does not invent information when the retrieved chunks are incomplete.


**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
