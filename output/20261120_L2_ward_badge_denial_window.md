# Ward Badge Denial Window

## Description

Fix and complete the badge-denial counting module so that it counts only recent DENIED swipes per badge, using a rolling 30-minute window with timezone-aware timestamps, and reports alert levels for the compliance reviewer. Use Python's standard library only.

## 📋 Instructions

Use the provided template code as the starting point. Implement your solution only within the TODO blocks, and do not modify the project structure, file names, or function signatures. The automated evaluation uses this template to assess your code, so any structural changes may cause your submission to fail evaluation.

## 🎯 Objective

Tidewater Renal Partners runs 14 outpatient dialysis clinics along a tidal coastline. Every badge swipe at a ward door is logged with an outcome of GRANTED or DENIED, and a nightly job reviews those denials because the OCR expects regular audit-log review. The job has a bug: it counts every DENIED swipe a badge has ever produced. A phlebotomist with three denials in March is flagged again in October, and the compliance reviewer's queue fills with stale noise. Clinics also record timestamps with different UTC offsets, so the same instant can appear as two different strings. Compliance wants a rolling 30-minute window per badge, with clear alert levels, so that only recent denial bursts reach a reviewer. Fix the counting, correct an alert threshold that misses exact-5 bursts, and add the per-badge summary the reviewer reads each morning.

## 📚 Log Analysis Concepts You'll Practice

- **Sliding-window counting**: restricting an event count to a time window with explicit start and end boundaries, so old events stop influencing today's result.
- **Boundary semantics**: deciding whether each end of a window is inclusive or exclusive and applying that rule exactly, since off-by-one errors on boundary events are the most common way detection logic goes wrong.
- **Timezone-aware timestamp comparison**: parsing ISO 8601 strings with offsets into aware datetimes and comparing instants, not text.
- **Principal normalisation**: trimming and case-folding identifiers before grouping, so that " Ana.Ruiz " and "ana.ruiz" count as one badge holder.
- **Threshold classification on integer counts**: mapping counts to alert levels with inclusive lower bounds that match the policy wording.

## Your Task

Implement three pieces in `badge_monitor.py`. Every `as_of` argument is an ISO 8601 string with an explicit offset (for example `"2024-03-10T12:00:00+00:00"`). Every event `ts` is also an ISO 8601 string with an offset. Parse both with `datetime.fromisoformat` and compare the resulting aware datetimes.

**1. `denials_in_window(events, principal, as_of, window_minutes=30)`** returns an `int`: the number of events where `outcome == "DENIED"` and the principal matches. Matching compares `principal.strip().casefold()` against each event's `principal.strip().casefold()`. An event counts only if `as_of - timedelta(minutes=window_minutes) < event_time <= as_of`. The lower bound is strict, so an event exactly at the window start is excluded, and the upper bound is inclusive. Two timestamps naming the same instant with different offsets are the same moment. Do not modify `events`.

**2. `alert_level(count)`** (fix the existing function) returns `"ALERT"` when `count >= 5`, `"REVIEW"` when `count` is 3 or 4, and `"OK"` otherwise. The current code uses `>` and misses exact-5 bursts.

**3. `scan_badges(events, as_of)`** returns a `list` of `dict`s, one per normalised principal that has at least one in-window DENIED event. Each dict has exactly these keys:
- `principal`: the trimmed original spelling of that principal's first in-window DENIED event, taken in input-list order (not chronological order).
- `count`: the `int` returned by `denials_in_window` for that principal with the default 30-minute window.
- `level`: `alert_level(count)`.

Sort the list by `count` descending, then by `principal` ascending. Do not modify the input list.

Sample:

```python
events = [
    {"event_id": "e1", "principal": " Ana.Ruiz ", "outcome": "DENIED",  "ts": "2024-03-10T12:00:00+00:00"},
    {"event_id": "e2", "principal": "ana.ruiz",   "outcome": "DENIED",  "ts": "2024-03-10T11:30:00+00:00"},
    {"event_id": "e3", "principal": "ANA.RUIZ",   "outcome": "DENIED",  "ts": "2024-03-10T12:45:00+01:00"},
    {"event_id": "e4", "principal": "ana.ruiz",   "outcome": "GRANTED", "ts": "2024-03-10T12:00:00+00:00"},
    {"event_id": "e5", "principal": "ben",        "outcome": "DENIED",  "ts": "2024-03-10T11:45:00+00:00"},
    {"event_id": "e6", "principal": "ben",        "outcome": "DENIED",  "ts": "2024-03-10T12:10:00+00:00"},
]
scan_badges(events, "2024-03-10T12:00:00+00:00")
# [{"principal": "Ana.Ruiz", "count": 2, "level": "OK"},
#  {"principal": "ben", "count": 1, "level": "OK"}]
```

Explanation: the window is (11:30Z, 12:00Z]. e1 (12:00Z) is inside. e2 (11:30Z) sits exactly on the window start and is excluded. e3 is written as 12:45+01:00, which is 11:45Z, so it is inside despite its different offset text. e4 is GRANTED. e5 (11:45Z) is inside. e6 (12:10Z) is after `as_of` and is excluded. Ana's first in-window DENIED event is e1, so her principal is `"Ana.Ruiz"`.

## Environment Setup

File Structure:

```
badge_denial_monitor/
├── badge_monitor.py       # denials_in_window(), alert_level() (fix), scan_badges() (TODO)
└── test_badge_monitor.py  # pytest suite (fixed, do not modify)
```

Open VS Code: Open the project folder in VS Code and launch the integrated terminal (Terminal → New Terminal).

Requires Python 3.9 or newer. The module uses only the standard library. Install pytest with `pip install pytest` if you want to run the local tests.

No API keys needed: this exercise is fully offline. No OPENAI_API_KEY or proxy gateway is required.

## How to Run

```bash
python badge_monitor.py
```

This runs `scan_badges` on a small built-in demo log at 12:00 UTC and prints the per-badge summary (principal, count, level) for the morning reviewer.

## How to Evaluate

To evaluate your solution and view the score:

Click the "t" icon on the left side of the VS Code editor, select Evaluate to run the automated evaluation, and view the evaluation score and results once the evaluation is complete.
