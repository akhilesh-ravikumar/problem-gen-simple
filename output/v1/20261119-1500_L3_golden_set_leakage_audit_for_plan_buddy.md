```bash 
python generate.py --course "LLM Evaluation methods and frameworks" --topic "Golden Datasets" --level L3 --description "mobile network operator, plan buddy" --stack "python, openai"
```

# Golden Set Leakage Audit for Plan Buddy

## Description

Build a deterministic leakage auditor for a golden evaluation dataset. It parses the golden cases, produces a comparable form of each question, and reports which golden cases have leaked into a fine-tuning or prompt-example pool. No LLM calls are made.

## 📋 Instructions

Use the provided template code as the starting point. Implement your solution only within the TODO blocks in main.py, and do not modify the project structure, file names, or function signatures. The automated evaluation uses this template to assess your code, so any structural changes may cause your submission to fail evaluation.

## 🎯 Objective

Kestrel Mobile runs Plan Buddy, an assistant that recommends tariffs to customers during sign-up. The evaluation team keeps a golden dataset of customer questions with reference answers. Before each release, they must confirm that none of those golden questions has leaked into the fine-tuning or prompt-example pool. A leaked case inflates the reported accuracy, so the release gate passes a weaker Plan Buddy to customers. Leaked questions in the pool are not always exact copies of the golden text, so the audit has to recognise the same customer question when it is written slightly differently. Build the three functions below so the golden set is loaded cleanly and every leak is reported.

## 📚 Golden Dataset Concepts You'll Practice

- **Golden dataset integrity**: a golden set is only useful if it stays separate from anything the system was tuned on. This problem turns that rule into a check you can run before every release.
- **Data contamination and leakage detection**: finding evaluation items that also appear in training or example pools, including forms that differ from the original text.
- **Canonical text normalisation**: producing one comparable form of a piece of text, so that strings that mean the same thing compare equal.
- **Defensive record loading**: parsing JSON records, dropping malformed entries, and returning a stable, sorted order that downstream checks can rely on.
- **Set-style matching results**: returning each finding once, in a deterministic order that a release report can diff between runs.

## Your Task

Implement three functions in main.py:

- `load_golden_cases(raw_json: str) -> list[dict]`: parse a JSON array of golden cases. Each case should have the keys `'id'`, `'question'` and `'reference'`, all strings. Drop any entry that is not a JSON object, is missing any of these three keys, or has a non-string value for `'id'`, `'question'` or `'reference'`. Return the remaining entries sorted by `'id'` in ascending string order. Each returned dict keeps its original keys and values unchanged. Malformed entries are dropped silently, with no exception and no report.
- `normalise_question(text: str) -> str`: return a canonical form of a question, used for comparison. The rules are yours to derive from the shipped cases. The function must be deterministic and return a `str`.
- `find_leaked_ids(golden: list[dict], pool: list[str]) -> list[str]`: return the golden `'id'` values whose question also appears in `pool` after normalisation.

Parameters (`find_leaked_ids`):
- `golden`: a list of dicts as returned by `load_golden_cases`, each with `'id'`, `'question'` and `'reference'`.
- `pool`: a list of strings, each a question used in the fine-tuning or prompt-example pool.

Returns: a sorted list of `str` IDs in ascending order. Each ID appears at most once. Return `[]` when nothing leaks. Use the same normalisation for golden questions and pool entries.

Sample:

```python
raw = '[{"id": "G2", "question": "Is the 5G plan cheaper?", "reference": "Yes."},
        {"id": "G1", "question": "Do you cover roaming in Spain?", "reference": "Yes, with add-on."},
        {"id": "G3", "reference": "Missing question, dropped."}]'

golden = load_golden_cases(raw)
# -> [{"id": "G1", "question": "Do you cover roaming in Spain?", "reference": "Yes, with add-on."},
#     {"id": "G2", "question": "Is the 5G plan cheaper?", "reference": "Yes."}]

find_leaked_ids(golden, ["  is THE 5G plan cheaper ", "What is the data cap?"])
# -> ["G2"]

find_leaked_ids(golden, ["Something unrelated"])
# -> []
```

## Environment Setup

File Structure:

```
golden_leakage_audit/
└── main.py  # load_golden_cases(), normalise_question(), find_leaked_ids()
```

Open VS Code: Open the project folder in VS Code and launch the integrated terminal (Terminal → New Terminal).

No API keys needed: this exercise is fully offline. No OPENAI_API_KEY or proxy gateway is required.

## How to Run

```bash
python main.py
```

This loads a small built-in golden set and a pool of example questions, then prints the parsed golden cases and the IDs flagged as leaked from the pool.

## How to Evaluate

To evaluate your solution and view the score:

Click the "t" icon on the left side of the VS Code editor, select Evaluate to run the automated evaluation, and view the evaluation score and results once the evaluation is complete.
