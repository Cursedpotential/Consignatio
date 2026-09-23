"""Byline: Codex | 2026-09-20. Append-only, metadata-only catalog generations."""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import io
import json
import sys
import uuid
from pathlib import Path

from core import VersionIndex, digest, integer, occurrence, source_sha1, stable_id, work_item
from io_utils import B2, Postgres, records, sha256_file, write_records

SOURCES = {
    "occurrences": "SELECT * FROM raw_duck.intake_catalog_fs_20260917",
    "b2_legacy": "SELECT * FROM raw_duck.b2_objects",
    "hash_bridge": "SELECT c.md5,c.size,c.b2_key,b.sha1 FROM raw_duck.b2_content c LEFT JOIN raw_duck.b2_objects b ON b.key=c.b2_key AND b.size=c.size",
    "legacy_version_ids": "SELECT key,size,b2_id,md5 FROM raw_duck.vault_objects WHERE sha1 IS NULL OR sha1 !~ '^[0-9A-Fa-f]{40}$'",
    "r2_occurrences": "SELECT * FROM raw_duck.r2_files",
    "alternative_route": "SELECT v.md5,v.size,v.canonical_key,k.dest_key FROM raw_duck.vault_content_v0 v JOIN raw_duck.vault_keep_v7 k ON k.canonical_key=v.canonical_key AND k.size=v.size",
    "recovery_manifest": "SELECT * FROM raw_duck.recovery_manifest_20260917",
    "recovery_quality": "SELECT * FROM raw_duck.recovery_integrity_20260916",
    "atomic_units": "SELECT * FROM raw_duck.atomic_units",
    "atomic_members": "SELECT * FROM raw_duck.atomic_unit_members",
    "export_units": "SELECT * FROM raw_duck.export_units_v1",
    "export_members": "SELECT * FROM raw_duck.export_unit_members_v1",
    "vault_units": "SELECT * FROM raw_duck.vault_units_v2",
    "integrity_holds": "SELECT * FROM raw_duck.integrity_hold",
}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def save_json(path, data):
    data.setdefault('byline','Codex | 2026-09-20')
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)


def emit(event, **data):
    print(json.dumps({"event": event, **data}), flush=True)


def capture(args):
    root = Path(args.generation)
    root.mkdir(parents=True, exist_ok=False)
    manifest = {"generation_id": str(uuid.uuid4()), "contract_version": 1, "started_at": now(),
                "status": "collecting", "sources": {}, "objects": {}, "content_reads": 0,
                "source_mutations": 0, "bas_decisions": 0, "r2_retirements": 0}
    save_json(root / "started.json", manifest)
    b2 = B2(args.config)
    pg = Postgres()
    for name, sql in SOURCES.items():
        started = now()
        count = write_records(root / (name + ".parquet"), pg.rows(sql))
        manifest["sources"][name] = {"rows": count, "query": sql, "started_at": started, "ended_at": now(),
                                       "sha256": sha256_file(root / (name + ".parquet"))}
        emit("source_captured", name=name, rows=count)
    maps = []
    for account in ("salemnet", "salem85"):
        path = f"/data/consignatio/migrations/gdrive-copy-20260913/native-export-{account}-idmap.tsv"
        text = pg.remote_read(path)
        for row in csv.reader(io.StringIO(text), delimiter="\t"):
            if len(row) >= 6:
                maps.append(dict(zip(("source_id", "native_path", "office_path", "pdf_path", "mime", "modtime"), row[:6]),
                                 source="gdrive/" + account, receipt_path=path))
    write_records(root / "native_export_maps.parquet", maps)
    visible_ids = set()
    def visible_rows():
        for row in b2.files():
            visible_ids.add(row["fileId"])
            yield row
    manifest["objects"]["visible_rows"] = write_records(root / "b2_visible.parquet", visible_rows())
    emit("visible_captured", rows=len(visible_ids))
    version_visible = set()
    def version_rows():
        for row in b2.files(versions=True):
            visible = row["fileId"] in visible_ids
            if visible:
                version_visible.add(row["fileId"])
            yield {"bucket": b2.bucket["bucketName"], "key": row["fileName"], "file_id": row["fileId"],
                   "action": row["action"], "size": row["contentLength"], "sha1": source_sha1(row),
                   "visible": visible, "upload_timestamp_ms": row["uploadTimestamp"], "metadata": row.get("fileInfo", {}),
                   "provider_record": row}
    manifest["objects"]["version_rows"] = write_records(root / "object_versions.parquet", version_rows())
    manifest["objects"]["visible_versions_missing"] = len(visible_ids - version_visible)
    unfinished = []
    cursor = {"bucketId": b2.bucket["bucketId"], "maxFileCount": 100}
    while True:
        page = b2.call("b2_list_unfinished_large_files", cursor)
        for f in page["files"]:
            parts = []; part_cursor = {"fileId": f["fileId"], "maxPartCount": 1000}
            while True:
                result = b2.call("b2_list_parts", part_cursor); parts.extend(result["parts"])
                if not result.get("nextPartNumber"):
                    break
                part_cursor["startPartNumber"] = result["nextPartNumber"]
            unfinished.append({"file": f, "parts": parts})
        if not page.get("nextFileId"):
            break
        cursor["startFileId"] = page["nextFileId"]
    write_records(root / "unfinished.parquet", unfinished)
    manifest["ended_at"] = now()
    manifest["status"] = "captured" if version_visible == visible_ids else "inconsistent_listing"
    manifest["lifecycle_rules_observed"] = b2.bucket.get("lifecycleRules")
    manifest["files"] = {p.name: sha256_file(p) for p in sorted(root.glob("*.parquet"))}
    save_json(root / "capture.json", manifest)
    emit("capture_complete", status=manifest["status"], generation_id=manifest["generation_id"])
    if manifest["status"] != "captured":
        raise RuntimeError("Visible/version listings diverged; publication prohibited")


def build(args):
    root = Path(args.generation)
    capture = json.loads((root / "capture.json").read_text(encoding="utf-8"))
    if capture["status"] != "captured":
        raise RuntimeError("Generation has no complete capture")
    for name, expected in capture["files"].items():
        if sha256_file(root / name) != expected:
            raise RuntimeError("Capture fingerprint differs: " + name)
    index = VersionIndex(records(root / "object_versions.parquet"))
    old = {r["key"]: r for r in records(root / "b2_legacy.parquet")}
    bridge = collections.defaultdict(set)
    for r in records(root / "hash_bridge.parquet"):
        if digest(r["md5"], 32) and digest(r.get("sha1"), 40):
            bridge[(r["md5"].lower(), integer(r["size"]))].add(r["sha1"].lower())
    by_md5 = collections.defaultdict(set)
    for r in records(root / "legacy_version_ids.parquet"):
        version = index.by_id.get(r["b2_id"])
        key = r["key"] if r["key"].startswith("consignatio/") else "consignatio/vault/v1/" + r["key"]
        if version and version["key"] == key and version["size"] == r["size"] and digest(r["md5"], 32):
            by_md5[(r["md5"].lower(), integer(r["size"]))].add(version["file_id"])
    route = collections.defaultdict(set)
    for r in records(root / "alternative_route.parquet"):
        route[(r["md5"], integer(r["size"]))].add(r["dest_key"])
    work = []; counts = collections.Counter(); seen_occ = set(); native_by_id = {}
    def links():
        for raw in records(root / "occurrences.parquet"):
            link = occurrence(raw, index)
            if link["occurrence_id"] in seen_occ:
                raise RuntimeError("Duplicate source occurrence identity")
            seen_occ.add(link["occurrence_id"])
            alternatives = sorted(route.get((raw.get("md5"), integer(raw.get("size"))), []))
            link["alternative_route_keys"] = alternatives
            link["route_status"] = "different_claims" if alternatives and raw.get("vault_key") not in alternatives else "compatible_or_unavailable"
            counts[(link["source"], link["state"])]+=1
            if "native_export_linkage_conflict" in link["quality_flags"]:
                native_by_id[(raw["source"], raw["source_id"])] = link
            if link["state"] not in ("visible_exact_path", "visible_exact_elsewhere"):
                kind = "relink_historical_version" if link["state"] == "historical_exact" else "native_export_linkage_conflict" if "native_export_linkage_conflict" in link["quality_flags"] else "unresolved_occurrence"
                work.append(work_item(kind, link["occurrence_id"], raw["source"], "high" if kind != "unresolved_occurrence" else "review",
                     link["state"], {"occurrence_id": link["occurrence_id"], "source_id": raw.get("source_id"),
                     "source_path": raw.get("path"), "version_ids": link["version_ids"], "disposition": raw.get("disposition"),
                     "quality_flags": link["quality_flags"]},
                     "Resolve B2 version linkage before source acquisition" if kind == "relink_historical_version" else "Inspect source metadata and receipts by source ID; do not re-pull yet"))
            yield link
    nlinks = write_records(root / "occurrence_links.parquet", links())
    emit("links_built", rows=nlinks)
    native_results = []
    for mapping in records(root / "native_export_maps.parquet"):
        source = mapping["source"]; results = {}
        for representation in ("office", "pdf"):
            key = "consignatio/intake/raw-dedupe/v1/source-buckets/" + source + "/" + mapping[representation + "_path"]
            previous = old.get(key)
            state, basis, ids = index.resolve(key, previous.get("sha1") if previous else None, previous.get("size") if previous else None)
            results[representation] = {"recorded_export_key": key, "state": state, "basis": basis, "version_ids": ids}
        result = {**mapping, "representations": results, "status": "metadata_linkage_only", "source_native_retained": "not_proven"}
        native_results.append(result)
        work.append(work_item("native_source_metadata_check", [source, mapping["source_id"]], source, "high",
                             "Verify original native source and receipt-linked export representations", result,
                             "Read provider metadata by file ID; preserve native source and both export claims"))
    write_records(root / "native_export_reconciliation.parquet", native_results)
    observations=[];bas_candidates=[]
    native_map={(r['source'],r['source_id']):r for r in native_results}
    observed=set()
    for probe_dir in getattr(args,'probe',[]):
        for r in records(Path(probe_dir)/'google_metadata.parquet'):
            identity=(r['source'],r['source_id'])
            if identity in observed:raise ValueError('Repeated provider observation identity')
            if identity not in native_map:raise ValueError('Provider observation not in captured source map')
            observed.add(identity);observations.append(r)
            metadata=r.get('metadata') or {}
            if r['state']=='metadata_observed' and metadata.get('trashed') is False and metadata.get('mimeType','').startswith('application/vnd.google-apps.'):
                bas_candidates.append({'family_id':stable_id('native',*identity),'source':r['source'],'source_id':r['source_id'],
                    'bas1_candidate':{'kind':'source_native_representation','provider_id':r['source_id'],'evidence':metadata,
                        'reason':'Live provider reports an accessible, non-trashed native item with timestamps and version'},
                    'bas2_candidate':None,'complementary_representations_to_review':native_map[identity]['representations'],
                    'status':'provisional_metadata_only','original_authorship':'not_proven','content_completeness':'not_assessed',
                    'retirement_status':'not_cleared','observed_at':r['observed_at']})
    write_records(root/'source_observations.parquet',observations)
    write_records(root/'bas_candidates.parquet',bas_candidates)
    r2_counts = collections.Counter()
    def r2_links():
        for raw in records(root / "r2_occurrences.parquet"):
            key = (str(raw.get("md5") or "").lower(), integer(raw.get("size")))
            hashes = bridge.get(key, set()); ids = set(); basis = "none"
            if len(hashes) == 1:
                for h in hashes:
                    ids.update(v["file_id"] for v in index.by_hash.get((h,key[1]), []))
                if ids: basis = "catalog_md5_to_b2_sha1_size"
            if by_md5.get(key):
                ids.update(by_md5[key]); basis = "catalog_md5_version_id" if basis == "none" else basis
            state = "visible_catalog_link" if any(index.by_id[i]["visible"] for i in ids) else "historical_catalog_link" if ids else "ambiguous_hash_bridge" if len(hashes)>1 else "unresolved"
            r2_counts[(raw["bucket"], state)]+=1
            result = {"occurrence_id": stable_id("r2",raw["bucket"],raw["path"]), "source_record": raw,
                      "state":state,"match_basis":basis,"version_ids":sorted(ids),"retirement_status":"not_cleared"}
            if state not in ("visible_catalog_link",):
                work.append(work_item("r2_identity_review", result["occurrence_id"], "r2/"+raw["bucket"], "review",
                             state, result, "Reuse SHA-256 ledger receipts; verify current source metadata and package membership"))
            yield result
    nr2 = write_records(root / "r2_links.parquet", r2_links())
    for r in records(root / "recovery_manifest.parquet"):
        src = index.resolve(r["src_key"],r["sha1"],r["size"])
        dst = index.resolve(r["dest_key"],r["sha1"],r["size"])
        work.append(work_item("recovery_quality_and_provenance", r["src_key"], "recovery", "high" if r["status"] != "ok" else "review",
                   "Legacy recovery assessment is scope-limited; ok is not original-completeness proof",
                   {**r,"source_state":src[0],"destination_state":dst[0]},
                   "Compare recovery provenance, embedded metadata, structural completeness and package membership before BAS"))
    for r in records(root / "atomic_units.parquet"):
        work.append(work_item("package_completeness", r["unit_id"], r.get("source"), "high",
                   "Atomic root preserved; current member completeness unverified", r,
                   "Reconcile every member and sidecar to retained versions; preserve package boundary"))
    nwork = write_records(root / "recovery_worklist.parquet", work)
    # A private, convenient item-level CSV; JSON evidence is preserved in its entirety.
    with (root / "recovery_worklist.csv").open("x",encoding="utf-8",newline="") as stream:
        writer=csv.writer(stream); writer.writerow(["item_id","kind","source","priority","reason","next_step","evidence"])
        for r in work: writer.writerow([r[k] for k in ("item_id","kind","source","priority","reason","next_step")]+[json.dumps(r["evidence"],ensure_ascii=False)])
    metrics = {"generation_id":capture["generation_id"],"built_at":now(),"occurrence_rows":nlinks,"work_items":nwork,
               "occurrence_states":[[*k,v] for k,v in sorted(counts.items())],"r2_states":[[*k,v] for k,v in sorted(r2_counts.items())],
               "native_maps":len(native_results),"r2_rows":nr2,"source_observations":len(observations),
               "provisional_bas1_candidates":len(bas_candidates),"retirement_cleared":0,"bas_decisions":0,
               "checks":{"source_occurrence_conservation":nlinks==capture["sources"]["occurrences"]["rows"],
                         "unique_occurrence_ids":len(seen_occ)==nlinks,"unique_work_item_ids":len({r["item_id"] for r in work})==nwork,
                         "r2_row_conservation":nr2==capture["sources"]["r2_occurrences"]["rows"],
                         "unique_native_source_ids":len({(r["source"],r["source_id"]) for r in native_results})==len(native_results),
                         "visible_version_conservation":capture["objects"]["visible_versions_missing"]==0}}
    if not all(metrics["checks"].values()): raise RuntimeError("Generation validation failed")
    metrics["files"]={p.name:sha256_file(p) for p in sorted(root.glob("*.parquet"))}
    metrics["status"]="validated_metadata_reconciliation"
    save_json(root / "validated.json",metrics)
    emit("build_complete", **{k:metrics[k] for k in ("occurrence_rows","work_items","native_maps","status")})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation",choices=("capture","build"))
    parser.add_argument("--generation",required=True)
    parser.add_argument("--config",default=str(Path.home()/"scoop/apps/rclone/current/rclone.conf"))
    parser.add_argument("--probe",action="append",default=[],help="Explicit bounded provider probe output to include")
    args=parser.parse_args()
    try: globals()[args.operation](args)
    except Exception as exc:
        # Do not emit HTTP responses, environment values, or credentials.
        emit("failed",error=type(exc).__name__,detail=str(exc)[:400]); return 1
    return 0


if __name__=="__main__":
    sys.exit(main())
