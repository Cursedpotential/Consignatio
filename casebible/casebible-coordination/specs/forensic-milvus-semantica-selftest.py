#!/usr/bin/env python3
"""
forensic-milvus-semantica-selftest.py
Byline: Claude Code (PIPELINE lane) · Opus 4.8 · 2026-07-01

Offline, $0, NO server + NO pymilvus/neo4j-install self-test for the reversible
build pass: evidence/milvus_forensic.py (forensic collection schema defs) +
evidence/semantica_wiring.py (seed-first hybrid wiring). Validates field-spec
correctness, the dim/contract match (bge-m3 1024-d), court-safety gate coverage,
that create() defaults to a no-server PLAN, and that NO secrets are inlined.

    python forensic-milvus-semantica-selftest.py
Exit 0 iff all assertions pass. Save stdout beside this file.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(r"E:\AI_Workspace\Projects\the-platform-workspace\Agno-MCP-Platform")
sys.path.insert(0, str(REPO))

from evidence import milvus_forensic as mf          # noqa: E402
from evidence import semantica_wiring as sw          # noqa: E402

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


GATE_FIELDS = {"review_status", "safe_for_legal_use", "requires_human_review",
               "bias_caution", "sensitivity_tier", "data_tier"}


def main() -> int:
    print("=== milvus_forensic + semantica_wiring — offline self-test (no server, $0) ===\n")

    print("1) every forensic collection spec validates + carries a dense vector at the contract dim:")
    for spec in mf.all_specs():
        errs = spec.validate()
        check(f"{spec.name} validates", errs == [], str(errs))
        dense = [f for f in spec.fields if f.dtype == "float_vector"]
        check(f"{spec.name} has exactly 1 dense vector", len(dense) == 1)
        check(f"{spec.name} dense dim == EMBED_TEXT_DIM ({mf.EMBED_TEXT_DIM})",
              bool(dense) and dense[0].dim == mf.EMBED_TEXT_DIM)
        check(f"{spec.name} dim is 1024 (bge-m3 contract)", mf.EMBED_TEXT_DIM == 1024)
        pk = [f for f in spec.fields if f.is_primary]
        check(f"{spec.name} single primary key", len(pk) == 1)

    print("\n2) court-safety gate fields present on EVERY forensic collection:")
    for spec in mf.all_specs():
        names = {f.name for f in spec.fields}
        missing = GATE_FIELDS - names
        check(f"{spec.name} carries all gate fields", missing == set(), f"missing={missing}")

    print("\n3) create_forensic_collections() defaults to a NO-SERVER plan:")
    plan = mf.create_forensic_collections(dry_run=True)
    check("dry_run flag true", plan["dry_run"] is True)
    check("no collections created in dry-run", plan["created"] == [])
    check("zero validation errors across specs", plan["validation_errors"] == [])
    check("plan lists all 3 forensic collections",
          {c["name"] for c in plan["collections"]}
          == {"forensic_records", "forensic_findings", "forensic_patterns"})
    check("index plan uses COSINE on dense", plan["index_params"]["dense"]["metric_type"] == "COSINE")
    check("plan points at MILVUS_ADDRESS contract", "19530" in plan["milvus_uri"])

    print("\n4) hybrid toggle is a definition, not a hardcode (default dense-only):")
    check("sparse BM25 off by default", plan["hybrid_sparse_bm25"] is False)
    check("no sparse field when hybrid off",
          all(not any(f.dtype == "sparse_vector" for f in s.fields) for s in mf.all_specs()))

    print("\n5) Semantica wiring targets OUR infra, seed-first, Graphiti-as-writer:")
    w = sw.full_wiring()
    check("mode = seed_first_hybrid", w["mode"] == "seed_first_hybrid")
    check("graph writer stays graphiti", w["graph_writer"] == "graphiti"
          and w["graph_store"]["writer"] == "graphiti" and w["graph_store"]["write_via_graphiti"] is True)
    check("neo4j role is read/derive (not writer)", w["graph_store"]["role"] == "read_derive")
    check("vector dim locked to ours (1024, not Semantica's 768 default)",
          w["vector_store"]["dimension"] == mf.EMBED_TEXT_DIM == 1024)
    check("milvus host/port derived from ours",
          "100.119.96.29" in w["vector_store"]["milvus_host"] and w["vector_store"]["milvus_port"] == 19530)
    check("Semantica targets the forensic_* collections",
          set(w["vector_store"]["target_collections"])
          == {"forensic_records", "forensic_findings", "forensic_patterns"})
    check("seed-first from PG ontology tables",
          "analysis.behavior_category" in w["seed"]["ontology_tables"] and w["seed"]["extend_not_replace"] is True)
    check("sealed lexicon skipped in seed", w["seed"]["seal_policy"] == "skip_sealed_lexicon")
    check("deploy is APPROVALS-gated", "gated" in w["deploy"].lower())

    print("\n6) NO secrets inlined — passwords/tokens referenced by ENV NAME only:")
    import inspect
    src = inspect.getsource(sw) + inspect.getsource(mf)
    leaked = [needle for needle in ("graphiti-7235e9db38e03a11", "graphiti-dev-password") if needle in src]
    check("no known secret literal in source", leaked == [], f"leaked={leaked}")
    check("secrets referenced via env names",
          set(sw.secrets_referenced()) == {"MILVUS_TOKEN", "NEO4J_PASSWORD", "GRAPHITI_MCP_URL"})
    check("password fields are *_env pointers",
          w["vector_store"]["milvus_password_env"] == "MILVUS_TOKEN"
          and w["graph_store"]["password_env"] == "NEO4J_PASSWORD")

    print(f"\n=== RESULT: {PASS} passed, {FAIL} failed ===")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
