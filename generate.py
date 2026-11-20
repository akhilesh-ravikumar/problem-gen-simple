"""Generate an assessment problem statement in the format.

    python generate.py --course "LLM Evaluation methods and frameworks" --topic "LLM-as-judge" --level L2
    (optional)  --description "an insurance claims assistant"  --stack "python,openai"

Five steps:
    1. Research    - Claude lists the topic's key concepts and common mistakes; Tavily finds real, niche cases
    2. Brainstorm  - Claude proposes several different ideas, each grounded in a real case
    3. Pick        - Claude scores them and picks the best one
    4. Write       - Claude writes the statement in the house format
    5. Check       - code + Claude check it; if anything is wrong, step 4 rewrites it once
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
from tavily import TavilyClient

HERE = Path(__file__).parent
RULES = yaml.safe_load((HERE / "rules.yaml").read_text(encoding="utf-8"))
EXAMPLES = {p.stem: p.read_text(encoding="utf-8") for p in sorted((HERE / "examples").glob("*.md"))}

SYSTEM = """You design hands-on programming problems that assess employees and candidates on one course topic.
The candidate gets a small template project and completes TODO blocks: functions, class methods, a command,
or fixes across a few files. Hidden tests grade the result automatically, so every piece needs a fixed name or
signature and an exact expected output (types, keys, allowed values, casing, rounding, order). If the code calls
an LLM, the tests replace the model with scripted replies, so grading never depends on what a real model says.
Great problems feel like a real job: a specific, slightly unusual organisation, a believable situation drawn
from how this topic is used in the real world, TODOs that are satisfying to solve, and a trap that a naive
solution quietly gets wrong."""

# ---------- the shapes of Claude's answers ----------

class Research(BaseModel):
    key_concepts: list[str]    # the most important concepts this topic tests
    common_mistakes: list[str] # mistakes practitioners really make with this topic (trap material)
    queries: list[str]         # web searches for real, niche situations where the topic matters


class Idea(BaseModel):
    title: str
    organisation: str          # fictional, e.g. "CareWell Pharmacy"
    real_world_basis: str      # the real case it is inspired by, and its source URL if any
    scenario: str              # who is affected, what goes wrong, what it costs
    task_shape: str            # one of the task shapes in rules.yaml
    concepts_tested: list[str] # which key concepts solving it requires
    tasks: list[str]           # the TODOs, e.g. "reconcile(shipments, payments) -> list of mismatches"
    setup: str                 # "offline", "openai", "openai + embeddings", or what else is needed
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


client = None
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
        sys.exit("Claude's answer was cut off. Raise max_tokens in ask() in generate.py and run again.")
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
                                            search_depth="basic", include_answer=False,
                                            include_raw_content=False)
        except Exception as error:  # a failed search should not stop the run
            print(f"    search failed for '{query}': {error}")
            continue
        for r in response.get("results", []):
            if r["url"] not in found or r.get("score", 0) > found[r["url"]].get("score", 0):
                found[r["url"]] = r
    best = sorted(found.values(), key=lambda r: r.get("score", 0), reverse=True)[: settings["max_results"]]
    return [{"title": r["title"], "url": r["url"], "content": shorten(r["content"], settings["snippet_chars"])}
            for r in best]

def describe_request(args) -> str:
    level = RULES["levels"][args.level]
    return f"""## The request
    - Course: {args.course}
    - Topic: {args.topic}
    - Level: {args.level} ({level['name']})
    - Time limit: {level['time']}
    - Tasks to implement: {level['tasks']}
    - Guidance: {level['guidance']}
    - Trap: {level['trap']}
    - Domain hint: {args.description or "none; choose a fitting, slightly unusual domain"}
    - Tech stack: {args.stack or "choose a fitting stack for the topic"}"""


# ---------- the 5 steps ----------
def research(args) -> tuple[Research, list[dict]]:
    prompt = f"""{describe_request(args)}

    Before anyone designs a problem for this topic, prepare the ground:
    - key_concepts: the 4-8 concepts that matter most when this topic is used in real work
    (what an expert would check first), not textbook trivia
    - common_mistakes: 5-8 mistakes practitioners really make with this topic
    - queries: {RULES['search']['queries']} web searches that would find REAL, specific, slightly unusual situations
    where this topic matters: incidents, postmortems, case studies, regulator findings, niche industry uses.
    Make each query specific (an industry + a concrete problem), not generic like "{args.topic} examples"."""

    found = ask(prompt, "research", Research)
    return found, web_search(found.queries)


def brainstorm(args, found: Research, sources: list[dict]) -> list[Idea]:
    n = RULES["ideas_per_run"]
    cases = "\n\n".join(f"[{i}] {s['title']} ({s['url']})\n{s['content']}" for i, s in enumerate(sources, 1))
    prompt = f"""{describe_request(args)}

    ## Key concepts of this topic
    {bullets(found.key_concepts)}

    ## Mistakes practitioners really make
    {bullets(found.common_mistakes)}

    ## Real-world cases found on the web
    {cases or "(no search results; draw on real situations you know of)"}

    ## Task shapes (use a DIFFERENT one for each idea)
    {bullets(RULES['task_shapes'])}

    Propose {n} clearly different problem ideas. Each idea must:
    - be inspired by a real situation (one of the cases above where possible; give its URL in real_world_basis),
    moved to a fictional organisation in a specific, slightly unusual industry
    - require at least two key concepts to solve
    - have TODOs that are satisfying to work on: the candidate discovers something, not just fills in boilerplate
    - have one trap drawn from the mistakes above (or these examples):
    {bullets(RULES['trap_ideas'])}
    - be gradeable by hidden tests with exact expected outputs (scripted model replies if it calls an LLM)

    Avoid:
    {bullets(RULES['avoid'])}"""
    return ask(prompt, "brainstorm", Ideas).ideas[:n]


def pick(args, ideas: list[Idea]) -> Idea:
    listing = "\n\n".join(f"### Idea {i}\n{idea.model_dump_json(indent=2)}" for i, idea in enumerate(ideas, 1))
    prompt = f"""{describe_request(args)}

    Pick the best idea. Judge strictly, in this order:
    1. interesting: a real-feeling situation and TODOs a candidate would enjoy; not generic
    2. tests the topic's most important concepts
    3. has a trap that a naive solution quietly gets wrong
    4. fits the level (guidance, amount of work, time)
    5. can be graded automatically with exact expected outputs

    {listing}"""
    choice = ask(prompt, "pick", Pick)
    return ideas[min(max(choice.best, 1), len(ideas)) - 1]


def write(args, idea: Idea, feedback: list[str] | None = None, previous: str = "") -> str:
    examples = "\n\n".join(f"### Example: {name}\n{text}" for name, text in EXAMPLES.items())
    prompt = f"""{describe_request(args)}

    ## The chosen idea
    {idea.model_dump_json(indent=2)}

    ## Write the problem statement
    Fill in this template. Replace every <...> part. Keep every [[...]] marker exactly as written; the script
    replaces them with fixed text. Length: {level_words(args)} words.

    {RULES['template']}

    Make it vivid and specific:
    - The Objective tells a short, concrete story: a named organisation, the people involved, real numbers,
    what went wrong and what it cost. The real case inspires it; never name the real company.
    - Your Task describes TODOs that feel like real work on a real codebase, in the shape the idea needs.
    Names, signatures and expected outputs must be exact, so hidden tests can grade them.
    - The Concepts section names the topic's key concepts this problem really exercises.

    ## Reference problems (format and level of detail only)
    These all come from one course and share one shape. Use them only for the section format, tone and how
    exact the contracts are. Your task shape, domain and setup should be your own. They show the fixed text
    written out in full; do NOT copy it, write the [[...]] markers instead.

    {examples}

    Return only the Markdown statement."""

    if feedback:
        prompt += (f"\n\n## Fix these problems in your previous draft\n{bullets(feedback)}"
                   f"\n\n## Previous draft\n{previous}")
    return strip_fence(ask(prompt, "write"))


def check(args, statement: str) -> tuple[list[str], list[str]]:
    """Returns (blocking problems that trigger a rewrite, minor notes that are only printed)."""
    blocking = []

    # Code checks: sections in the right order, markers present, length
    headings = [line.replace("’", "'") for line in statement.splitlines() if line.startswith("## ")]
    positions = [next((i for i, h in enumerate(headings) if name in h), -1) for name in RULES["sections"]]
    if -1 in positions or positions != sorted(positions):
        blocking.append(f"Sections must all appear as ## headings, in this order: {', '.join(RULES['sections'])}.")

    setup = section_text(statement, "Environment Setup")
    openai_marker = "[[OPENAI_SETUP]]" in setup or "[[OPENAI_EMBEDDINGS_SETUP]]" in setup
    if "openai" in re.sub(r"\[\[\w+\]\]", "", setup).lower() and not openai_marker:
        blocking.append("Environment Setup describes OpenAI access itself; use [[OPENAI_SETUP]] or "
                        "[[OPENAI_EMBEDDINGS_SETUP]] instead, so the proxy details are always correct.")

    finished = fill_fixed_text(statement)  # what the candidate will actually read
    low, high = RULES["levels"][args.level]["words"]
    words = len(re.findall(r"\w+", finished))
    if not low * 0.8 <= words <= high * 1.2:
        blocking.append(f"The statement is {words} words; aim for {low}-{high}.")

    # Claude check: read the finished statement as a candidate would
    prompt = f"""{describe_request(args)}
    You are reviewing this problem statement before it is given to {args.level} candidates.
    Mark an issue as blocking ONLY if one of these is true:
    - a candidate cannot know an exact name, signature, output, type, casing, rounding or order that the hidden tests check
    - the statement gives away the trap more than the level allows
    - the statement contradicts itself
    Everything else is not blocking: wording, style, suggestions, nice-to-have extra detail.
    Things the level deliberately leaves to the candidate (see Guidance above) are NOT issues at all.
    Fixed boilerplate (Instructions, OpenAI configuration, How to Evaluate) is correct; ignore it.
    Return an empty list if there are no issues.
    {finished}"""

    issues = ask(prompt, "check", Review, max_tokens=8000).issues
    blocking += [i.text for i in issues if i.blocking]
    notes = [i.text for i in issues if not i.blocking]
    return blocking, notes


def fill_fixed_text(statement: str) -> str:
    for name, text in RULES["fixed_text"].items():
        statement = statement.replace(f"[[{name}]]", text.strip())
    statement = replace_section(statement, "Instructions", RULES["fixed_text"]["INSTRUCTIONS"])
    statement = replace_section(statement, "How to Evaluate", RULES["fixed_text"]["HOW_TO_EVALUATE"])
    return statement.strip()

def section_text(statement: str, heading: str) -> str:
    """The text under the '## ... <heading>' line, up to the next '## ' heading."""
    match = re.search(rf"^## [^\n]*{re.escape(heading)}[^\n]*\n(.*?)(?=^## |\Z)", statement,
                      flags=re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""

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

    ## Inspired by
    {idea.real_world_basis}

    ## Concepts tested
    {bullets(idea.concepts_tested)}

    ## Trap
    {idea.trap}

    ## Key concepts found for the topic
    {bullets(found.key_concepts)}

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
    parser.add_argument("--description", default="", help="optional hint about the domain")
    parser.add_argument("--stack", default="", help="optional tech stack, e.g. python,ragas")
    args = parser.parse_args()

    load_dotenv(HERE / ".env")
    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and paste your key into it.")
    client = Anthropic()
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    if tavily_key and not tavily_key.endswith("..."):  # skip the placeholder from .env.example
        search_client = TavilyClient(api_key=tavily_key)
    else:
        print("(TAVILY_API_KEY not set: running without web search)")

    print("1/5 Researching the topic and searching the web...")
    found, sources = research(args)
    print(f"    key concepts: {', '.join(found.key_concepts)}")
    snippet_tokens = sum(len(s["title"]) + len(s["url"]) + len(s["content"]) for s in sources) // 4
    print(f"    {len(sources)} results kept for Claude (~{snippet_tokens} tokens)")

    print("2/5 Brainstorming ideas...")
    ideas = brainstorm(args, found, sources)
    for i, idea in enumerate(ideas, 1):
        print(f"    {i}. {idea.title} ({idea.organisation})")

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

    path, sources_path = save(args, fill_fixed_text(statement), found, sources, idea)
    print(f"\nSaved: {path}")
    print(f"Sources: {sources_path}")
    if blocking:
        print(f"Still {len(blocking)} blocking found, check these before using:")
        print(bullets(blocking))
    if notes:
        print("Minor notes (optional):")
        print(bullets(notes))

if __name__ == "__main__":
    main()
