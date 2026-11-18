# Support Tone Auditor

## Description

Build a custom LLM-as-judge auditor - a raw chat-completion call and hand-parsed JSON response, no evaluation framework and no tool/function calling - that batch-checks a cloud-storage support team's draft replies for tone and empathy.

## 📋 Instructions

Use the provided template code as the starting point. Implement your solution only within the TODO blocks and do not modify the project structure, file names, or function signatures. The automated evaluation uses this template to assess your code, so any structural changes may cause your submission to fail evaluation.

## 🎯 Objective

Nimbus Cloud Storage's support team drafts replies to frustrated customers - billing disputes, data-loss scares, account lockouts - before they go out. Whether a reply is empathetic, professional, and actually addresses what the customer said isn't something you can check with string matching or a similarity score - it takes judgment. Build a custom evaluator that uses an LLM as that judge: one raw chat-completion call per reply, with no evaluation framework involved and no tool/function calling - just a prompt you write yourself and a JSON response you parse by hand.

## 📚 LLM-as-Judge Concepts You'll Practice

- Raw judge prompting — writing a system prompt that tells the model exactly what to judge and exactly what shape of answer to return, without a framework's metric class doing that for you.

- Direct chat-completion calls — client.chat.completions.create(), the raw OpenAI SDK call, with no tool/function-calling schema involved - the judge answers in plain text that you parse yourself.

- Hand-rolled JSON parsing — models often wrap "JSON-only" answers in a \`\`\`json code fence anyway; your harness has to strip that and parse defensively, falling back safely when the response isn't valid JSON at all.

- Subjective, per-dimension verdicts — empathy, professionalism, and whether the reply addresses the customer's specific complaint are judgment calls, not facts you can check against a knowledge base - exactly the case where an LLM judge earns its keep over a rule-based check.

- Batch auditing — running the judge over many records and rolling per-case verdicts into one summary.

## Your Task

Implement four functions in main.py:

- build_judge_messages(customer_message, agent_response) — returns a list of two messages: a "system" message, then a "user" message whose content includes both the customer message and the agent reply.

- parse_judge_response(raw_text) — returns a dict with "empathy", "professionalism" and "addresses_complaint" (each "pass" or "fail") and "rationale" (str), whether or not the JSON is wrapped in a \`\`\` or \`\`\`json code fence. If the text cannot be read as that dict, all three dimensions are "fail".

- \_case_verdict(parsed) — return "Pass" only if all three dimensions are "pass", otherwise "Flag for Review".

- audit_support_responses(records) — call the judge on every record and return the report described below.

Parameters (audit_support_responses):

- records — a list of dicts, each with customer_message (str) and agent_response (str).

Returns: a dict with these keys:

- Per-Case Results — a list (same order as records) of dicts with Customer Message, Empathy, Professionalism, Addresses Complaint, Rationale, and Verdict.

- Passed — count of records verdicted "Pass".

- Total — total number of records.

- Summary — "All Clear" if every record passed, otherwise "Needs Review".

Sample input:

records = \[{"customer_message": "I was charged twice for my Pro plan upgrade this month.",

"agent_response": "I'm sorry about the double charge. I've refunded the duplicate \$12.99; it reaches your card in 3-5 business days."}\]

Sample output, when the judge rates all three dimensions "pass":

{"Per-Case Results": \[{"Customer Message": "I was charged twice for my Pro plan upgrade this month.",

"Empathy": "pass", "Professionalism": "pass", "Addresses Complaint": "pass",

"Rationale": \<the judge's one-sentence rationale\>, "Verdict": "Pass"}\],

"Passed": 1, "Total": 1, "Summary": "All Clear"}

## Environment Setup

File Structure:

support_tone_auditor/

└── main.py \# build_judge_messages(), parse_judge_response(), \_case_verdict(), audit_support_responses()

Open VS Code: Open the project folder in VS Code and launch the integrated terminal (Terminal → New Terminal).

OpenAI Configuration: OpenAI is used as the judge model provider, with the API key securely set as an environment variable. Use the gpt-4o-mini model, and point the OpenAI client at the proxy gateway below:

🔗 Proxy URL: https://llmgateway-lms.tekstac.com/v1

client = OpenAI(

api_key=api_key,

base_url="https://llmgateway-lms.tekstac.com/v1",

)

## How to Run

python main.py

This calls audit_support_responses(...) with 3 sample customer/agent records and prints the returned report (per-case verdicts, Passed/Total, and Summary).

## How to Evaluate

To evaluate your solution and view the score:

Click the "t" icon on the left side of the VS Code editor, select Evaluate to run the automated evaluation, and view the evaluation score and results once the evaluation is complete.
