# Sources for Lantern Mill Nightly Embedding Sync

- Area: cost and latency optimization
- Platform: openai
- Task shape: Build a small end-to-end pipeline (load, transform, decide, report)
- Material: Tables: products.csv with columns sku, name, material, colour, fit_notes, last_exported, plus the stored-hash dictionary saved from the previous run

## Inspired by
Inspired by [2] Best Vector Databases in 2026 (https://www.firecrawl.dev/blog/best-vector-databases), which builds an embedding index over product text with text-embedding-3-small, and [4] RAG advanced tips (https://billtcheng2013.medium.com/retrieval-augmented-generation-advanced-6ebcc4fa4914), which advises batching embedding requests and re-embedding only changed content.

## Concepts tested
- Embedding reuse: hash the embedding input and reuse stored vectors for unchanged text
- Batching: send up to 100 texts per embedding request

## Trap
Trap: a naive sync hashes the whole CSV row, so the last_exported column changes every night and every row is re-embedded. Handle it by hashing only the text returned by text_for_embedding.

## How it is graded
Hidden tests check text_for_embedding output strings exactly, check plan_sync lists and their order on fixture rows, and check run_sync counts and api_calls with a scripted embed_fn that records its calls, including the batch boundaries at 100 and 250 rows and the stored dictionary contents afterwards.

## Searches
- fashion apparel ecommerce product catalog LLM cost reduction case study gpt-4o-mini embeddings
- apparel retailer postmortem OpenAI API latency timeout product attribute extraction
- clothing catalog enrichment batch embeddings caching text-embedding-3-small production deployment

## Pages found
- [Ecommerce LLM Strategy 2026: Engine Optimization Guide](https://wearepresta.com/ecommerce-llm-the-2026-guide-to-engine-optimization-geo)
- [Best Vector Databases in 2026: A Complete Comparison Guide](https://www.firecrawl.dev/blog/best-vector-databases)
- [How to Build AI Agents Powered by Private Knowledge Bases | MindStudio](https://www.mindstudio.ai/blog/build-ai-agents-powered-private-knowledge-bases)
- [Medium](https://billtcheng2013.medium.com/retrieval-augmented-generation-advanced-6ebcc4fa4914)
- [Semantic Customer Embeddings - Harvard Business School](https://www.hbs.edu/ris/Publication%20Files/27-039_5db3f66b-106a-46f1-a042-490792bd52ed.pdf)
