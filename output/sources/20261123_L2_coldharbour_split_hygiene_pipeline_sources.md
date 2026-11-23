# Sources for Coldharbour Split Hygiene Pipeline

- Area: Fine-tuning data preparation
- Platform: aws
- Task shape: Build a small end-to-end pipeline (load, transform, decide, report)
- Material: SQLite database with tables reports(report_id, source_doc_id, cable_segment) and pairs(pair_id, report_id, question, answer)

## Inspired by
https://techbytes.app/posts/full-fine-tuning-fft-on-sagemaker-ai-serverless-model-customization (a 90/5/5 train, validation and test split over a large corpus)

## Concepts tested
- Deduplication by normalised text
- Group-aware train, validation and test splitting
- Held-out evaluation preservation
- Versioned dataset manifest with counts and checksums

## Trap
Randomly splitting rows by pair_id looks correct and gives the expected ratio, but paraphrases from the same report then appear in both train and validation, inflating validation scores. The naive split also leaks test rows into training through duplicates that differ only in case or spacing.

## How it is graded
Hidden tests check that no source_doc_id appears in two splits, compare split membership of every pair_id against the hash rule, verify the deduplicated counts and manifest sha256 values, and inspect S3 versioning and the object key layout.

## Searches
- fine-tuning LLM training data JSONL validation postmortem healthcare clinical notes PII leak Amazon Bedrock
- case study fine-tuning customer support chatbot on AWS SageMaker dataset deduplication train validation leakage
- Amazon Bedrock custom model fine-tuning data preparation insurance claims intent classification JSONL format lessons learned

## Pages found
- [Reinforcement Fine-Tuning in Amazon Bedrock: A Practical Guide](https://tutorialsdojo.com/reinforcement-fine-tuning-in-amazon-bedrock-a-practical-guide-for-enterprise-ai)
- [Full Fine-Tuning (FFT) on SageMaker AI Serverless Model Customization | Tech Bytes](https://techbytes.app/posts/full-fine-tuning-fft-on-sagemaker-ai-serverless-model-customization)
- [News · The Tech Gazette](https://techgazette.com.br/section/news)
- [Model Fine-Tuning Support in SageMaker Python SDK V3 · aws/sagemaker-python-sdk · Discussion #5364 · GitHub](https://github.com/aws/sagemaker-python-sdk/discussions/5364)
- [Medium](https://medium.com/@maghonei/fine-tuning-modernbert-on-amazon-sagemaker-for-intent-classification-router-agent-use-case-bd9728476f8b)
