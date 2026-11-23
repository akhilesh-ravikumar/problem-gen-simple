"""Generate an assessment problem statement in the house format.

    python generate.py --course "Generative AI Engineering" --topic "Retrieval-augmented generation" --level L2
    (optional)  --platform aws|openai|offline   --area "prompt caching"
                --description "an insurance claims assistant"   --stack "python,boto3"

Five steps:
    1. Research    - Claude lists the area's key concepts and common mistakes; Tavily finds real, recent cases
    2. Brainstorm  - Claude proposes several different ideas, each grounded in a real case
    3. Pick        - Claude scores them and picks the best one
    4. Write       - Claude writes the statement in the house format
    5. Check       - code + Claude check it; if anything is wrong, step 4 rewrites it once
"""

import argparse
import datetime
import os
import random
import re
import sys
from pathlib import Path

import yaml
from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from tavily import TavilyClient

HERE = Path(__file__).parent
RULES = yaml.safe_load((HERE / "rules.yaml").read_text(encoding="utf-8"))

SYSTEM = """You design hands-on assessment problems in AI and Generative AI for employees and candidates.
The candidate gets a small project and completes TODO work: code, configuration or cloud resources.
Hidden tests grade the result automatically, so every piece needs an exact name and an exact expected output
(types, keys, allowed values, casing, rounding, order). If the code calls a model, grading never depends on
the model's wording: tests use scripted replies or check structure.
Great problems feel like a real job: a specific, slightly unusual organisation, a believable situation drawn
from how this technology is really used, work that is satisfying to do, and a trap that a naive solution
quietly gets wrong."""


# ---------- the shapes of Claude's answers ----------

class Research(BaseModel):
    key_concepts: list[str]    # the most important concepts for this area
    common_mistakes: list[str] # mistakes practitioners really make (trap material)
    queries: list[str]         # web searches for real, recent, niche situations


class Idea(BaseModel):
    title: str
    organisation: str          # fictional, e.g. "CareWell Pharmacy"
    real_world_basis: str      # the real case it is inspired by, and its source URL if any
    scenario: str              # who is affected, what goes wrong, what it costs
    task_shape: str            # one of the task shapes in rules.yaml
    material: str              # one of the materials in rules.yaml
    concepts_tested: list[str] # which key concepts solving it requires
    tasks: list[str]           # the TODO work, each with an exact name
    trap: str                  # what a naive solution gets wrong
    how_graded: str            # how hidden tests check it deterministically


class Ideas(BaseModel):
    ideas: list[Idea]


class Pick(BaseModel):
    best: int                  # 1-based number of the chosen idea
    reason: str


class Issue(BaseModel):
    text: str
    blocking: bool             # True only if it must be fixed before the problem can be used


class Review(BaseModel):
    issues: list[Issue]        # empty if the statement is fine


# ---------- talking to Claude and Tavily ----------

client = None   # created in main(), after .env is loaded
search_client = None


def ask(prompt: str, step: str, answer_shape=None, max_tokens: int = 16000):
    """Send one prompt to Claude using the step's model. With answer_shape, get back a filled-in object."""
    request = dict(model=RULES["models"][step], max_tokens=max_tokens, system=SYSTEM,
                   messages=[{"role": "user", "content": prompt}])
    if answer_shape:
        try:
            response = client.messages.parse(**request, output_format=answer_shape)
        except ValidationError:  # the JSON answer was cut off or malformed
            sys.exit(f"Claude's answer in the {step} step was cut off or malformed. Raise max_tokens and retry.")
    else:
        response = client.messages.create(**request)
    if response.stop_reason == "max_tokens":
        sys.exit(f"Claude's answer in the {step} step was cut off. Raise max_tokens in ask() and run again.")
    if answer_shape:
        return response.parsed_output
    return "".join(block.text for block in response.content if block.type == "text")


def web_search(queries: list[str]) -> list[dict]:
    """Run the queries on Tavily and keep only the most relevant few, as short snippets.

    Returns at most search.max_results items of {title, url, content}; empty if search is switched off.
    """
    if search_client is None:
        return []
    settings = RULES["search"]
    found = {}
    for query in queries[: settings["queries"]]:
        try:
            response = search_client.search(query=query, max_results=settings["results_per_query"],
                                            search_depth="basic", time_range="year",
                                            include_answer=False, include_raw_content=False)
        except Exception as error:  # a failed search should not stop the run
            print(f"    search failed for '{query}': {error}")
            continue
        for r in response.get("results", []):
            if r["url"] not in found or r.get("score", 0) > found[r["url"]].get("score", 0):
                found[r["url"]] = r
    best = sorted(found.values(), key=lambda r: r.get("score", 0), reverse=True)[: settings["max_results"]]
    return [{"title": r["title"], "url": r["url"], "content": shorten(r["content"], settings["snippet_chars"])}
            for r in best]


def choose_area_and_platform(args) -> None:
    """Fill in --area and --platform when they were not given."""
    if not args.area:
        args.area = random.choice(RULES["areas"])
    if not args.platform:
        aws_area = any(word in args.area for word in ("Bedrock", "SageMaker", "AWS"))
        args.platform = "aws" if aws_area else random.choice(list(RULES["platforms"]))


def describe_request(args) -> str:
    level = RULES["levels"][args.level]
    return f"""## The request
- Course: {args.course}
- Topic: {args.topic}
- Technology area: {args.area}
- Platform: {args.platform} - {RULES['platforms'][args.platform]['description']}
- Level: {args.level} ({level['name']})
- Work to do: {level['tasks']}
- Guidance: {level['guidance']}
- Trap: {level['trap']}
- Domain hint: {args.description or "none; choose a fitting, slightly unusual domain"}
- Tech stack: {args.stack or "choose a fitting stack for the area and platform"}"""


# ---------- the 5 steps ----------

def research(args) -> tuple[Research, list[dict]]:
    prompt = f"""{describe_request(args)}

Before anyone designs a problem, prepare the ground for this technology area on this platform:
- key_concepts: the 4-8 concepts that matter most when this area is used in real work
  (what an expert would check first), not textbook trivia
- common_mistakes: 5-8 mistakes practitioners really make in this area
- queries: {RULES['search']['queries']} web searches that would find REAL, recent, specific situations where
  this area matters on this platform: incidents, postmortems, case studies, launch posts, niche industry uses.
  Make each query specific (an industry + a concrete problem), not generic."""
    found = ask(prompt, "research", Research)
    return found, web_search(found.queries)


def brainstorm(args, found: Research, sources: list[dict]) -> list[Idea]:
    n = RULES["ideas_per_run"]
    cases = "\n\n".join(f"[{i}] {s['title']} ({s['url']})\n{s['content']}" for i, s in enumerate(sources, 1))
    prompt = f"""{describe_request(args)}

## Key concepts of this area
{bullets(found.key_concepts)}

## Mistakes practitioners really make
{bullets(found.common_mistakes)}

## Real-world cases found on the web
{cases or "(no search results; draw on real situations you know of)"}

## Task shapes
{bullets(RULES['task_shapes'])}

## Materials
{bullets(RULES['materials'])}

Propose {n} clearly different problem ideas. Give each idea a DIFFERENT task shape and a DIFFERENT material.
Each idea must:
- be inspired by a real situation (one of the cases above where possible; give its URL in real_world_basis),
  moved to a fictional organisation in a specific, slightly unusual industry
- require at least two key concepts to solve
- be satisfying to work on: the candidate discovers something, not just fills in boilerplate
- have a trap drawn from the mistakes above
- be gradeable automatically with exact expected outputs (for AWS: the grader inspects the account)
- if using AWS, stay within a small budget (smallest instances, no long-running jobs)

Avoid:
{bullets(RULES['avoid'])}"""
    return ask(prompt, "brainstorm", Ideas).ideas[:n]


def pick(args, ideas: list[Idea]) -> Idea:
    listing = "\n\n".join(f"### Idea {i}\n{idea.model_dump_json(indent=2)}" for i, idea in enumerate(ideas, 1))
    prompt = f"""{describe_request(args)}

Pick the best idea. Judge strictly, in this order:
1. interesting: a real-feeling situation and work a candidate would enjoy; not generic
2. tests the area's most important concepts
3. has a trap that a naive solution quietly gets wrong
4. fits the level (and, on AWS, stays within a small budget)
5. can be graded automatically with exact expected outputs

{listing}"""
    choice = ask(prompt, "pick", Pick)
    return ideas[min(max(choice.best, 1), len(ideas)) - 1]


def write(args, idea: Idea, feedback: list[str] | None = None, previous: str = "") -> str:
    prompt = f"""{describe_request(args)}

## The chosen idea
{idea.model_dump_json(indent=2)}

## Write the problem statement
Fill in this template. Replace every <...> part. Keep every [[...]] marker exactly as written; the script
replaces them with fixed text. Length: {level_words(args)} words.

{RULES['template']}

## Style guide
{bullets(RULES['style_guide'])}

Return only the Markdown statement."""
    if feedback:
        prompt += (f"\n\n## Fix these problems in your previous draft\n{bullets(feedback)}"
                   f"\n\n## Previous draft\n{previous}")
    return strip_fence(ask(prompt, "write"))


def check(args, statement: str) -> tuple[list[str], list[str]]:
    """Returns (blocking problems that trigger a rewrite, minor notes that are only printed)."""
    blocking = []

    # Code checks: sections in the right order, length
    headings = [line.replace("’", "'") for line in statement.splitlines() if line.startswith("## ")]
    positions = [next((i for i, h in enumerate(headings) if name in h), -1) for name in RULES["sections"]]
    if -1 in positions or positions != sorted(positions):
        blocking.append(f"Sections must all appear as ## headings, in this order: {', '.join(RULES['sections'])}.")

    finished = fill_fixed_text(args, statement)  # what the candidate will actually read
    low, high = RULES["levels"][args.level]["words"]
    words = len(re.findall(r"\w+", finished))
    if not low * 0.8 <= words <= high * 1.2:
        blocking.append(f"The statement is {words} words; aim for {low}-{high}.")

    # Claude check: read the finished statement as a candidate would
    prompt = f"""{describe_request(args)}

You are reviewing this problem statement before it is given to {args.level} candidates.
Mark an issue as blocking ONLY if one of these is true:
- a candidate cannot know an exact name, signature, resource setting, output, type, casing, rounding or order
  that the hidden tests (or, on AWS, the account inspection) check
- the statement gives away the trap more than the level allows
- the statement contradicts itself
Everything else is not blocking: wording, style, suggestions, nice-to-have extra detail.
Things the level deliberately leaves to the candidate (see Guidance above) are NOT issues at all.
Fixed boilerplate (Instructions, the platform configuration, How to Evaluate) is correct; ignore it.
Return an empty list if there are no issues.

{finished}"""
    issues = ask(prompt, "check", Review, max_tokens=8000).issues
    blocking += [i.text for i in issues if i.blocking]
    notes = [i.text for i in issues if not i.blocking]
    return blocking, notes


def fill_fixed_text(args, statement: str) -> str:
    """Insert the fixed text: the platform setup, Instructions and How to Evaluate."""
    setup = RULES["platforms"][args.platform]["setup"].strip()
    if "[[SETUP]]" in statement:
        statement = statement.replace("[[SETUP]]", setup)
    else:  # Claude left the marker out: add the setup at the end of Environment Setup
        statement = re.sub(r"^## How to Run", lambda m: setup + "\n\n" + m.group(0), statement,
                           count=1, flags=re.MULTILINE)
    statement = replace_section(statement, "Instructions", RULES["fixed_text"]["INSTRUCTIONS"])
    statement = replace_section(statement, "How to Evaluate", RULES["fixed_text"]["HOW_TO_EVALUATE"])
    return statement.strip()


def replace_section(statement: str, heading: str, body: str) -> str:
    """Replace the text under the '## ... <heading>' line, up to the next '## ' heading, with body."""
    pattern = rf"(^## [^\n]*{re.escape(heading)}[^\n]*\n)(.*?)(?=^## |\Z)"
    return re.sub(pattern, lambda m: m.group(1) + "\n" + body.strip() + "\n\n", statement,
                  count=1, flags=re.MULTILINE | re.DOTALL)


# ---------- small helpers ----------

def shorten(text: str, limit: int) -> str:
    """Cut text to at most `limit` characters, at a word boundary."""
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


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


def save(args, statement: str, found: Research, sources: list[dict], idea: Idea) -> tuple[Path, Path]:
    """Save the statement in output/, and a _sources.md for reviewers in output/sources/."""
    title = re.search(r"^# (.+)$", statement, flags=re.MULTILINE)
    slug = re.sub(r"[^a-z0-9]+", "_", (title.group(1) if title else args.topic).lower()).strip("_")
    name = f"{datetime.date.today():%Y%m%d}_{args.level}_{slug}"
    path = HERE / "output" / f"{name}.md"
    sources_path = HERE / "output" / "sources" / f"{name}_sources.md"
    sources_path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(statement + "\n", encoding="utf-8")

    found_list = "\n".join(f"- [{s['title']}]({s['url']})" for s in sources) or "- (search was off)"
    sources_path.write_text(f"""# Sources for {title.group(1) if title else slug}

- Area: {args.area}
- Platform: {args.platform}
- Task shape: {idea.task_shape}
- Material: {idea.material}

## Inspired by
{idea.real_world_basis}

## Concepts tested
{bullets(idea.concepts_tested)}

## Trap
{idea.trap}

## How it is graded
{idea.how_graded}

## Searches
{bullets(found.queries)}

## Pages found
{found_list}
""", encoding="utf-8")
    return path, sources_path


# ---------- run ----------

def main():
    global client, search_client
    parser = argparse.ArgumentParser(description="Generate a problem statement.")
    parser.add_argument("--course", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--level", required=True, choices=sorted(RULES["levels"]))
    parser.add_argument("--platform", choices=sorted(RULES["platforms"]), help="optional; random if not given")
    parser.add_argument("--area", default="", help="optional technology area; random from rules.yaml if not given")
    parser.add_argument("--description", default="", help="optional hint about the domain")
    parser.add_argument("--stack", default="", help="optional tech stack, e.g. python,boto3")
    args = parser.parse_args()
    choose_area_and_platform(args)

    load_dotenv(HERE / ".env")
    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and paste your key into it.")
    client = Anthropic()
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    if tavily_key and not tavily_key.endswith("..."):  # skip the placeholder from .env.example
        search_client = TavilyClient(api_key=tavily_key)
    else:
        print("(TAVILY_API_KEY not set: running without web search)")

    print(f"Area: {args.area} | Platform: {args.platform}")
    print("1/5 Researching and searching the web...")
    found, sources = research(args)
    snippet_tokens = sum(len(s["title"]) + len(s["url"]) + len(s["content"]) for s in sources) // 4
    print(f"    key concepts: {', '.join(found.key_concepts)}")
    print(f"    {len(sources)} results kept for Claude (~{snippet_tokens} tokens)")

    print("2/5 Brainstorming ideas...")
    ideas = brainstorm(args, found, sources)
    for i, idea in enumerate(ideas, 1):
        print(f"    {i}. {idea.title} ({idea.organisation}) - {idea.material}")

    print("3/5 Picking the best idea...")
    idea = pick(args, ideas)
    print(f"    -> {idea.title}")
    print(f"       inspired by: {idea.real_world_basis}")

    print("4/5 Writing the statement...")
    statement = write(args, idea)

    print("5/5 Checking...")
    blocking, notes = check(args, statement)
    if blocking:
        print(f"    {len(blocking)} blocking problem(s) found, rewriting once:")
        print(bullets(blocking))
        statement = write(args, idea, feedback=blocking, previous=statement)
        blocking, notes = check(args, statement)
    else:
        print("    No blocking problems.")

    path, sources_path = save(args, fill_fixed_text(args, statement), found, sources, idea)
    print(f"\nSaved: {path}")
    print(f"Sources: {sources_path}")
    if blocking:
        print(f"Still {len(blocking)} blocking, check these before using:")
        print(bullets(blocking))
    if notes:
        print("Minor notes (optional):")
        print(bullets(notes))


if __name__ == "__main__":
    main()
