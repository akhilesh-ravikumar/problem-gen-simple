"""Generate an assessment problem statement in the format.

    python generate.py --course "LLM Evaluation methods and frameworks" --topic "LLM-as-judge" --level L2
    (optional)  --description "an insurance claims assistant"  --stack "python,openai"

Four steps:
    1. Brainstorm  - Claude proposes several different problem ideas
    2. Pick        - Claude scores them and picks the best one
    3. Write       - Claude writes the statement in the format
    4. Check       - code + Claude check it; if anything is wrong, step 3 rewrites it once
"""

import argparse
import datetime
import os
import re
import sys
from pathlib import Path
import yaml
from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

HERE = Path(__file__).parent
RULES = yaml.safe_load((HERE / "rules.yaml").read_text(encoding="utf-8"))
EXAMPLES = {p.stem: p.read_text(encoding="utf-8") for p in sorted((HERE / "examples").glob("*.md"))}

SYSTEM = ("""
    You design hands-on programming problems that assess employees and candidates on one course topic. 
    Each problem gives the candidate a small template project where they implement 2-5 functions inside TODO blocks in main.py. 
    Hidden tests grade those functions automatically, so every function needs a fixed signature and an exact return contract (keys, allowed values, casing, rounding, order). 
    If the code calls an LLM, the tests replace the model with scripted replies, so grading never depends on what a real model says. 
    Good problems use a fictional organisation with real stakes and contain a trap that a naive solution quietly gets wrong."""
)


class Idea(BaseModel):
    title: str
    organisation: str          # fictional, e.g. "CareWell Pharmacy"
    scenario: str              # who uses the AI feature, what goes wrong, what it costs
    functions: list[str]       # e.g. "route_decision(parsed) -> one of 3 actions"
    trap: str                  # what a naive solution gets wrong
    how_graded: str            # how hidden tests check it deterministically


class Ideas(BaseModel):
    ideas: list[Idea]


class Pick(BaseModel):
    best: int              
    reason: str


class Review(BaseModel):
    problems: list[str]        # empty if the statement is fine


client = None  # created in main(), after .env is loaded


def ask(prompt: str, answer_shape=None, max_tokens: int = 16000):
    """Send one prompt to Claude. With answer_shape, get back a filled-in object; otherwise plain text."""
    request = dict(model=RULES["model"], max_tokens=max_tokens, system=SYSTEM,
                   messages=[{"role": "user", "content": prompt}])
    if answer_shape:
        response = client.messages.parse(**request, output_format=answer_shape)
    else:
        response = client.messages.create(**request)
    if response.stop_reason == "max_tokens":
        sys.exit("Claude's answer was cut off. Raise max_tokens in ask() in generate.py and run again.")
    if answer_shape:
        return response.parsed_output
    return "".join(block.text for block in response.content if block.type == "text")

def describe_request(args) -> str:
    level = RULES["levels"][args.level]
    return f"""## The request
    - Course: {args.course}
    - Topic: {args.topic}
    - Level: {args.level} ({level['name']})
    - Time limit: {level['time']}
    - Functions to implement: {level['functions']}
    - Guidance: {level['guidance']}
    - Trap: {level['trap']}
    - Domain hint: {args.description or "none; choose a fitting, slightly unusual domain"}
    - Tech stack: {args.stack or "whatever the topic needs"}"""


# ---------- the 4 steps ----------

def brainstorm(args) -> list[Idea]:
    n = RULES["ideas_per_run"]
    prompt = f"""{describe_request(args)}

    Propose {n} clearly different problem ideas for this request. For each idea give a fictional organisation and
    its AI feature, the functions the candidate implements in main.py, one trap, and how hidden tests grade it.

    Trap ideas you may use or adapt:
    {bullets(RULES['trap_ideas'])}

    Avoid:
    {bullets(RULES['avoid'])}"""
    return ask(prompt, Ideas).ideas[:n]


def pick(args, ideas: list[Idea]) -> Idea:
    listing = "\n\n".join(f"### Idea {i}\n{idea.model_dump_json(indent=2)}" for i, idea in enumerate(ideas, 1))
    prompt = f"""{describe_request(args)}

    Pick the best idea. Judge strictly on:
    - fits the level (guidance, number of functions, time)
    - can be graded automatically with exact return values (mocked model replies if it calls an LLM)
    - makes the candidate practise the topic
    - has a trap that a naive solution quietly gets wrong
    - realistic and original
    {listing}"""

    choice = ask(prompt, Pick)
    return ideas[min(max(choice.best, 1), len(ideas)) - 1]


def write(args, idea: Idea, feedback: list[str] | None = None, previous: str = "") -> str:
    examples = "\n\n".join(f"### Example: {name}\n{text}" for name, text in EXAMPLES.items())
    prompt = f"""{describe_request(args)}

    ## The chosen idea
    {idea.model_dump_json(indent=2)}

    ## Write the problem statement
    Fill in this template. Replace every <...> part. Keep every [[...]] marker exactly as written; the script
    replaces them with fixed text. Use exactly one of the setup markers. Length: {level_words(args)} words.

    {RULES['template']}

    Match the tone and level of detail of these reference problems, but do not reuse their scenarios:

    {examples}

    Return only the Markdown statement."""

    if feedback:
        prompt += (f"\n\n## Fix these problems in your previous draft\n{bullets(feedback)}"
                   f"\n\n## Previous draft\n{previous}")
    return strip_fence(ask(prompt))


def check(args, statement: str) -> list[str]:
    problems = []

    # Code checks: sections in the right order, markers present, length
    headings = [line.replace("’", "'") for line in statement.splitlines() if line.startswith("## ")]
    positions = [next((i for i, h in enumerate(headings) if name in h), -1) for name in RULES["sections"]]
    if -1 in positions or positions != sorted(positions):
        problems.append(f"Sections must all appear as ## headings, in this order: {', '.join(RULES['sections'])}.")
    for marker in ["[[INSTRUCTIONS]]", "[[HOW_TO_EVALUATE]]"]:
        if statement.count(marker) != 1:
            problems.append(f"The marker {marker} must appear exactly once.")
    setup_markers = ["[[OPENAI_SETUP]]", "[[OPENAI_EMBEDDINGS_SETUP]]", "[[OFFLINE_SETUP]]"]
    if sum(statement.count(m) for m in setup_markers) != 1:
        problems.append(f"Use exactly one setup marker: {', '.join(setup_markers)}.")
    low, high = RULES["levels"][args.level]["words"]
    words = len(re.findall(r"\w+", fill_fixed_text(statement)))
    if not low * 0.9 <= words <= high * 1.1:
        problems.append(f"The statement is {words} words; aim for {low}-{high}.")


    prompt = f"""{describe_request(args)}

            You are a {args.level} candidate reading this problem statement. List only real problems:
            - anything you would have to ask before you could write code that the hidden tests accept
            (unclear return keys, values, casing, rounding, order, or behaviour on bad input)
            - anything that gives away the trap more than the level allows
            - contradictions, or requirements that can't be checked automatically
            Return an empty list if there are none.

            {statement}"""
    return problems + ask(prompt, Review, max_tokens=8000).problems


def fill_fixed_text(statement: str) -> str:
    for name, text in RULES["fixed_text"].items():
        statement = statement.replace(f"[[{name}]]", text.strip())
    return statement


# ---------- small helpers ----------

def bullets(items) -> str:
    return "\n".join(f"- {item}" for item in items)


def level_words(args) -> str:
    low, high = RULES["levels"][args.level]["words"]
    return f"{low}-{high}"


def strip_fence(text: str) -> str:
    """Remove a ```markdown fence if Claude wrapped the whole answer in one."""
    text = text.strip()
    match = re.fullmatch(r"```(?:markdown|md)?\n(.*)\n```", text, flags=re.DOTALL)
    return match.group(1).strip() if match else text


def save(args, statement: str) -> Path:
    title = re.search(r"^# (.+)$", statement, flags=re.MULTILINE)
    slug = re.sub(r"[^a-z0-9]+", "_", (title.group(1) if title else args.topic).lower()).strip("_")
    path = HERE / "output" / f"{datetime.datetime.now():%Y%m%d-%H%M}_{args.level}_{slug}.md"
    path.parent.mkdir(exist_ok=True)
    path.write_text(statement + "\n", encoding="utf-8")
    return path


# ---------- run ----------

def main():
    global client
    parser = argparse.ArgumentParser(description="Generate an assessment problem statement.")
    parser.add_argument("--course", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--level", required=True, choices=sorted(RULES["levels"]))
    parser.add_argument("--description", default="", help="optional hint about the domain")
    parser.add_argument("--stack", default="", help="optional tech stack, e.g. python,ragas")
    args = parser.parse_args()

    load_dotenv(HERE / ".env")
    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and paste your key into it.")
    client = Anthropic()

    print("1/4 Brainstorming ideas...")
    ideas = brainstorm(args)
    for i, idea in enumerate(ideas, 1):
        print(f"    {i}. {idea.title} ({idea.organisation})")

    print("2/4 Picking the best idea...")
    idea = pick(args, ideas)
    print(f"    -> {idea.title}")

    print("3/4 Writing the statement...")
    statement = write(args, idea)

    print("4/4 Checking it...")
    problems = check(args, statement)
    if problems:
        print(f"    {len(problems)} problem(s) found, rewriting once:")
        print(bullets(problems))
        statement = write(args, idea, feedback=problems, previous=statement)
        problems = check(args, statement)

    path = save(args, fill_fixed_text(statement))
    print(f"\nSaved: {path}")
    if problems:
        print("Check if these problems still need to be addressed:")
        print(bullets(problems))


if __name__ == "__main__":
    main()
