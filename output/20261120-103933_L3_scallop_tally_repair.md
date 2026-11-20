# Scallop Tally Repair

## Description

Fix the nightly validation module of a scallop cooperative so that every landing row is reported exactly once as passed or failed. Work only in the TODO blocks of `checks.py`, and do not mutate the DataFrames you receive.

## 📋 Instructions

Use the provided template code as the starting point. Implement your solution only within the TODO blocks, and do not modify the project structure, file names, or function signatures. The automated evaluation uses this template to assess your code, so any structural changes may cause your submission to fail evaluation.

## 🎯 Objective

The Skerry Isles Scallop Cooperative has 14 boats landing dredged scallops across the season. Each night `main.py` validates the day's landings and prints `rows_in`, `passed` and `failed` for the harbour-office dashboard. Lately those three numbers don't add up. Landings with a missing weight or date appear in neither the valid nor the invalid set. A boat that landed exactly its hold capacity was flagged, and a boat landing on the last day of the season was rejected. Last week a quota overrun went unnoticed because the row was silently lost. Repair the checks so that every input row is accounted for, every failure is explained with a reason code, and the totals reconcile.

## 📚 Data Quality Concepts You'll Practice

- **Null semantics** — missing weights and dates must be reported as failures in their own right, not vanish from every filter.
- **Boundary inclusivity** — weight limits and season dates have precisely defined edges, set in `config.py`.
- **Referential integrity** — landings must reference vessels in the registry. Unmatched vessels have to be reported rather than dropped.
- **Structured failure output** — checks return one row per failure instead of raising on the first error.
- **Row count reconciliation** — in = passed + failed, verified rather than assumed.
- **Non-mutation** — checks must leave the caller's data untouched.

## Your Task

Implement four functions in `checks.py`. The input `df` has columns `row_id` (int), `vessel_id`, `landing_date` (text) and `weight_kg`. The `weight_kg` column may hold numbers, blanks or text.

**Failure frame (returned by the three checks).** A DataFrame with columns exactly `['row_id', 'check', 'reason']`, one row per failure. It is sorted by `row_id`, then `reason`, and has a fresh `RangeIndex`. `row_id` keeps the input's integer dtype, and `check` and `reason` are strings. With no failures, return an empty frame with the same columns and dtypes.

1. `check_weight(df, cfg)` — `check` is `'weight'`. Reasons are exactly `'NULL_WEIGHT'` and `'WEIGHT_RANGE'`. A weight that cannot be read as a number counts as missing. A row gets at most one weight failure.
2. `check_season(df, cfg)` — `check` is `'season'`. Reasons are exactly `'NULL_DATE'` (missing or blank date), `'BAD_DATE'` (non-blank text that is not a valid `YYYY-MM-DD` date) and `'OUT_OF_SEASON'`. A row gets at most one season failure.
3. `check_hold_capacity(df, vessels)` — `check` is `'hold_capacity'`. `vessels` has columns `vessel_id` and `hold_capacity_kg`. Reasons are exactly `'OVER_CAPACITY'` and `'UNKNOWN_VESSEL'`. A landing whose `vessel_id` is not in the registry is `UNKNOWN_VESSEL`, and this includes a landing whose `vessel_id` is missing (null or blank). A row gets at most one hold-capacity failure. This check never reports a row merely because its weight is missing or unreadable.
4. `reconcile(df, failures)` returns a dict with exactly these keys:
   - `rows_in`: the number of input rows (`int`).
   - `rows_failed`: the number of distinct `row_id`s in `failures` (`int`).
   - `rows_passed`: the number of input rows that have no failure recorded against their `row_id` (`int`).
   - `reconciled`: a `bool`, `True` only when `rows_in == rows_passed + rows_failed`.

`cfg` is any object with these attributes, as in `config.py`:

- `MIN_WEIGHT_KG`, `MAX_WEIGHT_KG`
- `MIN_INCLUSIVE`, `MAX_INCLUSIVE`
- `SEASON_OPEN`, `SEASON_CLOSE` (ISO date strings)
- `OPEN_INCLUSIVE`, `CLOSE_INCLUSIVE`

A flag set to `True` means a value exactly on that boundary is acceptable. The flags differ between weight and season, and hidden tests use other values.

Sample, with `MIN_WEIGHT_KG=5`, `MAX_WEIGHT_KG=400`, `MIN_INCLUSIVE=True` and `MAX_INCLUSIVE=False`:

```python
df = pd.DataFrame({"row_id": [1, 2, 3, 4],
                   "weight_kg": [120.0, None, 400.0, 2.0]})
check_weight(df, cfg)
```
```
   row_id   check        reason
0       2  weight   NULL_WEIGHT
1       3  weight  WEIGHT_RANGE
2       4  weight  WEIGHT_RANGE
```

Run on `df` with those failures, `reconcile` returns `{'rows_in': 4, 'rows_failed': 3, 'rows_passed': 1, 'reconciled': True}`.

## Environment Setup

File Structure:
```
scallop_tally/
├── config.py                  # season window, weight limits, inclusivity flags (fixed, do not modify)
├── main.py                    # runs all checks on the sample data and prints the summary (fixed)
├── checks.py                  # check_weight(), check_season(), check_hold_capacity(), reconcile() (TODO)
└── data/
    ├── landings_sample.csv    # about 15 sample landings (fixed, do not modify)
    └── vessels.csv            # vessel registry: vessel_id, hold_capacity_kg (fixed, do not modify)
```
Open VS Code: Open the project folder in VS Code and launch the integrated terminal (Terminal → New Terminal).

Python 3 with `pandas` and `pytest` installed (`pip install pandas pytest`). All data is local and no network is needed.

No API keys needed: this exercise is fully offline. No OPENAI_API_KEY or proxy gateway is required.

## How to Run

```bash
python main.py
```

This loads the sample landings and the vessel registry, runs the three checks, and prints the combined failure frame followed by the `reconcile` dictionary.

## How to Evaluate

To evaluate your solution and view the score:

Click the "t" icon on the left side of the VS Code editor, select Evaluate to run the automated evaluation, and view the evaluation score and results once the evaluation is complete.
