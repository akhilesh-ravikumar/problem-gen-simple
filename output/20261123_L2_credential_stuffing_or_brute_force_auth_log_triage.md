# Credential Stuffing or Brute Force? Auth Log Triage

## Description

Build a small offline triage tool that reads a player-account login log, groups events into 5-minute windows, and classifies each suspicious IP as credential stuffing, brute force, shared-NAT noise, or unknown, using only the Python standard library.

## 📋 Instructions

Use the provided template code as the starting point. Implement your solution only within the TODO blocks, and do not modify the project structure, file names, or function signatures. The automated evaluation uses this template to assess your code, so any structural changes may cause your submission to fail evaluation.

## 🎯 Objective

Lumen Arcades runs 40 location-based VR arcades in Osaka and Leeds, and each arcade's player accounts are handled by the company's own login service. Last month, login timeouts spiked during evening sessions. The front-desk team assumed a DDoS and asked for the network to be throttled, which locked out real players for most of a weekend. The auth log told a different story. One wave of roughly 4,000 login attempts came from a handful of IPs, each trying a different account with one or two passwords (credential stuffing). A second group of IPs hammered a single account with hundreds of guesses (brute force). The arcade wifi also sits behind carrier-grade NAT, so dozens of legitimate players share a few public addresses, and some of those addresses look alarming on a naive count.

The Security Operations Centre needs a triage tool that reads the login log and labels each IP so the right response is chosen: block a credential-stuffing source, lock a targeted account, or leave shared-NAT addresses alone. Your job is to implement the parser, the per-IP classification rules, and the report builder.

## 📚 Auth Log Triage Concepts You'll Practice

- **Indicators of compromise (bursts of failed authentications)**: You turn raw failed logins into signals, such as how many distinct accounts an IP tried and how many failures any single account received.
- **Distinguishing attack categories by vector, target and impact**: Credential stuffing spreads attempts across many accounts, while brute force concentrates them on one. Your rules separate the two by the shape of the attempts, not by raw volume.
- **Detection false positives from shared NAT addresses**: Many real players behind one public IP can look like an attack. You implement a rule that recognises this pattern and whose precedence over other rules is fixed by the rule order.
- **Tumbling time windows**: You bucket events into fixed 300-second windows using integer arithmetic on ISO 8601 timestamps, so the same log always produces the same buckets.
- **Defensive log parsing**: Real logs contain blank lines and malformed entries. Your parser skips them quietly and never crashes the pipeline.

## Your Task

Implement three functions in `triage.py`. Each TODO block is marked with a comment.

**1. `parse_events(lines: list[str]) -> list[dict]`**

A valid line matches this form exactly:

`TS LOGIN_OK|LOGIN_FAIL user=ACCOUNT ip=IP`

- `TS` is a timestamp that parses with `datetime.strptime(TS, "%Y-%m-%dT%H:%M:%SZ")`. Fractional seconds, offsets and other formats are invalid, and so are impossible dates such as `2024-02-30T...`.
- Exactly one space separates the three parts. `ACCOUNT` and `IP` are non-empty runs of non-whitespace characters, so `user= BOB`, a double space, or a tab makes the line invalid.
- Strip only a trailing `\n` or `\r\n` before matching. Any other leading or trailing whitespace makes the line invalid.

Return one dict per valid line, in input order, with exactly these keys:
- `ts`: the timestamp string exactly as written.
- `account`: the account value lowercased.
- `ip`: the IP value.
- `result`: `"ok"` for `LOGIN_OK`, `"fail"` for `LOGIN_FAIL`.

Skip blank or whitespace-only lines and any line that fails the rules above. Never raise an exception for any input.

**2. `classify_ip(events: list[dict], ip: str) -> str`**

`events` holds the events of one 300-second window. Consider only events whose `ip` equals `ip`. Apply these rules in order and return the first match:
1. If failed attempts come from at least 20 distinct accounts **and** no single account has more than 3 failures, return `"credential_stuffing"`.
2. If any single account has at least 20 failures, return `"brute_force"`.
3. If the IP has at least 5 distinct successful accounts, return `"shared_nat"`. This applies regardless of how many failures the IP also has, but rules 1 and 2 are checked first.
4. Otherwise return `"unknown"`.

All thresholds are inclusive: exactly 20 accounts, exactly 20 failures and exactly 5 successful accounts each satisfy their rule.

**3. `build_report(events: list[dict]) -> dict`**

The inputs are dicts in the `parse_events` format, with valid timestamps. Use one global anchor, the earliest timestamp across all events. An event's window index is `int((event_time - anchor).total_seconds()) // 300`. Parse timestamps with the format above.

For each IP, split its events by window index and call `classify_ip` on each window's events. The IP's final classification is the result for the window containing the most events for that IP. On a tie, use the earlier window.

Return:

`{"ips": {ip: classification, ...}, "counts": {classification: n, ...}}`

- `ips` maps each IP to its final classification.
- `counts` counts how many IPs received each classification. Include only classifications that occurred, and sort the keys alphabetically.
- For empty input, return `{"ips": {}, "counts": {}}`.

**Sample**

```python
lines = [
    "2024-05-01T10:00:01Z LOGIN_FAIL user=Alice ip=203.0.113.7",
    "",
    "not a valid line",
    "2024-05-01T10:00:02Z LOGIN_OK user= BOB ip=198.51.100.4",
    "2024-05-01T10:00:03Z LOGIN_OK user=Bob ip=198.51.100.4",
    "2024-05-01T10:00:04Z LOGIN_OK user=Bob  ip=198.51.100.4",
    "2024-02-30T10:00:05Z LOGIN_OK user=Carol ip=198.51.100.4",
]
parse_events(lines)
# [{"ts": "2024-05-01T10:00:01Z", "account": "alice", "ip": "203.0.113.7", "result": "fail"},
#  {"ts": "2024-05-01T10:00:03Z", "account": "bob", "ip": "198.51.100.4", "result": "ok"}]
```

Lines 4, 6 and 7 are skipped because of the space rules and the impossible date.

## Environment Setup

File Structure:
```
auth_triage/
├── auth_sample.log  # sample login log for local runs (fixed, do not modify)
└── triage.py        # parse_events(), classify_ip(), build_report() (TODO)
```

Open VS Code: Open the project folder in VS Code and launch the integrated terminal (Terminal → New Terminal).

No API keys needed: this exercise is fully offline. No OPENAI_API_KEY or proxy gateway is required.

## How to Run

```bash
python triage.py
```

This reads `auth_sample.log`, parses it, builds the 5-minute report, and prints the resulting dict with the per-IP classifications and the sorted counts.

## How to Evaluate

To evaluate your solution and view the score:

Click the "t" icon on the left side of the VS Code editor, select Evaluate to run the automated evaluation, and view the evaluation score and results once the evaluation is complete.
