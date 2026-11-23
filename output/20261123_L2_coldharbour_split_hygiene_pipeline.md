# Coldharbour Split Hygiene Pipeline

## Description
Build a pipeline that deduplicates fault-report Q&A pairs, splits them into train, validation and test sets by source document, writes JSONL files and a manifest, and uploads the splits to S3. Use only the Python standard library plus `boto3`.

## 📋 Instructions

Use the provided template code as the starting point. Implement your solution only within the TODO blocks, and do not modify the project structure, file names, or function signatures. The automated evaluation uses this template to assess your code, so any structural changes may cause your submission to fail evaluation.

## 🎯 Objective
Coldharbour Subsea Repair writes technician Q&A from cable-fault reports. Each report produced several near-paraphrased question and answer pairs, and the team wants to fine-tune a fault-diagnosis assistant on them. The last training run reported 0.94 validation accuracy, but the same model scored 0.71 on a field-technician check set. Priya Raman, the ML lead, suspects that paraphrases of the same fault report landed in both training and validation, so the validation score measured memorisation rather than diagnosis. Each bad run costs about two days of GPU time and a week of re-review. Rebuild the split so that no source document contributes to more than one split, remove duplicate pairs before splitting, record the result in a versioned manifest, and publish the splits to S3.

## 📚 Data Preparation Concepts You'll Practise
- **Deduplication by normalised text** — exact duplicates often differ only in case or spacing, so normalise before you compare.
- **Group-aware splitting** — split by the group key, not by row, so near-copies from one source cannot cross a split boundary.
- **Held-out evaluation preservation** — the test split must stay out of training, including through duplicates.
- **Versioned dataset manifests** — counts and file checksums let a reviewer confirm exactly which data a model saw.

## Your Task
Implement five functions in `pipeline.py`. The source data is in `fault_pairs.db`.

**1. `normalise(text: str) -> str`**
Lowercase the text, replace every run of whitespace (spaces, tabs, newlines) with a single space, then strip leading and trailing spaces.

**2. `deduplicate(conn) -> list[dict]`**
Read `pairs` joined to `reports` on `report_id`, ordered by `pair_id`. A pair is a duplicate if both its normalised question and its normalised answer equal those of an earlier pair (lower `pair_id`). Keep the first occurrence. Return dicts with keys `pair_id` (int), `source_doc_id` (str), `question` (normalised str), `answer` (normalised str), ordered by `pair_id`.

**3. `assign_split(source_doc_id: str) -> str`**
Compute `h = int(hashlib.sha256(source_doc_id.encode("utf-8")).hexdigest()[:8], 16) % 100`. Return `"train"` for 0 to 79, `"validation"` for 80 to 89, `"test"` for 90 to 99.

**4. `build_outputs(records: list[dict], out_dir: str) -> dict`**
Assign each record to a split with `assign_split`. Write `out/train.jsonl`, `out/validation.jsonl` and `out/test.jsonl`. Each line is a JSON object with exactly the keys `pair_id`, `question`, `answer`, in `pair_id` order, written with `json.dumps(obj, ensure_ascii=False)` and a trailing `\n`. Then write `out/manifest.json`:

```json
{
  "dataset_version": "v1",
  "total_pairs": 0,
  "splits": {
    "train": {"pair_count": 0, "source_doc_id_count": 0, "file": "train.jsonl", "sha256": "..."},
    "validation": {"pair_count": 0, "source_doc_id_count": 0, "file": "validation.jsonl", "sha256": "..."},
    "test": {"pair_count": 0, "source_doc_id_count": 0, "file": "test.jsonl", "sha256": "..."}
  }
}
```

`sha256` is the hex digest of the file's bytes as written. `total_pairs` is the count after deduplication. Write the manifest with `indent=2` and `sort_keys=True`. Return the manifest dict. A split with no pairs still gets an entry with a zero count and an empty file.

**5. `upload(out_dir: str, bucket: str)`**
Upload to S3 in `us-east-1`. Create the bucket if it does not exist, enable versioning, and upload exactly these keys:
- `splits/v1/train.jsonl`
- `splits/v1/validation.jsonl`
- `splits/v1/manifest.json`
- `splits/v1/test/test.jsonl`

Do not upload the test file under any other key.

**Sample.** `reports` has report 7 with `source_doc_id` `DOC-A`. `pairs` contains:

| pair_id | report_id | question | answer |
|---|---|---|---|
| 1 | 7 | `"Why  is the  SEGMENT flagged?"` | `"Sheath breach\nat 4.2 km"` |
| 2 | 7 | `"why is the segment flagged?"` | `"sheath breach at 4.2 km"` |
| 3 | 7 | `"Where is the joint?"` | `"Splice box 3"` |

`deduplicate` drops pair 2. Pair 1 becomes `question = "why is the segment flagged?"`, `answer = "sheath breach at 4.2 km"`. Pairs 1 and 3 both have `source_doc_id = "DOC-A"`, so they go to the same split.

## Environment Setup
File Structure:
```
coldharbour_split/
├── fault_pairs.db  # SQLite database, 320 reports and about 1,150 pairs (fixed, do not modify)
└── pipeline.py  # TODO functions: normalise, deduplicate, assign_split, build_outputs, upload
```
Open VS Code: Open the project folder in VS Code and launch the integrated terminal (Terminal → New Terminal).

Use Python 3.11 or later and install boto3 with `pip install boto3`. The database has two tables:
- `reports(report_id INTEGER, source_doc_id TEXT, cable_segment TEXT)`
- `pairs(pair_id INTEGER, report_id INTEGER, question TEXT, answer TEXT)`

AWS: The region is `us-east-1`. Configure the CLI with `aws configure`. Your bucket must be named `coldharbour-ft-v1-<your 12-digit account id>`. Find the account id with `aws sts get-caller-identity --query Account --output text`. Create no other buckets.

AWS Configuration: A temporary AWS account has been provisioned for you. Credentials are already configured in the terminal, so the AWS CLI and boto3 work without extra setup, and you can also use the AWS Management Console. Create every resource with the exact names, region and settings given in this statement: the automated evaluation inspects your account after you submit.

The account has a fixed budget and time limit. Use the smallest instance types that work, avoid long-running jobs, and delete anything you create that the task does not ask you to keep.

## How to Run
```bash
python pipeline.py            # builds out/ locally
python pipeline.py --upload   # also uploads to S3
```
This builds the three JSONL files and the manifest under `out/`, then prints the manifest as JSON. With `--upload`, it also publishes the splits to your bucket.

## How to Evaluate

To evaluate your solution and view the score:

Click the "t" icon on the left side of the VS Code editor, select Evaluate to run the automated evaluation, and view the evaluation score and results once the evaluation is complete.
