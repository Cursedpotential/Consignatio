# Coco super index — backend service image.
# Byline: Claude Code · Opus 5 · 2026-09-22
#
# Runs next to the data on ovh-files (owner rule: nothing runs on the desktop). The API
# binds 0.0.0.0:8765 inside the container; the compose file publishes it on the tailnet
# address only, never on a public interface.
#
# Tesseract is NOT installed: the image lane (INTAKE_IMAGES_*) is a separate app with its
# own collection and is not part of this service's text index. Adding OCR here would put a
# ~200 MB dependency in an image that does not call it.

FROM ghcr.io/astral-sh/uv:0.9.7-python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dependency layer first so a source edit does not re-resolve the lock.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY src ./src
COPY main.py ./main.py
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:${PATH}" \
    CASEBIBLE_OUTPUT_DIR=/var/lib/superindex/output \
    INTAKE_LOCK_DIR=/var/lib/superindex/state/.source-locks \
    TMPDIR=/var/lib/superindex/spool

# Non-root: the service only ever reads the bucket and writes its own derived output.
RUN useradd --system --create-home --uid 10001 superindex \
    && mkdir -p /var/lib/superindex/output /var/lib/superindex/state /var/lib/superindex/spool \
    && chown -R superindex:superindex /var/lib/superindex
USER superindex

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=4).status==200 else 1)"

CMD ["uvicorn", "casebible_index.api:app", "--host", "0.0.0.0", "--port", "8765"]
