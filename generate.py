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


class Issue(BaseModel):
    text: str
    blocking: bool  

class Review(BaseModel):
    issues: list[Issue]        # empty if the statement is fine


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
    - Tech stack: {args.stack or "choose a fitting stack for the topic"}"""


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

    Match the tone and level of detail of these reference problems, but do not reuse their scenarios.
    They show the fixed text written out in full; do NOT copy it, write the [[...]] markers instead:

    {examples}

    Return only the Markdown statement."""

    if feedback:
        prompt += (f"\n\n## Fix these problems in your previous draft:\n{bullets(feedback)}"
                   f"\n\n## Previous draft:\n{previous}")
    return strip_fence(ask(prompt))


def check(args, statement: str) -> tuple[list[str], list[str]]:
    """Returns (blocking problems that trigger a rewrite, minor notes that are only printed)."""
    blocking = []

    # Code checks: sections in the right order, markers present, length
    headings = [line.replace("’", "'") for line in statement.splitlines() if line.startswith("## ")]
    positions = [next((i for i, h in enumerate(headings) if name in h), -1) for name in RULES["sections"]]
    if -1 in positions or positions != sorted(positions):
        blocking.append(f"Sections must all appear as ## headings, in this order: {', '.join(RULES['sections'])}.")


    setup_markers = ["[[OPENAI_SETUP]]", "[[OPENAI_EMBEDDINGS_SETUP]]", "[[OFFLINE_SETUP]]"]
    setup_written_out = "llmgateway-lms.tekstac.com" in statement or "no api key" in statement.lower() or "fully offline" in statement.lower()
    if sum(statement.count(m) for m in setup_markers) != 1 and not setup_written_out:
        blocking.append(f"Environment Setup needs exactly one setup marker: {', '.join(setup_markers)}.")
     
    finished = fill_fixed_text(statement)  # what the candidate will actually read
    low, high = RULES["levels"][args.level]["words"]
    words = len(re.findall(r"\w+", finished))
    if not low * 0.8 <= words <= high * 1.2:
        blocking.append(f"The statement is {words} words; aim for {low}-{high}.")

    # Claude check: read the finished statement as a candidate would
    prompt = f"""{describe_request(args)}
    You are reviewing this problem statement before it is given to {args.level} candidates.
    Mark an issue as blocking ONLY if one of these is true:
    - a candidate cannot know an exact return value, key, type, casing, rounding or order that the hidden tests check
    - the statement gives away the trap more than the level allows
    - the statement contradicts itself
    Everything else is not blocking: wording, style, suggestions, nice-to-have extra detail.
    Things the level deliberately leaves to the candidate (see Guidance above) are NOT issues at all.
    Fixed boilerplate (Instructions, OpenAI configuration, How to Evaluate) is correct; ignore it.
    Return an empty list if there are no issues.
    {finished}"""

    issues = ask(prompt, Review, max_tokens=8000).issues
    blocking += [i.text for i in issues if i.blocking]
    notes = [i.text for i in issues if not i.blocking]
    return blocking, notes


def fill_fixed_text(statement: str) -> str:
    for name, text in RULES["fixed_text"].items():
        statement = statement.replace(f"[[{name}]]", text.strip())
    statement = replace_section(statement, "Instructions", RULES["fixed_text"]["INSTRUCTIONS"])
    statement = replace_section(statement, "How to Evaluate", RULES["fixed_text"]["HOW_TO_EVALUATE"])
    return statement.strip()


def replace_section(statement: str, heading: str, body: str) -> str:
    """Replace the text under the '## ... <heading>' line, up to the next '## ' heading, with body."""
    pattern = rf"(^## [^\n]*{re.escape(heading)}[^\n]*\n)(.*?)(?=^## |\Z)"
    return re.sub(pattern, lambda m: m.group(1) + "\n" + body.strip() + "\n\n", statement,
                  count=1, flags=re.MULTILINE | re.DOTALL)


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
    parser = argparse.ArgumentParser(description="Generate a problem statement.")
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

    print("4/4 Checking...")
    blocking, notes = check(args, statement)
    if blocking:
        print(f"    {len(blocking)} blocking problem(s) found, rewriting once:")
        print(bullets(blocking))
        statement = write(args, idea, feedback=blocking, previous=statement)
        blocking, notes = check(args, statement)
    else:
        print("    No blocking problems.")

    path = save(args, fill_fixed_text(statement))
    print(f"\nSaved: {path}")
    if blocking:
        print(f"Still {len(blocking)} blocking found, check these before using:")
        print(bullets(blocking))
    if notes:
        print("Minor notes (optional):")
        print(bullets(notes))

if __name__ == "__main__":
    main()
