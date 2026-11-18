# Academic Integrity Auditor

## Description

Build a human-in-the-loop academic-integrity reviewer - a raw LLM-as-judge call, no framework, no tool/function-calling - that decides between Auto-Refer to Integrity Office, Auto-Clear, and Escalate to Human Reviewer.

## 📋 Instructions

Use the provided template code as the starting point. Implement your solution only within the TODO blocks in main.py, and do not modify the project structure, file names, or function signatures. The automated evaluation uses this template to assess your code, so any structural changes may cause your submission to fail evaluation.

## 🎯 Objective

Meridian University's Academic Integrity Office gets submissions flagged by similarity scans and AI-generated-text detectors. An AI reviewer drafts a first-pass decision for each flag - but it should never silently guess on a genuinely ambiguous case, since a wrongful violation finding can mean a failing grade or a disciplinary record. Build a human-in-the-loop reviewer that uses an LLM as the judge (one raw chat-completion call, no framework, no tool calling) and routes every flagged submission to exactly one of three outcomes: Auto-Refer to Integrity Office, Auto-Clear, or Escalate to a human reviewer - with a broken or unparseable model response ALSO escalating, never silently auto-deciding.

## 📚 Human-in-the-Loop Concepts You'll Practice

- Three-way routing, not pass/fail — most of the other activities in this folder reach a two-way verdict. Here the judge itself chooses between three outcomes, and the middle one ("uncertain") is the point of the whole exercise.

- Fail-safe defaults — a response that doesn't parse, or that returns a verdict value you didn't expect, must ALSO escalate to a human - never fall through to an auto-decision by accident.

- Raw judge prompting — a system prompt you write yourself, instructing the model exactly when to say "I'm not sure" instead of guessing.

- Hand-rolled JSON parsing — stripping a code fence, validating the response shape, and defaulting safely on any failure.

- Operational metrics — an Escalation Rate isn't a pass/fail number, it's something an Academic Integrity Office would track over time to see how much human review load the system is generating.

## Your Task

Implement four functions in main.py:

- build_judge_messages(record) — build and return the system + user messages list sent to the judge model.

- parse_judge_response(raw_text) — strip a code fence if present, parse the JSON, and fall back to "uncertain" on any failure - never to "no_violation" or "violation".

- route_decision(parsed) — map "violation" to Auto-Refer to Integrity Office, "no_violation" to Auto-Clear, and everything else to Escalate to Human Reviewer.

- audit_cases(records) — call the judge on every record and return the report described below.

Parameters (audit_cases):

- records — a list of dicts, each with submission_excerpt, flag_reason, and policy_excerpt (all str).

Returns: a dict with these keys:

- Per-Case Results — a list (same order as records) of dicts with Submission, Flag Reason, Judge Verdict, Rationale, and Action.

- Auto-Refer / Auto-Clear / Escalated — counts of records landing on each action.

- Total — total number of records.

- Escalation Rate — Escalated / Total, rounded to 3dp.

Sample:

records = \[{"submission_excerpt": "Paragraph 3 is word-for-word identical to another student's paragraph 2.",

"flag_reason": "Similarity-scan match: 98% overlap.",

"policy_excerpt": "Substantially identical work is a violation."}\]

\# when the judge decides this case is a violation, audit_cases(records) returns:

{"Per-Case Results": \[{"Submission": "Paragraph 3 is word-for-word identical to another student's paragraph 2.",

"Flag Reason": "Similarity-scan match: 98% overlap.",

"Judge Verdict": "violation",

"Rationale": \<the judge's sentence\>,

"Action": "Auto-Refer to Integrity Office"}\],

"Auto-Refer": 1, "Auto-Clear": 0, "Escalated": 0, "Total": 1, "Escalation Rate": 0.0}

## Environment Setup

File Structure:

academic_integrity_auditor/

└── main.py \# build_judge_messages(), parse_judge_response(), route_decision(), audit_cases()

Open VS Code: Open the project folder in VS Code and launch the integrated terminal (Terminal → New Terminal).

OpenAI Configuration: OpenAI is used as the LLM provider, with the API key read from the OPENAI_API_KEY environment variable. Use the gpt-4o-mini model, and point the OpenAI client at the proxy gateway below:

🔗 Proxy URL: https://llmgateway-lms.tekstac.com/v1

client = OpenAI(

api_key=api_key,

base_url="https://llmgateway-lms.tekstac.com/v1",

)

## How to Run

python main.py

This calls audit_cases(...) with 4 sample flagged submissions and prints the returned report (per-case verdicts/actions, Auto-Refer/Auto-Clear/Escalated counts, and Escalation Rate).

## How to Evaluate

To evaluate your solution and view the score:

Click the "t" icon on the left side of the VS Code editor, select Evaluate to run the automated evaluation, and view the evaluation score and results once the evaluation is complete.
