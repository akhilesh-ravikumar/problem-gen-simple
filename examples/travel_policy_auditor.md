# Travel Policy Auditor

## Description

Build a custom, rule-based evaluation harness - fully offline, no LLM judge, no API calls - that scores groundedness, hallucination, and citation accuracy for a travel-support assistant's answers.

## 📋 Instructions

Use the provided template code as the starting point. Implement your solution only within the TODO blocks in eval_harness.py, and do not modify the project structure, file names, function signatures, source_documents.json, or anything above the "DO NOT MODIFY ABOVE THIS LINE" marker in eval_harness.py (the similarity function and the 6 shipped cases). The automated evaluation uses this template to assess your code, so any structural changes may cause your submission to fail evaluation.

## 🎯 Objective

SkyLine Airlines' travel-support assistant answers customer questions - baggage allowances, refunds, flight changes, elite-tier perks, pet policy - by retrieving policy chunks from a small knowledge base and generating an answer from them. Before trusting a batch of its answers, you need a deterministic audit: is each answer actually supported by what was retrieved, does it fabricate or contradict a fact, and does it cite the right source document? Build a custom, rule-based evaluation harness - no LLM judge involved, every check is logic you write yourself - that scores all three and reaches a pass/fail verdict on 6 cases, several of which have a planted defect for your harness to catch.

## 📚 Custom Rule-Based Evaluation Concepts You'll Practice

- Deterministic similarity scoring — embed() / cosine_similarity(): a hand-rolled, hashed bag-of-words function - not a trained model, no API calls - that gives you a repeatable similarity number to build rules on top of, in place of an LLM judge.

- Groundedness — does the answer's meaning actually match what was retrieved?

- Hallucination detection — does the answer state a number that never appears anywhere in the retrieved text?

- Citation checking — verifying a cited source is among the retrieved chunks, or otherwise is the document that best supports the answer.

- Schema-driven, not case-ID-driven — your harness must work from the data shape (questions/answers/retrieved_chunks/cited_source), so it works for any case with this shape.

## Your Task

Implement four functions in eval_harness.py:

- score_groundedness(case, docs) — semantic similarity to the retrieved text; "pass" requires a score of at least 0.3.

- score_hallucination(case, docs) — "fail" if the answer states a number absent from the retrieved text entirely.

- score_citation(case, docs) — "pass" if cited_source is retrieved, or is the best-supporting doc; refusals need no citation.

- run_evaluation() — call all three for every case in CASES, combine into an overall verdict, print a summary table, and write eval_results.json.

Each scoring function returns a dict whose "verdict" is "pass" or "fail" (lowercase). score_groundedness's dict also has "score", the similarity as a float; with no retrieved text the verdict is "fail" and the score is 0.0.

eval_results.json is a list with one dict per case in CASES, with keys case_id, question, groundedness, hallucination, citation and overall_verdict ("pass" only when all three verdicts are "pass").

Your functions must work for any case with this shape, not only the 6 shipped cases.

## Environment Setup

File Structure:

travel_policy_auditor/

├── eval_harness.py \# embed()/cosine_similarity() + the 6 shipped cases (fixed, do not modify)

│ \# score_groundedness(), score_hallucination(), score_citation(), run_evaluation() (TODO)

└── source_documents.json \# the 5-document policy knowledge base (fixed, do not modify)

Open VS Code: Open the project folder in VS Code and launch the integrated terminal (Terminal → New Terminal).

No API keys needed: this exercise is fully offline - the embedding utility is a deterministic hashed bag-of-words vectorizer, not a hosted model. No OPENAI_API_KEY or proxy gateway is required.

## How to Run

python eval_harness.py

This scores all 6 shipped cases, prints a per-case summary table (groundedness / hallucination / citation / overall), and writes eval_results.json next to eval_harness.py.

Sample

For shipped case C1:

score_groundedness(C1, docs) -\> {"verdict": "pass", "score": 0.6882, ...}

score_hallucination(C1, docs) -\> {"verdict": "pass", ...}

score_citation(C1, docs) -\> {"verdict": "pass", ...}

eval_results.json entry:

{"case_id": "C1", "question": "...", "groundedness": {...},

"hallucination": {...}, "citation": {...}, "overall_verdict": "pass"}

## How to Evaluate

To evaluate your solution and view the results:

Click the "t" icon on the left side of the VS Code editor, select Evaluate to run the automated evaluation, and view the results once the evaluation is complete.
