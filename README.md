# The Unofficial Guide — Project 1: HSA RAG SYSTEM

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

This domain is a beginner’s guide to using Health Savings Accounts (HSAs) that explains how to save, spend, and grow money tax-free for qualified medical expenses. This information is hard to understand because official documents can be full of legal and tax language, while provider pages often focus on their own products. By using official government sources and educational finance websites, this guide provides clearer explanations of HSA rules, benefits, spending, eligibility, and account management.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->


| # | Source | Type | URL or location |
|---|--------|------|-----------------|
| 1 | Investopedia| Webpage | https://www.investopedia.com/terms/h/hsa.asp |
| 2 | IRS| Webpage | https://www.irs.gov/publications/p969 |
| 3 | HealthCare.gov | Webpage | https://www.healthcare.gov/high-deductible-health-plan/hdhp-hsa-information/|
| 4 | Fidelity| Webpage | https://www.fidelity.com/learning-center/personal-finance/spending-from-hsa|
| 5 | Fidelity| Webpage | https://www.fidelity.com/learning-center/personal-finance/hsa-what-to-look-for|
| 6 | Fidelity| Webpage | https://www.fidelity.com/learning-center/personal-finance/how-to-open-an-HSA|
| 7 | Optum Bank | Webpage | https://www.optumbank.com/resources/library/money-management-hsa.html |
| 8 | Optum Bank| Webpage | https://www.optumbank.com/health-savings-accounts/resources/managing-hsa.html|
| 9 | HSA Bank | Webpage | https://www.hsabank.com/HSABank/Learning-Center/IRS-qualified-medical-expenses|
| 10 | HSA Bank| Webpage | https://www.hsabank.com/Members/Members-FAQs.html| 

---

## Chunking Strategy

**Chunk size:**

Chunks will usually contain one article section or a small group of closely related paragraphs. If a cleaned section is longer than 2,000 characters, it will be split into smaller chunks of about 2,000 characters.

**Overlap:**
I will use about 300 characters of overlap when splitting long sections so important context is not lost between adjacent chunks.

**Why these choices fit your documents:**
The sources are mostly structured web pages with headings, FAQs, and article sections. Splitting by headings, paragraphs, and sentence boundaries preserves the meaning of each section and makes it easier for retrieval to find focused explanations about eligibility, tax benefits, qualified expenses, and non-qualified withdrawals. The 2,000-character size is large enough to keep a full explanation together, while the 300-character overlap helps preserve context when a long section has to be split.
**Final chunk count:**
142 chunks were created
---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**
I will use all-MiniLM-L6-v2 through the sentence-transformers library. This model is lightweight, fast, and commonly used for simple RAG systems and works because the corpus is small and made up of structured web pages about one focused topic.

**Production tradeoff reflection:**
If this system were being deployed for real users and cost was not a constraint, I would consider using a more accurate embedding model with stronger semantic understanding and a larger context length. I would weigh tradeoffs such as retrieval accuracy, latency, multilingual support, and how well the model understands HSA-related terminology. A larger or more domain-specific model may improve answer quality, but it could also increase cost and slow down retrieval. 
---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

The system prompt explicitly instructs the model:
- Answer only using the retrieved context provided by the system.
- Do not use outside knowledge, even if you think you know the answer.
- If the context does not contain enough information to answer, say exactly: "I don't have enough information on that."
- Do not invent facts, contribution limits, penalties, dates, or eligibility rules.


**Structural mechanisms:**
- Retrieved chunks are formatted with explicit source labels ([S1], [S2], etc.), metadata (source name, title, section, URL), and text boundaries
- Temperature is set to 0.1 for conservative outputs
- Max tokens limited to 600 to prevent rambling
- Response checks for "I don't have enough information" and handles it appropriately

**How source attribution is surfaced in the response:**

The data ources are displayed in a separate "Retrieved from" section listing each unique source with its title, section, and URL. The model can reference sources using [S1], [S2] notation within the answer.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What is an HSA, and who is allowed to contribute to one? | An HSA is a tax-advantaged savings account used to pay or reimburse qualified medical expenses. To contribute, a person generally must be covered by an HSA-eligible high-deductible health plan, not be enrolled in Medicare, not be claimed as someone else's dependent, and not have disqualifying other health coverage. | System correctly defines HSA as a tax-advantaged account for HDHP holders and mentions eligibility requirements including not being claimed as a dependent. However, it does not fully address Medicare enrollment or other disqualifying coverage restrictions. | Partially relevant | Partially accurate |
| 2 | What are the main tax benefits of an HSA? | HSAs have three major tax advantages: contributions can reduce taxable income, earnings can grow tax-free, and withdrawals are tax-free when used for qualified medical expenses. | System identifies all three tax benefits clearly: tax-free contributions, tax-free earnings, and tax-free distributions for qualified expenses. Explicitly refers to them as "triple tax advantage." | Relevant | Accurate |
| 3 | Can HSA money roll over from year to year? | Yes. HSA funds roll over from year to year and stay with the account owner. The money is not lost at the end of the year like some FSA funds can be. | System confirms money rolls over year to year with no use-it-or-lose-it rule and account remains indefinitely. | Relevant | Accurate |
| 4 | What qualified medical expenses can HSA funds be used for tax-free? | HSA funds can be used tax-free for qualified medical expenses, such as deductibles, copayments, coinsurance, prescriptions, dental care, vision care, and many other IRS-qualified health expenses. They generally cannot be used tax-free for regular health insurance premiums. | System lists many qualified expenses (deductibles, co-insurance, prescriptions, dental, vision, sunscreen, contacts) and references the IRS for complete list. However, it does not mention the important restriction that health insurance premiums cannot be paid tax-free. | Partially relevant | Partially accurate |
| 5 | Are HSA withdrawals for non-qualified medical expenses taxable or penalized? | Non-qualified HSA withdrawals are generally taxable. If the person is under age 65, they may also owe an additional 20% penalty. After age 65, non-qualified withdrawals are generally taxed as income but are not subject to the 20% penalty. | System correctly states non-qualified withdrawals are taxed as income with a 20% penalty, and correctly notes that after age 65 only income tax applies without the additional 20% penalty. | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** If I have both an FSA and HSA, how do the rules interact?

**What the system returned:** I don't have enough information on that.

**Root cause (tied to a specific pipeline stage):** Answering this question requires multi-chunk synthesis which I did not include in my pipeline. Additionally, I also removed FSA to keep the system focused on HSA accounts.

**What you would change to fix it:** Include information related to FSA. I would implement multi-chunk synthesis to allow the system to answer questions about health-related accounts.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** It simplifies my implementation. It also served as a reference for some of the choices I made e.g which top k to use. Finally, it helped me remain on a focused goal of ensuring that my RAG is focused on HSA systems.

**One way your implementation diverged from the spec, and why:** I had to change the Top K size to improve responses. Originally, I was using 2 and it gave partially correct response. Thus, increasing it to 4 gave more accurate responses.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* I asked Codex to implement data retrieval functions for scraping the source links.
- *What it produced:* It produced a functional file with basic retrieval data.
- *What I changed or overrode:* The file it provided did not clean the data. I prompted it to clean the data and remove html headings and encodings. I also prompted it to save the data in json file to avoid querying the internet everytime for the data from the source links.

**Instance 2**

- *What I gave the AI:* To make it easier for me to check what the chunks looked like, I asked Codex to create a functions for checking the created chunks for me
- *What it produced:* It created the file for me which met the request
- *What I changed or overrode:* Nothing, the implementation produced the desired results.

**Instance 3**

- *What I gave the AI:* I asked Copilot help me format and complete parts of the README using planning.md
- *What it produced:* It filled in all the sections
- *What I changed or overrode:* I had to tell it which sections needed to be completed. It had completed some of the sections with the wrong answers so I had to specify which sections to use and complete. It did complete the file correctly.