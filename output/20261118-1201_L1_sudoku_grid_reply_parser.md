# Sudoku Grid Reply Parser

## Description

Build the reply-handling layer for a photographed-sudoku scanner: write `strip_code_fence()` and `parse_grid_reply()` so that a model's JSON grid is accepted only when it is a valid 9x9 digit grid, and anything else returns `None`. The key rule is that a markdown code fence around the JSON is removed before parsing, and bad input never raises.

## 📋 Instructions

Use the provided template code as the starting point. Implement your solution only within the TODO blocks in main.py, and do not modify the project structure, file names, or function signatures. The automated evaluation uses this template to assess your code, so any structural changes may cause your submission to fail evaluation.

## 🎯 Objective

Brightline Puzzle Labs publishes sudoku books. Its scanner lets a reader photograph a puzzle, and an OCR assistant replies with the 9x9 grid as JSON, which the Brightline solver then uses. If the reply is parsed wrongly, the solver receives a malformed grid and either crashes or confidently solves a puzzle that was never printed. The OCR assistant often wraps its JSON in a markdown code fence, so a plain `json.loads` call fails on the first line. Your job is to write the parsing layer that strips that fence, validates the grid strictly, and returns `None` for anything it cannot accept. The tests replace the model with scripted replies, so your code is graded on exact return values.

## 📚 Output Parsing Concepts You'll Practice

- **Code-fence stripping**: models often wrap structured output in a fenced block. You remove exactly one opening and one closing fence line so the parser sees only the payload.
- **Defensive `json.loads`**: model text is untrusted input. You catch decoding failures and return a fallback value instead of letting an exception escape.
- **Shape validation**: a parsed JSON value is not automatically the shape you need. You check list lengths, element types and value ranges before accepting it.
- **Strict type checks**: in Python, `bool` is a subclass of `int`, and strings and floats can look like numbers to a careless check. You reject these explicitly.
- **Fail-safe returns**: the contract is "a valid grid or `None`", never a partly valid structure.

## Your Task

Implement two functions in main.py:

- `strip_code_fence(raw: str) -> str` — removes at most one opening fence and at most one closing fence. Procedure:
  1. Split `raw` into lines. Ignore leading blank lines and trailing blank lines when identifying fences.
  2. A fence line is a line whose text, with surrounding whitespace removed, is exactly ` ``` ` or ` ```json ` (lowercase only). If the first non-blank line is a fence line, remove that line.
  3. If the last non-blank remaining line, with surrounding whitespace removed, is exactly ` ``` `, remove that line. Each check is independent, so an opening fence with no closing fence is still removed, and a lone fence line such as ` ``` ` is removed once as the opening fence and nothing more.
  4. Return the joined remaining text with surrounding whitespace removed.

  Uppercase `JSON` or other tags such as `python` are not fences and are left in place. Never remove more than one opening and one closing fence.
- `parse_grid_reply(raw: str) -> list[list[int]] | None` — the main parser. Call `strip_code_fence(raw)`, then `json.loads` on the result. Accept the value only if it is a list of exactly 9 lists, and each inner list has exactly 9 elements. Every element must be an `int` (not a `bool`, float or string) with a value from 0 to 9 inclusive, where 0 means a blank cell. Return `None` for invalid JSON, the wrong shape, or any bad element. The function must never raise for any string input, including the empty string and deeply nested input. Catch `Exception` around the parsing step, because `json.loads` can raise `RecursionError` on very deep nesting, and that is not a `ValueError`.

**Trap:** a naive solution calls `json.loads(raw)` directly, which fails on the opening fence line. Strip exactly one fence pair with `strip_code_fence` first, then parse. Never let an exception escape.

Parameters (`parse_grid_reply`):

- `raw` — the complete text reply from the OCR assistant, which may or may not be wrapped in a code fence.

Returns: the parsed 9x9 list of lists of ints, in the same row order as the reply, or `None`.

Sample:

```python
reply = (
    "```json\n"
    "[[5,3,0,0,7,0,0,0,0],[6,0,0,1,9,5,0,0,0],[0,9,8,0,0,0,0,6,0],"
    "[8,0,0,0,6,0,0,0,3],[4,0,0,8,0,3,0,0,1],[7,0,0,0,2,0,0,0,6],"
    "[0,6,0,0,0,0,2,8,0],[0,0,0,4,1,9,0,0,5],[0,0,0,0,8,0,0,7,9]]\n"
    "```"
)
parse_grid_reply(reply)

parse_grid_reply("not json")      # None
strip_code_fence("```\n[1,2]\n```")  # "[1,2]"
```

## Environment Setup

File Structure:

```
sudoku_reply_parser/
└── main.py  # strip_code_fence(), parse_grid_reply()
```

Open VS Code: Open the project folder in VS Code and launch the integrated terminal (Terminal → New Terminal).

No API keys needed: this exercise is fully offline. No OPENAI_API_KEY or proxy gateway is required.

## How to Run

```bash
python main.py
```

This calls `parse_grid_reply(...)` on three scripted replies (a fenced valid grid, an unfenced valid grid, and a 9x8 grid) and prints the results. You will see the parsed grid for the first two and `None` for the third.

## How to Evaluate

To evaluate your solution and view the score:

Click the "t" icon on the left side of the VS Code editor, select Evaluate to run the automated evaluation, and view the evaluation score and results once the evaluation is complete.
