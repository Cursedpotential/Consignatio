# CocoIndex upstream examples synthesis

> Byline: OpenAI Codex · 2026-09-06

Reviewed source: `cocoindex-io/cocoindex`, commit
`3b4e54c3b76a3c633a878c6ea1ae9f4ef8d15ce5`, `examples/` tree, on 2026-09-06.
The review covered the catalog instructions, every top-level example's README and primary code
path, and the Rust port catalog. Fixture media and vendored/generated lock data were inventoried but
were not treated as implementation guidance.

## Cross-example conclusions

The reusable v1 shape is `target state = transform(source state)`: `localfs.walk_dir` or a remote
source produces stable keyed items, `mount_each` gives each item an incremental component,
`@coco.fn(memo=True)` protects expensive extraction/model calls, and the target declares rows,
points, relations, messages, or files. Stable paths and IDs matter more than target choice.

For this app, six patterns are combined:

1. `text_embedding`: recursive splitting, per-chunk vectors, exact offsets, semantic query.
2. `multi_codebase_summarization` and the extraction examples: typed per-file LLM metadata and
   explicit aggregation boundaries.
3. `paper_metadata`: keep document metadata separate from chunk embeddings.
4. `entire_session_search`: route multiple source shapes into consistent metadata/chunk records.
5. `files_transform` / `pdf_to_markdown`: local-file incremental processing and file outputs.
6. `sec_edgar_analytics`: multi-format normalization and semantic-plus-lexical retrieval.

Parquet is not a built-in CocoIndex target in the reviewed catalog. The app therefore uses a
memoized, append-only immutable Parquet sink, which CocoIndex's current custom-target guidance
explicitly recommends as the simple option when connector-grade reconciliation is unnecessary.
This also prevents source disappearance from causing a hard delete of derived artifacts.

## Every example and the lesson retained

| Example | Primary pattern | Applied or deferred lesson |
|---|---|---|
| `amazon_s3_embedding` | S3 -> chunks -> vectors | Source connector can change without rewriting transforms; remote source deferred. |
| `audio_to_text` | Memoized transcription | Expensive per-file model work is memoized; audio deferred. |
| `azure_blob_embedding` | Azure source | Same source-adapter lesson; deferred. |
| `bigquery_target` | Typed warehouse target | Portable typed row contracts retained. |
| `code_embedding` | Syntax-aware chunk/vector search | Stable chunk IDs and exact offsets retained; code-specific parsing not needed. |
| `code_embedding_lancedb` | Embedded vector target | File-portable search motivated Parquet + DuckDB instead of a server. |
| `conversation_to_knowledge` | Multi-phase graph + entity resolution | Separate extraction from later resolution; knowledge graph deferred. |
| `csv_to_kafka` | Declarative keyed stream state | Stable keys and explicit upsert/delete semantics informed immutable versions. |
| `docs_to_knowledge_graph` | Typed LLM triples | Machine extraction stays proposal data; graph promotion deferred. |
| `entire_session_search` | Routed heterogeneous text records | Different text formats normalize into one chunk schema. |
| `face_recognition` | GPU-bound image vectors | Images and face analysis explicitly deferred. |
| `files_transform` | Local live file transform | Per-file memoization and local output pattern retained. |
| `gdrive_text_embedding` | Google Drive source | Connector swap remains a future option. |
| `hn_trending_topics` | LLM topic extraction | Topics are structured columns with model provenance. |
| `image_search` | FastAPI + React over Qdrant | FastAPI search boundary retained; image UI deferred. |
| `image_search_colpali` | Multi-vector image retrieval | Multi-vector/image retrieval deferred. |
| `kafka_to_lancedb` | Live stream routing | Streaming source deferred; explicit source identities retained. |
| `manuals_llm_extraction` | Docling + Instructor/Pydantic | Schema-validated structured extraction retained; direct NIM JSON avoids extra adapters. |
| `meeting_notes_graph_falkordb` | Meeting graph | Nested entity graph is a later projection, not an indexing prerequisite. |
| `meeting_notes_graph_neo4j` | Meeting graph + resolution | Review/resolution should follow extraction. |
| `meeting_notes_graph_surrealdb` | Local notes -> graph | Local source and graph-target separation retained. |
| `multi_codebase_summarization` | Per-file and aggregate summaries | Per-document summary boundary and memoization retained. |
| `multi_format_indexing` | Page-level multimodal retrieval | Images and rendered PDF pages explicitly deferred. |
| `oci_object_storage_embedding` | OCI source | Remote source adapter deferred. |
| `paper_metadata` | PDF metadata + vectors | Separate document and chunk datasets retained. |
| `patient_intake_extraction_baml` | Generated structured extraction | Strong schemas retained; BAML code generation not needed. |
| `patient_intake_extraction_dspy` | DSPy structured extraction | Typed validation retained; DSPy optimization deferred. |
| `pdf_embedding` | PDF -> text -> chunks -> vectors | Text-layer PDFs supported; OCR/docling vision work deferred. |
| `pdf_to_markdown` | Incremental file conversion | Extract once per changed PDF and preserve extraction method. |
| `postgres_source` | Database rows as source | Future governed Postgres source can reuse transforms. |
| `product_recommendation` | LLM taxonomy graph | Neutral document types/topics retained; recommendations deferred. |
| `sec_edgar_analytics` | Multi-format hybrid retrieval | Normalize first; semantic retrieval plus bounded lexical reranking retained. |
| `slides_to_speech` | Nested page components | Nested components are useful later for per-page PDF/image processing. |
| `snowflake_target` | Typed warehouse target | Target portability reinforced Parquet schema discipline. |
| `text_embedding` | Baseline pgvector search | Core split/embed/search pattern retained. |
| `text_embedding_lancedb` | Embedded vector DB | Demonstrates portable local target tradeoff. |
| `text_embedding_qdrant` | Managed vector DB | Target can be swapped later without changing source normalization. |
| `text_embedding_turbopuffer` | Serverless vector target | Same separation; deferred. |
| `rust/` | Rust ports of source/target/search patterns | Confirms language-independent v1 model; Python chosen for document tooling. |

## Primary references

- <https://github.com/cocoindex-io/cocoindex/tree/main/examples>
- <https://cocoindex.io/docs/programming_guide/target_state/>
- <https://cocoindex.io/docs/advanced_topics/custom_target_connector/>
- <https://docs.nvidia.com/nim/nemo-retriever/text-embedding/latest/reference.html>
- <https://docs.nvidia.com/nim/large-language-models/2.0.10/get-started/advanced/get-started-nemotron-3.5-lightning.html>
- <https://duckdb.org/docs/lts/sql/data_types/array>
- <https://duckdb.org/docs/current/sql/functions/array>
