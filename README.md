# Problem Statement Generator

Give it a course, a topic and a level. It researches how the topic is used in the real world, brainstorms
original problems based on real cases, and writes the best one in our house format
(Description → Instructions → Objective → Concepts → Your Task → Environment Setup → How to Run → How to Evaluate).

## How it works

1. **Research**: Claude lists the topic's key concepts and the mistakes practitioners really make, then writes
   web searches for real, niche cases (incidents, case studies, unusual industry uses). Tavily runs them.
2. **Brainstorm**: Claude proposes 5 ideas. Each is based on a real case, uses a different task shape
   (fix a broken module, build a pipeline, write a validator...), tests key concepts and contains a trap.
3. **Pick**: Claude chooses the most interesting idea that tests the key concepts and fits the level.
4. **Write**: Claude writes the statement. The reference problems in `examples/` set the format, not the shape.
5. **Check**: the script checks sections, OpenAI setup and length; Claude reads it as a candidate.
   If anything is blocking, step 4 rewrites it once.

Fixed text (Instructions, OpenAI proxy setup, How to Evaluate) is inserted by the script, never written by Claude.

## Files

| File | What it is |
|---|---|
| `generate.py` | The whole program: the 5 steps and their prompts |
| `rules.yaml` | Everything you might change: models per step, search settings, levels, task shapes, trap ideas, template, fixed text |
| `examples/` | Reference problems for format and level of detail |
| `output/` | For each run: the statement `.md`, plus a `_sources.md` for reviewers (real cases used, concepts, trap) |

## Setup (Windows, once)

```powershell
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and paste your Anthropic key. For web search, also paste a Tavily key
(free at app.tavily.com, 1,000 searches a month). Without a Tavily key the generator still works, just without search.

## Run

```powershell
python generate.py --course "LLM Evaluation methods and frameworks" --topic "LLM-as-judge" --level L2
python generate.py --course "Data Engineering" --topic "Data validation" --level L3 --description "vaccine cold chain" --stack "python,pandas"
```

A run takes 2-4 minutes. Estimated cost: about $0.15-$0.25 in Claude tokens, plus 4 Tavily searches
(free within the monthly allowance, otherwise about $0.03).
