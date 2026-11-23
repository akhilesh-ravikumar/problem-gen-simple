# Lantern Mill Nightly Embedding Sync

## Description
Build a sync step that embeds only the product rows whose embedding text has changed since the last run, and sends those texts to the embeddings API in batches of at most 100. Hash only the embedding text, never the whole CSV row.

## 📋 Instructions

Use the provided template code as the starting point. Implement your solution only within the TODO blocks, and do not modify the project structure, file names, or function signatures. The automated evaluation uses this template to assess your code, so any structural changes may cause your submission to fail evaluation.

## 🎯 Objective
Lantern Mill Workwear sells hi-vis clothing, boilerwear and safety boots online and to local councils. Each night its export job writes `products.csv` with about 4,200 SKUs, and the search team re-embeds the whole catalogue with `text-embedding-3-small` so semantic search stays current. Most rows have not changed, but the job still embeds every row, which costs money and takes over an hour. The export also adds a `last_exported` value to every row, so a naive change check would mark every row as changed. Write the planning and sync code that embeds only rows whose embedding text actually changed, batches the requests, and reports the counts.

## 📚 LLM Cost and Latency Concepts You'll Practice
- **Embedding reuse**: Store a hash of each embedding input and skip re-embedding when the hash has not changed.
- **Input normalisation**: Build the embedding text in one deterministic function so that spacing or case differences do not trigger new embeddings.
- **Batching**: Send up to 100 texts per embeddings request to cut round trips and total run time.
- **Change planning**: Separate the decision of what to embed from the act of embedding, so the plan can be tested without any API call.
- **Idempotent state updates**: Update stored hashes only after a chunk succeeds, so a failed run never records vectors that were not created.

## Your Task
Complete three functions. Each depends on the one before it.

**1. `text_for_embedding(row: dict) -> str`** in `workwear/prep.py`

Take the values of `name`, `material`, `colour` and `fit_notes`, in that order. A missing key counts as an empty value. Strip each value and skip values that are empty after stripping. Join the remaining values with `' | '`. Collapse every run of whitespace to a single space, then lowercase the result. Never use `last_exported`.

**2. `plan_sync(rows: list[dict], stored: dict[str, str]) -> dict`** in `workwear/prep.py`

For each row in CSV order, compute the SHA-256 hex digest (lowercase, 64 characters) of the UTF-8 bytes of `text_for_embedding(row)`. If the row's `sku` is not a key in `stored`, or `stored[sku]` differs from the digest, add the `sku` to `to_embed`. Otherwise add it to `unchanged`. Both lists keep CSV order. Do not modify `stored`. Return `{'to_embed': [...], 'unchanged': [...]}`.

**3. `run_sync(rows: list[dict], stored: dict[str, str], embed_fn, batch_size: int = 100) -> dict`** in `workwear/sync.py`

Call `plan_sync(rows, stored)` once. Build the list of texts for the `to_embed` rows, in that order, and split it into chunks of at most `batch_size`. For each chunk, in order, call `embed_fn(chunk_texts)` once. Never call `embed_fn` with an empty list. When a call returns, set `stored[sku]` to the digest for each row in that chunk. If `embed_fn` raises, let the exception propagate. Chunks that finished earlier keep their new digests, and the remaining rows keep their old ones. Return `{'embedded': int, 'skipped': int, 'api_calls': int}`, where `embedded` is the number of rows embedded, `skipped` is the number of unchanged rows, and `api_calls` is the number of `embed_fn` calls made.

**Watch out:** the hash must cover only the output of `text_for_embedding`. Hashing the full row, including `last_exported`, marks every row as changed on every run.

Sample for `text_for_embedding`:
```python
text_for_embedding({'name': 'Hi-Vis  Parka', 'material': 'Polyester', 'colour': '', 'fit_notes': 'Runs large', 'last_exported': '2025-01-03'})
# 'hi-vis parka | polyester | runs large'
```

Sample for `run_sync`: 250 changed rows and 10 unchanged rows return `{'embedded': 250, 'skipped': 10, 'api_calls': 3}`. The three calls receive 100, 100 and 50 texts.

## Environment Setup
File Structure:
```
lantern_mill_sync/
├── products.csv          # Nightly export, 4,200 rows, columns sku,name,material,colour,fit_notes,last_exported (fixed, do not modify)
├── stored_hashes.json    # JSON object mapping sku to digest from the previous run (fixed, do not modify)
├── main.py               # Loads the files, calls run_sync with the real API, saves stored_hashes.json (fixed, do not modify)
├── workwear/
│   ├── __init__.py       # Empty package marker (fixed, do not modify)
│   ├── prep.py           # TODO: text_for_embedding, plan_sync
│   └── sync.py           # TODO: run_sync
```
Open VS Code: Open the project folder in VS Code and launch the integrated terminal (Terminal → New Terminal).

Use Python 3.11 or later and install the client library:
```bash
pip install openai
```
Set the proxy and key before running, using the values your course admin gave you:
```bash
export OPENAI_BASE_URL="<company proxy URL>"
export OPENAI_API_KEY="<your key>"
```
Use only the standard library in `prep.py` and `sync.py`. Do not import `openai` there. The graders replace `embed_fn` with a scripted function.

OpenAI Configuration: OpenAI is used as the LLM provider, with the API key read from the OPENAI_API_KEY environment variable. Use the gpt-4o-mini chat model and, where embeddings are needed, the text-embedding-3-small embedding model. Route all calls through the proxy gateway below:

🔗 Proxy URL: https://llmgateway-lms.tekstac.com/v1

```python
client = OpenAI(
    api_key=api_key,
    base_url="https://llmgateway-lms.tekstac.com/v1",
)
```

## How to Run
```bash
python main.py
```
This loads `products.csv` and `stored_hashes.json`, runs `run_sync` with `text-embedding-3-small`, saves the updated hashes back to `stored_hashes.json`, and prints `embedded`, `skipped` and `api_calls`.

## How to Evaluate

To evaluate your solution and view the score:

Click the "t" icon on the left side of the VS Code editor, select Evaluate to run the automated evaluation, and view the evaluation score and results once the evaluation is complete.
