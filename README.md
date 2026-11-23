# Problem Statement Generator

Give it a course, a topic and a level. It picks a technology area and platform (or uses yours), researches real,
recent cases, brainstorms varied problems and writes the best one in our house format
(Description → Instructions → Objective → Concepts → Your Task → Environment Setup → How to Run → How to Evaluate).

## How it works

0. **Choose**: area (e.g. RAG, guardrails, Bedrock Knowledge Bases) and platform (offline, openai, aws).
   Given with `--area` / `--platform`, otherwise picked at random from `rules.yaml`.
   Areas naming Bedrock, SageMaker or AWS always use the aws platform.
1. **Research**: Claude lists the area's key concepts and common mistakes and writes web searches;
   Tavily finds a few recent real cases (only short snippets are kept).
2. **Brainstorm**: 5 ideas, each based on a real case, each with a different task shape and material
   (tables, JSONL, documents, logs, transcripts, images, config files).
3. **Pick**: the most interesting idea that tests the key concepts, fits the level and is doable in time and budget.
4. **Write**: Claude writes the statement from the template and style guide.
5. **Check**: the script checks sections and length; Claude reads it as a candidate. Blocking issues trigger one rewrite.

The script inserts the fixed text: Instructions, the platform's setup block (offline / OpenAI proxy / AWS account), and How to Evaluate.

## Files

| File | What it is |
|---|---|
| `generate.py` | The whole program: the steps and their prompts |
| `rules.yaml` | Everything you might change: models, search limits, levels, areas, platforms and their setup text, materials, task shapes, style guide, template, fixed text |
| `output/` | Generated statements |
| `output/sources/` | One `_sources.md` per statement for reviewers: area, platform, real case used, concepts, trap, how it is graded |

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
python generate.py --course "Generative AI Engineering" --topic "Retrieval-augmented generation" --level L2
python generate.py --course "Generative AI Engineering" --topic "Guardrails" --level L3 --platform aws --area "Bedrock guardrails for a claims assistant"
python generate.py --course "Applied LLMs" --topic "Fine-tuning" --level L2 --platform offline --area "Fine-tuning data preparation"
```

A run takes 2-4 minutes and costs roughly $0.15-$0.25, plus 3 Tavily searches.
