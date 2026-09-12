from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from .source_runtime import resolve_source_alias

SUPPORTED_EXTENSIONS = (
    ".csv",
    ".docx",
    ".eml",
    ".htm",
    ".html",
    ".json",
    ".jsonl",
    ".log",
    ".markdown",
    ".md",
    ".pdf",
    ".rst",
    ".rtf",
    ".text",
    ".tsv",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
)


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    return default if raw is None else int(raw)


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    return default if raw is None else float(raw)


@dataclass(frozen=True)
class Settings:
    source_dir: Path
    source_id: str
    output_dir: Path
    nim_base_url: str
    embed_model: str
    summary_model: str
    embed_dimensions: int
    chunk_size: int
    chunk_overlap: int
    summary_max_chars: int
    embed_batch_size: int
    max_concurrency: int
    timeout_seconds: float
    max_retries: int
    max_file_bytes: int = 8 * 1024 * 1024
    max_extracted_chars: int = 1_000_000
    max_chunks_per_file: int = 512
    max_inflight_files: int = 2
    source_registry: Path | None = None
    lock_dir: Path = Path(__file__).resolve().parents[2] / "output" / ".source-locks"

    @classmethod
    def from_env(cls, *, env_file: Path | None = None) -> Settings:
        load_dotenv(dotenv_path=env_file, override=False)
        return cls(
            source_dir=Path(os.getenv("CASEBIBLE_SOURCE_DIR", "./sample_docs")).expanduser(),
            source_id=os.getenv("CASEBIBLE_SOURCE_ID", "casebible").strip() or "casebible",
            output_dir=Path(os.getenv("CASEBIBLE_OUTPUT_DIR", "./output")).expanduser(),
            nim_base_url=os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip(
                "/"
            ),
            embed_model=os.getenv("NIM_EMBED_MODEL", "nvidia/nemotron-3-embed-1b"),
            summary_model=os.getenv("NIM_SUMMARY_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b"),
            embed_dimensions=_int_env("NIM_EMBED_DIMENSIONS", 2048),
            chunk_size=_int_env("CASEBIBLE_CHUNK_SIZE", 2400),
            chunk_overlap=_int_env("CASEBIBLE_CHUNK_OVERLAP", 300),
            summary_max_chars=_int_env("CASEBIBLE_SUMMARY_MAX_CHARS", 48000),
            embed_batch_size=_int_env("NIM_EMBED_BATCH_SIZE", 16),
            max_concurrency=_int_env("NIM_MAX_CONCURRENCY", 4),
            timeout_seconds=_float_env("NIM_TIMEOUT_SECONDS", 90.0),
            max_retries=_int_env("NIM_MAX_RETRIES", 4),
            max_file_bytes=_int_env("INTAKE_MAX_FILE_BYTES", 8 * 1024 * 1024),
            max_extracted_chars=_int_env("INTAKE_MAX_EXTRACTED_CHARS", 1_000_000),
            max_chunks_per_file=_int_env("INTAKE_MAX_CHUNKS_PER_FILE", 512),
            max_inflight_files=_int_env("INTAKE_MAX_INFLIGHT_FILES", 2),
            source_registry=Path(os.environ["INTAKE_SOURCE_REGISTRY"])
            if os.getenv("INTAKE_SOURCE_REGISTRY") else None,
            lock_dir=Path(os.getenv("INTAKE_LOCK_DIR") or str(
                Path(__file__).resolve().parents[2] / "output" / ".source-locks"
            )),
        )

    def resolved(self, base_dir: Path | None = None) -> Settings:
        base = (base_dir or Path.cwd()).resolve()

        def resolve(path: Path) -> Path:
            return path.resolve() if path.is_absolute() else (base / path).resolve()

        source, source_id = resolve_source_alias(
            resolve(self.source_dir), self.source_id,
            resolve(self.source_registry) if self.source_registry else None,
        )
        return Settings(
            **{
                **self.__dict__,
                "source_dir": source,
                "source_id": source_id,
                "output_dir": resolve(self.output_dir),
                "lock_dir": resolve(self.lock_dir),
            }
        )

    def validate(self, *, require_source: bool = True) -> None:
        if require_source and not self.source_dir.is_dir():
            raise ValueError(f"CASEBIBLE_SOURCE_DIR is not a directory: {self.source_dir}")
        if self.source_dir == self.output_dir:
            raise ValueError("Source and output directories must be different")
        if self.output_dir.is_relative_to(self.source_dir):
            raise ValueError("Output directory must not be nested inside the source tree")
        if self.output_dir.exists() and self.output_dir.is_symlink():
            raise ValueError("Refusing to write through a symlinked output directory")
        if self.chunk_size <= 0 or self.chunk_overlap < 0:
            raise ValueError("Chunk size must be positive and overlap must be non-negative")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("Chunk overlap must be smaller than chunk size")
        if self.embed_dimensions <= 0 or self.embed_batch_size <= 0:
            raise ValueError("Embedding dimensions and batch size must be positive")
        if min(self.max_file_bytes, self.max_extracted_chars, self.max_chunks_per_file) < 1:
            raise ValueError("File, extracted text and chunk limits must be positive")
        if not 1 <= self.max_inflight_files <= 8:
            raise ValueError("INTAKE_MAX_INFLIGHT_FILES must be between 1 and 8")

    @property
    def state_dir(self) -> Path:
        # Deliberately distinct from ccc's ~/.cocoindex_code state and process namespace.
        return self.output_dir / ".casebible-corpus" / "cocoindex"
