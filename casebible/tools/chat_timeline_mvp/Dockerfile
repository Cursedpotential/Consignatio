# Byline: Claude Code · Opus 5 · 2026-09-18
# chat_timeline_mvp runner: DuckDB (extraction engine) + pyarrow + pydantic (Probata backup parsers) + httpx (Surreal/Weaviate).
FROM python:3.12-slim
RUN pip install --no-cache-dir duckdb==1.4.3 pyarrow pydantic httpx pytz
WORKDIR /app
