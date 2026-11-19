# Harbour Container Clearance Review Loop

## Description

Build the review-loop controller for a customs clearance agent. It parses each model reply into a verdict, decides when a review loop should stop, and returns one final decision per manifest. The model call is supplied by the caller, so your code is pure control logic.

## 📋 Instructions

Use the provided template code as the starting point. Implement your solution only within the TODO blocks in main.py, and do not modify the project structure, file names, or function signatures. The automated evaluation uses this template to assess your code, so any structural changes may cause your submission to fail evaluation.

## 🎯 Objective

Halvard Port Authority is a mid-sized container terminal. Its customs desk uses a Claude-backed agent to draft a clearance recommendation for each container manifest. A second critic pass re-checks that draft, and the two passes repeat for a bounded number of rounds. Whatever the loop produces goes to a human inspector, so the loop's output matters. If the loop accepts a draft that was never confirmed, a container of restricted goods can leave the port. If it holds or escalates too often, inspectors drown in cases. Build the loop controller that runs the review rounds, parses each reply into one of three verdicts (CLEAR, HOLD, ESCALATE), decides when to stop, and reports how the loop ended. The model call is passed in as `review_fn`, so your code can be tested with scripted replies.

## 📚 Loop Engineering Concepts You'll Practice

- **Bounded iteration**: an agent loop needs an explicit round budget. You return the rounds actually used and a stop reason, so the caller can see why the loop ended.
- **Stop conditions**: deciding when a loop has converged is a rule you must derive from the data. Stopping too early and stopping too late are both failures.
- **Defensive output parsing**: model replies may be code-fenced, malformed, or use words outside the allowed set. Each reply must map to a known verdict.
- **Fail-safe defaults**: when the loop cannot reach a trustworthy answer, the final outcome must be the safe one, not whatever the last draft happened to say.
- **Verdict history**: a controller often has to reason over the sequence of past outputs, not only the latest one.

## Your Task

Implement three functions in main.py:

- `parse_verdict(reply: str) -> str`: maps a raw model reply to `'CLEAR'`, `'HOLD'`, or `'ESCALATE'`. The reply may be plain text, code-fenced, or JSON-like. Any reply that cannot be mapped to CLEAR or HOLD (including unparseable text, unknown words such as `'maybe'` or `'PASS'`, and empty strings) returns `'ESCALATE'`. Work out the accepted forms from the shipped replies.
- `next_action(history: list[str]) -> str`: `history` is the list of verdicts parsed so far, in round order. Returns `'stop'` or `'continue'`.
- `run_review_loop(manifest: dict, review_fn, max_rounds: int) -> dict`: runs the review rounds and returns the final result.

Parameters (`run_review_loop`):

- `manifest`: a dict describing one container manifest (keys include `manifest_id` and `declared_goods`, both str). Pass it unchanged to `review_fn`.
- `review_fn`: a callable `review_fn(manifest, round_no) -> str` that returns the raw model reply for that round. `round_no` starts at 1.
- `max_rounds`: the maximum number of rounds the loop may run (int, at least 1).

Each reply must be passed through `parse_verdict` before it enters the history used by `next_action`.

Returns: a dict with these keys:

- `decision`: str, one of `'CLEAR'`, `'HOLD'`, `'ESCALATE'`.
- `rounds_used`: int, the number of `review_fn` calls made. A call that raises an exception still counts as a call made.
- `stop_reason`: str, one of `'agreed'`, `'max_rounds'`, `'error'`.

If `review_fn` raises an exception, the loop stops immediately with `stop_reason` `'error'` and `decision` `'ESCALATE'`. If the loop uses all `max_rounds` without stopping on agreement, the decision must be the safe one given the objective above. Work out the remaining decision rules from the shipped cases in `manifests.json`.

Sample:

```python
def scripted(manifest, round_no):
    return "CLEAR" if round_no <= 2 else "HOLD"

run_review_loop({"manifest_id": "HPA-2291", "declared_goods": "Ceramic tiles"}, scripted, 3)
# -> {"decision": "CLEAR", "rounds_used": 2, "stop_reason": "agreed"}
```

## Environment Setup

File Structure:

```
harbour_clearance_loop/
├── manifests.json  # 4 sample manifests with declared goods and scripted reviewer replies (fixed, do not modify)
└── main.py         # parse_verdict(), next_action(), run_review_loop() (TODO)
```

Open VS Code: Open the project folder in VS Code and launch the integrated terminal (Terminal → New Terminal).

No API keys needed: this exercise is fully offline. No OPENAI_API_KEY or proxy gateway is required.

## How to Run

```bash
python main.py
```

This runs `run_review_loop(...)` on the 4 sample manifests with their scripted review replies and prints each manifest's decision, rounds used, and stop reason.

## How to Evaluate

To evaluate your solution and view the score:

Click the "t" icon on the left side of the VS Code editor, select Evaluate to run the automated evaluation, and view the evaluation score and results once the evaluation is complete.
