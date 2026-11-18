# Contract Clause Auditor

## Description

Use Ragas to score a legal-assistant chatbot's answer about a contract clause for faithfulness, relevancy and correctness — then turn those scores into a single Pass / Needs Review verdict.

## 📋 Instructions

Use the provided template code as the starting point. Implement your solution only within the TODO blocks and do not modify the project structure, file names, or function/class signatures. The automated evaluation uses this template to assess your code, so any structural changes may cause your submission to fail evaluation.

## 🎯 Objective

A legal-assistant chatbot answers questions about a contract's clauses (termination notice, liability caps, confidentiality terms, ...) using text retrieved from the contract itself. Before an answer is shown to a paralegal, you want an automated check: is it grounded in the retrieved clause text, does it actually answer the question asked, and does it match what a human reviewer would say? Build a function that runs all three checks with Ragas and returns one report.

## 📚 Ragas Concepts You'll Practice

- SingleTurnSample — the unit Ragas evaluates: one question, one answer, the retrieved context(s), and a reference (correct) answer, held in its user_input, response, retrieved_contexts and reference fields.

- EvaluationDataset — wraps one or more samples so evaluate() can score them.

- Faithfulness — does the answer stick to claims supported by the retrieved clause text (i.e. no invented terms)?

- Answer Relevancy — does the answer actually address the question that was asked?

- Answer Correctness — how closely does the answer match a known-correct reference answer (factual + semantic overlap)?

- Multi-metric aggregation — running several metrics through one evaluate() call and combining the results into a single verdict.

## Your Task

Implement three functions in main.py:

- \_verdict_from_scores(scores) — given a dict of metric label → score, return "Pass" if every score is ≥ PASS_THRESHOLD (0.7), otherwise "Needs Review".

- build_sample(question, answer, contexts, ground_truth) — build and return a SingleTurnSample from these four values.

- evaluate_contract_answer(question, answer, contexts, ground_truth) — score the answer with Faithfulness, AnswerRelevancy and AnswerCorrectness in a single evaluate() call, with evaluator_llm (and evaluator_embeddings where a metric needs embeddings) as the judge, and return the report described below.

Parameters (evaluate_contract_answer):

- question — the question asked about the contract.

- answer — the assistant's generated answer.

- contexts — a list of retrieved clause snippets the answer should be grounded in.

- ground_truth — the correct reference answer to compare against.

Returns: a dict with these keys:

- Faithfulness, Answer Relevancy, Answer Correctness — each a float rounded to 3 decimal places.

- Overall Verdict — "Pass" if all three scores are ≥ PASS_THRESHOLD (0.7), otherwise "Needs Review".

Sample: \_verdict_from_scores({"Faithfulness": 0.92, "Answer Relevancy": 0.81, "Answer Correctness": 0.75}) returns "Pass".

evaluate_contract_answer(...) returns {"Faithfulness": \<float, 3 dp\>, "Answer Relevancy": \<float, 3 dp\>, "Answer Correctness": \<float, 3 dp\>, "Overall Verdict": \<"Pass" \| "Needs Review"\>}. The scores come from the judge model and vary between runs.

## Environment Setup

File Structure:

contract_clause_auditor/

└── main.py \# \_verdict_from_scores(), build_sample(), evaluate_contract_answer()

Open VS Code: Open the project folder in VS Code and launch the integrated terminal (Terminal → New Terminal).

OpenAI Configuration: OpenAI is used as the LLM provider (as the Ragas judge model) and embedding provider, with the API key set in the OPENAI_API_KEY environment variable. Use the gpt-4o-mini chat model and the text-embedding-3-small embedding model. Route both through the proxy gateway below:

🔗 Proxy URL: https://llmgateway-lms.tekstac.com/v1

## How to Run

python main.py

This calls evaluate_contract_answer(...) on two sample answers - one faithful, one that invents a detail the retrieved clause doesn't support - and prints both returned reports (scores + Overall Verdict), so you see both a "Pass" and a "Needs Review" result.

## How to Evaluate

To evaluate your solution and view the score:

Click the "t" icon on the left side of the VS Code editor, select Evaluate to run the automated evaluation, and view the evaluation score and results once the evaluation is complete.
