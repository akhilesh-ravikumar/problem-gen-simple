# Mountain Rescue Dispatch Triage

## Description

Build a fail-safe intake parser and router for mountain rescue call reports using only the Python standard library. Use the `json` module for parsing, and do not call any language model.

## 📋 Instructions

Use the provided template code as the starting point. Implement your solution only within the TODO blocks in main.py, and do not modify the project structure, file names, or function signatures. The automated evaluation uses this template to assess your code, so any structural changes may cause your submission to fail evaluation.

## 🎯 Objective

Cairn Valley Mountain Rescue is a volunteer team. Its call-intake tool sends each incoming report to a language model, which replies with a JSON object giving a category and an urgency score. The duty officer sees only the result, so the parsing layer decides what happens to every report. Models sometimes reply with prose instead of JSON, such as "Sure, here is the classification...". A parser that turns such a reply into a harmless-looking result can leave a missing hiker unattended. Build the parsing and routing layer so that a malformed reply is never treated as safe, every report maps to exactly one route, and the team can count how many reports went to each route.

## 📚 Output Parsing Concepts You'll Practice

- **Strict JSON parsing with fallbacks**: `json.loads` raises on malformed text. Your handler must turn that failure into an explicit, safe result.
- **Schema validation of model output**: a parsed object still has to be checked. Fields may be missing, have the wrong type, or hold values outside the allowed set.
- **Type-aware validation**: Python's type system has some surprises when you compare and classify values. Know exactly which Python types a JSON integer produces.
- **Boundary-based routing**: a rule with thresholds is only correct if its edges are handled exactly as specified.
- **Aggregating routed outcomes**: counting results into a fixed-key dictionary so that zero counts still appear in the output.

## Your Task

Implement three functions in main.py:

- `parse_intake(reply: str) -> dict`: parse the model's JSON reply into a normalised intake dictionary.
  - If the reply cannot be parsed as JSON, or the parsed value is not a JSON object, return `{"category": "human_review", "urgency": 5}`.
  - `category` must be one of `"dispatch"`, `"standby"`, or `"human_review"`. Any other value, including a missing field or a non-string, becomes `"human_review"`.
  - `urgency` must be an integer from 1 to 5 inclusive. Any other value, including a missing field, becomes `5`.
  - Category values are matched exactly as written (lowercase). Do not change their case.
  - Return a dict with exactly the keys `"category"` (str) and `"urgency"` (int).
- `route_report(intake: dict) -> str`: return the route for one intake dictionary with keys `category` and `urgency`.
  - Return `"DISPATCH_NOW"` if `category` is `"dispatch"`, or if `urgency` is 4 or higher.
  - Return `"STANDBY_LOG"` only if `category` is `"standby"` and `urgency` is 3 or lower.
  - Otherwise return `"DUTY_OFFICER"`.
- `count_routes(routes: list[str]) -> dict`: count route strings.
  - Return a dict with exactly the keys `"DISPATCH_NOW"`, `"STANDBY_LOG"`, and `"DUTY_OFFICER"`, each an `int`. All three keys must always be present, even when the count is zero.
  - Ignore any string in `routes` that is not one of these three names.

Sample:

```python
parse_intake('{"category": "standby", "urgency": 2}')
# -> {"category": "standby", "urgency": 2}

parse_intake("Sure, here is the classification: standby")
# -> {"category": "human_review", "urgency": 5}

route_report({"category": "standby", "urgency": 3})
# -> "STANDBY_LOG"

route_report({"category": "standby", "urgency": 4})
# -> "DISPATCH_NOW"

route_report({"category": "human_review", "urgency": 1})
# -> "DUTY_OFFICER"

count_routes(["STANDBY_LOG", "DISPATCH_NOW", "STANDBY_LOG"])
# -> {"DISPATCH_NOW": 1, "STANDBY_LOG": 2, "DUTY_OFFICER": 0}
```

## Environment Setup

File Structure:

```
mountain_rescue_triage/
└── main.py  # parse_intake(), route_report(), count_routes()
```

Open VS Code: Open the project folder in VS Code and launch the integrated terminal (Terminal → New Terminal).

No API keys are needed. This exercise runs fully offline and works only with the reply strings included in main.py. The standard library is sufficient.

## How to Run

```bash
python main.py
```

This calls parse_intake(), route_report(), and count_routes() on a set of sample model replies, including one malformed reply, and prints each parsed intake, its route, and the final route counts. The output should show the malformed reply routed to the duty officer.

## How to Evaluate

To evaluate your solution and view the score:

Click the "t" icon on the left side of the VS Code editor, select Evaluate to run the automated evaluation, and view the evaluation score and results once the evaluation is complete.
