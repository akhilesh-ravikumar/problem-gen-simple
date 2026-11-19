# Golden Case Matcher for Plan Buddy Regression Runs

## Description

Build two small matching functions that pair each new Plan Buddy run result with its golden test case by normalized question text. Matching must never use the case `id` field.

## 📋 Instructions

Use the provided template code as the starting point. Implement your solution only within the TODO blocks in main.py, and do not modify the project structure, file names, or function signatures. The automated evaluation uses this template to assess your code, so any structural changes may cause your submission to fail evaluation.

## 🎯 Objective

Brightwave Mobile is a mobile network operator whose Plan Buddy assistant recommends tariffs to customers. Every night, the evaluation team replays a golden dataset of 200 approved plan questions through Plan Buddy and compares each answer to the expected plan. Before a release, each new run result must be paired with its golden case so regressions can be counted. If the pairing is wrong, a regression can be hidden or a fixed answer can be marked as failing, and a customer could then be recommended the wrong tariff. The golden dataset is rebuilt from time to time and its IDs are renumbered, so pairing must rely on the question text. Build the normalization and matching logic that the nightly evaluator uses.

## 📚 Golden Dataset Concepts You'll Practice

- **Golden dataset** — a fixed, human-approved set of inputs with expected outputs that every regression run is compared against.
- **Text normalization** — making two strings comparable by applying the same deterministic cleanup (case, edge whitespace, internal whitespace) to both before comparing.
- **Key stability** — why an identifier that is reassigned on every dataset rebuild cannot be used as a join key, and why content should be used instead.
- **First-match semantics** — returning the first element in list order when several records match, so results are repeatable.
- **Preserving object identity** — returning the original record unchanged, so the evaluator can read its `expected_plan` field directly.

## Your Task

Implement two functions in main.py:

- `normalize_question(text: str) -> str` — lowercase the text, strip leading and trailing whitespace, and collapse every run of internal whitespace to one single space. Do not remove or change any punctuation.
- `match_case(run_question: str, golden_cases: list[dict]) -> dict | None` — compare `normalize_question(run_question)` with `normalize_question(case["question"])` for each case in list order. Return the first matching case dict, unchanged. Return `None` if nothing matches.

Parameters (`match_case`):
- `run_question` — the question text from a Plan Buddy run result.
- `golden_cases` — a list of dicts, each with `id`, `question` and `expected_plan` keys (all str).

Returns: the matching golden case dict itself (the same object, not a copy), or `None`.

**Trap: the `id` field.** A naive solution matches on `id`, which fails once the dataset is renumbered. In this exercise the `id` key is ignored entirely. Only the normalized `question` text decides a match, and your code must never read `case["id"]`.

Sample:
```python
normalize_question('  Cheapest  5G PLAN? ')
# returns 'cheapest 5g plan?'

cases = [{'id': 'G-17', 'question': 'Best plan for 2 lines?', 'expected_plan': 'Duo Unlimited'}]

match_case('best plan for 2 lines?', cases)
# returns cases[0]  (the same dict, found by text although the id is 'G-17')

match_case('Is there a roaming pass?', cases)
# returns None
```

## Environment Setup

File Structure:
```
golden_case_matcher/
├── golden.json  # 200 golden plan questions with id, question, expected_plan (fixed, do not modify)
└── main.py  # normalize_question(), match_case()
```

Open VS Code: Open the project folder in VS Code and launch the integrated terminal (Terminal → New Terminal).

No API keys needed: this exercise is fully offline. No OPENAI_API_KEY or proxy gateway is required.

## How to Run

```bash
python main.py
```

This loads golden.json, runs match_case on a few sample run questions (including variants in case and spacing, and one unknown question), and prints the matched expected_plan or None for each.

## How to Evaluate

To evaluate your solution and view the score:

Click the "t" icon on the left side of the VS Code editor, select Evaluate to run the automated evaluation, and view the evaluation score and results once the evaluation is complete.
