# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

This domain is a beginner’s guide to Health Savings Accounts (HSAs) that explains how to save, spend, and grow money tax-free for qualified medical expenses. This information is hard to understand because official documents can be full of legal and tax language, while provider pages often focus on their own products. By using official government sources and educational finance websites, this guide provides clearer explanations of HSA rules, benefits, spending, eligibility, and account management.

---

## Documents

<!-- List your specific sources: URLs, website names, article titles, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Investopedia| This describes HSA terms and gives a basic introduction| https://www.investopedia.com/terms/h/hsa.asp |
| 2 | IRS| This explains official HSA rules, eligibility, contribution limits, and tax treatment | https://www.irs.gov/publications/p969 |
| 3 | HealthCare.gov | This explains HSA-eligible health plans and how HSAs work with HDHP coverage | https://www.healthcare.gov/high-deductible-health-plan/hdhp-hsa-information/|
| 4 | Fidelity| This explains how to spend money from an HSA on qualified medical expenses | https://www.fidelity.com/learning-center/personal-finance/spending-from-hsa|
| 5 | Fidelity| This explains what to look for when choosing an HSA account provider| https://www.fidelity.com/learning-center/personal-finance/hsa-what-to-look-for|
| 6 | Fidelity| This explains how to open an HSA and who may be eligible| https://www.fidelity.com/learning-center/personal-finance/how-to-open-an-HSA|
| 7 | Optum Bank | This gives a beginner-friendly overview of HSA benefits, contributions, and tax savings | https://www.optumbank.com/resources/library/money-management-hsa.html |
| 8 | Optum Bank| This explains how to manage an HSA, make deposits, use funds, and handle transfers | https://www.optumbank.com/health-savings-accounts/resources/managing-hsa.html|
| 9 | HSA Bank | This lists common IRS-qualified medical expenses for HSAs, FSAs, and HRAs | https://www.hsabank.com/HSABank/Learning-Center/IRS-qualified-medical-expenses|
| 10 | HSA Bank| This answers common member questions about HSAs, FSAs, HRAs, reimbursements, and rollovers | https://www.hsabank.com/Members/Members-FAQs.html| 

---
## Chunking Strategy

Use a section-based chunking strategy. Each web page will be split by headings first, then by paragraphs if a section is too long. If the cleaned text no longer has clear paragraph breaks, the long section will be split by sentence boundaries instead. This keeps related information together while preventing very long article sections from becoming hard to retrieve accurately.

**Chunk size:**

Chunks will usually contain one article section or a small group of closely related paragraphs. If a cleaned section is longer than 2,000 characters, it will be split into smaller chunks of about 2,000 characters.

**Overlap:**

I will use about 300 characters of overlap when splitting long sections so important context is not lost between adjacent chunks.

**Reasoning:**
The sources are mostly structured web pages with headings, FAQs, and article sections. Splitting by headings, paragraphs, and sentence boundaries preserves the meaning of each section and makes it easier for retrieval to find focused explanations about eligibility, tax benefits, qualified expenses, and non-qualified withdrawals. The 2,000-character size is large enough to keep a full explanation together, while the 300-character overlap helps preserve context when a long section has to be split.
---

## Retrieval Approach

**Embedding model:**
I will use all-MiniLM-L6-v2 through the sentence-transformers library. This model is lightweight, fast, and commonly used for simple RAG systems. It is a good fit for this project because the corpus is small and made up of structured web pages about one focused topic.

**Top-k:**
I will retrieve the top 4 chunks for each query. This gives the system enough context to answer the question while reducing the chance of including unrelated or noisy chunks. I chose 4 instead of 3 after adding ChromaDB retrieval because the HSA sources often split related details across nearby sections, and 4 chunks gives slightly better coverage without adding too much off-topic context.
**Production tradeoff reflection:**
If this system were being deployed for real users and cost was not a constraint, I would consider using a more accurate embedding model with stronger semantic understanding and a larger context length. I would weigh tradeoffs such as retrieval accuracy, latency, multilingual support, and how well the model understands HSA-related terminology. A larger or more domain-specific model may improve answer quality, but it could also increase cost and slow down retrieval. 

---

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What is an HSA, and who is allowed to contribute to one? | An HSA is a tax-advantaged savings account used to pay or reimburse qualified medical expenses. To contribute, a person generally must be covered by an HSA-eligible high-deductible health plan, not be enrolled in Medicare, not be claimed as someone else's dependent, and not have disqualifying other health coverage. |
| 2 | What are the main tax benefits of an HSA? | HSAs have three major tax advantages: contributions can reduce taxable income, earnings can grow tax-free, and withdrawals are tax-free when used for qualified medical expenses. |
| 3 | Can HSA money roll over from year to year? | Yes. HSA funds roll over from year to year and stay with the account owner. The money is not lost at the end of the year like some FSA funds can be. |
| 4 | What qualified medical expenses can HSA funds be used for tax-free? | HSA funds can be used tax-free for qualified medical expenses, such as deductibles, copayments, coinsurance, prescriptions, dental care, vision care, and many other IRS-qualified health expenses. They generally cannot be used tax-free for regular health insurance premiums. |
| 5 | Are HSA withdrawals for non-qualified medical expenses taxable or penalized? | Non-qualified HSA withdrawals are generally taxable. If the person is under age 65, they may also owe an additional 20% penalty. After age 65, non-qualified withdrawals are generally taxed as income but are not subject to the 20% penalty. |

---

## Anticipated Challenges

1. Dense official language:
Some government sources may use legal or tax language that is difficult for beginners to understand. This could make it harder for the system to retrieve short, plain-language explanations unless the chunks preserve enough surrounding context.

2. Similar topics across sources:
Many sources explain overlapping ideas such as eligibility, tax savings, and qualified expenses. This could make retrieval return several similar chunks instead of the single most useful section for a specific question.

3. Chunk boundary issues:
Important information may be split across two chunks, especially in the longer web page. The overlap helps reduce this risk, but poor chunking could still cause the system to miss context needed for a complete answer.

---

## Architecture

A[Document Ingestion<br>HSA web pages] --> B[Chunking<br>documents/hsa_chunks.jsonl section-based chunks]
    B --> C[Embedding + Vector Store<br>sentence-transformers all-MiniLM-L6-v2 + ChromaDB]
    C --> D[Retrieval<br>Top-k = 3 most relevant chunks]
    D --> E[Generation<br>LLM answers using retrieved context]
---

## AI Tool Plan

## AI Tool Plan

For **document ingestion**, I will use ChatGPT to help design the loading process for my web page sources. I will give it my project requirements, source URLs, and Architecture section. I expect it to produce Python code that extracts readable article text from each web page. I will verify the output by checking that the documents are loaded correctly, that the text is not empty, and that each document keeps useful metadata such as source type, title, section, and URL.

For **chunking**, I will use ChatGPT or GitHub Copilot to implement the `chunk_text()` function. I will give it my Chunking Strategy section, including the plan to split web pages by headings and paragraphs with light overlap for long sections. I expect it to produce code that keeps related article paragraphs together while splitting long sections cleanly. I will verify this by printing sample chunks and making sure key information is not cut off awkwardly.

For **embedding and vector storage**, I will use Codex to help set up `sentence-transformers` with the `all-MiniLM-L6-v2` embedding model and connect it to a vector store such as FAISS or Chroma. I will give it my Retrieval Approach section and Architecture diagram. I expect it to produce code that embeds each chunk, stores the embeddings, and saves metadata with each chunk. I will verify this by checking that the number of embeddings matches the number of chunks and that similarity search returns relevant results.

For **retrieval**, I will use Codex or Copilot to implement the retrieval function using top-k = 3. I will give it my Retrieval Approach section and Evaluation Plan. I expect it to produce a function that takes a user question, embeds it, retrieves the top 3 most relevant chunks, and returns those chunks with source information. I will verify this by running my five test questions and checking whether the retrieved chunks contain the expected answer.

For **generation and evaluation**, I will use Codex to help write the prompt that instructs the language model to answer only using retrieved context. I will give it my Evaluation Plan and Anticipated Challenges section. I expect it to produce a prompt template that encourages accurate, grounded answers and source attribution. I will verify the output by comparing the generated answers to my expected answers and checking that the model does not invent information when the retrieved chunks are incomplete.


**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
