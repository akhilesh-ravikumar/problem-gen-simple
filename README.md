# Problem Statement Generator

Give it a course, a topic and a level. It writes a new hands-on problem statement in our house format
(Description → Instructions → Objective → Concepts → Your Task → Environment Setup → How to Run → How to Evaluate).

## How it works

1. **Brainstorm**: Claude proposes 5 different problem ideas for the course, topic and level.
2. **Pick**: Claude scores them (level fit, can be auto-graded, practises the topic, has a good trap) and picks one.
3. **Write**: Claude writes the statement from our template, imitating the 4 reference problems in `examples/`.
4. **Check**: the script checks sections, fixed text and length; Claude reads it as a candidate and lists anything unclear.
   If there are problems, step 3 rewrites it once.

Fixed text (Instructions, OpenAI proxy setup, How to Evaluate) is inserted by the script, never written by Claude.

## Files

| File | What it is |
|---|---|
| `generate.py` | The whole program: the 4 steps and the prompts |
| `rules.yaml` | Everything you might want to change: model, level rules, trap ideas, the template, the fixed text |
| `examples/` | The 4 reference problems Claude imitates |
| `output/` | Generated statements, one `.md` file per run |

## Setup (Windows, once)

1. Install Python 3.12+ from python.org (tick **Add python.exe to PATH**) and the **Python** extension in VS Code.
2. Open this folder in VS Code, then open a terminal (**Terminal → New Terminal**) and run:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

3. Open `.env` and paste your Anthropic API key.
4. In VS Code: `Ctrl+Shift+P` → **Python: Select Interpreter** → pick the one in `.venv`.

If `activate` is blocked, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again.

## Run

```powershell
python generate.py --course "LLM Evaluation methods and frameworks" --topic "LLM-as-judge" --level L2
python generate.py --course "LLM Evaluation methods and frameworks" --topic "Ragas metrics" --level L3 --description "an insurance claims assistant" --stack "python,ragas"
```

The statement is saved in `output/`. A run takes 1-3 minutes and costs roughly $0.10-$0.20.
